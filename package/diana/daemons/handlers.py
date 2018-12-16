import os
from typing import Union, Mapping
from ..apis import Orthanc, DcmDir, Splunk, Redis
from ..utils import DicomLevel
from ..utils.endpoint import Endpoint


def anonymize_and_send_item(oid: str, source: Orthanc, dest: Union[Orthanc, str],
                       remove_src=True,
                       remove_anon=True):

    e = source.anonymize(oid, remove=remove_src)
    source.psend(e, dest=dest)
    if remove_anon:
        source.delete(e)


def upload_item(fn: str, source: DcmDir, dest: Orthanc):

    if os.path.splitext(fn)[1] == "zip":
        worklist = source.get_zipped(fn)
        for item in worklist:
            dest.put(item)
    else:
        item = source.get(fn, file=True)
        dest.put(item)


def index_item(item: str, level: DicomLevel, source: Endpoint, dest: Union[Splunk, Redis], index=None):

    d = source.get(item, level=level, view="tags")
    dest.put(d, index=index)

