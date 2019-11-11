import logging
import attr
from twilio.rest import TwilioRestClient
from crud.abc import Serializable
from ..abc import Messenger


@attr.s
class TwilioMessenger(Messenger):

    # Account SID and Auth Token from twilio.com/user/account
    account_sid = attr.ib(type=str, default=None)
    auth_token = attr.ib(type=str, default=None)
    from_number = attr.ib(type=str, default=None)

    gateway = attr.ib()
    @gateway.default
    def create_gateway(self):
        return TwilioRestClient(self.account_sid, self.auth_token)

    def _send(self, msg, to_number):

        logger = logging.getLogger(self.name)
        logger.info("Sending message via twilio connector:\n{}".format(msg))

        msg_obj = self.gateway.messages.create(body=msg, to=to_number, from_=self.from_number)

TwilioMessenger.register()
