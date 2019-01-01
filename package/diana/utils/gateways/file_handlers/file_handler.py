import logging, os
from glob import glob
import attr

@attr.s
class FileHandler(object):

    name = attr.ib(default="FileHandler")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

    def get_path(self, fn: str) -> str:
        fp = self.path
        for i in range(self.subpath_depth):
            start = i*self.subpath_width
            end = start + self.subpath_width
            segment = fn[start:end]
            fp = os.path.join(fp, segment)
        fp = os.path.join(fp, fn)
        return fp

    def get_files(self, rex="*"):
        fp = self.get_path(rex)
        return [os.path.basename(x) for x in glob(fp)]

    def write_file(self, fn: str, fdata):
        """Write binary file data"""
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Writing {}".format(fp))

        if not os.path.exists( os.path.dirname(fp) ):
            os.makedirs(os.path.dirname(fp))

        with open(fp, "wb" ) as f:
            f.write(fdata)

    def read_file(self, fn: str):
        """Read binary file data"""
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Reading file {}".format(fp))
        with open(fp, "rb") as f:
            fdata = f.read()
        return fdata

    def exists(self, fn: str):
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Checking exists {}".format(fp))
        return os.path.exists(fp)

    def delete(self, fn: str):
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Deleting {}".format(fp))
        os.remove(fp)

    def get(self, fn: str):
        raise NotImplementedError

    def put(self, fn: str, data):
        raise NotImplementedError
