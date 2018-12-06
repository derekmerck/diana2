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
    # ctype = attr.ib(default=None)

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=8042)
    path = attr.ib(default=None)

    user = attr.ib(default="orthanc")
    password = attr.ib(default="password!")

    gateway = attr.ib(init=False, type=OrthancGateway, repr=False)

    domains = attr.ib(factory=dict)

    @gateway.default
    def setup_gateway(self):
        return OrthancGateway(
            name = "OrthancGateway",
            protocol = self.protocol,
            host = self.host,
            port = self.port,
            path = self.path,
            user = self.user,
            password = self.password
        )

    def put(self, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Put")

        if item.level is not DicomLevel.INSTANCES:
            raise TypeError("Can only 'put' instances")
        if item.file is None:
            raise ValueError("No file to 'put'")

        r = self.gateway.put(item.file)

    def id_from_item(self, item: Union[Dixel, str],
                     level: DicomLevel=DicomLevel.STUDIES):
        if isinstance(item, Dixel) or hasattr(item, "oid"):
            return item.oid(), item.level
        if isinstance(item, str):
            return item, level
        else:
            raise TypeError("Unable to get id for type {}".format(type(item)))


    def get(self, item: Union[Dixel, str],
            level: DicomLevel=DicomLevel.STUDIES,
            view: OrthancView=OrthancView.TAGS, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Get")

        oid, level = self.id_from_item(item, level)
        r = self.gateway.get(oid, level, view)

        if r:
            if isinstance(item, Dixel):
                # Want to update with data
                if view=="tags":
                    item.tags = r
                elif view=="file":
                    item.file = r
                elif view=="meta":
                    item.mea = "meta"
                return item
            else:
                # Want a new file
                if view=="tags":
                    return Dixel(meta={"ID", oid}, tags=r, level=level)
                elif view=="file":
                    d = Dixel(meta={"ID", oid}, level=level)
                    d.file = r
                    return d


        raise FileNotFoundError("Item {} does not exist".format(item))

    def find(self, query: Mapping, level=DicomLevel.STUDIES, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Find")

        q = {"Level": "{!s}".format(level),
             "Query": query }
        r = self.gateway.find(q)

        # Returns a list of OIDs
        return r

    def rfind(self, query: Mapping, domain: str, level=DicomLevel.STUDIES):
        logger = logging.getLogger(self.name)
        logger.debug("Remote Find")

        q = {"Level": "{!s}".format(level),
             "Query": query }

        try:
            r = self.gateway.rfind(q, domain)
        except Exception as e:
            logger.warning(e)
            r = None

        # Returns a list of maps that should be converted into Dixels
        return r

    def delete(self, item: Union[str, Dixel], level=DicomLevel.STUDIES, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Delete")

        oid, level = self.id_from_item(item, level)
        r = self.gateway.delete(oid, level)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("Check")

        try:
            return self.gateway.statistics() is not None
        except GatewayConnectionError as e:
            logger.warning("Failed to connect to Endpoint")
            logger.error(type(e))
            logger.error(e)
            return False


Serializable.Factory.register(Orthanc)