import os, logging, json as _json
import requests
import attr
from ..exceptions import GatewayConnectionError
from ..utils.smart_json import SmartJSONEncoder

"""
print out RequestException respnose and header info:
  pprint(e.response)
  pprint(e.request.headers)
"""

# Enabled sessions to handle cookies from Docker swarm for sticky connections
USE_SESSIONS = False

NORMAL_TIMEOUT = (3.1, 12.1)  # (connect to, read to)
LARGE_TIMEOUT  = (6.1, 360.1) # Use large timeout on <1Gb connections

# On a raspberry pi with a 400Mb connection:
#   - ~5 mins to pull a 1500 image study
#   - ~2 mins to anonymize
#   - ~2 mons to zip

TIMEOUTS = LARGE_TIMEOUT


def suppress_urllib_debug():
    logging.getLogger("urllib3").setLevel(logging.WARNING)


@attr.s
class Requester(object):

    name = attr.ib(default="Requester")

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=80)
    path = attr.ib(default=None)

    user = attr.ib(default=None)
    password = attr.ib(default=None)
    auth_tok = attr.ib(default=None)

    base_url = attr.ib(init=False, default=None)
    auth_header = attr.ib(init=False, default=None)
    auth = attr.ib(init=False, default=None)
    session = attr.ib(init=False, default=None)

    # Can't use attr.s defaults here b/c the derived classes don't see the vars yet
    def __attrs_post_init__(self):
        base_url = "{protocol}://{host}:{port}/".format(
            protocol = self.protocol,
            host = self.host,
            port = self.port )
        if self.path:
            base_url = os.path.join( base_url, self.path )
        self.base_url = base_url

        # If auth is assigned, it cannot be overwritten with a header
        if self.user and self.password:
            self.auth = (self.user, self.password)

        if self.auth_tok and hasattr(self, "setup_auth_header"):
            self.auth_header = self.setup_auth_header()

        if USE_SESSIONS:
            self.session = requests.Session()
            if self.auth:
                self.session.auth = self.auth
            if self.auth_header:
                self.session.headers = self.auth_header
            self.session.verify = False

    def make_url(self, resource):
        return "{}/{}".format( self.base_url, resource )

    @staticmethod
    def handle_result(result):
        if result.status_code > 299 or result.status_code < 200:
            # logging.debug("Cookies: {}".format(self.session.cookies))
            try:
                result.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise GatewayConnectionError(e)

        # logging.debug(result.headers)

        if 'application/json' in result.headers.get('Content-type'):
            return result.json()
        return result.content

    def _get(self, resource, params=None, headers=None):
        logger = logging.getLogger(self.name)
        logger.debug("Calling get")
        url = self.make_url(resource)
        # logger.debug(url)

        try:
            if USE_SESSIONS:
                result = self.session.get(url, params=params, headers=headers, timeout=TIMEOUTS)
            else:
                if self.auth_header and headers:
                    headers.update(self.auth_header)
                else:
                    headers = self.auth_header
                result = requests.get(url, params=params, headers=headers, auth=self.auth, timeout=TIMEOUTS)

        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            raise GatewayConnectionError(e)
        except requests.exceptions.Timeout as e:
            raise GatewayConnectionError("Response timed out")
        return self.handle_result(result)

    def _put(self, resource, json=None, data=None, headers=None):
        logger = logging.getLogger(self.name)
        logger.debug("Calling put")
        url = self.make_url(resource)
        if json:
            data = _json.dumps(json, cls=SmartJSONEncoder)
        try:
            if USE_SESSIONS:
                result = self.session.put(url, data=data, headers=headers,timeout=TIMEOUTS)
            else:
                if self.auth_header and headers:
                    headers.update(self.auth_header)
                else:
                    headers = self.auth_header
                result = requests.put(url, data=data, headers=headers, auth=self.auth, timeout=TIMEOUTS)
        except requests.exceptions.Timeout as e:
            raise GatewayConnectionError("Response timed out")
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            raise GatewayConnectionError(e)
        return self.handle_result(result)

    def _post(self, resource, json=None, data=None, headers=None):
        logger = logging.getLogger(self.name)
        logger.debug("Calling post")
        url = self.make_url(resource)
        if json:
            data = _json.dumps(json, cls=SmartJSONEncoder)
        try:
            if USE_SESSIONS:
                result = self.session.post(url, data=data, headers=headers,timeout=TIMEOUTS)
            else:
                if self.auth_header and headers:
                    headers.update(self.auth_header)
                else:
                    headers = self.auth_header
                result = requests.post(url, data=data, headers=headers, auth=self.auth, timeout=TIMEOUTS)
        except requests.exceptions.Timeout as e:
            raise GatewayConnectionError("Response timed out")
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            raise GatewayConnectionError(e)
        return self.handle_result(result)

    def _delete(self, resource, headers=None):
        logger = logging.getLogger(self.name)
        logger.debug("Calling delete")
        url = self.make_url(resource)
        try:
            if USE_SESSIONS:
                result = self.session.delete(url, headers=headers)
            else:
                if self.auth_header and headers:
                    headers.update(self.auth_header)
                else:
                    headers = self.auth_header
                result = requests.delete(url, headers=headers, auth=self.auth)
        except requests.exceptions.Timeout as e:
            raise GatewayConnectionError("Response timed out")
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            raise GatewayConnectionError(e)
        return self.handle_result(result)
