# Diana-agnostic API for Splunk, with no endpoint or dixel dependencies

# splunk-sdk does not support Python 3; this gateway provides a minimal
# replacement to 'find' and 'put' events

import time, logging, datetime, json as _json
from pprint import pformat
from datetime import timedelta
# from pprint import pprint
from collections import OrderedDict
from typing import Mapping
import attr
from bs4 import BeautifulSoup
import requests
from .requester import Requester
from . import GatewayConnectionError
from .. import SmartJSONEncoder

@attr.s
class Splunk(Requester):

    name = attr.ib(default="Splunk")
    port = attr.ib( default="8088")
    user     = attr.ib( default="admin" )
    password = attr.ib( default="passw0rd!" )
    hec_protocol = attr.ib( default="http" )
    hec_port = attr.ib( default="8089" )
    hec_token = attr.ib( default=None, type=str )

    def find_events(self, q, timerange=None):
        logger = logging.getLogger(self.name)

        if not timerange:
            earliest = "-1d"
            latest = "now"
        else:
            earliest = (timerange.earliest - timedelta(minutes=2)).isoformat()
            latest = (timerange.latest + timedelta(minutes=2)).isoformat()

        # self.logger.debug("Earliest: {}\n           Latest:   {}".format(earliest, latest))

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
                   timestamp: datetime,
                   event: Mapping,
                   host: str,
                   index: str,
                   token: str ):
        logger = logging.getLogger(self.name)

        if not timestamp:
            timestamp = datetime.datetime.now()

        def epoch(dt):
            tt = dt.timetuple()
            return time.mktime(tt)

        event_json = _json.dumps(event, cls=SmartJSONEncoder)

        data = OrderedDict([('time', epoch(timestamp)),
                            ('host', host),
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

        def hec_post(self, json=None):
            logger = logging.getLogger(self.name)
            logger.debug("Calling HEC post")
            url = make_hec_url()

            data = None
            if json:
                data = _json.dumps(json, cls=SmartJSONEncoder)
            headers = {'Authorization': 'Splunk {0}'.format(self.hec_token)}

            try:
                result = requests.post(url, data=data, headers=headers, auth=self.auth)
            except requests.exceptions.ConnectionError as e:
                raise GatewayConnectionError(e)

            return self.handle_result(result)

        return hec_post(json=data)
