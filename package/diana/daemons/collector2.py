from multiprocessing import Pool, Value
import itertools, logging
from time import sleep
from functools import partial
from datetime import datetime, timedelta
from typing import Union, Iterable
from pathlib import Path
import attr

from ..apis import ProxiedDicom, DcmDir, ImageDir, CsvFile, Montage, ReportDir
from ..dixel import Dixel
from .routes import put_item, pull_and_save_item
from ..utils.endpoint import Serializable

handled = Value('i', 0)
skipped = Value('i', 0)


@attr.s
class Collector(object):

    pool_size = attr.ib( default=0 )
    pool = attr.ib( init=False, repr=False )

    @pool.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    sublist_len = attr.ib( init=False )

    @sublist_len.default
    def estimate_sublist_len(self):
        return 2 * self.pool_size

    def run(self, worklist: Iterable,
            source: ProxiedDicom,
            dest_path: Path,
            inline_reports: bool = True,
            anonymize: bool = True,
            save_as_im: bool = False):

        tic = datetime.now()

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

        if not inline_reports:
            report_dest = ReportDir(path=dest_path / "reports",
                                    subpath_width=2,
                                    subpath_depth=2,
                                    anonymizing=anonymize)
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
            while True:
                result = self.pool.map(p, itertools.islice(worklist, self.sublist_len))
                if result:
                    sleep(0.1)
                else:
                    break

        toc = datetime.now()
        elapsed_time = (toc - tic).seconds or 1
        handling_rate = handled.value / elapsed_time

        print("Handled {} objects in {} seconds".format(handled.value, elapsed_time))
        print("Handling rate: {} objects per second".format(round(handling_rate, 1)))

    @staticmethod
    def handle_item(item: Dixel,
                    source: ProxiedDicom,
                    meta_path: Path,
                    data_dest: Union[DcmDir, ImageDir],
                    report_dest: ReportDir = None,
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

        # Get a fresh source, in case this is a pooled job
        source = Serializable.Factory.copy(source)

        r = source.find(mkq(item))
        if not r:
            logging.error("Item {} not findable!")
            return
        item.tags.update(r[0])

        # TODO: Should report data to redis and aggregate later to avoid mp locks
        # meta_fn = "{:04}-{:02}.csv".format(item.meta["StudyDateTime"].year,
        #                             item.meta["StudyDateTime"].month)
        # key = CsvFile(fp=meta_path / meta_fn)
        # key.put(item, include_report=(report_dest is not None), anonymize=anonymize)

        if report_dest:
            # report_dest.put(item, anonymize=anonymize)
            report_dest.put(item)

        result = pull_and_save_item(item, source, data_dest, anonymize=anonymize)

        if result:
            handled.value += 1
        else:
            skipped.value += 1

        print("Handled {} items and skipped {}".format(handled.value, skipped.value))

