# Diana-agnostic API for DICOM files, with no endpoint or dixel dependencies

import logging, binascii
import attr
import pydicom
from .file_handler import FileHandler
from ...dicom import DicomFormatError

@attr.s
class DcmFileHandler(FileHandler):

    name = attr.ib(default="DcmFileHandler")

    @staticmethod
    def is_dicom(fp) -> bool:
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

    def get(self, fn: str, get_pixels=False) -> pydicom.Dataset:
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)

        if not self.is_dicom(fp):
            raise DicomFormatError("Not a DCM file: {}".format(fp))

        logger.debug("Reading {}".format(fp))
        ds = pydicom.dcmread(fp, stop_before_pixels=not get_pixels)
        return ds

    def put(self, fn: str, data):
        # Convert data into a file
        self.write_file(fn, data)
