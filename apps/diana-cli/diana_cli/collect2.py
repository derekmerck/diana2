import os
import logging
import click
from enum import Enum
from typing import Tuple
from diana.utils.endpoint import Serializable
from diana.apis import *
from diana.dixel import Dixel, ShamDixel

epilog = """
\b
$ diana-cli -S /services.yml collect pacs path:/data 9999999 ...

"""

import attr
from diana.utils import Endpoint
from diana.dixel import DixelView


class HandlerStatus(Enum):
    FAILED = "failed"
    SKIPPED = "skipped"
    HANDLED = "handled"


@attr.s
class Collector2(object):

    source = attr.ib(type=Endpoint)
    meta = attr.ib(type=Endpoint)
    reports = attr.ib(type=Endpoint, default=None)
    images = attr.ib(type=Endpoint, default=None)

    pool = attr.ib(default=0)
    pause = attr.ib(default=0.01)

    dryrun = attr.ib(default=False)

    handled = attr.ib(init=False, default=0)
    skipped = attr.ib(init=False, default=0)
    failed  = attr.ib(init=False, default=0)

    def reset(self):
        self.handled = 0
        self.skipped = 0
        self.failed = 0

    @staticmethod
    def handle_item(item,
                    source: Endpoint,
                    meta: Endpoint,
                    reports: Endpoint,
                    images: Endpoint,
                    anonymize=False, dryrun=False):

        if isinstance(item, str):
            # It's an accession number
            accession_number = item
            item = Dixel(tags={"AccessionNumber": accession_number})

        # Check meta
        if not meta.exists(item):
            items = source.find(item, retrieve=False)
            if items:
                item = Dixel(tags=items[0])
                if anonymize:
                    item = ShamDixel.from_dixel(item)
                meta.put(item)  # force_write=True
            else:
                logging.warning("Failed on unfindable item {}".format(item))
                return HandlerStatus.FAILED
        else:
            item = meta.get(item)
            logging.info("Skipping find on keyed item")

        # Check reports
        if item.report and not reports.exists(item):
            reports.put(item)

        if anonymize:
            item.meta["FileName"] = "{}.zip".format(item.meta["ShamAccessionNumber"])
        else:
            item.meta["FileName"] = "{}.zip".format(item.tags["AccessionNumber"])

        # Check file
        if not images.exists(item):
            try:
                if not dryrun:
                    if anonymize:
                        _item = item
                        oid = source.anonymize(_item)
                        item = source.get(oid)
                        item.meta["FileName"] = "{}.zip".format(
                            item.tags["AccessionNumber"])

                    item = source.get(item, view=DixelView.FILE)
                    images.put(item)

                    source.delete(item)
                    if anonymize:
                        source.delete(_item)
            except FileNotFoundError as e:
                logging.warning(e)
                logging.warning("Failed on un-pullable item {}".format(item))
                return HandlerStatus.FAILED
        elif images.exists(item):
            logging.info("Skipping pull on existing item")
            return HandlerStatus.SKIPPED

        logging.info("Handled item {}".format(item))
        return HandlerStatus.HANDLED

    def run(self, worklist, anonymize=False, dryrun=False) -> Tuple[int, int, int]:

        logging.debug(worklist)
        for item in worklist:

            result = Collector2.handle_item(item,
                                            source=self.source,
                                            meta=self.meta,
                                            reports=self.reports,
                                            images=self.images,
                                            anonymize=anonymize,
                                            dryrun=dryrun)

            if result == HandlerStatus.SKIPPED:
                self.skipped += 1
            elif result == HandlerStatus.FAILED:
                self.failed += 1
            elif result == HandlerStatus.HANDLED:
                self.handled += 1
            else:
                raise ValueError("Unknown exit code from collection handler! {}".format(result))

        return self.handled, self.skipped, self.failed


@click.command(short_help="Collect and handle studies v2", epilog=epilog)

@click.argument("source", type=click.STRING)
@click.argument("dest",   type=click.STRING)

@click.argument("worklist", nargs=-1)
@click.option("-W", "--worklist_source", help="file or service")
@click.option("-q", "--query", help="worklist query (json)")
@click.option("-Q", "--query_source", help="json file with worklist query")
@click.option("-t", "--time_range", help="run query over time range")

@click.option("-a", "--anonymize", is_flag=True, default=False)

@click.option("-i", "--image_dest", help="Specify image dest")
@click.option("-m", "--meta_dest",  help="Specify meta dest")
@click.option("-r", "--report_dest", help="Specify report dest")

@click.option("-I", "--image_format", type=click.Choice("dicom", "png"),
              default="dicom", help="Convert images to format")
@click.option("-M", "--meta_format", type=click.Choice("csv", "json"), default="csv")
@click.option("-R", "--report_format", type=click.Choice("inline", "txt"))

@click.option("-b", "--subfolders", default=(2,2))
@click.option("-B", "--split_meta", type=int, default=None)

@click.option("-p", "--pool", type=int, default=None, help="Pool size for multi-threading")
@click.option("-P", "--pause", type=float, default=0.01, help="Pause between threads")
@click.option("-d", "--dryrun", is_flag=True, default=False, help="Process worklist and create keys without PACS pulls")

@click.pass_context
def collect2(ctx, source, dest,
            worklist, worklist_source,
            query, query_source,
            time_range,
            anonymize,
            image_dest, meta_dest, report_dest,
            image_format, meta_format, report_format,

            subfolders, split_meta,
            pool, pause, dryrun):

    """Pull data from SOURCE and save/send to DEST.  If source is a service,
    a QUERY must be provided, and a time range can be optionally provided for
    retrospective data collection (otherwise defaulting to real-time monitoring)."""
    services = ctx.obj.get('services')

    click.echo(click.style('Collect DICOM data', underline=True, bold=True))

    # Setup source
    _source = services[source]
    source_inst = Serializable.Factory.create(**_source)

    # Setup image destination
    if dest.startswith("path:") and image_format == "dicom":
        fp = os.path.join( dest[5:], image_dest or "images" )
        image_dest_inst = DcmDir(path=fp,
                                 subpath_depth=subfolders[0],
                                 subpath_width=subfolders[1])

    elif dest.startswith("path:") and image_format == "png":
        fp = os.path.join( dest[5:], image_dest or "images" )
        image_dest_inst = ImageDir(path=fp,
                                   subpath_depth=subfolders[0],
                                   subpath_width=subfolders[1])

    elif image_dest and services.get(image_dest):
        _dest = services(image_dest)
        image_dest_inst = Serializable.Factory.create(**_dest)

    elif services.get(dest):
        _dest = services(dest)
        image_dest_inst = Serializable.Factory.create(**_dest)

    else:
        image_dest_inst = None

    # Setup report destination
    if dest.startswith("path:") and report_format == "txt":
        fp = os.path.join( dest[5:], report_dest or "reports")
        report_dest_inst = ReportDir(path=fp,
                                     subpath_depth=subfolders[0],
                                     subpath_width=subfolders[1])

    elif report_dest and services.get(report_dest):
        _dest = services(report_dest)
        report_dest_inst = Serializable.Factory.create(**_dest)

    else:
        report_dest_inst = None

    # Setup meta dest
    if dest.startswith("path:") and meta_format == "csv":
        fp = os.path.join( dest[5:], meta_dest or "meta")
        meta_dest_inst = CsvFile(fp=fp)

    elif meta_dest and services.get(meta_dest):
        _dest = services(meta_dest)
        meta_dest_inst = Serializable.Factory.create(**_dest)

    else:
        meta_dest_inst = None

    # Create collector
    C = Collector2(source = source_inst,
                   meta = meta_dest_inst,
                   reports = report_dest_inst,
                   images = image_dest_inst,
                   pool = pool,
                   pause = pause )

    # Run it
    C.run(worklist, anonymize=anonymize, dryrun=dryrun)
