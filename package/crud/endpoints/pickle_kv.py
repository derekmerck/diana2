from typing import Union
# import logging
import os
from tempfile import TemporaryDirectory
import attr
from ..abc import Endpoint, Serializable, Item, ItemID
from ..gateways import PickleGateway


@attr.s
class PickleKV(Endpoint, Serializable):
    """
    CRUD endpoint using a pickle file for persistent kv storage
    """

    tmp_path = attr.ib(factory=TemporaryDirectory, init=False)
    fp = attr.ib()

    @fp.default
    def set_fp(self):
        return os.path.join(self.tmp_path.name, "ep_tmp.pik")

    gateway = attr.ib(init=False)

    @gateway.default
    def set_gateway(self):
        return PickleGateway(fp=self.fp)

    def get_data(self):
        return self.gateway.read() or {}

    def persist_data(self, data):
        return self.gateway.write(data)

    def keys(self):
        data = self.get_data()
        return list(data.keys())

    def get(self, item: Union[Item, ItemID], *args, **kwargs):

        if hasattr(item, "epid"):
            item_id = item.epid
        else:
            item_id = item

        data = self.get_data()
        item = data[item_id]

        return item

    def put(self, item: Item, *args, **kwargs):
        data = self.get_data()
        item_id = item.epid
        data[item_id] = item
        self.persist_data(data)
