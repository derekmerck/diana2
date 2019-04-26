import logging, zipfile
from typing import Collection, Union, IO as filelike
from pathlib import Path
import attr
from .file_handler import FileHandler

@attr.s
class ZipFileHandler(FileHandler):

    name = attr.ib(default="ZipFileHandler")

    def zip(self, item: Union[str, Path, filelike], items: Collection):
        logger = logging.getLogger(self.name)

        if isinstance(item, Path) or isinstance(item, str):
            item = self.get_path(item)
            logger.debug("Zipping file {}".format(item))
        else:
            logger.debug("Zipping file-like")

        zf = zipfile.ZipFile(item, "w")
        for item in items:
            zf.writestr(item.fn, item.file)
        zf.close()

    def unzip(self, item: Union[str, Path, filelike]):
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
                        fn = member.filename
                        f = z.read(member)
                        result.append((fn,f))
            return result
        except zipfile.BadZipFile as e:
            logging.error(e)
