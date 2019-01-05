"""
Collect a list of accession numbers, process them, and save them

1. Get patient info and StudyUIDs for each a/n
2. Copy each item and anonymize it
3. Send each item to the destination orthanc/path for review

"""

import os, logging
from pathlib import Path
from multiprocessing import Pool
import attr

from diana.apis import Orthanc, CsvFile, DcmDir
from diana.dixel import Dixel, ShamDixel, DixelView
from diana.utils.dicom import DicomLevel


########################

proxy = "bridge"
domain = "pacs"
dest = "review01"

########################

@attr.s
class Collector(object):

    pool_size = attr.ib( default=0 )
    pool = attr.ib( init=False, repr=False )
    @pool.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    def run(self, project, data_path: Path, source=None, dest=None):

        studies_path = data_path / "{}.studies.csv".format(project)
        key_path = data_path / "{}.key.csv".format(project)
        if not os.path.isfile(key_path):
            # Need to create a key from studies
            with open(studies_path) as f:
                study_ids = f.read().splitlines()
                worklist = self.make_key(study_ids, source)
                C = CsvFile(fp=key_path, level=DicomLevel.STUDIES)
                C.dixels = worklist
                C.write(fieldnames="ALL")
        else:
            C = CsvFile(fp=key_path, level=DicomLevel.STUDIES)
            worklist = C.read().dixels
        self.handle_worklist(worklist, source, dest)

    def make_key(self, ids, source: Orthanc) -> set:

        # Minimal data for oid and sham plus study and series desc
        def mkq(accession_num):
            return {
                "PatientName": "",
                "PatientID": "",
                "PatientBirthDate": "",
                "PatientSex": "",
                "AccessionNumber": accession_num,
                "StudyDescription": "",
                "StudyInstanceUID": ""
            }

        items = set()
        for id in ids:

            q = mkq(id)
            # logging.debug(pformat(q))
            r = source.rfind(q, domain, level=DicomLevel.STUDIES)

            tags = {
                "PatientName": r[0]["PatientName"],
                "PatientID": r[0]["PatientID"],
                "PatientBirthDate": r[0]["PatientBirthDate"],
                "PatientSex": r[0]["PatientSex"],
                "AccessionNumber": r[0]["AccessionNumber"],
                "StudyDescription": r[0]["StudyDescription"],
                "StudyInstanceUID": r[0]["StudyInstanceUID"]
            }

            d = Dixel(tags=tags)
            e = ShamDixel.from_dixel(d)
            items.add(e)
            logging.debug(e)

        return items

    # Check for exists, pull if needed, anon if needed based on shams, dl and save arch
    def handle_worklist(self, items, source, dest):

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

