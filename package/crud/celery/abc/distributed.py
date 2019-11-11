from typing import Union
import json
import logging
import attr
from redis import Redis as RedisHandler
from ..app import app, handle
from ...abc import Serializable, Item, ItemID, Query


@attr.s
class LockingGatewayMixin(Serializable):
    """Lock for file load/dump functions"""

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if name in ["read", "write"] and hasattr(attr, '__call__'):
            def newfunc(*args, **kwargs):
                logging.debug('Locking for %s' % attr.__name__)
                with RedisHandler.from_url(app.conf.broker_url).lock(self.fp):
                    result = attr(*args, **kwargs)
                logging.debug('Unlocking for %s' % attr.__name__)
                return result
            return newfunc
        else:
            return attr


class DistributedMixin(Serializable):

    def get(self, item: Union[Item, ItemID], *args, **kwargs):
        """Distributed GET"""
        return self.handle(item, "get", *args, **kwargs)

    def put(self, item: Item, *args, **kwargs):
        """Distributed PUT"""
        return self.handle(item, "put", *args, **kwargs)

    def find(self, item: Query, *args, **kwargs):
        """Distributed FIND"""
        return self.handle(item, "find", *args, **kwargs)

    def handle(self, item: Union[Item, ItemID, Query], handler: str, *args, **kwargs):
        """Distributed HANDLE"""

        # Try to flatten inputs
        if hasattr(item, "json"):
            item_flat = item.json()
        else:
            item_flat = item
        ep_flat = self.json()

        job = handle.delay(item_flat, ep_flat, handler, *args, **kwargs)
        result_flat = job.get()

        # Try to unflatten result
        try:
            result_dict = json.loads(result_flat)
            result = Serializable.Factory.create(**result_dict)
        except TypeError:
            result = result_flat

        return result
