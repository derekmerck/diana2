import os, logging
import attr
import pydicom

@attr.s
class DcmFileHandler():

    name = attr.ib(default="DcmFileHandler")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

    def make_path(self, fn: str) -> str:
        fp = self.path
        for i in range(self.subpath_depth):
            start = i*self.subpath_width
            end = start + self.subpath_width
            segment = fn[start:end]
            fp = os.path.join(fp, segment)
        fp = os.path.join(fp, fn)
        return fp

    def write(self, fn: str, fdata):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Writing {}".format(fp))
        with open(fp, "wb" ) as f:
            f.write(fdata)

    def read(self, fn: str, get_pixels=False):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Reading {}".format(fp))
        ds = pydicom.dcmread(fp, stop_before_pixels=not get_pixels)
        return ds

    def get_file(self, fn: str):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Getting file {}".format(fp))
        with open(fp, "rb") as f:
            fdata = f.read()
        return fdata

    def exists(self, fn: str):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Checking exists {}".format(fp))
        return os.path.exists(fp)

    def delete(self, fn: str):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Deleting {}".format(fp))
        os.remove(fp)
