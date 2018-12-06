import csv, logging
import attr
from ..dixel import Dixel
from ..utils import Endpoint, Serializable
from ..utils.dicom import DicomLevel

@attr.s
class CsvFile(Endpoint, Serializable):

    fp = attr.ib(default=None)
    level = attr.ib(default=DicomLevel.STUDIES)
    name = attr.ib(default="CsvFile")
    dixels = attr.ib(init=False, factory=set)
    fieldnames = attr.ib(init=False, factory=list)

    def read(self, fp: str=None):
        logger = logging.getLogger(self.name)

        fp = fp or self.fp
        if not fp:
            raise ValueError("No file provided")

        with open(fp) as f:
            reader = csv.DictReader(f)
            self.fieldnames = reader.fieldnames
            for item in reader:
                # logger.debug(item)
                d = Dixel(tags=dict(item), level=self.level)
                self.dixels.add(d)

    def write(self, fp: str=None):
        logger = logging.getLogger(self.name)

        fp = fp or self.fp
        if not fp:
            raise ValueError("No file provided")

        with open(fp, "w") as f:
            fields = self.fieldnames
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for item in self.dixels:
                writer.writerow(item.tags)
