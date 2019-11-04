# Diana-agnostic API for DICOM files, with no endpoint or dixel dependencies

import logging, binascii
from pathlib import Path
import attr
import pydicom
from .file_handler import FileHandler
from ...dicom import DicomFormatError

@attr.s
class DcmFileHandler(FileHandler):

    name = attr.ib(default="DcmFileHandler")

    @staticmethod
    def is_dicom(item) -> bool:

        logger = logging.getLogger("DcmFileHandler")

        def check(data):
            data.seek(0x80)
            header = data.read(4)
            magic = binascii.hexlify(header)
            if magic == b"4449434d":
                # logging.debug("Passed")
                return True
            logger.warning("{} is NOT dcm format".format(data))
            return False

        if isinstance(item, Path) or isinstance(item, str):
            logger.debug("Checking file is dicom")
            with open(item, 'rb') as f:
                return check(f)
        else:
            logger.debug("Checking data is dicom")
            return check(item)

    def get(self, fn: str, get_pixels=False, force=False) -> pydicom.Dataset:
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)

        if not self.is_dicom(fp):
            raise DicomFormatError("Not a DCM file: {}".format(fp))

        logger.debug("Reading {}".format(fp))
        ds = pydicom.dcmread(fp, stop_before_pixels=not get_pixels, force=force)
        return ds

    def put(self, fn: str, data):
        # Convert data into a file
        self.write_file(fn, data)
