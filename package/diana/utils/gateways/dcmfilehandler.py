# Diana-agnostic API for DICOM files, with no endpoint or dixel dependencies

import os, logging, binascii
import attr
import pydicom
from ..dicom import DicomFormatError

@attr.s
class DcmFileHandler():

    name = attr.ib(default="DcmFileHandler")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

    @staticmethod
    def is_dicom(fp):
        try:
            with open(fp, 'rb') as f:
                f.seek(0x80)
                header = f.read(4)
                magic = binascii.hexlify(header)
                if magic == b"4449434d":
                    # self.logger.debug("{} is dcm".format(fp))
                    return True
        except:
            logger = logging.getLogger("DcmFileHandler")
            logger.warning("{} is NOT dcm format".format(fp))
            return False


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

        if not self.is_dicom(fp):
            raise DicomFormatError("Not a DCM file: {}".format(fp))

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
