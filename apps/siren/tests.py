# SIREN/DIANA basic functionality testing framework
#
# -[x] Upload to Orthanc
# -[x] Anonymize and tag in Orthanc
# -[x] Email via SMTP
# -[x] Distribute email by tag/subscription
# -[x] Index  to Splunk
# -[x] Watch directory for files
# -[ ] Watch orthanc for studies
# -[ ] Stage 1: Automatic upload, anonymize, sign from watched directory
# -[ ] Stage 2: Automatic index and distribute email from watched orthanc
# -[ ] Execute both stages


import os
import time
import logging
import shutil
import io
from contextlib import redirect_stdout
from multiprocessing import Process
from datetime import datetime, timedelta
from interruptingcow import timeout
from crud.manager import EndpointManager
from crud.endpoints import Splunk
from diana.utils.endpoint import Watcher, Trigger
from wuphf.endpoints import SmtpMessenger
from wuphf.daemons import Dispatcher
from wuphf.daemons.dispatcher import Transport
from diana.apis import Orthanc, ObservableOrthanc, DcmDir, ObservableDcmDir
from diana.dixel import Dixel, ShamDixel
from diana.utils.dicom import DicomLevel as DLV, DicomEventType as DEV
from crud.utils import deserialize_dict
from wuphf.cli.string_descs import *

from handlers import handle_upload_file, handle_upload_dir, handle_upload_zip, handle_notify_study

# Retrofit DIANA apis to crud manager
from crud.abc import Serializable
Serializable.Factory.registry["ObservableOrthanc"] = ObservableOrthanc
Serializable.Factory.registry["Dixel"] = Dixel

# CONFIG
_services          = "@./siren_services.yaml"
os.environ["ORTHANC_PASSWORD"] = "passw0rd!"  # Set defaults
os.environ["SPLUNK_PASSWORD"] = "passw0rd!"

salt               = "Test+Test+Test"
fkey               = b'o-KzB3u1a_Vlb8Ji1CdyfTFpZ2FvdsPK4yQCRzFCcss='
messenger_name     = "gmail:"   # Use "gmail:" or "local_smtp"
splunk_index       = "testing" # Set to "dicom" for production or "testing"
msg_t              = """to: {{ recipient.email }}\nfrom: {{ from_addr }}\nsubject: Test Message\nThis is the message text: "{{ item.msg_text }}"""""
# msg_t = "@/notify.txt.j2"

# TESTING CONfIG
test_resources_dir = "./resources"
test_sample_zip    = "resources/test.zip"
test_sample_dir    = "~/data/test"
test_email_addr1   = os.environ.get("TEST_EMAIL_ADDR1")
test_email_addr2   = os.environ.get("TEST_EMAIL_ADDR2")
test_check_splunk  = True       # Set False to skip long wait for dixel to index

# TESTS

def test_upload(orth: Orthanc, dixels):
    print("Testing can upload")

    orth.clear()
    assert (len(orth.studies()) == 0)

    for d in dixels:
        orth.put(d)

    assert (len(orth.studies()) > 0)

    for d in dixels:
        assert (orth.exists(d))

    orth.clear()
    assert (len(orth.studies()) == 0)

    print("Passed!")
    return True


def test_anonymize(orth: Orthanc, dixels):
    print("Testing can anonymize")

    orth.clear()
    assert (len(orth.studies()) == 0)

    pnames = set()

    for d in dixels:
        pnames.add(d.tags["PatientName"])
        orth.put(d)

        anon = ShamDixel.from_dixel(d, salt=salt)
        afile = orth.anonymize(anon, replacement_map=anon.orthanc_sham_map())
        anon.file = afile

        orth.put(anon)
        orth.putm(anon.sham_parent_oid(DLV.STUDIES),
               level=DLV.STUDIES,
               key=cipher_meta_name,
               value=pack_tags(d, mkey))
        orth.delete(d)

    assert (len(orth.studies()) > 0)

    anon_oid = orth.studies()[0]
    anon = orth.get(anon_oid)

    assert( anon.tags["PatientName"] not in pnames )

    enc = orth.getm(anon, key=cipher_meta_name)
    tags = unpack_tags(enc, mkey)

    assert( tags["PatientName"] in pnames )

    orth.clear()
    assert (len(orth.studies()) == 0)

    print("Passed!")
    return True


def test_email( messenger: SmtpMessenger, email_addr: str, dixel: Dixel ):
    print("Testing can email")

    messenger.send({**dixel.tags}, target=email_addr)

    print("Passed!")
    return True


def test_index( splunk: Splunk, dixel: Dixel, check_exists=True ):
    print("Testing can index")

    splunk.put(dixel)

    if check_exists:
        print("Waiting for 1 min to index")
        time.sleep(60)
        time_range = [
            datetime.now()-timedelta(minutes=2),
            datetime.now()
        ]
        r = splunk.find("search index=testing", time_range=time_range)
        logging.debug(r)
        assert( len(r) > 0 )

    print("Passed")
    return True


def test_distribute( dispatch: Dispatcher, _dixels ):
    # Should generate distinct messages to addr1 for proj1 and addr2 for proj2

    print("Testing can dispatch")

    dixels = list(_dixels)

    logging.debug(dispatch.subscriptions)

    dispatch.put(dixels[0].tags, channels=["project1"])
    dispatch.put(dixels[1].tags, channels=["project2"])

    dispatch.handle_queue()

    print("Passed!")
    return True


def test_watch_dcmdir(watch_path, test_data):

    shutil.rmtree(watch_path, ignore_errors=True)
    os.mkdir(watch_path)
    dcmdir = ObservableDcmDir(path=watch_path)

    watcher = Watcher()

    trigger = Trigger(
        evtype=DEV.FILE_ADDED,
        source=dcmdir,
        action=dcmdir.say)
    watcher.add_trigger(trigger)

    def runner():
        """Pause to start watcher and then copy sample file to incoming"""
        time.sleep(1.0)
        shutil.copy(test_data, watch_path)

    p = Process(target=runner)
    p.start()

    f = io.StringIO()
    print("Starting watcher")
    with redirect_stdout(f):

        print("In capture")
        try:
            with timeout(5):  # Give it a little time to say the filename
                watcher.run()
        except RuntimeError:
            print("Stopping watcher")

    out = f.getvalue()
    print("Watcher output:")
    print(out)

    if test_sample_data in out:
        print("Passed!")
        return True


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # Create service endpoints
    mgr = EndpointManager(serialized_ep_descs=_services)

    print(mgr.ep_descs)

    orth: Orthanc = mgr.get("orthanc_hobit")
    messenger: SmtpMessenger = mgr.get(messenger_name)
    splunk: Splunk = mgr.get("splunk")

    # Verify that all endpoints are online
    assert(orth.check())
    assert(messenger.check())
    assert(splunk.check())

    exit()

    # Load some dixels
    dixels = DcmDir(path=test_resources_dir).get_zipped(test_sample_data)
    for d in dixels:
        logging.info(d)

    # Verify expected capabilities
    # assert( test_upload(orth, dixels) )
    # assert( test_anonymize(orth, dixels) )
    # assert( test_email(messenger, test_email_addr1, list(dixels)[0]) )
    # assert( test_index(splunk, list(dixels)[0], check_exists=test_check_splunk))
    # assert( test_watch_dcmdir( incoming_dir, os.path.join(test_resources_dir, test_sample_data) ) )

    # Manually configure the dispatcher
    dispatch = Dispatcher()
    dispatch.messengers[Transport.EMAIL] = messenger
    subscribers_desc = [
        {"name": "Tester 1",
         "channels": ["project1"],
         "email": test_email_addr1},
        {"name": "Tester 2",
         "channels": ["project2"],
         "email": test_email_addr2}]
    for s in subscribers_desc:
        dispatch.add_subscriber(s)

    # assert( test_distribute( dispatch, dixels ) )

    # assert( test_watch_orth( O, dixels ) )
    # assert( test_pipeline( O, D, S, T, sample_data ) )




    # handle_dir("/Users/derek/data/duke/duke", orth, mkey)

    # handle_study("eb08f9d5-fc93f2ef-f88bf9e1-e32767bd-39da8c10", orth, None, None, mkey)

