import logging
import os
import yaml
import json
from typing import Union, Mapping
import attr
from crud.abc import Endpoint, Serializable, Item
from crud.utils import render_template
from crud.utils import deserialize_str


@attr.s
class Messenger(Endpoint, Serializable):

    target = attr.ib(default=None)
    msg_t = attr.ib(default="{{msg_text}}", converter=deserialize_str)
    wrap = attr.ib(default=70)

    # Any special template funcs from the caller
    j2_funcs = attr.ib(factory=dict)

    def set_msg_t(self, value):
        self.msg_t = deserialize_str(value)

    # String send
    def _send(self, msg, target, **kwargs):
        raise NotImplementedError

    def get(self, item: Union[Item, Mapping], target=None, msg_t=None, **kwargs):
        if not target:
            target = self.target
        if not target:
            raise ValueError("No target address provided")
        if not msg_t:
            msg_t = self.msg_t
        if not msg_t:
            raise ValueError("No message template provided")

        if isinstance(item, dict):
            data = item
        elif hasattr(item, 'data'):
            data = item.data
        elif hasattr(item, 'meta'):
            data = item.meta
        else:
            raise TypeError("Cannot convert {} to mapping")

        if hasattr(self, "from_addr"):
            data["from_addr"] = self.from_addr

        msg = render_template(msg_t, target=target, funcs=self.j2_funcs, **data, **kwargs )
        return msg

    # Item send with template
    def send(self, item: Union[Item, Mapping], target=None, msg_t=None, dryrun=False, **kwargs):
        msg = self.get(item, target, msg_t, **kwargs)
        if not dryrun:
            self._send(msg, target, **kwargs)
        else:
            logger = logging.getLogger(self.name)
            logger.info("Dry run message is:\n{}".format(msg))

        return msg
