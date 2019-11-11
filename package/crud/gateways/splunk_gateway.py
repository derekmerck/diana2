# Diana-agnostic API for Splunk, with no endpoint or dixel dependencies

import time, logging, datetime, json as _json, socket
from pprint import pformat
from datetime import datetime, timedelta
from collections import OrderedDict
from typing import Mapping
import attr
from bs4 import BeautifulSoup
import requests
from .requester import Requester
from ..exceptions import GatewayConnectionError
from ..utils.smart_json import SmartJSONEncoder

@attr.s
class SplunkGateway(Requester):
    """The official splunk-sdk is for Python2.7 only, so this class
    provides a minimal Python3 query/put replacement for data logging"""

    port = attr.ib( default="8089")
    user = attr.ib( default="admin" )
    password = attr.ib( default="passw0rd!" )
    hec_protocol = attr.ib( default="http" )
    hec_port = attr.ib( default="8088" )
    hec_token = attr.ib( default=None, type=str )
    index = attr.ib( default="main" )

    hostname = attr.ib( )
    @hostname.default
    def set_hostname(self):
        return socket.gethostname()

    def info(self):
        r = self._get("services/server/info", params={'output_mode': 'json'})
        return r

    def find_events(self, q, time_range=None):
        logger = logging.getLogger(self.name)

        if not time_range:
            earliest = "-1d"
            latest = "now"
        else:
            earliest = time_range[0].isoformat()
            latest   = time_range[1].isoformat()

        logger.debug("Earliest: {}\nLatest: {}".format(earliest, latest))

        response = self._post('services/search/jobs',
                             data = {'search': q,
                                     'earliest_time': earliest,
                                     'latest_time': latest})

        soup = BeautifulSoup(response, 'xml')  # Should have returned xml
        sid = soup.find('sid').string  # If it returns multiple sids, it didn't parse the request and did a "GET"

        # self.logger.debug(pformat(soup))
        logger.debug(sid)

        def poll_until_done(sid):
            isDone = False
            i = 0
            while not isDone:
                i = i + 1
                time.sleep(1)
                response = self._get('services/search/jobs/{0}'.format(sid),
                                    params={'output_mode': 'json'})

                logger.debug(response)

                isDone = response['entry'][0]['content']['isDone']
                status = response['entry'][0]['content']['dispatchState']
                if i % 5 == 1:
                    logger.debug('Waiting to finish {0} ({1})'.format(i, status))
            return response['entry'][0]['content']['resultCount']

        n = poll_until_done(sid)
        offset = 0
        result = []
        i = 0
        while offset < n:
            count = 50000
            offset = 0 + count*i
            response = self._get('services/search/jobs/{0}/results'.format(sid),
                                params={'output_mode': 'json',
                                        'count': count,
                                        'offset': offset})

            for r in response['results']:

                try:
                    data = _json.loads(r['_raw'])
                    result.append( data )
                except (_json.decoder.JSONDecodeError, KeyError):
                    logger.warning("Skipping non-json string: {}".format(pformat(r)))
            i = i+1

        return result

    def put_event( self,
                   event: Mapping,
                   timestamp: datetime = None,
                   hostname: str = None,
                   index: str = None,
                   hec_token: str = None ):
        logger = logging.getLogger(self.name)

        if not timestamp:
            logging.warning("Did not declare timestamp, using now")
            timestamp = datetime.now()

        hec_token = hec_token or self.hec_token
        index = index or self.index

        if hostname:
            hostname = "{}@{}".format(hostname, self.hostname)
        else:
            hostname = self.hostname

        def epoch(dt):
            tt = dt.timetuple()
            return time.mktime(tt)

        event_json = _json.dumps(event, cls=SmartJSONEncoder)

        data = OrderedDict([('time', epoch(timestamp)),
                            ('host', hostname),
                            ('sourcetype', '_json'),
                            ('index', index ),
                            ('event', event_json )])

        logger.debug(pformat(data))

        def make_hec_url() -> str:
            if self.path:
                return "{}://{}:{}/{}/services/collector/event". \
                    format(self.hec_protocol, self.host, self.hec_port, self.path)
            else:
                return "{}://{}:{}/services/collector/event". \
                    format(self.hec_protocol, self.host, self.hec_port)

        def hec_post(json=None):
            logger.debug("Calling HEC post")
            url = make_hec_url()

            data = None
            if json:
                data = _json.dumps(json, cls=SmartJSONEncoder)
            headers = {'Authorization': 'Splunk {0}'.format(hec_token)}

            try:
                logging.debug(headers)
                result = requests.post(url, data=data, headers=headers)
            except requests.exceptions.ConnectionError as e:
                raise GatewayConnectionError(e)

            return self.handle_result(result)

        return hec_post(json=data)
