import os
import attr
from .file_handler import FileHandler


@attr.s
class TextFileHandler(FileHandler):

    def put(self, fn: str, data: str):

        fp = self.get_path(fn)
        # logger = logging.getLogger(self.name)

        if not os.path.exists( os.path.dirname(fp) ):
            os.makedirs(os.path.dirname(fp))

        with open(fp, 'w') as f:
            f.write(data)
