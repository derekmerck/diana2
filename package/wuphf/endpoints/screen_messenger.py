"""
Simple default messenger that prints items to the terminal
"""

from pprint import pprint
import attr
from ..abc import Messenger


@attr.s
class ScreenMessenger(Messenger):

    def send(self, item, **kwargs):
        pprint(item)


ScreenMessenger.register()