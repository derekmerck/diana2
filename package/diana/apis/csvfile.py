import csv, logging, json
import attr
from ..dixel import Dixel, ShamDixel
from ..utils import Endpoint, Serializable
from ..utils.dicom import DicomLevel


@attr.s
class CsvFile(Endpoint, Serializable):

    fp = attr.ib(default=None)
    level = attr.ib(default=DicomLevel.STUDIES)
    name = attr.ib(default="CsvFile")
    dixels = attr.ib(init=False, factory=set)
    fieldnames = attr.ib(init=False, factory=list)

    def put(self, item: Dixel, force_write=False):
        self.dixels.add(item)

        if force_write:
            self.write()

    def exists(self, item: Dixel, **kwargs):
        logging.debug("Checking exists {}".format(item))
        logging.debug(self.dixels)
        if item in self.dixels:
            return True

    def read(self, fp: str=None):
        # logger = logging.getLogger(self.name)

        fp = fp or self.fp
        if not fp:
            raise ValueError("No file provided")

        with open(fp) as f:
            reader = csv.DictReader(f)
            self.fieldnames = reader.fieldnames
            for item in reader:

                meta = {k[1:]:v for (k,v) in item.items() if k.startswith("_")}
                tags = {k:v for (k,v) in item.items() if not k.startswith("_")}

                # logger.debug(item)
                d = Dixel(meta=meta,
                          tags=tags,
                          level=self.level)
                self.dixels.add(d)

    def write(self, fp: str=None, fieldnames=None):
        logger = logging.getLogger(self.name)

        fp = fp or self.fp
        # if not fp:
        #     raise ValueError("No file provided")

        if fieldnames=="ALL":
            sample = list(self.dixels)[0]
            data = {("_" + k): v for (k, v) in sample.meta.items()}
            data.update(sample.tags)
            fieldnames = data.keys()

        fieldnames = fieldnames or self.fieldnames

        with open(fp, "w+") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for item in self.dixels:
                data = {("_"+k):v for (k,v) in item.meta.items()}
                data.update(item.tags)
                writer.writerow(data)
