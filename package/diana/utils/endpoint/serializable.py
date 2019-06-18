import json, inspect
from hashlib import sha1
import attr
from dateutil import parser as DateTimeParser
from ..smart_json import SmartJSONEncoder

@attr.s(cmp=False, hash=False)
class AttrSerializable(object):
    """
    Provides id, hashing, and serializing funcs via "attrs".  Useful for extending
    the generic CRUD endpoint.
    """

    @property
    def epid(self):
        """endpoint id"""
        return self.sha1().hexdigest()

    def sha1(self) -> sha1:
        return sha1(self.json().encode("UTF-8"))

    def __hash__(self):
        return hash(self.sha1().digest())

    def __eq__(self, other: "AttrSerializable"):
        return hash(self) == hash(other)

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
                raise TypeError("No ctype, cannot instantiate")

            # Anything that has been "asdict" serialized will be registered
            _cls = cls.registry.get(ctype)
            if not _cls:
                # Voodoo for unregistered root objects
                _cls = inspect.stack()[1][0].f_globals.get(ctype)
            if not _cls:
                raise TypeError("No class {} is registered, cannot instantiate".format(ctype))
            for k, v in kwargs.items():
                if hasattr(v, "keys"):
                    for kk, vv in v.items():
                        if "DateTime" in kk:
                            v[kk] = DateTimeParser.parse(vv)

            return _cls(**kwargs)

        def copy(cls, ref: "AttrSerializable"):
            kwargs = ref.asdict()
            obj = cls.create(**kwargs)
            return obj

    Factory = AttrFactory()
