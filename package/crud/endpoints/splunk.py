import logging
import json
from pprint import pformat
from typing import Mapping, List
from datetime import datetime
import attr
from ..abc import Endpoint, Serializable, Item
from ..gateways import SplunkGateway

# Suppress insecure warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@attr.s
class Splunk(Endpoint, Serializable):
    name = attr.ib(default="Splunk")

    protocol = attr.ib(default="https")
    host = attr.ib(default="localhost")
    port = attr.ib(default=8089)
    path = attr.ib(default=None)

    hec_protocol = attr.ib(default="http")
    hec_port = attr.ib(default=8088)
    hec_token = attr.ib(default=None)

    index = attr.ib(default="main")

    user = attr.ib(default="admin")
    password = attr.ib(default="passw0rd!")

    gateway = attr.ib(init=False, type=SplunkGateway, repr=False)

    @gateway.default
    def setup_gateway(self):
        return SplunkGateway(
            name = "SplunkGateway",
            protocol = self.protocol,
            host = self.host,
            port = self.port,
            path = self.path,
            user = self.user,
            password = self.password,
            hec_port = self.hec_port,
            hec_protocol = self.hec_protocol,
            hec_token=self.hec_token,
            index = self.index
        )

    def find(self,
             query: str,
             time_range=None) -> List[Item]:

        ret = self.gateway.find_events(query, time_range)

        logging.debug("Splunk query: {}".format(query))
        logging.debug("Splunk results: {}".format(ret))

        if ret:
            result = []
            for item_dict in ret:
                item = Serializable.Factory.create(**item_dict)
                if item not in result:
                    result.append( item )
            return result

    def put(self, item: Item,
            hostname: str = None,
            index: str = None,
            hec_token: str = None,
            **kwargs ):

        logger = logging.getLogger(self.name)
        logger.debug("Put")

        if hasattr(item, "timestamp"):
            timestamp = item.timestamp()
        elif hasattr(item, "meta") and item.meta.get("creation_time"):
            timestamp = item.meta.get("creation_time")
        else:
            logging.warning("Failed to get item timestamp, using now()")
            timestamp = datetime.now()

        item_dict = item.asdict()

        hec_token = hec_token or self.hec_token
        if not hec_token:
            raise ValueError("No hec token provided!")

        index = index or self.index

        # logger.debug(timestamp)
        # logger.debug(event)
        # logger.debug(index)
        # logger.debug(hec_token)

        # at $time $event was reported by $host for $index with credentials $auth
        self.gateway.put_event( event=item_dict, timestamp=timestamp,
                                hostname=hostname, index=index, hec_token=hec_token )

        # Real auth description
        # headers = {'Authorization': 'Splunk {0}'.format(self.hec_tok[hec])}

    def check(self):

        logger = logging.getLogger(self.name)
        logger.debug("Check")

        r = self.gateway.info()

        if r:
            logger.info("Service available")
            logger.debug(pformat(r))
            return True

        logger.warning("Service unavailble")


Splunk.register()
