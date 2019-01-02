import logging
from typing import Mapping
import attr
from pprint import pformat

from ..utils import Endpoint, Serializable
from ..utils.gateways import Montage as MontageGateway, GatewayConnectionError
from ..dixel import Dixel

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
            name = "MontageGateway",
            protocol = self.protocol,
            host = self.host,
            port = self.port,
            path = self.path,
            user = self.user,
            password = self.password
        )

    def find(self, query: Mapping, index="rad", ignore_errs=True):
        r = self.gateway.find(query=query, index=index)
        ret = set()
        for item in r:
            try:
                d = Dixel.from_montage_json(item)
                d = self.get_meta(d)
                ret.add(d)
            except Exception as e:
                logger = logging.getLogger(self.name)
                logger.warning("Failed to dixelize an item")
                if not ignore_errs:
                    raise e
        return ret


    def get_meta(self, item: Dixel):
        cpts = self.gateway.lookup_cpts(item.meta["MontageCPTCodes"])
        body_part = self.gateway.lookup_body_part(item.meta["MontageCPTCodes"])

        item.meta['CPTCodes'] = cpts
        item.meta['BodyParts'] = body_part
        return item


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
