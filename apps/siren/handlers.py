"""
SIREN Trial image management handlers

Desired process:

1. As each new PHI, partial-anon, or anon study arrives in the folder
   "/incoming/site/trial":
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
from functools import partial
import logging
from pathlib import Path
from collections import deque
from crud.abc import Endpoint, Watcher, Trigger
from crud.endpoints import Splunk
from crud.exceptions import GatewayConnectionError
from wuphf.daemons import Dispatcher
from diana.apis import Orthanc, DcmDir
from diana.dixel import Dixel, ShamDixel
from diana.utils.dicom import DicomLevel as DLv, DicomEventType as DEvT
from diana.utils import unpack_data


SIGNATURE_ELEMENTS = ["AccessionNumber", "PatientName", "AccessionNumber",
                      "StudyDateTime", "trial", "site"]

tagged_studies = deque(maxlen=20)  # Remember last 20 studies


def handle_notify_study(item,
                        source: Orthanc=None,
                        dispatcher: Dispatcher=None,
                        dryrun: bool=False,
                        indexer: Splunk=None,
                        index_name="dicom",
                        fkey=None,
                        signature_meta_key="signature"):

    logger = logging.getLogger("SirenNotify")

    oid = item.get("oid")
    try:
        item = source.get(oid, level=DLv.STUDIES)
    except GatewayConnectionError:
        logger.error(f"Unable to collect study: {oid}@{source}")
        return

    if fkey and signature_meta_key:
        try:
            metadata = source.getm(item, key=signature_meta_key)
            metadata = unpack_data(metadata, fkey)
            item.meta[signature_meta_key] = metadata
        except GatewayConnectionError:
            # This is not an anonymized study
            logger.warning(f"Found non-anonymized study: {oid}")
            return

    if dispatcher:
        # Trial Dispatcher type can infer the channels from the item signature
        dispatcher.put(item, dryrun=dryrun)

    if indexer:
        indexer.put(item, index=index_name)


def handle_upload_file(item: Dixel,
                       dest: Orthanc,
                       fkey=None,
                       signature_meta_key=None,
                       anon_salt=None):
    dest.put(item)
    anon = ShamDixel.from_dixel(item, salt=anon_salt)
    f = dest.anonymize(item, replacement_map=anon.orthanc_sham_map())
    dest.delete(item)
    anon.file = f
    dest.put(anon)

    logging.debug(f"Packing data w fkey: {fkey}")
    logging.debug(f"Packing data to sig meta: {signature_meta_key}")

    if fkey and signature_meta_key:
        anon_study_oid = anon.sham_parent_oid(DLv.STUDIES)
        if anon_study_oid not in tagged_studies:
            sig_value = item.pack_fields(fkey, SIGNATURE_ELEMENTS)
            dest.putm(anon.sham_parent_oid(DLv.STUDIES),
                      level=DLv.STUDIES, key=signature_meta_key, value=sig_value)
            tagged_studies.appendleft(anon_study_oid)
        # else:
        #     logging.debug("Already tagged study")


def handle_upload_zip(source: DcmDir,
                      fn,
                      dest: Orthanc,
                      fkey=None,
                      signature_meta_key="signature",
                      anon_salt=None):

    # Assume input DcmDir basepath is incoming/site/trial
    _path, trial = os.path.split(source.path)
    _, site = os.path.split(_path)

    items = source.get_zipped(fn)
    for item in items:
        item.meta["trial"] = trial
        item.meta["site"] = site
        handle_upload_file(item, dest, fkey=fkey,
                           signature_meta_key=signature_meta_key,
                           anon_salt=anon_salt)


def handle_upload_dir(source: DcmDir,
                      dest: Orthanc,
                      fkey=None,
                      signature_meta_key="signature",
                      anon_salt=None):

    # Assume input DcmDir basepath is incoming/site/trial
    _path, trial = os.path.split(source.path)
    _, site = os.path.split(_path)

    items = []
    for root, dirs, files in os.walk(source.path):
        for file in files:
            items.append(os.path.join(root, file))

    for item in items:
        try:
            _item = source.get(item, file=True)
        except NotImplementedError as e:
            print(f"Failed to read {item}")
            print(e)
            _item = None

        if _item:
            _item.meta["trial"] = trial
            _item.meta["site"] = site
            handle_upload_file(_item, dest,
                        fkey=fkey,
                        signature_meta_key=signature_meta_key,
                        anon_salt=anon_salt)


def handle_file_arrived(item,
                        source: DcmDir=None,
                        dest: Orthanc=None,
                        fkey=None,
                        signature_meta_key="signature",
                        anon_salt=None):

    fn = item.get("fn")

    # Assume input DcmDir basepath is /incoming and fn is trial/site/fn

    p = Path(fn).relative_to(source.path)
    pp = p.parent
    trial, site = os.path.split(pp)

    if fn.endswith(".zip"):
        items = source.get_zipped(fn)
        for _item in items:
            if _item:
                _item.meta["trial"] = trial
                _item.meta["site"] = site
            handle_upload_file(_item, dest,
                               fkey=fkey,
                               signature_meta_key=signature_meta_key,
                               anon_salt=anon_salt)
    else:
        try:
            _item = source.get(fn, file=True)
        except NotImplementedError as e:
            print(f"Failed to read {fn}")
            print(e)
            _item = None

        if item:
            _item.meta["trial"] = trial
            _item.meta["site"] = site
        handle_upload_file(_item, dest,
                           fkey=fkey,
                           signature_meta_key=signature_meta_key,
                           anon_salt=anon_salt)


def start_watcher(source: DcmDir,
                  dest: Orthanc,
                  fkey=None,
                  signature_meta_key="signature",
                  anon_salt=None,
                  dispatcher: Dispatcher=None,
                  dryrun: bool=False,
                  indexer: Splunk=None,
                  index_name="dicom"):

        def add_route(self: Watcher, source: Endpoint, event_type, func, **kwargs):
            func = partial(func, source=source, **kwargs)
            t = Trigger(event_type,
                        source=source,
                        action=func)
            self.add_trigger(t)

        Watcher.add_route = add_route
        w = Watcher()

        w.add_route(source, DEvT.FILE_ADDED, handle_file_arrived,
                    dest=dest, anon_salt=anon_salt,
                    fkey=fkey, signature_meta_key=signature_meta_key)

        def say(item, source):
            """Testing callback"""
            logging.debug(f"Received item: {item}@{source})")
            print(f"{item}@{source}")

        w.add_route(dest, DEvT.INSTANCE_ADDED, say)

        w.add_route(dest, DEvT.STUDY_ADDED, handle_notify_study,
                    dispatcher=dispatcher, dryrun=dryrun,
                    indexer=indexer, index_name=index_name,
                    fkey=fkey, signature_meta_key=signature_meta_key)

        w.run()