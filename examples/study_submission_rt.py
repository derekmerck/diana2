"""
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

from pathlib import Path
from collections import deque
from functools import partial
from typing import Mapping
from datetime import datetime
import yaml
import json
from cryptography.fernet import Fernet
from crud.abc import Endpoint
from diana.apis import DcmDir, Orthanc
from diana.dixel import Dixel, ShamDixel
from diana.utils.endpoint import Watcher, Trigger
from diana.utils.dicom import DicomLevel as DCMLv
from diana.utils.dicom.events import DicomEventType as DCMEv
from wuphf.daemons import Dispatcher

service_descs = """

incoming_dir:
  ctype: DicomDir
  path: "/incoming"
  
dicom_arch:
  ctype: ObservableOrthanc
  host: localhost
  port: 8080
  user: blah
  password: blah
  meta_keys: siren_info

smtp_server:  &SMTP_SERVER
  ctype: SmtpMessenger
  host: localhost
  user: blah
  password: blah

subscriptions: &SUBSCRIPTIONS
- channel: hobit
  subscribers:
    - name: someone
      email: someone@umich.hosp

- channel: hobit/hennepin
  subscribers:
    - name: abc
      email: abc@hennepin.hosp
      role: pi  
    - name: xyz
      email: xyz@hennepin.hosp
      role: coord
  
- channel: hobit/detroit
  subscribers:
    - name: def
      email: def@detroit.hosp
      role: pi
      
dispatcher:
  ctype: Dispatcher
  smtp_messenger_desc: *SMTP_SERVER
  subscriptions_desc: *SUBSCRIPTIONS
  
"""

salt = "SiReN+SaLt+123!"
# fernet_key = Fernet.generate_key()
fernet_key = b'Y8m2LL3poi1rA7NYwDSYHsaItIF7_sGM8TR5Ah5criE='
tagged_studies = deque(maxlen=50)  # history
base_dir_name = "/incoming"


def pack_siren_info(d: Dixel, source: str, salt=None) -> str:

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


def _handle_instance_in_dcm_dir(item, orth, salt):

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

    services = yaml.load(service_descs)

    d = DcmDir(**services["incoming_dir"])
    o = Orthanc(**services["dicom_arch"])
    p = Dispatcher(**services["dispatcher"])

    def add_route(self: Watcher, source: Endpoint, event_type, func, **kwargs):

        func = partial(func, source=source, **kwargs)
        t = Trigger(event_type,
                    source=source,
                    action=func)
        self.add_trigger(t)

    Watcher.add_route = add_route
    w = Watcher()

    w.add_route(d, DCMEv.INSTANCE_ADDED, handle_study_arrived_in_dcm_dir, dest=o, salt=salt)
    w.add_route(d, DCMEv.INSTANCE_ADDED, handle_instance_arrived_in_dcm_dir, dest=o, salt=salt)
    w.add_route(o, DCMEv.STUDY_ADDED, handle_study_arrived_at_orthanc, dest=p)

    print(w.triggers)

    # w.run()
