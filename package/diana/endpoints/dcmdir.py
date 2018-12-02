import os, logging
from typing import Union
import attr
from ..dixel import Dixel
from ..utils import Endpoint, Serializable

@attr.s
class DcmFileHandler():

    name = attr.ib(default="DcmFileHandler")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

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
        raise NotImplementedError

    def read(self, fn: str):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Reading {}".format(fp))
        raise NotImplementedError

    def exists(self, fn: str):
        fp = self.make_path(fn)
        logger = logging.getLogger(self.name)
        logger.debug("Checking exists {}".format(fp))
        return os.path.exists(fp)


@attr.s
class DcmDir(Endpoint, Serializable):

    name = attr.ib(default="DcmDir")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

    gateway = attr.ib(init=False)
    @gateway.default
    def setup_gateway(self):
        return DcmFileHandler(path=self.path,
                              subpath_width = self.subpath_width,
                              subpath_depth = self.subpath_depth)

    def put(self, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP PUT")
        if not item.file:
            raise ValueError("Dixel has no file attribute, can only save file data")
        self.gateway.write(Dixel.fn(), Dixel.file)

    def update(self, fn: str, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP UPDATE")
        if not item.file:
            raise ValueError("Dixel has no file attribute, can only save file data")
        self.gateway.write(fn, Dixel.file)

    def get(self, item: Union[str, Dixel], **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP GET")
        if isinstance(item, str):
            fn = item
        elif isinstance(item, Dixel) or hasattr(item, 'fn'):
            fn = item.fn()
        else:
            raise ValueError("Item has no fn attribute, so it requires an explicit filename")
        return self.gateway.read(fn)

    def delete(self, item: Union[str, Dixel], **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP DELETE")
        if isinstance(item, str):
            fn = item
        elif isinstance(item, Dixel) or hasattr(item, 'fn'):
            fn = item.fn()
        else:
            raise ValueError("Item has no fn attribute, so it requires an explicit filename")
        return self.gateway.delete(fn)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CHECK")
        return os.path.exists(self.path)


