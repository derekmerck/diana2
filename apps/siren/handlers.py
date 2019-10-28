import os
from functools import partial
import logging
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


def handle_notify_study(source: Orthanc,
                        oid,
                        dispatcher: Dispatcher=None,
                        dryrun: bool=False,
                        indexer: Splunk=None,
                        index_name="dicom",
                        fkey=None,
                        signature_meta_key="signature"):

    try:
        item = source.get(oid, level=DLv.STUDIES)
    except:
        logging.error(f"Received bad study oid for upload: {oid}")
        return

    if fkey and signature_meta_key:
        try:
            metadata = source.getm(item, key=signature_meta_key)
            metadata = unpack_data(metadata, fkey)
            item.meta[signature_meta_key] = metadata
        except GatewayConnectionError:
            # This is not an anonymized study
            logging.warning(f"Found non-anonymized study: {oid}")
            return

    if dispatcher:
        trial = item.meta.get(signature_meta_key).get("trial")
        site = item.meta.get(signature_meta_key).get("site")
        if not trial or not site:
            raise ValueError("Missing info to set study distribution channel")
        channel = "{}-{}".format(trial,site)
        dispatcher.put(item, channels=[channel])
        dispatcher.handle_queue(dryrun=dryrun)

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

    if fkey and signature_meta_key:
        anon_study_oid = anon.sham_parent_oid(DLv.STUDIES)
        if anon_study_oid not in tagged_studies:
            sig_value = item.pack_fields(fkey, SIGNATURE_ELEMENTS)
            dest.putm(anon.sham_parent_oid(DLv.STUDIES),
                      level=DLv.STUDIES, key=signature_meta_key, value=sig_value)
            tagged_studies.appendleft(anon_study_oid)


def handle_upload_zip(source: DcmDir,
                      fn,
                      dest: Orthanc,
                      fkey=None,
                      signature_meta_key="signature",
                      anon_salt=None):

    # Assume input DcmDir basepath is incoming/trial/site
    _path, site = os.path.split(source.path)
    _, trial = os.path.split(_path)

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

    # Assume input DcmDir basepath is incoming/trial/site
    _path, site = os.path.split(source.path)
    _, trial = os.path.split(_path)

    items = []
    for root, dirs, files in os.walk(source.path):
        for file in files:
            items.append(os.path.join(root, file))

    for item in items:
        _item = source.get(item, file=True)
        if _item:
            _item.meta["trial"] = trial
            _item.meta["site"] = site
            handle_upload_file(_item, dest,
                        fkey=fkey,
                        signature_meta_key=signature_meta_key,
                        anon_salt=anon_salt)


def handle_file_arrived(item, source: DcmDir,
                        dest: Orthanc,
                        fkey=None,
                        signature_meta_key="signature",
                        anon_salt=None):

    # Assume input DcmDir basepath is incoming/trial/site
    _path, site = os.path.split(source.path)
    _, trial = os.path.split(_path)

    fn = item.get("fn")
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
        _item = source.get(fn, file=True)
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
                  index_name = "dicom"):

        def add_route(self: Watcher, source: Endpoint, event_type, func, **kwargs):
            func = partial(func, source=source, **kwargs)
            t = Trigger(event_type,
                        source=source,
                        action=func)
            self.add_trigger(t)

        Watcher.add_route = add_route
        w = Watcher()

        w.add_route(source, DEvT.FILE_ADDED, handle_file_arrived,
                    dest=dest, salt=anon_salt,
                    fkey=fkey, signature_meta_key=signature_meta_key)
        w.add_route(dest, DEvT.STUDY_ADDED, handle_notify_study,
                    dispatcher=dispatcher, dryrun=dryrun,
                    index=indexer, index_name=index_name,
                    fkey=fkey, signature_meta_key=signature_meta_key)

        w.run()