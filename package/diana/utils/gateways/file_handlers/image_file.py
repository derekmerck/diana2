import os, enum, logging
import attr
from PIL.Image import fromarray
import numpy as np
from .file_handler import FileHandler


class ImageFileFormat(enum.Enum):
    PNG = "png"
    JPG = "jpg"


@attr.s
class ImageFileHandler(FileHandler):

    @staticmethod
    def squash_to_8bit(data: np.array):

        data = np.float32(data)


        data = np.maximum(data, -1024)
        data -= np.min(data)
        data /= 2**12
        data *= 2**8 - 1
        data = np.uint8(data)
        return data

    def put(self, fn: str, data, max_size=1024):
        fp = self.get_path(fn)
        # logger = logging.getLogger(self.name)

        if fn.endswith(".jpg") or fn.endswith(".jpeg"):
            logging.warning("JPEG compression requires additional libraries and is untested")
        elif fn.endswith(".png"):
            # Convert to 8-bit
            data = self.squash_to_8bit(data)

        if not os.path.exists( os.path.dirname(fp) ):
            os.makedirs(os.path.dirname(fp))

        im = fromarray(data)
        logging.debug(im)

        if np.max(im.size) > max_size:
            logging.debug("Resizing")
            logging.debug(data.shape)
            _max = np.max(im.size)
            new_size = np.int32((im.size / _max) * max_size)
            logging.debug(new_size)
            im = im.resize(new_size)
            logging.debug(im)

        im.save(fp)

