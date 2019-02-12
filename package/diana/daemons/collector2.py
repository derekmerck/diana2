from multiprocessing import Pool, Value, Process, Queue, Manager
from multiprocessing.managers import BaseProxy
import itertools, logging, hashlib
from time import sleep
from functools import partial
from datetime import datetime, timedelta
from typing import Union, Iterable
from pathlib import Path
import attr

from ..apis import ProxiedDicom, DcmDir, ImageDir, CsvFile, ReportDir
from ..dixel import Dixel, DixelView
from ..utils.endpoint import Serializable
from ..utils.gateways import CSVPMap, CSVArrayPMap

handled = Value('i', 0)
skipped = Value('i', 0)
failed = Value('i', 0)

# TODO: Don't write key if no change
# TODO: Don't write report if no change
# DONE: Don't pull images if images already exist
# TODO: Add image file hashes for each key item?
# TODO: Add consistent patient id and datetime for each key item?


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

    @staticmethod
    def worklist_from_accession_nums(fn: Path):
        with open(fn) as f:
            study_ids = f.read().splitlines()
            print("Created study id set with {} items".format(len(study_ids)))
            return study_ids

    def run(self, worklist: Iterable,
            source: ProxiedDicom,
            dest_path: Path,
            inline_reports: bool = True,
            anonymize: bool = True,
            save_as_im: bool = False,
            delay: float=0.1):

        tic = datetime.now()

        if save_as_im:
            data_dest = ImageDir(path=dest_path / "images",
                                 subpath_width=2,
                                 subpath_depth=2,
                                 anonymizing=anonymize)
        else:
            data_dest = DcmDir(path=dest_path / "images",
                               subpath_width=2,
                               subpath_depth=2)

        if not inline_reports:
            report_dest = ReportDir(path=dest_path / "reports",
                                    subpath_width=2,
                                    subpath_depth=2,
                                    anonymizing=anonymize)
        else:
            report_dest = None

        pattern = "{}/meta/key-{{}}.csv".format(dest_path)
        fieldnames = ["id", "modality", "body_parts", "cpts",
                      "age", "sex", "status", "radcat"]
        key_handler = CSVArrayPMap(fn=pattern, keyfield="id", fieldnames=fieldnames)

        if self.pool_size == 0:
            for item in worklist:
                Collector.handle_item(item=item,
                                 source=source,
                                 data_dest=data_dest,
                                 report_dest=report_dest,
                                 anonymize=anonymize,
                                 key_handler=key_handler)
        else:
            m = Manager()
            q = m.Queue()
            kh = Process(target=key_handler.run, args=[q], kwargs={"early_exit": True})
            kh.start()

            p = partial(Collector.handle_item,
                         source=source,
                         data_dest=data_dest,
                         report_dest=report_dest,
                         anonymize=anonymize,
                         key_handler=q)

            while True:
                result = self.pool.map(p, itertools.islice(worklist, self.sublist_len))
                if result:
                    sleep(delay)
                else:
                    break
            kh.terminate()

        toc = datetime.now()
        elapsed_time = (toc - tic).seconds or 1
        handling_rate = handled.value / elapsed_time

        print("Handled {} objects in {} seconds".format(handled.value, elapsed_time))
        print("Handling rate: {} objects per second".format(round(handling_rate, 1)))
        print("Skipped {}".format(skipped.value))
        print("Failed {}".format(failed.value))


    @staticmethod
    def handle_item(item: Dixel,
                    source: ProxiedDicom,
                    data_dest: Union[DcmDir, ImageDir],
                    report_dest: ReportDir = None,
                    anonymize: bool=True,
                    key_handler=None):

        ####################
        # KEYING
        ####################

        try:
            radcat = item.report.radcat()
        except ValueError as e:
            logging.error(e)
            radcat = ""

        # The key handler anonymizes id by default
        key_id = item.tags["AccessionNumber"]
        key_data = {
            "modality": item.tags["Modality"],
            "body_parts": item.meta["BodyParts"],
            "cpts": item.meta["CPTCodes"],
            "age": item.meta['PatientAge'],
            "sex": item.tags["PatientSex"],
            "status": item.meta["PatientStatus"],
            "radcat": radcat
        }

        if key_handler:
            if isinstance(key_handler, BaseProxy):
                logging.debug("Found mp keying")
                key_handler.put((key_id, key_data))
            else:
                logging.debug("Direct keying")
                key_handler.put(key_id, key_data)

        ####################
        # REPORT
        ####################

        if report_dest:
            if not report_dest.exists(item):
                logging.debug("Adding report")
                report_dest.put(item)
            else:
                logging.debug("Skipping report")

        ####################
        # IMAGES
        ####################

        if data_dest.exists(item):
            logging.info("File already exists, exiting early")
            skipped.value += 1
            print("Handled {} items, skipped {}, failed {}".format(handled.value,
                                                                   skipped.value,
                                                                   failed.value))
            return

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
                "StudyTime": ""
            }

        # Get a fresh source, in case this is a pooled job
        source = Serializable.Factory.copy(source)

        r = source.find(mkq(item), retrieve=True)
        if not r:
            logging.error("Item {} not findable!".format(item))
            failed.value += 1
            print("Handled {} items, skipped {}, failed {}".format(handled.value,
                                                                   skipped.value,
                                                                   failed.value))
            return
        item.tags.update(r[0])

        # TODO: Log failures so we can retry them
        if not source.proxy.exists(item):
            logging.error("Item {} not retrieved!".format(item))
            failed.value += 1
            print("Handled {} items, skipped {}, failed {}".format(handled.value,
                                                                   skipped.value,
                                                                   failed.value))
            return

        if anonymize and not isinstance(data_dest, ImageDir):
            # No need to anonymize if we are converting to images
            item = source.proxy.anonymize(item, remove=True)

        try:
            item = source.proxy.get(item, view=DixelView.FILE)
        except FileNotFoundError as e:
            logging.error(e)
            failed.value += 1
            print("Handled {} items, skipped {}, failed {}".format(handled.value,
                                                                   skipped.value,
                                                                   failed.value))
            return

        data_dest.put(item)
        source.proxy.delete(item)

        handled.value += 1
        print("Handled {} items, skipped {}, failed {}".format(handled.value,
                                                               skipped.value,
                                                               failed.value))
