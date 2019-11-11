# Functions to read in and instantiate services from yaml and json

from os import PathLike
from typing import Union, TextIO, List, Mapping
import attr

from .abc import Endpoint
from .abc.serializable import AttrSerializable as Serializable
from .exceptions import EndpointHealthException, EndpointFactoryException
from .utils import deserialize_dict


@attr.s
class EndpointManager(object):

    serialized_ep_descs = attr.ib(default=None, type=Union[str, PathLike, TextIO])
    ep_descs = attr.ib(type=Mapping)

    @ep_descs.default
    def set_descs(self):
        # if not self.serialized_ep_descs:
        #     raise ValueError("No descs or serialized descs provided!")
        return deserialize_dict(self.serialized_ep_descs) or {}

    prefixes = {}

    @classmethod
    def add_prefix(cls, prefix, func):
        cls.prefixes[prefix] = func

    def get(self, key, check=False):

        for k, v in self.prefixes.items():
            if key.startswith(k):
                return v(key)

        v = self.ep_descs.get(key)
        if not v:
            raise EndpointFactoryException(key)

        ep = Serializable.Factory.create(name=key, **v)

        if check and not ep.check():
            raise EndpointHealthException(ep)

        return ep

    def get_all(self, check=False):
        for k, v in self.ep_descs.items():
            if hasattr(v, "get") and v.get("ctype"):
                yield self.get(k, check=check)

    # "service_descs" aliases for compatibility
    service_descs = ep_descs


EndpointManager.add_prefix("fake", Endpoint)
Endpoint.check = lambda x: True
