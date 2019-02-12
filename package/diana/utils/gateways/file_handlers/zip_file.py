
import logging, zipfile
from pathlib import Path
import attr
from .file_handler import FileHandler

@attr.s
class ZipFileHandler(FileHandler):

    name = attr.ib(default="ZipFileHandler")

    def unpack(self, item):
        logger = logging.getLogger(self.name)

        if isinstance(item, Path) or isinstance(item, str):
            item = self.get_path(item)
            logger.debug("Unzipping file {}".format(item))
        else:
            logger.debug("Unzipping file-like")

        try:
            result = []
            with zipfile.ZipFile(item) as z:
                for member in z.infolist():
                    if not member.is_dir():
                    # if not member.filename.endswith("/"):
                        # read the file
                        logging.debug("Collecting {}".format(member))
                        f = z.read(member)
                        result.append(f)
            return result
        except zipfile.BadZipFile as e:
            logging.error(e)
