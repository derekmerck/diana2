import os
import attr
from PIL.Image import fromarray
from .file_handler import FileHandler

@attr.s
class ImageFileHandler(FileHandler):

    def put(self, fn: str, data):
        fp = self.get_path(fn)
        # logger = logging.getLogger(self.name)

        if not os.path.exists( os.path.dirname(fp) ):
            os.makedirs(os.path.dirname(fp))

        im = fromarray(data)
        im.save(fp)

