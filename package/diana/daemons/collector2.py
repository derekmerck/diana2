from multiprocessing import Pool
from datetime import datetime, timedelta
from typing import Union, Mapping, Iterable
from pathlib import Path
import attr

from diana.apis import ProxiedDicom, Orthanc, DcmDir, ImageDir, TextDir, CsvFile, Montage
from diana.dixel import Dixel, DixelView
from .routes import put_item
from diana.utils.endpoint import Endpoint
from diana.utils.gateways import MontageModality as Modality

montage = Montage()
query = {"q": "", "Modality": Modality.CR}
start = datetime(year=2018, month=1, day=1)
stop = datetime(year=2018, month=1, day=2)
step = timedelta(hours=1)

def test():
    worklists = montage.iter_query_by_date(query, start, stop, step)

    source = ProxiedDicom()
    dest_path = Path("/a/b/c")

    c = Collector()
    c.run(worklist=worklist,
          source=source,
          dest_path=dest_path,
          inline_reports=False,
          anonymize=True)


@attr.s
class Collector(object):

    pool_size = attr.ib( default=0 )
    pool = attr.ib( init=False, repr=False )
    @pool.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    # Worklists = iterable of lists of partial dixels, i.e., small Montage queries
    def run(self, worklists: Iterable,
            source: ProxiedDicom,
            dest_path: Path,
            inline_reports: bool = True,
            anonymize: bool = True):

        meta_path = dest_path / "meta"
        data_dest = ImageDir( dest_path / "images" )
        if inline_reports:
            report_dest = TextDir( dest_path / "reports" )
        else:
            report_dest = None

        for worklist in worklists:
            for item in worklist:

                self.handle_item(item=item,
                                 source=source,
                                 meta_path=meta_path,
                                 data_dest=data_dest,
                                 report_dest=report_dest,
                                 anonymize=anonymize)

    @staticmethod
    def handle_item(item: Dixel,
                    source: ProxiedDicom,
                    meta_path: Path,
                    data_dest: Union[DcmDir, ImageDir],
                    report_dest: TextDir = None,
                    anonymize=True):

        # Minimal data for oid and sham plus study and series desc
        def mkq(item):
            return {
                "PatientName": "",
                "PatientID": "",
                "PatientBirthDate": "",
                "PatientSex": "",
                "AccessionNumber": item.tags["AccessionNumber"],
                "StudyDescription": "",
                "StudyInstanceUID": "",
                "StudyDate": "",
                "StudyTime": "",
            }

        r = source.find(mkq(item))
        item.tags.update(r[0])

        meta_fn = "{}/{}.csv".format(item.meta["StudyDate"].year,
                                     item.meta["StudyDate"].month)
        key = CsvFile(fp=meta_path / meta_fn)
        key.put(item, include_report=(report_dest is not None), anonymize=anonymize)

        if report_dest:
            report_dest.put(item, anonymize=anonymize)

        put_item(item, source, data_dest, anonymize=anonymize)


