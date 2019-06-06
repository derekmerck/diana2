"""
Collect a list of accession numbers, process them, and save them

1. Get patient info and StudyUIDs for each a/n
2. Copy each item and anonymize it
3. Send each item to the destination orthanc/path for review

"""

import os, logging
from typing import Iterable, Union
from pathlib import Path
from multiprocessing import Pool
import attr

from diana.apis import Orthanc, CsvFile, DcmDir
from diana.dixel import Dixel, ShamDixel, DixelView
# from diana.utils.endpoint import Endpoint
from diana.utils.dicom import DicomLevel

from requests.exceptions import HTTPError
from diana.utils.gateways.exceptions import GatewayConnectionError


@attr.s
class Collector(object):

    pool_size = attr.ib( default=0 )
    pool = attr.ib( init=False, repr=False )

    @pool.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    def run(self,
            project: str,
            data_path: Path,
            source: Orthanc, domain: str,
            dest: Union[Orthanc, DcmDir],
            anonymize=False):

        logging.getLogger("GUIDMint").setLevel(level=logging.WARNING)

        studies_path = data_path / Path("{}.studies.txt".format(project))
        key_path = data_path / Path("{}.key.csv".format(project))
        if not os.path.isfile(key_path):
            # Need to create a key from studies
            with open(studies_path) as f:
                study_ids = f.read().splitlines()
                print("Created study id set ({})".format(len(study_ids)))
                worklist = self.make_key(study_ids, source, domain)
                C = CsvFile(fp=key_path, level=DicomLevel.STUDIES)
                C.dixels = worklist
                C.write(fieldnames="ALL")
        else:
            C = CsvFile(fp=key_path, level=DicomLevel.STUDIES)
            C.read()
            worklist = C.dixels
        self.handle_worklist(worklist, source, domain, dest, anonymize)

    def make_key(self, ids, source: Orthanc, domain: str) -> set:

        print("Making key")

        # Minimal data for oid and sham plus study and series desc
        def mkq(accession_num):
            return {
                "PatientName": "",
                "PatientID": "",
                "PatientBirthDate": "",
                "PatientSex": "",
                "AccessionNumber": accession_num,
                "StudyDescription": "",
                "StudyInstanceUID": "",
                "StudyDate": "",
                "StudyTime": "",
            }

        items = set()
        for id in ids:

            q = mkq(id)

            try:
                r = source.rfind(q, domain, level=DicomLevel.STUDIES)
            except:
                r = None

            if not r:
                print("Failed to collect an id")
                continue

            tags = {
                "PatientName": r[0]["PatientName"],
                "PatientID": r[0]["PatientID"],
                "PatientBirthDate": r[0]["PatientBirthDate"],
                "PatientSex": r[0]["PatientSex"],
                "AccessionNumber": r[0]["AccessionNumber"],
                "StudyDescription": r[0]["StudyDescription"],
                "StudyInstanceUID": r[0]["StudyInstanceUID"],
                "StudyDate": r[0]["StudyDate"],
                "StudyTime": r[0]["StudyTime"]
            }

            d = Dixel(tags=tags)
            e = ShamDixel.from_dixel(d)

            items.add(e)
            print("Found {} items".format(len(items)))

            logging.debug(e)

        return items

    # TODO: Could replace Orthanc + domain with a ProxiedDICOM source
    def handle_worklist(self, items: Iterable, source: Orthanc, domain: str, dest: Union[Orthanc, DcmDir], anonymize):

        print("Handling worklist")

        if isinstance(source, Orthanc) and isinstance(dest, Orthanc):
            self.pull_and_send(items, source, domain, dest, anonymize)
        elif isinstance(source, Orthanc) and isinstance(dest, DcmDir):
            self.pull_and_save(items, source, domain, dest, anonymize)
        else:
            raise ValueError("Unknown handler")

    # TODO: Could merge with pull_and_send if the api for Orthanc and DcmDir were closer
    def pull_and_save(self, items: Iterable, source: Orthanc, domain: str, dest: DcmDir, anonymize=False):

        def mkq(d: Dixel):
            return {
                "StudyInstanceUID": d.tags["StudyInstanceUID"]
            }

        for d in items:

            working_level = DicomLevel.STUDIES

            if anonymize:

                if working_level == DicomLevel.SERIES:
                    d_fn = "{}-{}.zip".format(
                        d.meta["ShamAccessionNumber"][0:6],
                        d.meta["ShamSeriesDescription"])
                else:
                    d_fn = "{}.zip".format(
                        d.meta["ShamAccessionNumber"][0:16])

            else:

                if working_level == DicomLevel.SERIES:
                    d_fn = "{}-{}-{}.zip".format(
                        d.tags["PatientName"][0:6],
                        d.tags["AccessionNumber"][0:8],
                        d.tags["SeriesDescription"])
                else:
                    d_fn = "{}-{}.zip".format(
                        d.tags["PatientName"][0:6],
                        d.tags["AccessionNumber"][0:8])

            if dest.exists(d_fn):
                logging.debug("SKIPPING {}".format(d.tags["PatientName"]))
                continue

            if not source.exists(d):
                source.rfind(mkq(d),
                             domain,
                             level=working_level,
                             retrieve=True)
            else:
                logging.debug("SKIPPING PULL for {}".format(d.tags["PatientName"]))

            if anonymize:
                try:
                    replacement_map = ShamDixel.orthanc_sham_map(d)

                    anon_id = source.anonymize(d, replacement_map=replacement_map)

                    e = source.get(anon_id, level=working_level, view=DixelView.FILE)
                    e.meta["FileName"] = d_fn
                    logging.debug(e)

                    dest.put(e)
                    source.delete(e)

                except (HTTPError, GatewayConnectionError) as e:
                    logging.error("Failed to anonymize dixel")
                    logging.error(e)
                    with open("errors.txt", "a+") as f:
                        f.write(d.tags["AccessionNumber"] + "\n")

            else:
                d = source.get(d, level=working_level, view=DixelView.FILE)
                dest.put(d)

            try:
                source.delete(d)
            except GatewayConnectionError as e:
                logging.error("Failed to delete dixel")
                logging.error(e)

    def pull_and_send(self, items: Iterable, source: Orthanc, domain: str, dest: Orthanc, anonymize=False):

        def mkq(d: Dixel):
            return {
                "StudyInstanceUID": d.tags["StudyInstanceUID"]
            }

        for d in items:

            sham_oid = ShamDixel.sham_oid(d)
            logging.debug(sham_oid)
            if dest.exists(sham_oid):
                logging.debug("SKIPPING {}".format(d.tags["PatientName"]))
                continue

            if not source.exists(d):
                source.rfind(mkq(d),
                        domain,
                        level=DicomLevel.STUDIES,
                        retrieve=True)
            else:
                logging.debug("SKIPPING PULL for {}".format(d.tags["PatientName"]))

            replacement_map = ShamDixel.orthanc_sham_map(d)
            anon_id = source.anonymize(d, replacement_map=replacement_map)

            source.psend(anon_id, dest)
            source.delete(anon_id)
            source.delete(d)

