import os, enum, logging
import attr
from PIL.Image import fromarray
from .file_handler import FileHandler


class ImageFileFormat(enum.Enum):
    PNG = "png"
    JPG = "jpg"


@attr.s
class ImageFileHandler(FileHandler):

    def put(self, fn: str, data):
        fp = self.get_path(fn)
        # logger = logging.getLogger(self.name)

        if fn.endswith(".jpg") or fn.endswith(".jpeg"):
            logging.warning("JPEG compression requires additional libraries and is untested")

        if not os.path.exists( os.path.dirname(fp) ):
            os.makedirs(os.path.dirname(fp))

        im = fromarray(data)
        im.save(fp)

