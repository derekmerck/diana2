"""
SIREN Trial Network upload monitor

Desired process:

1. As each new PHI, partial-anon, or anon study arrives in the folder
   "/incoming/proj/site":
2.   Each instance is uploaded
3.   Each uploaded instance is anonymized and deleted (instance-by-instance to
     create serial instance times, if possible)
3. As each anonymized study becomes stable:
4.   Meta for each study is pulled, including pre-anon meta + source directory
5.   Meta is forwarded to indexer for logging
6.   Meta is forwarded to the dispatcher along with source dir (channel)
7.   Meta is multiplexed from subscription roster to produce messages
8.     Each message is submitted to the appropriate transport mechanism
9.     Each message forwarded to indexer to be logged

"""

import os
import logging
from pathlib import Path
from collections import deque
from functools import partial
from typing import Mapping
from datetime import datetime
from pprint import pformat
import yaml
import json
from cryptography.fernet import Fernet
from crud.abc import Endpoint
from diana.apis import DcmDir, Orthanc, ObservableDcmDir, ObservableOrthanc
from diana.dixel import Dixel, ShamDixel
from diana.utils.endpoint import Watcher, Trigger
from diana.utils.dicom import DicomLevel as DCMLv
from diana.utils.dicom.events import DicomEventType as DCMEv
from diana.utils import SmartJSONEncoder
from wuphf.daemons import Dispatcher

service_descs = """
---
incoming_dir:
  ctype:     DicomDir
  path:      "/data/incoming"
  
dicom_arch:
  ctype:     ObservableOrthanc
  # host:      orthanc
  host:      debian-testing
  user:      orthanc
  password:  $ORTHANC_PASSWORD
  
splunk_index:
  ctype:     Splunk
  host:      splunk
  user:      admin
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

"""
$ docker run -d -p 8042:8042 \
  -e ORTHANC_PASSWORD=$ORTHANC_PASSWORD \
  -e ORTHANC_METADATA_0=siren_info,9875 \
  -e ORTHANC_WBV_ENABLED=true \
  --tmpfs /etc/orthanc \
  --name orthanc derekmerck/orthanc-wbv:latest-amd64
  
$ docker run -d -p 8000:8000 -p 8088:8088 -p 8089:8089 \
   -e SPLUNK_START_ARGS=--accept-license \
   -e SPLUNK_PASSWORD=$SPLUNK_PASSWORD \
   -e SPLUNK_HEC_TOKEN=$SPLUNK_HEC_TOKEN \
   --name splunk splunk/splunk:latest
   
$ docker run -d \
   -v /data:/data \
   -v `pwd`/services.yaml:/services.yaml:ro \
   --env-file .env \
   -e DIANA_SERVICES_PATH=/services.yaml \
   --link splunk --link orthanc \
   --name diana diana2.1
"""

# 1. Create and source .env file
# 2. Create orthanc container w/meta for siren_info
# 3. Create and configure splunk container
# 4. Create /data/incoming directory\
# 5. Create services.yaml file (from services_desc)
# 6. Create diana2 container with map to /data, /services.yaml,
#    and links to splunk, orthanc

# Parameters
salt = os.environ.get("PROJECT_SALT") # Unique subject anonymization namespace
# fernet_key = Fernet.generate_key()
fernet_key = os.environ.get("PROJECT_FERNET_KEY").encode("UTF8")
base_dir_name = "/data/incoming"  # dispatcher channels are relative paths to here

# Globals
tagged_studies = deque(maxlen=50)  # history


def pack_siren_info(d: Dixel) -> str:

    res = {
        "ShamID": d.meta["ShamID"],
        "PatientID": d.tags.get("PatientID"),
        "PatientName": d.tags.get("PatientName"),
        "BirthDate": d.tags.get("PatientBirthDate"),
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


def handle_study_arrived_at_orthanc(item, source: Orthanc, dest: Dispatcher):

    orth = source
    disp = dest
    oid = item.get("oid")

    _item = orth.get(oid)
    siren_info = orth.gateway.get_metadata(oid, DCMLv.STUDIES, "siren_info")
    if not siren_info:
        # This is not an anonymized study
        return

    _item.meta["siren_info"] = unpack_siren_info(siren_info)
    logging.debug(pformat(_item.meta["siren_info"]))

    fp = Path(_item.meta["siren_info"]["FileName"]).relative_to(base_dir_name)
    channels = [
        fp.parts[0],              # ie, hobit
        "/".join(fp.parts[0:2])   # ie, hobit/hennepin
    ]
    logging.debug(channels)
    disp.put(_item, channels=channels)  # Will put multiple messages on the queue
    disp.handle_queue()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    _service_descs = os.path.expandvars(service_descs)
    services = yaml.load(_service_descs)

    d = ObservableDcmDir(**services["incoming_dir"])
    o = ObservableOrthanc(**services["dicom_arch"])
    p = Dispatcher(**services["dispatcher"])

    def add_route(self: Watcher, source: Endpoint, event_type, func, **kwargs):

        func = partial(func, source=source, **kwargs)
        t = Trigger(event_type,
                    source=source,
                    action=func)
        self.add_trigger(t)

    Watcher.add_route = add_route
    w = Watcher()

    w.add_route(d, DCMEv.FILE_ADDED,  handle_file_arrived_in_dcm_dir,  dest=o, salt=salt)
    w.add_route(o, DCMEv.STUDY_ADDED, handle_study_arrived_at_orthanc, dest=p)

    # print(w.triggers)

    # o.clear()
    # w.run()

    item = {"oid": "91499a9e-abbc193d-fb780cbb-5fd054d3-46a4e2fe"}
    handle_study_arrived_at_orthanc(item, o, p)
