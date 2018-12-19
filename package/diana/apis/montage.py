import logging
from typing import Mapping
import attr
from pprint import pformat

from ..utils import Endpoint, Serializable
from ..utils.gateways import Montage as MontageGateway, GatewayConnectionError
from ..dixel import Dixel, RadiologyReport
from ..utils.dicom import DicomLevel

@attr.s(hash=False)
class Montage(Endpoint, Serializable):

    name = attr.ib(default="Montage")

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=80)
    path = attr.ib( default="api/v1" )

    user = attr.ib( default="montage" )
    password = attr.ib( default="montage" )

    gateway = attr.ib(init=False, type=MontageGateway, repr=False)

    @gateway.default
    def setup_gateway(self):
        return MontageGateway(
            name = "OrthancGateway",
            protocol = self.protocol,
            host = self.host,
            port = self.port,
            path = self.path,
            user = self.user,
            password = self.password
        )

    def find(self, query: Mapping, index="rad", **kwargs):
        r = self.gateway.find(query=query, index=index)
        ret = set()
        for item in r["objects"]:
            ret.add(Dixel.from_montage_json(item))
        return ret


    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("Check")

        try:
            return self.gateway._get("index") is not None
        except GatewayConnectionError as e:
            logger.warning("Failed to connect to Endpoint")
            logger.error(type(e))
            logger.error(e)
            return False
