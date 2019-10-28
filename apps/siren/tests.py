# SIREN/DIANA basic functionality testing framework
#
# Requires env vars:
# - TEST_EMAIL_ADDR1
# - LOCAL_SMTP_HOST
# - GMAIL_USER
# - GMAIL_APP_PASSWORD

import os
import yaml
import time
import logging
import shutil
import io
from pprint import pformat
from contextlib import redirect_stdout, redirect_stderr
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
from wuphf.cli.string_descs import *
from diana.utils import unpack_data
from crud.utils import deserialize_dict

from handlers import handle_upload_file, handle_upload_dir, handle_upload_zip, handle_notify_study

# Retrofit DIANA apis to crud manager
from crud.abc import Serializable
Serializable.Factory.registry["ObservableOrthanc"] = ObservableOrthanc
Serializable.Factory.registry["Dixel"] = Dixel

# CONFIG
_services          = "@./siren_services.yaml"
_subscriptions     = "@./subscriptions.yaml"

os.environ["ORTHANC_PASSWORD"] = "passw0rd!"  # Set defaults
os.environ["SPLUNK_PASSWORD"]  = "passw0rd!"
os.environ["SPLUNK_HEC_TOKEN"] = "b45a6398-ec35-4552-8b9b-9492a12e60a4"

anon_salt          = "Test+Test+Test"
fkey               = b'o-KzB3u1a_Vlb8Ji1CdyfTFpZ2FvdsPK4yQCRzFCcss='
messenger_name     = "gmail:"   # Use "gmail:" or "local_smtp"
splunk_index       = "testing"  # Set to "dicom" for production or "testing"
msg_t              = """to: {{ recipient.email }}\nfrom: {{ from_addr }}\nsubject: Test Message\n\nThis is the message text: "{{ item.msg_text }}"\n"""
notify_msg_t = "@./siren_notify.txt.j2"

# TESTING CONfIG
test_sample_zip    = os.path.abspath("./resources/test.zip")
test_sample_dir    = os.path.expanduser("~/data/test")
test_email_addr1   = os.environ.get("TEST_EMAIL_ADDR1")
os.environ["TEST_GMAIL_BASE"] = test_email_addr1.split("@")[0]

CHECK_SPLUNK       = False   # Set False to skip long wait for dixel to index
EMAIL_DRYRUN       = True    # Set False to send live emails

# TESTS


def test_upload_one(orth: Orthanc, dixel: Dixel):
    print("Testing can upload")

    orth.clear()
    assert (len(orth.studies()) == 0)

    orth.put(dixel)

    assert (len(orth.studies()) > 0)
    assert (orth.exists(dixel))

    orth.clear()
    assert (len(orth.studies()) == 0)

    print("Passed!")
    return True


def test_anonymize_one(orth: Orthanc, dixel: Dixel):
    print("Testing can anonymize, tag, and untag")

    orth.clear()
    assert (len(orth.studies()) == 0)

    orth.put(dixel)

    anon = ShamDixel.from_dixel(dixel, salt=anon_salt)
    afile = orth.anonymize(anon, replacement_map=anon.orthanc_sham_map())
    anon.file = afile

    orth.put(anon)

    orth.putm(anon.sham_parent_oid(DLV.STUDIES),
           level=DLV.STUDIES,
           key="signature",
           value=anon.pack_fields(fkey))

    assert (len(orth.studies()) == 2)
    orth.delete(dixel)
    assert (len(orth.studies()) == 1)

    oid = orth.studies()[0]
    test = orth.get(oid)

    assert( test.tags["PatientName"] == anon.meta["ShamName"] )

    enc = orth.getm(test, key="signature")
    tags = unpack_data(enc, fkey)

    assert( tags["PatientName"] in dixel.tags["PatientName"] )

    orth.clear()
    assert (len(orth.studies()) == 0)

    print("Passed!")
    return True


def test_index_one( splunk: Splunk, dixel: Dixel, check_exists=True ):
    print("Testing can index")

    splunk.put(dixel, index=splunk_index)

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


def test_email_messenger( messenger: SmtpMessenger, dryrun=False ):
    print("Testing can email from template")

    outgoing = "The quick brown fox jumped over the lazy dog"
    data = {"item": {"msg_text": outgoing},
            "recipient": {"email": test_email_addr1}}

    msg = messenger.get(data, target=test_email_addr1)

    assert( test_email_addr1 in msg )
    assert( outgoing in msg )

    if not dryrun:
        messenger.send(data, target=test_email_addr1)

    print("Passed!")
    return True


def test_distribute( subscriptions, messenger: SmtpMessenger, dryrun=False ):
    print("Testing can dispatch")

    ch, subs = deserialize_dict(subscriptions)
    dispatch = Dispatcher(
        subscribers_desc=subs,
        channels_desc=ch
    )
    messenger.set_msg_t(notify_msg_t)
    dispatch.add_messenger("email", messenger)

    logging.debug(pformat(dispatch.subscribers))

    data = {"tags": {"AccessionNumber": "ABC123",
                     "PatientName": "DOE^JOHN^S"},
            "meta": {"signature":
                         {"StudyDateTime": "Some date/time",
                          "trial": "SOME TRIAL",
                          "site":  "Some site"}
                     }
            }

    dispatch.put(data, channels=["hobit-duke"])
    dispatch.put(data, channels=["hobit-detroit"])

    msgs = dispatch.peek_queue()

    assert( "SIREN/SOME TRIAL" in "".join(msgs) )
    assert( "+testing+hobit@gmail.com" in "".join(msgs))
    assert( 'subject jacket for "DOE^JOHN^S"' in "".join(msgs))

    print("Passed!")
    return True


def test_upload_dir_handler(dcm_dir: DcmDir, orth: Orthanc):
    print("Testing can upload dir w handler")

    orth.clear()
    assert (len(orth.studies()) == 0)

    handle_upload_dir(dcm_dir, orth, fkey, anon_salt=anon_salt)
    assert (len(orth.instances()) > 20)

    orth.clear()
    assert (len(orth.studies()) == 0)

    print("Passed!")
    return True


def test_upload_zip_handler(zip_file, orth: Orthanc):
    print("Testing can upload zip w handler")

    orth.clear()
    assert (len(orth.studies()) == 0)

    handle_upload_zip(DcmDir(), zip_file, orth, fkey, anon_salt=anon_salt)
    assert (len(orth.instances()) > 1)

    orth.clear()
    assert (len(orth.studies()) == 0)

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

    print(pformat(mgr.ep_descs))

    orth: Orthanc = mgr.get("orthanc_hobit")
    messenger: SmtpMessenger = mgr.get(messenger_name)
    messenger.msg_t = msg_t
    splunk: Splunk = mgr.get("splunk")
    dcm_dir = DcmDir(path=test_sample_dir)

    # Verify that all endpoints are online
    # assert(orth.check())
    # assert(messenger.check())
    # assert(splunk.check())

    # Load a dixel
    dixel = dcm_dir.get("IN000001", file=True)
    assert( dixel )
    assert( dixel.file )

    # Verify capabilities:
    # - upload
    # - anonymize
    # - index
    # - message
    # - distribute

    # assert( test_upload_one( orth, dixel ) )
    # assert( test_anonymize_one( orth, dixel ) )
    # assert( test_index_one(splunk, dixel, check_exists=CHECK_SPLUNK))
    # assert( test_email_messenger(messenger, dryrun=EMAIL_DRYRUN) )
    # assert( test_distribute(_subscriptions, messenger, dryrun=EMAIL_DRYRUN) )

    # Verify handlers:
    # - directory
    # - zip
    # - file
    # - notify

    # assert( test_upload_dir_handler( dcm_dir, orth) )
    assert( test_upload_zip_handler( test_sample_zip, orth ))
    # TODO: assert( test_upload_file( orth, dcm_dir, file, zip_file ))
    # TODO: assert( test_notify( orth, oid, disp_kwargs, messenger ))

    # Verify watcher pipeline
    # TODO: assert( test_watcher( dcm_dir, orth, disp_kwargs, messenger)
