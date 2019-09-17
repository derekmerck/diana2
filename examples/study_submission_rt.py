"""
SIREN Trial Network upload monitor

Desired process:

1. As each new PHI, partial-anon, or anon study arrives in the folder
   "/incoming/proj/site":
2.   Each instance is uploaded
3.   Each uploaded instance is anonymized and deleted (instance-by-instance to
     create serial instance times, if possible)
4. As each anonymized study becomes stable:
5.   Meta for each study is pulled, including pre-anon meta + source directory
6.   Meta is forwarded to indexer for logging
7.   Meta is forwarded to the dispatcher along with source dir (channel)
8.   Meta is multiplexed from subscription roster to produce messages
9.     Each message is submitted to the appropriate transport mechanism
10.    Each message forwarded to indexer to be logged

"""

import os
import logging
from pathlib import Path
from collections import deque
from functools import partial
from typing import Mapping
from datetime import datetime
from pprint import pformat
import json
from dateutil import parser as DateTimeParser
from cryptography.fernet import Fernet
from crud.abc import Endpoint
from diana.apis import DcmDir, Orthanc, ObservableDcmDir, ObservableOrthanc, Splunk
from diana.dixel import Dixel, ShamDixel
from diana.utils.endpoint import Watcher, Trigger
from diana.utils.dicom import DicomLevel as DCMLv
from diana.utils.dicom.events import DicomEventType as DCMEv
from diana.utils import SmartJSONEncoder
from diana.utils.gateways import GatewayConnectionError
from wuphf.daemons import Dispatcher

DRYRUN = False
CLEAR_DCM_ARCH = False

service_descs = """
---
incoming_dir:
  ctype:     DicomDir
  # path:      "/data/incoming"
  path:      /Users/derek.merck/vms/debian
  
dicom_arch:
  ctype:     ObservableOrthanc
  # host:      orthanc-hobit
  host:      debian-testing
  user:      orthanc
  password:  $ORTHANC_PASSWORD
  
splunk_index:
  ctype:     Splunk
  # host:      splunk
  host:      debian-testing
  user:      admin
  index:     dicom
  password:  $SPLUNK_PASSWORD
  hec_token: $SPLUNK_HEC_TOKEN

smtp_server: &SMTP_SERVER
  ctype:     SmtpMessenger
  host:      smtp.gmail.com
  user:      $SMTP_USER
  password:  $SMTP_PASSWORD
  tls:       True
  port:      587

subscriptions: &SUBSCRIPTIONS
- channel: project
  subscribers:
    - name: Central Reader
      email: $TEST_EMAIL_RCV0

- channel: project/site1
  subscribers:
    - name: Site 1 PI
      email: $TEST_EMAIL_RCV1
      role: pi  
    - name: Site 1 Coord
      email: $TEST_EMAIL_RCV2
      role: coord
  
- channel: project/site2
  subscribers:
    - name: Site 2 PI
      email: $TEST_EMAIL_RCV3
      role: pi
      
dispatcher:
  ctype: Dispatcher
  smtp_messenger_desc: *SMTP_SERVER
  subscriptions_desc:  *SUBSCRIPTIONS
  
"""

# Remap channel names to formal site names
channel_lu={
    "project": "Project",
    "site1":   "Site 1",
    "site2":   "Site 2"
}

msg_t="""
Subject: SIREN/{{ Project }} Study Received {{ now() }}

{{ recipient.name }}, {{ Site }}
 
{{ Modality }} scan images from {{ Site }} that were uploaded at {{ now() }} have been received and anonymized (or re-anonymized) at the University of Michigan SIREN/{{ Project }} image registry.
 
The anonymized study originally performed on {{ OriginalStudyDate }} has been added to the unique registry subject jacket for "{{ PatientName }}.  The study has been assigned the unique image identifier "{{ AccessionNumber[0:8] }}.  Please save this information with your trial records.  You will be responsible for associating this registry assigned unique image identifier with your subject enrollment in the WEBDCU database.
 
If imaging for this subject has previously been submitted to the SIREN/{{ Project }} image registry, the unique registry subject jacket should be the same, however, the unique image identifier will be different.  If this study has been filed under the wrong subject jacket, please ensure that any pre-anonymized data from your fileroom includes a consistent subject name, gender, and birthdate (i.e., "Subject 1", "Male", "1/1/2000"), and email the contact the registry administration team.
"""


"""
SETUP
---------------

1. Create and source .env file

2. Create and configure splunk container (admin stack, create dicom 
   and logging indices, turn off hec ssl if necc)

$ docker run -d -p 8000:8000 -p 8088:8088 -p 8089:8089 \
   -e SPLUNK_START_ARGS=--accept-license \
   -e SPLUNK_PASSWORD=$SPLUNK_PASSWORD \
   -e SPLUNK_HEC_TOKEN=$SPLUNK_HEC_TOKEN \
   --name splunk splunk/splunk:latest

3. Create orthanc container w/meta for siren_info that logs to splunk

$ docker run -d -p 8042:8042 \
  -e ORTHANC_PASSWORD=$ORTHANC_PASSWORD \
  -e ORTHANC_METADATA_0=siren_info,9875 \
  -e ORTHANC_WBV_ENABLED=true \
  --tmpfs /etc/orthanc \
  --log-driver=splunk \
  --log-opt splunk-token=$SPLUNK_HEC_TOKEN \
  --log-opt splunk-url=http://$SPLUNK_HOST:8088 \
  --log-opt splunk-format=json \
  --log-opt splunk-source=orthanc \
  --log-opt tag="{{.Name}}/{{.ID}}" \
  --log-opt splunk-index=logging \
  --name orthanc-hobit derekmerck/orthanc-wbv:latest-amd64

4. Create /data/incoming directory\
5. Create services.yaml file (from services_desc)
6. Create diana2 container with map to /data, /services.yaml,
   and links to splunk, orthanc and run this file
   
$ docker run -d \
   -v /data:/data \
   -v `pwd`/services.yaml:/services.yaml:ro \
   --env-file .env \
   -e DIANA_SERVICES_PATH=/services.yaml \
   --link splunk --link orthanc \
   --log-driver=splunk \
   --log-opt splunk-token=$SPLUNK_HEC_TOKEN \
   --log-opt splunk-url=http://localhost:8088 \
   --log-opt splunk-format=json \
   --log-opt splunk-source=orthanc \
   --log-opt tag="{{.Name}}/{{.ID}}" \
   --log-opt splunk-index=logging \
   --name diana diana2.1 python3 examples/study_submission_rt.py
"""

# Parameters
salt = os.environ.get("PROJECT_SALT") # Unique subject anonymization namespace
# fernet_key = Fernet.generate_key()
fernet_key = os.environ.get("PROJECT_FERNET_KEY").encode("utf8")

# Globals
tagged_studies = deque(maxlen=50)  # history


def pack_siren_info(d: Dixel) -> str:

    res = {
        "ShamID": d.meta["ShamID"],  # Just for tracking
        "AccessionNumber": d.tags.get("AccessionNumber"),
        "PatientID": d.tags.get("PatientID"),
        "PatientName": d.tags.get("PatientName"),
        "PatientBirthDate": d.tags.get("PatientBirthDate"),
        "StudyDateTime": d.meta["StudyDateTime"],
        "FileName": d.meta["FileName"],
        "timestamp": datetime.now()
    }
    clear_text = json.dumps(res, cls=SmartJSONEncoder)
    f = Fernet(fernet_key)
    token = f.encrypt(clear_text.encode("utf8"))
    return token


def unpack_siren_info(token: str) -> Mapping:

    f = Fernet(fernet_key)
    clear_text = f.decrypt(token)
    res = json.loads(clear_text.decode("utf8"))
    return res


def _handle_instance_in_dcm_dir(item: Dixel, orth: Orthanc, salt: str):

    orth.put(item)
    anon = ShamDixel.from_dixel(item, salt=salt)
    afile = orth.anonymize(anon, replacement_map=anon.orthanc_sham_map())
    anon.file = afile
    orth.put(anon)
    orth.delete(item)

    anon_study_id = anon.sham_parent_oid(DCMLv.STUDIES)
    logging.debug(anon_study_id)
    logging.debug(tagged_studies)
    if anon_study_id not in tagged_studies:
        logging.debug("Tagging parent study: {}".format(anon_study_id))
        siren_info = pack_siren_info(anon)
        orth.gateway.put_metadata(anon_study_id, DCMLv.STUDIES, "siren_info", siren_info)
        tagged_studies.append(anon_study_id)


def handle_file_arrived_in_dcm_dir(item, source: DcmDir, dest: Orthanc, salt=None):

    dcm_dir = source
    fn = item.get("fn")
    if fn.endswith(".zip"):
        items = dcm_dir.get_zipped(fn)
        for item in items:
            _handle_instance_in_dcm_dir(item, dest, salt)
    else:
        item = dcm_dir.get(fn, file=True)
        _handle_instance_in_dcm_dir(item, dest, salt)


def handle_study_arrived_at_orthanc(item, source: Orthanc, dest: Dispatcher, splunk: Splunk = None, base_path = "/data/incomimg"):

    orth = source
    disp = dest
    oid = item.get("oid")

    _item = orth.get(oid)
    try:
        siren_info_tok = orth.gateway.get_metadata(oid, DCMLv.STUDIES, "siren_info")
    except GatewayConnectionError:
        # This is not an anonymized study
        logging.warning("Found non-anonymized study: {}".format(oid))
        return

    _item.meta["siren_info_tok"] = siren_info_tok
    _item.meta["siren_info"] = unpack_siren_info(siren_info_tok)
    logging.debug(pformat(_item.meta["siren_info"]))

    fp = Path(_item.meta["siren_info"]["FileName"]).relative_to(base_path)
    channels = [
        fp.parts[0],              # ie, hobit
        "/".join(fp.parts[0:2])   # ie, hobit/hennepin
    ]
    logging.debug(channels)

    original_study_date = DateTimeParser.parse(_item.meta["siren_info"]["StudyDateTime"]).date()
    timestamp = DateTimeParser.parse(_item.meta["siren_info"]["timestamp"])
    project = fp.parts[0]
    if channel_lu.get(project):
        project = channel_lu.get(project, project)
    site = fp.parts[1]
    if channel_lu.get(site):
        site = channel_lu.get(site, site)

    _item.meta.update(
        {"OriginalStudyDate": original_study_date,
         "Project": project,
         "Site": site,
         "SubmissionTimestamp": timestamp}
    )

    data = {**_item.tags, **_item.meta}
    disp.put(data, channels=channels)  # Will put multiple messages on the queue
    disp.handle_queue(dryrun=DRYRUN)

    if splunk:
        del(_item.meta["siren_info"])
        splunk.put(_item)


def test_upload_zipfile(dcmdir: DcmDir, orth: Orthanc):

    f0 = "006dfa27cc5c6c4e.zip"        # Small CR
    f1 = "anon.left_arm_ct_angio.zip"  # Large CT
    item = {"fn": f0}
    handle_file_arrived_in_dcm_dir(item, dcmdir, orth)


def test_study_alert(orth: Orthanc, disp: Dispatcher,
                     splunk: Splunk = None,
                     base_path: str = "/data"):

    item = {"oid": "91499a9e-abbc193d-fb780cbb-5fd054d3-46a4e2fe"}
    handle_study_arrived_at_orthanc(item, orth, disp, splunk=splunk, base_path=base_path)


def main(dcmdir: ObservableDcmDir, orth: ObservableOrthanc,
         disp: Dispatcher, splunk: Splunk):

    def add_route(self: Watcher, source: Endpoint, event_type, func, **kwargs):

        func = partial(func, source=source, **kwargs)
        t = Trigger(event_type,
                    source=source,
                    action=func)
        self.add_trigger(t)

    Watcher.add_route = add_route
    w = Watcher()

    w.add_route(dcmdir, DCMEv.FILE_ADDED,  handle_file_arrived_in_dcm_dir,  dest=orth, salt=salt)
    w.add_route(orth, DCMEv.STUDY_ADDED, handle_study_arrived_at_orthanc, dest=disp, splunk=splunk, base_path=dcmdir.path)

    w.run()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    from crud.manager import EndpointManager as Manager
    m = Manager(file=os.environ.get("DIANA_SERVICES_PATH"))
    dcmdir = ObservableDcmDir(**m.service_descs["dcm_incoming"])
    orth = ObservableOrthanc(**m.service_descs["hobit"])
    disp = Dispatcher(**m.service_descs["dispatcher"])
    splunk = Splunk(**m.service_descs["splunk"])

    if CLEAR_DCM_ARCH:
        orth.clear()

    #main(dcmdir, orth, disp, splunk)

    # test_upload_zipfile(dcmdir, orth)
    test_study_alert(orth, disp, splunk=splunk, base_path=dcmdir.path)
