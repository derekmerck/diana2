import logging
from typing import Mapping, Union
from ..dixel import Dixel
from ..utils import Endpoint, Serializable
from ..utils.gateways import Orthanc as OrthancGateway, OrthancView, GatewayConnectionError
from ..utils.dicom import DicomLevel
import attr


@attr.s
class Orthanc(Endpoint, Serializable):

    name = attr.ib(default="Orthanc")

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=8042)
    path = attr.ib(default=None)

    user = attr.ib(default="orthanc")
    password = attr.ib(default="password!")

    gateway = attr.ib(init=False, type=OrthancGateway, repr=False)

    @gateway.default
    def setup_gateway(self):
        return OrthancGateway(
            name = "OrthancGateway",
            protocol = self.protocol,
            host = self.host,
            port = self.port,
            path = self.path
        )

    def find(self, query: Mapping, level=DicomLevel.STUDIES, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP FIND")

        q = {"Level": "{!s}".format(level),
             "Query": query }
        r = self.gateway.find(q)
        return r

    def put(self, item, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP PUT")

        if item.level() is not DicomLevel.INSTANCES:
            raise TypeError("Can only 'put' instances")
        if item.file is None:
            raise ValueError("No file to 'put'")

        r = self.gateway.put(item.file)

    def get(self, item: Union[Dixel, str],
            level: DicomLevel=DicomLevel.STUDIES,
            view: OrthancView=OrthancView.TAGS, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP GET")

        if isinstance(item, Dixel):
            oid = item.oid()
            level = item.level()
        elif isinstance(item, str):
            oid = item
            level = level
        else:
            raise TypeError("Unable to get type {}".format(type(item)))
        r = self.gateway.get(oid, level, view)
        if r:
            return Dixel(meta=r)
        raise FileNotFoundError("Item {} does not exist".format(item))

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CHECK")

        try:
            return self.gateway.statistics() is not None
        except GatewayConnectionError as e:
            logger.warning("Failed to connect to EP")
            logger.error(type(e))
            logger.error(e)
            return False


Serializable.Factory.register(Orthanc)