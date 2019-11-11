from typing import Union, Mapping
import logging
import os
from tempfile import TemporaryDirectory
import attr
from ..abc import Endpoint, Serializable
from ..abc.endpoint import Item, ItemID
from ..gateways import CsvGateway


@attr.s
class CsvKV(Endpoint, Serializable):
    """
    Meta-only CRUD endpoint using a CSV file for persistent storage.
    Useful for human-readable data keying.  Not suited for data-preserving
    round trips.
    """

    tmp_path = attr.ib(factory=TemporaryDirectory, init=False)
    fp = attr.ib()

    @fp.default
    def set_fp(self):
        return os.path.join(self.tmp_path.name, "ep_tmp.csv")

    gateway = attr.ib(init=False)

    @gateway.default
    def set_gateway(self):
        return CsvGateway(fp=self.fp)

    # If tags are remapped, it's not guaranteed round-trip (esp if epid is lost)
    remapper = attr.ib(factory=dict)
    fieldnames = attr.ib(default=None)

    cache = attr.ib(factory=dict, init=False)
    key_field = attr.ib(default="epid")

    exclusive = attr.ib(default=True)      # No need to refresh on access
    autopersist = attr.ib(default=False)   # Automatically persist after a "put"

    item_ctype = attr.ib(default=None)     # Return object type

    def __attrs_post_init__(self):
        self.get_data()

    def get_data(self):
        items = self.gateway.read()
        if not items:
            self.cache = {}
        else:
            for item in items:
                logging.debug(item)
                key = item[self.key_field]
                self.cache[key] = item

    def persist(self):
        self.gateway.write(self.cache.values(), self.fieldnames)

    def keys(self):

        if not self.exclusive:
            self.get_data()

        return list(self.cache.keys())

    def get(self, item: Union[Item, ItemID], *args, **kwargs) -> [Item, Mapping]:

        if not self.exclusive:
            self.get_data()

        if hasattr(item, "meta") and item.meta.get(self.key_field):
            item_id = item.meta.get(self.key_field)
        else:
            item_id = item

        meta = self.cache.get(item_id)

        if hasattr(item, "meta"):
            item.meta = meta
            return item
        elif self.item_ctype:
            # logging.warning("casting to {}".format(self.item_ctype))
            item = Serializable.Factory.create(ctype=self.item_ctype, meta=meta)
            return item
        else:
            return meta

    def put(self, item: Item, *args, **kwargs):

        if not self.exclusive:
            self.get_data()

        item_id = item.meta.get(self.key_field)
        self.cache[item_id] = item.meta

        if not self.exclusive or self.autopersist:
            self.persist()
