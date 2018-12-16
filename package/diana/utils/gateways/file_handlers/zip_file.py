
import logging, zipfile
import attr
from .file_handler import FileHandler

@attr.s
class ZipFileHandler(FileHandler):

    name = attr.ib(default="ZipFileHandler")

    def unpack(self, fn):
        fp = self.get_path(fn)
        logger = logging.getLogger(self.name)

        logger.debug("Unzipping {}".format(fp))

        try:
            result = []
            with zipfile.ZipFile(fp) as z:
                for member in z.infolist():
                    if not member.is_dir():
                    # if not member.filename.endswith("/"):
                        # read the file
                        logging.debug("Collecting {}".format(member))
                        f = z.read(member)
                        result.append(f)
        except zipfile.BadZipFile as e:
            logging.error(e)