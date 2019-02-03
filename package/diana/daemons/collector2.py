from multiprocessing import Pool
from functools import partial
from datetime import datetime, timedelta
from typing import Union, Iterable
from pathlib import Path
import attr

from ..apis import ProxiedDicom, DcmDir, ImageDir, CsvFile, Montage
from ..dixel import Dixel
from ..utils.gateways import MontageModality as Modality, TextFileHandler
from .routes import put_item, pull_and_save_item


def test(montage: Montage, pacs: ProxiedDicom, dest_path: Path):

    query = {"q": "", "Modality": Modality.CR}
    start = datetime(year=2018, month=1, day=1)
    stop = datetime(year=2018, month=1, day=2)
    step = timedelta(hours=1)

    worklist = montage.iter_query_by_date(query, start, stop, step)

    c = Collector()
    c.run(worklist=worklist,
          source=pacs,
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

    def run(self, worklist: Iterable,
            source: ProxiedDicom,
            dest_path: Path,
            inline_reports: bool = True,
            anonymize: bool = True,
            save_as_im: bool = False):

        meta_path = dest_path / "meta"

        if save_as_im:
            data_dest = ImageDir(path=dest_path / "images",
                                 subpath_width=2,
                                 subpath_depth=2,
                                 anonymizing=anonymize
                                 )
        else:
            data_dest = DcmDir(path=dest_path / "images",
                               subpath_width=2,
                               subpath_depth=2
                               )

        if inline_reports:
            report_dest = TextFileHandler(path=dest_path / "reports",
                                          subpath_width=2,
                                          subpath_depth=2)
        else:
            report_dest = None

        if self.pool_size == 0:
            for item in worklist:
                Collector.handle_item(item=item,
                                 source=source,
                                 meta_path=meta_path,
                                 data_dest=data_dest,
                                 report_dest=report_dest,
                                 anonymize=anonymize)
        else:
            p = partial(Collector.handle_item,
                         source=source,
                         meta_path=meta_path,
                         data_dest=data_dest,
                         report_dest=report_dest,
                         anonymize=anonymize)
            self.pool.map(p, worklist)

    @staticmethod
    def handle_item(item: Dixel,
                    source: ProxiedDicom,
                    meta_path: Path,
                    data_dest: Union[DcmDir, ImageDir],
                    report_dest: TextFileHandler = None,
                    anonymize=True):

        # TODO: Need early exit for already handled, ie, hash a/n exists

        # Minimal data for oid and sham plus study desc
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

        # TODO: Should report data to redis and aggregate later to avoid mp locks
        meta_fn = "{:04}-{:02}.csv".format(item.meta["StudyDateTime"].year,
                                     item.meta["StudyDateTime"].month)
        key = CsvFile(fp=meta_path / meta_fn)
        # key.put(item, include_report=(report_dest is not None), anonymize=anonymize)

        if report_dest:
            # report_dest.put(item, anonymize=anonymize)
            report_dest.put(item)

        pull_and_save_item(item, source, data_dest, anonymize=anonymize)


