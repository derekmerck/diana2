import os
from typing import Union, Mapping
from functools import partial
from ..dixel import Dixel, DixelView
from ..apis import *
from ..utils import DicomLevel, DicomEventType
from ..utils.endpoint import Endpoint, Serializable, Trigger


def put_item(item: str, source: Endpoint, dest: Endpoint, **kwargs):

    if isinstance(source, DcmDir) and isinstance(dest, Orthanc):
        return upload_item(fn=item, source=source,
                           dest=dest)

    elif isinstance(source, Orthanc) and isinstance(dest, Orthanc):
        return send_item(  oid=item, level=kwargs.get("level"), source=source,
                           dest=dest,
                           remove_src=kwargs.get("remove_src"),
                           anonymize=kwargs.get("anonymize"),
                           remove_anon=kwargs.get("remove_anon"))

    elif isinstance(source, Orthanc) and isinstance(dest, Splunk):
        return index_item( oid=item, level=kwargs.get("level"), source=source,
                           dest=dest, index=kwargs.get("index"), token=kwargs.get("token"))

    raise NotImplementedError

def send_item(oid: str, level: DicomLevel, source: Orthanc,
              dest: Union[Orthanc, str],
              remove_src=True,
              anonymize=False,
              remove_anon=True):

    if anonymize:
        _oid = source.anonymize(oid, level=level, remove=remove_src)
    else:
        _oid = oid

    source.psend(_oid, dest=dest)

    if remove_src:
        source.delete(oid, level=level)

    if anonymize and remove_anon:
        source.delete(_oid, level=level)

def upload_item(fn: str, source: DcmDir, dest: Orthanc):

    if os.path.splitext(fn)[1] == "zip":
        worklist = source.get_zipped(fn)
        for item in worklist:
            dest.put(item)
    else:
        item = source.get(fn, file=True)
        dest.put(item)


def index_item(oid: str, level: DicomLevel, source: Endpoint,
               dest: Endpoint, index=None, token=None):

    d = source.get(oid, level=level, view=DixelView.TAGS)
    dest.put(d, index=index, token=token)


def query_and_index(query: Mapping, level: DicomLevel, source: Orthanc, domain: str,
                    dest: Splunk, token: str, index: str):

    r = source.rfind(query=query, level=level, domain=domain)
    d = Dixel(tags=r)
    dest.put(d, index=index, hec_token=token)


# TESTING
def say(item: str, suffix: str=None):
    if suffix:
        item = item + suffix
    print(item)


def mk_route(hname, source_desc, dest_desc=None):

    print("Adding route {}".format(hname))

    if source_desc:
        source = Serializable.Factory.create(**source_desc)
    else:
        raise ValueError("Must include a source")

    dest = None
    if dest_desc:
        dest = Serializable.Factory.create(**dest_desc)

    # TESTING HANDLERS
    if hname == "say_instances":
        evtype = DicomEventType.INSTANCE_ADDED
        func = partial(say)

    elif hname == "say_hello_instances":
        evtype = DicomEventType.INSTANCE_ADDED
        func = partial(say, suffix=" says hello")

    elif hname == "say_series":
        evtype = DicomEventType.SERIES_ADDED
        func = partial(say)

    elif hname == "say_hello_series":
        evtype = DicomEventType.SERIES_ADDED
        func = partial(say, suffix=" says hello")

    elif hname == "say_studies":
        evtype = DicomEventType.STUDY_ADDED
        func = partial(say)

    elif hname == "say_hello_studies":
        evtype = DicomEventType.STUDY_ADDED
        func = partial(say, suffix=" says hello")

    # HANDLERS
    elif hname == "anon_and_send_studies":
        evtype = DicomEventType.STUDY_ADDED
        func = partial(send_item,
                       level=DicomLevel.STUDIES,
                       source=source, dest=dest,
                       anonymize=True)

    elif hname == "anon_and_send_instances":
        evtype = DicomEventType.INSTANCE_ADDED
        func = partial(send_item,
                       level=DicomLevel.INSTANCES,
                       source=source, dest=dest,
                       anonymize=True)

    elif hname == "upload_files":
        evtype = DicomEventType.FILE_ADDED
        func = partial(upload_item,
                       source=source, dest=dest)

    elif hname == "index_series":
        evtype = DicomEventType.SERIES_ADDED
        func = partial(index_item,
                       level=DicomLevel.SERIES,
                       source=source, dest=dest)

    elif hname == "index_instances":
        evtype = DicomEventType.INSTANCE_ADDED
        func = partial(index_item,
                       level=DicomLevel.INSTANCES,
                       source=source, dest=dest)

    else:
        raise NotImplementedError("No handler defined for {}".format(hname))

    return Trigger(source=source,
                   evtype=evtype,
                   action=func)

