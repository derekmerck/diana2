import os, logging, io
from typing import Union
import attr
from ..dixel import Dixel, DixelView, ShamDixel
from ..utils import Endpoint, Serializable
from ..utils.dicom import DicomLevel
from ..utils.gateways import DcmFileHandler, ZipFileHandler, ImageFileHandler, ImageFileFormat



import pydicom


@attr.s
class DcmDir(Endpoint, Serializable):

    name = attr.ib(default="DcmDir")
    path = attr.ib(default=".")
    subpath_width = attr.ib(default=2)
    subpath_depth = attr.ib(default=0)

    gateway = attr.ib(init=False, repr=False)
    @gateway.default
    def setup_gateway(self):
        return DcmFileHandler(path=self.path,
                              subpath_width = self.subpath_width,
                              subpath_depth = self.subpath_depth)

    anonymizing = attr.ib(default=False)
    recurse_style = attr.ib(default="UNSTRUCTURED")
    _gen = attr.ib(init=False, repr=False, default=None)

    def put(self, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP PUT")
        if not item.file:
            raise ValueError("Dixel has no file attribute, can only save file data")
        self.gateway.write_file(item.fn, item.file)

    def update(self, fn: str, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP UPDATE")
        if not item.file:
            raise ValueError("Dixel has no file attribute, can only save file data")
        self.gateway.write_file(fn, Dixel.file)

    def get(self, item: Union[str, Dixel], view=DixelView.TAGS, **kwargs):

        logger = logging.getLogger(self.name)
        logger.debug("EP GET")
        if isinstance(item, str):
            fn = item
        elif isinstance(item, Dixel) or hasattr(item, 'fn'):
            fn = item.fn
        else:
            raise ValueError("Item has no fn attribute, so it requires an explicit filename")

        if not self.gateway.exists(fn):
            raise FileNotFoundError(fn)

        get_pixels = DixelView.PIXELS in view
        # logger.debug("Pixels: {}".format(get_pixels))

        if DixelView.TAGS in view or DixelView.PIXELS in view:
            ds = self.gateway.get(fn, get_pixels=get_pixels)
            # logging.debug(ds)
            result = Dixel.from_pydicom(ds, fn)
        else:
            result = Dixel(level=DicomLevel.INSTANCES, meta={"FileName": fn})

        get_file = DixelView.FILE in view
        if get_file:
            result.file = self.gateway.read_file(fn)

        return result

    def delete(self, item: Union[str, Dixel], **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP DELETE")
        if isinstance(item, str):
            fn = item
        elif isinstance(item, Dixel) or hasattr(item, 'fn'):
            fn = item.fn
        else:
            raise ValueError("Item has no fn attribute, so it requires an explicit filename")
        return self.gateway.delete(fn)

    def exists(self, fn: str):
        logger = logging.getLogger(self.name)
        logger.debug("EP EXISTS")
        # if self.gateway.isdir(fn):
        #     return False
        return self.gateway.exists(fn)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CHECK")
        return os.path.exists(self.path)

    def get_zipped(self, item: str):
        gateway = ZipFileHandler(path=self.path)
        files = gateway.unpack(item)
        result = set()
        for f in files:
            d = Dixel(level=DicomLevel.INSTANCES)
            d.file = f
            result.add(d)
        return result

    def subdirs(self):
        """Generator for nested sub-directories.

        Performed lazily because this can be expensive for UNSTRUCTURED directories."""
        if self.recurse_style == "UNSTRUCTURED":
            self._gen = DcmDir.unstructured_subdirs(base_dir=self.path)
        elif self.recurse_style == "ORTHANC":
            self._gen = DcmDir.orthanc_subdirs(base_dir=self.path)
        else:
            raise ValueError("Unknown subdir structure requested ({})".format(self.recurse_style))

        for item in self._gen:
            yield item

    class orthanc_subdirs(object):
        """Generates 1024 Orthanc-style nested subdirs"""

        def __init__(self, base_dir=None, low=0, high=256 * 256 - 1):
            self.base_dir = base_dir
            self.current = low
            self.high = high

        def __iter__(self):
            return self

        def __next__(self):
            if self.current > self.high:
                raise StopIteration
            else:
                self.current += 1
                hex = '{:04X}'.format(self.current - 1).lower()
                orthanc_dir = os.path.join(self.base_dir, hex[0:2], hex[2:4])
                return orthanc_dir

    class unstructured_subdirs(object):
        """Generates subdirs with os.walk, this remains _very_ slow for large datasets!"""

        def __init__(self, base_dir):
            self.base_dir = base_dir
            self.generator = os.walk(base_dir)

        def __iter__(self):
            return self

        def __next__(self):
            item = self.generator.__next__()
            return item[0]

    def files(self, rex="*.dcm"):
        return self.gateway.get_files(rex=rex)


@attr.s
class ImageDir(DcmDir):

    name = attr.ib(default="ImageDir")
    format = attr.ib(default=ImageFileFormat.PNG)

    gateway = attr.ib(init=False, repr=False)
    @gateway.default
    def setup_gateway(self):
        return ImageFileHandler(path=self.path,
                                subpath_width = self.subpath_width,
                                subpath_depth = self.subpath_depth)

    # TODO: handle pulling an image instance format directly from Orthanc (im_file attr?)
    def put(self, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP PUT")

        if item.pixels is None:
            raise ValueError("Dixel has no pixels attribute, can only save pixel data")

        if self.anonymizing:
            item = ShamDixel.from_dixel(item)

        fn = "{}.{}".format(item.image_base_fn, self.format.value)
        self.gateway.put(fn, item.get_pixels())

    def put_zipped(self, item: str):

        gateway = ZipFileHandler(path=self.path)
        files = gateway.unpack(item)  # Returns files as bytes
        for f in files:
            if not DcmFileHandler.is_dicom(io.BytesIO(f)):
                continue
            ds = pydicom.dcmread(io.BytesIO(f), stop_before_pixels=False)
            d = Dixel.from_pydicom(ds)
            self.put(d)
