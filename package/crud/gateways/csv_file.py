import csv
import logging
import attr
from ..utils import stringify


@attr.s
class CsvGateway(object):
    """
    Simple dictionary read/write handler for csv files
    """

    fp = attr.ib()

    def read(self):
        logging.debug("Reading")
        try:
            with open(self.fp, "r") as f:
                items = []
                reader = csv.DictReader(f)
                for item in reader:
                    items.append(item)
                return items
        except FileNotFoundError:
            logging.warning("No csv file")

    def write(self, items, fieldnames=None):
        logging.debug("Writing")

        if not fieldnames:
            fieldnames = set()
            for item in items:
                for key in item.keys():
                    fieldnames.add(key)
            fieldnames = list(fieldnames)

        logging.debug(fieldnames)

        with open(self.fp, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in items:
                _item = {}
                for key in fieldnames:
                    _item[key] = stringify(item[key])
                logging.debug(_item)
                writer.writerow(_item)
