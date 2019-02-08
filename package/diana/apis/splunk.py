import logging
from typing import Mapping
from datetime import datetime
import attr
from ..dixel import Dixel
from ..utils.endpoint import Endpoint, Serializable
from ..utils.dicom import DicomLevel
from ..utils.gateways import Splunk as SplunkGateway
# splunk-sdk is 2.7 only, so diana.utils.gateway provides a minimal query/put replacement

# Suppress insecure warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@attr.s
class Splunk(Endpoint, Serializable):

    name = attr.ib(default="Splunk")

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=8089)
    path = attr.ib(default=None)

    hec_protocol = attr.ib(default="http")
    hec_port = attr.ib(default=8088)
    hec_token = attr.ib(default=None)

    index = attr.ib(default="dicom")

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
            index = self.index
        )


    def find_items(self,
            query: Mapping,
            time_interval=None):

        results = self.gateway.find_events(query, time_interval)

        # logging.debug("Splunk query: {}".format(query))
        # logging.debug("Splunk results: {}".format(results))

        if results:
            worklist = set()
            for d in results:
                worklist.add( Dixel(meta=d, level=DicomLevel.of( d['level'] ) ) )

            # logging.debug(worklist)

            return worklist


    def put(self, item: Dixel,
            hostname: str=None,
            index: str=None,
            hec_token: str=None,
            **kwargs ):

        logger = logging.getLogger(self.name)
        logger.debug("Put")

        if item.meta.get('InstanceDateTime'):
            timestamp = item.meta.get('InstanceCreationDateTime')
        elif item.meta.get('StudyDateTime'):
            timestamp = item.meta.get('StudyDateTime')
        else:
            logging.warning("Failed to get inline 'DateTime', using now()")
            timestamp = datetime.now()

        event = item.tags

        event['level'] = str(item.level)
        event['oid'] = item.oid()

        hec_token = hec_token or self.hec_token
        if not hec_token:
            raise ValueError("No hec token provided!")

        index = index or self.index

        logger.debug(timestamp)
        logger.debug(event)
        logger.debug(index)
        logger.debug(hec_token)

        # at $time $event was reported by $host for $index with credentials $auth
        self.gateway.put_event( timestamp=timestamp, event=event,
                                hostname=hostname, index=index, hec_token=hec_token )

        # Real auth description
        # headers = {'Authorization': 'Splunk {0}'.format(self.hec_tok[hec])}
