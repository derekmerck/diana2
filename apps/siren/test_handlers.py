"""
SIREN/DIANA basic functionality testing framework

Requires env vars:
- GMAIL_USER
- GMAIL_APP_PASSWORD
- GMAIL_BASE_NAME  -- ie, abc -> abc+hobitduke@gmail.com

These env vars are set to default:
- ORTHANC_PASSWORD
- SPLUNK_PASSWORD
- SPLUNK_HEC_TOKEN

TODO: Move stuff to archive after collected
TODO: Write data into daily folder or something from mi-share ingress
TODO: Suppress dicom-simplify missing (series) creation time

"""

import time
import logging
import shutil
import io
import tempfile
from pathlib import Path
from pprint import pformat
from contextlib import redirect_stdout
from multiprocessing import Process
from datetime import datetime, timedelta
from interruptingcow import timeout
from crud.manager import EndpointManager
from crud.abc import Watcher, Trigger
from crud.endpoints import Splunk
from wuphf.endpoints import SmtpMessenger
from diana.apis import Orthanc, ObservableOrthanc, DcmDir, ObservableDcmDir
from diana.dixel import Dixel, ShamDixel
from diana.utils.dicom import DicomLevel as DLv, DicomEventType as DEv
from wuphf.cli.string_descs import *
from diana.utils import unpack_data
from crud.utils import deserialize_dict
from diana.utils.gateways import suppress_urllib_debug
from diana.utils.endpoint.watcher import suppress_watcher_debug

from handlers import handle_upload_dir, handle_upload_zip, handle_notify_study, \
    handle_file_arrived, start_watcher, tagged_studies
from trial_dispatcher import TrialDispatcher as Dispatcher


LOCAL_SERVICES     = False   # Set False to use UMich services
USE_GMAIL          = True   # Set False to use UMich smtp
DO_DIR_UPLOAD      = False
CHECK_SPLUNK       = False   # Set False to skip long wait for dixel to index
CHECK_WATCH_STUDIES= False   # Set False to skip long wait for orthanc watcher
EMAIL_DRYRUN       = False   # Set False to send live emails


# CONFIG
_services          = "@services.yaml"
_subscriptions     = "@subscriptions.yaml"
os.environ["SPLUNK_INDEX"] = "testing"
SMTP_MESSENGER_NAME = "smtp_server"

if LOCAL_SERVICES:
    # Set everythin back to default
    os.environ["UMICH_HOST"] = "localhost"  # For testing
    del os.environ["ORTHANC_USER"]
    del os.environ["ORTHANC_PASSWORD"]
    del os.environ["SPLUNK_USER"]
    del os.environ["SPLUNK_PASSWORD"]

if USE_GMAIL:
    SMTP_MESSENGER_NAME = "gmail:"

test_email_addr1 = "derek.merck@ufl.edu"
#test_email_addr1 = "ejacob@med.umich.edu"
#test_email_addr1   = os.environ.get("TEST_EMAIL_ADDR1")
# os.environ["TEST_GMAIL_BASE"] = test_email_addr1.split("@")[0]

anon_salt          = "Test+Test+Test"
fkey               = b'o-KzB3u1a_Vlb8Ji1CdyfTFpZ2FvdsPK4yQCRzFCcss='
msg_t              = """to: {{ recipient.email }}\nfrom: {{ from_addr }}\nsubject: Test Message\n\nThis is the message text: "{{ item.msg_text }}"\n"""
notify_msg_t = "@./notify.txt.j2"

# TESTING CONfIG
test_sample_zip    = os.path.abspath("../../tests/resources/dcm_zip/test.zip")
test_sample_file   = os.path.abspath("../../tests/resources/dcm/IM2263")
test_sample_dir    = os.path.expanduser("~/data/test")  # Need to dl separately

# TESTS

def test_upload_one(orth: Orthanc, dixel: Dixel):
    print("Testing can upload")

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    orth.put(dixel)

    assert (len(orth.studies()) > 0)
    assert (orth.exists(dixel))

    print("Passed!")
    return True


def test_anonymize_one(orth: Orthanc, dixel: Dixel):
    print("Testing can anonymize, tag, and untag")

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    orth.put(dixel)

    anon = ShamDixel.from_dixel(dixel, salt=anon_salt)
    afile = orth.anonymize(anon, replacement_map=anon.orthanc_sham_map())
    anon.file = afile

    orth.put(anon)

    orth.putm(anon.sham_parent_oid(DLv.STUDIES),
           level=DLv.STUDIES,
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

    print("Passed!")
    return True


def test_index_one( splunk: Splunk, dixel: Dixel, check_exists=CHECK_SPLUNK ):
    print("Testing can index")

    splunk.put(dixel, index=os.environ.get("SPLUNK_INDEX"))

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


def test_email_messenger( messenger: SmtpMessenger, dryrun=EMAIL_DRYRUN ):
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


def test_distribute( subscriptions, messenger: SmtpMessenger ):
    print("Testing can dispatch")

    ch, subs = deserialize_dict(subscriptions)
    dispatch = Dispatcher(channel_tags=ch)
    dispatch.add_subscribers(subs)

    messenger.set_msg_t(notify_msg_t)
    dispatch.email_messenger = messenger

    logging.debug(pformat(dispatch.subscribers))

    data = {"tags": {"AccessionNumber": "ABC123",
                     "PatientName": "DOE^JOHN^S"},
            "meta": {"signature":
                         {"trial": "hobit",
                          "site":  "duke"}
                     }
            }

    sent = dispatch.put(data, dryrun=EMAIL_DRYRUN)

    data["meta"]["signature"]["site"] = "detroit"
    sent += dispatch.put(data, dryrun=EMAIL_DRYRUN)

    print(sent)

    msgs = [x['msg'] for x in sent]
    msgs = "\n".join(msgs)

    # logging.debug(pformat(msgs))

    assert( "SIREN/HOBIT" in msgs )
    assert( "+testing+hobit@gmail.com" in msgs )
    assert( 'subject jacket for "DOE^JOHN^S"' in msgs )

    print("Passed!")
    return True


def test_upload_dir_handler(dcm_dir: DcmDir, orth: Orthanc):
    print("Testing can upload dir w handler")

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    handle_upload_dir(dcm_dir, orth, fkey, anon_salt=anon_salt)
    assert (len(orth.instances()) > 20)

    print("Passed!")
    return True


def test_upload_zip_handler(zip_file, orth: Orthanc):
    print("Testing can upload zip w handler")

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    handle_upload_zip(DcmDir(), zip_file, orth, fkey, anon_salt=anon_salt)
    assert (len(orth.instances()) > 1)

    print("Passed!")
    return True


def test_file_arrived_handler(dcm_file, zip_file, orth: Orthanc):
    print("Testing can handle file arrived")

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    watch_path = tempfile.mkdtemp()
    site_path = os.path.join(watch_path, "my_trial", "my_site")
    os.makedirs(site_path)

    shutil.copy(zip_file, site_path)
    data = {"fn": os.path.join( site_path, Path(zip_file).name )}
    handle_file_arrived(data, DcmDir(path=watch_path), orth,
                        fkey=fkey, anon_salt=anon_salt, signature_meta_key="signature")
    assert (len(orth.instances()) > 1)

    oid = orth.studies()[0]
    data = orth.getm(oid, key="signature")
    clear = unpack_data(data, fkey)
    print(pformat(clear))
    assert(clear["trial"] == "my_trial")

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    shutil.copy(dcm_file, site_path)

    data = {"fn": os.path.join(site_path, Path(dcm_file).name)}
    handle_file_arrived(data, DcmDir(path=watch_path), orth,
                        fkey=fkey, anon_salt=anon_salt, signature_meta_key="signature")
    assert (len(orth.instances()) == 1)

    time.sleep(1.0)
    oid = orth.studies()[0]
    data = orth.getm(oid, key="signature")
    clear = unpack_data(data, fkey)
    print(pformat(clear))
    assert(clear["trial"] == "my_trial")

    orth.clear()
    assert (len(orth.studies()) == 0)

    shutil.rmtree(watch_path, ignore_errors=True)

    print("Passed!")
    return True


def test_notify_handler(dixel, orth: Orthanc,
                        subscriptions, messenger: SmtpMessenger,
                        indexer: Splunk, dryrun=EMAIL_DRYRUN):

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    orth.put(dixel)
    dixel.meta["trial"] = "hobit"
    dixel.meta["site"] = "testing"

    orth.putm(dixel.parent_oid(DLv.STUDIES),
              level=DLv.STUDIES,
              key="signature",
              value=dixel.pack_fields(fkey, fields=["trial", "site"]))

    ch, subs = deserialize_dict(subscriptions)
    dispatch = Dispatcher(
        channel_tags=ch
    )
    dispatch.add_subscribers(subs)
    messenger.set_msg_t(notify_msg_t)
    dispatch.email_messenger = messenger

    data = {"oid": dixel.parent_oid(DLv.STUDIES)}
    handle_notify_study(data, source=orth,
                        dispatcher=dispatch, dryrun=dryrun,
                        indexer=indexer, index_name=SPLUNK_INDEX,
                        fkey=fkey)

    print("Passed!")
    return True


def test_watch_orthanc(test_dixel, orth: ObservableOrthanc):

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    watcher = Watcher()

    trigger0 = Trigger(
        evtype=DEv.INSTANCE_ADDED,
        source=orth,
        action=orth.say)
    watcher.add_trigger(trigger0)

    trigger1 = Trigger(
        evtype=DEv.STUDY_ADDED,
        source=orth,
        action=orth.say)
    watcher.add_trigger(trigger1)

    def runner():
        """Pause to start watcher and then copy sample file to incoming"""
        time.sleep(1.0)
        orth.put(test_dixel)

    p = Process(target=runner)
    p.start()

    f = io.StringIO()
    print("Starting watcher")
    with redirect_stdout(f):

        print("In capture")
        try:
            with timeout(5):  # Give it a little time to say the instance
                watcher.run()
        except RuntimeError:
            print("Stopping watcher")
        finally:
            watcher.stop()

    out = f.getvalue()
    print("Watcher output:")
    print(out)

    if dixel.oid() in out:
        print("Passed!")
        return True


def test_watch_dir(test_file):

    watch_path = tempfile.mkdtemp()
    site_path = os.path.join(watch_path, "my_trial", "my_site")
    os.makedirs(site_path)

    dcm_dir = ObservableDcmDir(path=watch_path)

    watcher = Watcher()

    trigger = Trigger(
        evtype=DEv.FILE_ADDED,
        source=dcm_dir,
        action=dcm_dir.say)
    watcher.add_trigger(trigger)

    def runner():
        """Pause to start watcher and then copy sample file to incoming"""
        time.sleep(1.0)
        shutil.copy(test_file, site_path)

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
        finally:
            watcher.stop()

    out = f.getvalue()
    print("Watcher output:")
    print(out)

    shutil.rmtree(watch_path, ignore_errors=True)

    from pathlib import Path
    if Path(test_file).name in out:
        print("Passed!")
        return True


def test_siren_receiver(test_file, orth: Orthanc,
                        subscriptions, messenger: SmtpMessenger,
                        indexer: Splunk, dryrun=EMAIL_DRYRUN):

    orth.clear()
    tagged_studies.clear()
    assert (len(orth.studies()) == 0)

    ch, subs = deserialize_dict(subscriptions)
    dispatch = Dispatcher(
        channel_tags=ch
    )
    dispatch.add_subscribers(subs)
    messenger.set_msg_t(notify_msg_t)
    dispatch.email_messenger = messenger

    watch_path = tempfile.mkdtemp()
    site_path = os.path.join(watch_path, "hobit", "testing")
    os.makedirs(site_path)

    incoming = ObservableDcmDir(path=watch_path)

    def runner():
        """Pause to start watcher and then copy sample file to incoming/trial/site"""
        time.sleep(1.0)
        shutil.copy(test_file, site_path)

    p = Process(target=runner)
    p.start()

    f = io.StringIO()
    print("Starting SIREN Receiver")
    with redirect_stdout(f):

        print("In capture")
        try:
            with timeout(90):  # Give it a little time for the study to settle
                watcher = start_watcher(
                    incoming,
                    orth,
                    fkey=fkey,
                    anon_salt=anon_salt,
                    dispatcher=dispatch,
                    dryrun=dryrun,
                    indexer=indexer,
                    index_name=os.environ.get("SPLUNK_INDEX")
                )
        except RuntimeError:
            print("Stopping watcher subprocess")

    out = f.getvalue()
    print("SIREN Reciever output:")
    print(out)

    shutil.rmtree(watch_path, ignore_errors=True)

    return True


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    suppress_urllib_debug()
    suppress_watcher_debug()

    # Create service endpoints
    services = EndpointManager(serialized_ep_descs=_services)

    print(pformat(services.ep_descs))

    orth: ObservableOrthanc = services.get("hobit")
    orth.polling_interval = 2.0
    messenger: SmtpMessenger = services.get(SMTP_MESSENGER_NAME)
    messenger.msg_t = msg_t
    splunk: Splunk = services.get("splunk")
    dcm_dir = DcmDir(path=test_sample_dir)

    # Load a dixel
    dixel = dcm_dir.get("HOBIT1172/IM0", file=True)
    # assert( dixel )
    # assert( dixel.file )
    #
    # # Verify that all endpoints are online
    # assert( orth.check() )
    # assert( messenger.check() )
    # assert( splunk.check() )
    #
    # # Verify basic capabilities:
    # # - upload
    # # - anonymize
    # # - index
    # # - message
    # # - distribute
    #
    # assert( test_upload_one(orth, dixel) )
    # assert( test_anonymize_one(orth, dixel) )
    # assert( test_index_one(splunk, dixel) )
    assert( test_email_messenger(messenger) )
    # assert( test_distribute(_subscriptions, messenger) )

    exit()

    # Verify observer daemons:
    # - watch dir
    # - watch orth

    assert( test_watch_dir(test_sample_file) )
    assert( test_watch_orthanc(dixel, orth) )

    # Verify handlers:
    # - directory
    # - zip
    # - file
    # - notify

    if DO_DIR_UPLOAD:
        assert( test_upload_dir_handler(dcm_dir, orth) )
    assert( test_upload_zip_handler(test_sample_zip, orth) )
    assert( test_file_arrived_handler(test_sample_file, test_sample_zip, orth) )
    assert( test_notify_handler(dixel, orth, _subscriptions, messenger, splunk) )

    # Verify watcher pipeline
    # - run watcher

    assert( test_siren_receiver(test_sample_file, orth, _subscriptions, messenger, splunk) )
