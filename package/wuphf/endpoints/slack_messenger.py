import json
import logging
import attr
import requests
from ..abc import Messenger


@attr.s
class SlackMessenger(Messenger):

    url = attr.ib(default="http://workspace.slack.com")

    def _send(self, msg, slack_channel, **kwaqrgs):
        # "target" param is a slack channel

        logger = logging.getLogger(self.name)
        logger.info("Sending message via Slack connector:\n{}".format(msg))

        payload = {
            'text': msg,
            'channel': slack_channel
        }
        headers = {'content-type': 'application/json'}
        requests.post(self.url, json.dumps(payload), headers=headers)

SlackMessenger.register()
