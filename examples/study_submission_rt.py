"""
SIREN Trial Network upload monitor

Desired process:

1. As each new PHI, partial-anon, or anon study arrives in folder proj/site
2.   Each instance is uploaded and anonymized (instance-by-instance to
     create serial instance times if possible)
3. As each anonymized study becomes stable
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
import yaml
import json
from cryptography.fernet import Fernet
from crud.abc import Endpoint
from diana.apis import DcmDir, Orthanc, ObservableDcmDir, ObservableOrthanc
from diana.dixel import Dixel, ShamDixel
from diana.utils.endpoint import Watcher, Trigger
from diana.utils.dicom import DicomLevel as DCMLv
from diana.utils.dicom.events import DicomEventType as DCMEv
# from wuphf.endpoints import SmtpMessenger
from wuphf.daemons import Dispatcher

service_descs = """
---
incoming_dir:
  ctype:     DicomDir
  path:      "/data/incoming"
  
dicom_arch:
  ctype:     ObservableOrthanc
  host:      orthanc
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
  -e ORTHANC_PASSWORD \
  -e ORTHANC_METADATA_0=siren_info,9875 \
  --name orthanc derekmerck/orthanc-wbv:latest-amd64
  
$ docker run -d -p 8000:8000 -p 8088:8088 -p 8089:8089 \
   -e SPLUNK_START_ARGS=--accept-license \
   -e SPLUNK_PASSWORD \
   -e SPLUNK_HEC_TOKEN \
   --name splunk splunk/splunk:latest
   
$ docker run -d \
   -v /data:/data \
   -v `pwd`/services.yaml:/services.yaml:ro \
   --env-file .env \
   -e DIANA_SERVICES_PATH=/services.yaml \
   --link splunk --link orthanc \
   --name diana diana2.1
"""

# 1. Create .env file
# 2. Create orthanc container w/meta for siren_info
# 3. Create and configure splunk container
# 4. Create /incoming directory\
# 5. Create services.yaml file (as above)
# 5. Create diana2 container with map to /incoming, /services.yaml,
#    and links to splunk, orthanc

# Parameters
salt = os.environ.get("PROJECT_SALT") # Unique subject anonymization namespace
# fernet_key = Fernet.generate_key()
fernet_key = os.environ.get("PROJECT_FERNET_KEY").encode("UTF8")
base_dir_name = "/incoming"  # dispatcher channels are relative paths to here

# Globals
tagged_studies = deque(maxlen=50)  # history


def pack_siren_info(d: Dixel, source: str) -> str:

    res = {
        "PatientName": d.tags["PatientName"],
        "ShamPatientName": d.meta["ShamPatientName"],
        "filename": d.fn,
        "timestamp": datetime.now(),
        "source": source
    }
    clear_text = json.dumps(res)
    f = Fernet(fernet_key)
    token = f.encrypt(clear_text)
    return token


def unpack_siren_info(token: str) -> Mapping:

    f = Fernet(fernet_key)
    clear_text = f.decrypt(token)
    res = json.loads(clear_text)
    return res


def _handle_instance_in_dcm_dir(item: Dixel, orth: Orthanc, salt: str):

    orth.put(item)
    anon = ShamDixel(item, salt=salt)
    afile = orth.anonymize(anon)
    anon.file = afile
    orth.put(anon)
    orth.delete(item)

    anon_study_id = anon.parent_oid(DCMLv.STUDIES)
    if anon_study_id not in tagged_studies:
        siren_info = pack_siren_info(anon)
        orth.gateway.put_metadata(anon_study_id, DCMLv.STUDIES, "siren_info", siren_info)
        tagged_studies.append(anon_study_id)


def handle_study_arrived_in_dcm_dir(filename, source: DcmDir, dest: Orthanc, salt=None):

    dcm_dir = source
    items = dcm_dir.get_zipped(filename)
    for item in items:
        _handle_instance_in_dcm_dir(item, dest, salt)


def handle_instance_arrived_in_dcm_dir(filename, source: DcmDir, dest: Orthanc, salt=None):

    dcm_dir = source
    item = dcm_dir.get(filename)
    _handle_instance_in_dcm_dir(item, dest, salt)


def handle_study_arrived_at_orthanc(oid, source: Orthanc, dest: Dispatcher):

    orth = source
    disp = dest

    item = orth.get(oid)
    siren_info = orth.gateway.get_metadata(oid, DCMLv.STUDIES, "siren_info")
    if not siren_info:
        # This is not an anonymized study
        return

    item.meta["siren_info"] = unpack_siren_info(siren_info)

    fp = Path(item.meta["siren_info"]["filename"]).relative_to(base_dir_name)
    channels = [
        fp.parents[0], # ie, hobit/hennepin
        fp.parents[1]  # ie, hobit
    ]
    disp.put(item, channels=channels)  # Will put multiple messages on the queue
    disp.handle_queue()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    services = yaml.load(service_descs)

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

    w.add_route(d, DCMEv.STUDY_ADDED, handle_study_arrived_in_dcm_dir, dest=o, salt=salt)
    w.add_route(d, DCMEv.INSTANCE_ADDED, handle_instance_arrived_in_dcm_dir, dest=o, salt=salt)
    w.add_route(o, DCMEv.STUDY_ADDED, handle_study_arrived_at_orthanc, dest=p)

    print(w.triggers)

    w.run()
