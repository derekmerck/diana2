import os
from typing import Union
from ..apis import Orthanc, DcmDir, Splunk, Redis
from ..dixel import Dixel
from ..utils.endpoint import Endpoint


def anonymize_and_send(oid: str, source: Orthanc, dest: Union[Orthanc, str],
                       remove_src=True,
                       remove_anon=True):

    e = source.anonymize(oid, remove=remove_src)
    source.psend(e, dest=dest)
    if remove_anon:
        source.delete(e)

def upload_files(fn: str, source: DcmDir, dest: Orthanc):

    if os.path.splitext(fn)[1] == "zip":
        worklist = source.get_zipped(fn)
    else:
        worklist = [ source.get(fn, file=True) ]

    for item in worklist:
        dest.put(item)

def add_to_index(item: str, source: Endpoint, dest: Union[Splunk, Redis], index=None):

    d = source.get(item, view="tags")
    dest.put(d, index=index)