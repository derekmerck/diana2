from abc import ABC
import json
import inspect
import logging
from hashlib import sha1
import attr
from dateutil import parser as DateTimeParser
from ..utils import SmartJSONEncoder
from ..exceptions import EndpointFactoryException


@attr.s(cmp=False, hash=False)
class AttrSerializable(ABC):
    """
    Provides id, hashing, and serializing funcs via "attrs".  Useful for extending
    the generic CRUD endpoint.
    """

    _epid = attr.ib(default=None, init=False)

    @property
    def epid(self):
        """CRUD endpoint id"""
        if not self._epid:
            self._epid = self.sha1().hexdigest()
        return self._epid

    @epid.setter
    def epid(self, value):
        self._epid = value

    def sha1(self) -> sha1:
        return sha1(self.json().encode("UTF-8"))

    def __hash__(self):
        return hash(self.sha1().digest())

    def __eq__(self, other: "AttrSerializable"):
        return hash(self) == hash(other)

    @classmethod
    def register(cls, override=None):
        cls.Factory.registry[cls.__name__] = override or cls

    def asdict(self):
        # Remove non-init and default variables
        d = attr.asdict(self,
                        filter=lambda attr, val: attr.init and (val != attr.default))
        for k, v in d.items():
            if k.startswith("_"):
                d[k[1:]] = v
                del d[k]
        d['ctype'] = self.__class__.__name__
        self.Factory.registry[self.__class__.__name__] = self.__class__
        return d

    def json(self):
        map = self.asdict()
        data = json.dumps(map, cls=SmartJSONEncoder)
        return data

    class AttrFactory(object):

        registry = {}

        @classmethod
        def create(cls, **kwargs):
            ctype = kwargs.pop('ctype')
            if not ctype:
                raise EndpointFactoryException("No ctype, cannot instantiate")

            # Anything that has been "asdict" serialized will be registered
            _cls = cls.registry.get(ctype)
            if not _cls:
                # Voodoo for unregistered root objects
                _cls = inspect.stack()[1][0].f_globals.get(ctype)
            if not _cls:
                raise EndpointFactoryException(f"No class {ctype} is registered, cannot instantiate")
            for k, v in kwargs.items():
                if hasattr(v, "keys"):
                    for kk, vv in v.items():
                        if "DateTime" in kk:
                            try:
                                v[kk] = DateTimeParser.parse(vv)
                            except:
                                logging.warning(f"Failed to parse dt from {kk}: {vv}")
                                pass

            return _cls(**kwargs)

        def copy(cls, ref: "AttrSerializable"):
            kwargs = ref.asdict()
            obj = cls.create(**kwargs)
            return obj

    Factory = AttrFactory()
