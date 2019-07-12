import os, logging
from pprint import pprint
from typing import Union, Mapping
from functools import partial
from ..dixel import Dixel, DixelView, ShamDixel
from ..apis import *
from ..utils import DicomLevel, DicomEventType
from ..utils.endpoint import Endpoint, Serializable, Trigger


def put_item(item: str, source: Endpoint, dest: Endpoint, **kwargs):

    if isinstance(source, DcmDir) and isinstance(dest, Orthanc):
        return upload_item(fn=item, source=source,
                           dest=dest)

    elif isinstance(source, ProxiedDicom) and (isinstance(dest, ImageDir) or isinstance(dest, DcmDir)):
        query = {"AccessionNumber", item.tags["AccessionNumber"]}
        return pull_and_save_item(query=query, level=item.level, source=source,
                           dest=dest,
                           anonymize=kwargs.get("anonymize"))

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


def pull_and_save_item(item: Dixel, source: ProxiedDicom,
              dest: Union[DcmDir, ImageDir],
              anonymize=False) -> str:

    if dest.exists(item):
        logging.debug("File already exists, exiting early")
        return "SKIPPED"

    query = {"AccessionNumber": item.tags["AccessionNumber"]}
    source.find(query=query, level=item.level, retrieve=True)

    # logging.debug("Retrieved id: {} vs item id: {}".format(r[0], item.oid() ))

    if anonymize and not isinstance(dest, ImageDir):
        # No need to anonymize if we are converting to images
        item = source.proxy.anonymize(item, remove=True)

    try:
        item = source.proxy.get(item, view=DixelView.FILE)
    except FileNotFoundError as e:
        logging.error(e)
        return "FAILED"

    dest.put(item)
    source.proxy.delete(item)

    return "COMPLETED"


def upload_item(item: Mapping, source: DcmDir, dest: Orthanc, anonymizing=False):

    logger = logging.getLogger("upload_item")
    logger.debug("Trying to upload {}".format(item))

    try:

        def _upload_instance(item):  # Should be all instances
            dest.put(item)
            if not dest.exists(item):
                raise ValueError("Missing Dixel {}".format(item.oid()))
            dest.gateway.put_metadata(item.oid(), DicomLevel.INSTANCES, "source", source.path)
            # Todo tag item with source metadata/make sure it persists on anonymized
            if anonymizing:
                shammed = ShamDixel.from_dixel(item)
                map = ShamDixel.orthanc_sham_map(shammed)
                f = dest.anonymize(item, level=DicomLevel.INSTANCES, replacement_map=map)
                dest.delete(item)
                F = Dixel(level=DicomLevel.INSTANCES)
                F.file = f
                dest.put(F)


        fn = item.get("fn", "")

        logger.debug("fn: {}".format(fn))
        logger.debug("ext: {}".format(os.path.splitext(fn)[1]))

        if os.path.splitext(fn)[1] == ".zip":
            worklist = source.get_zipped(fn)
            for item in worklist:
                _upload_instance(item)

        else:
            item = source.get(fn, view=DixelView.TAGS_FILE)
            dest.put(item)
            _upload_instance(item)

    except FileNotFoundError as e:
        logging.warning("Skipping {}".format(e))
        pass




def index_item(item: Mapping, level: DicomLevel, source: Endpoint,
               dest: Endpoint, index=None, token=None):

    try:
        oid = item.get("oid")
        d = source.get(oid, level=level, view=DixelView.TAGS)
        dest.put(d, index=index, token=token)
    except FileNotFoundError as e:
        logging.warning("Skipping {}".format(e))
        pass


def query_and_index(query: Mapping, level: DicomLevel, source: Orthanc, domain: str,
                    dest: Splunk, token: str, index: str):

    r = source.rfind(query=query, level=level, domain=domain)
    d = Dixel(tags=r)
    dest.put(d, index=index, hec_token=token)


# TESTING
def say(item: str, suffix: str=None):
    if suffix:
        item = item + suffix
    pprint(item)


def mk_route(hname, source_desc, dest_desc=None):

    print("Adding route {}".format(hname))

    if source_desc:
        source = Serializable.Factory.create(**source_desc)
    else:
        raise ValueError("Must include a source")

    dest = None
    if dest_desc:
        dest = Serializable.Factory.create(**dest_desc)

    logger = logging.getLogger("mk_route")
    logger.debug("Source: {}".format(source))
    logger.debug("Dest: {}".format(dest))

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

    elif hname == "upload_and_anonymize_files":
        evtype = DicomEventType.FILE_ADDED
        func = partial(upload_item,
                       source=source, dest=dest, anonymizing=True)

    elif hname == "say_files":
        evtype = DicomEventType.FILE_ADDED
        func = partial(say)

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

