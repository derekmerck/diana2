import json, inspect
from uuid import uuid4
import attr
from dateutil import parser as DateTimeParser
from ..smart_json import SmartJSONEncoder

@attr.s(cmp=False, hash=None)
class AttrSerializable(object):

    uuid = attr.ib(repr=False)
    @uuid.default
    def set_uuid(self):
        return str(uuid4())

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def sid(self):
        """Overload in sub-classes to assign specific id fields for serializers"""
        return str(self.uuid)

    def asdict(self):
        # Remove non-init and default variables
        d = attr.asdict(self,
                        filter=lambda attr, val: attr.init and val != attr.default)
        for k, v in d.items():
            if k.startswith("_"):
                d[k[1:]] = v
                del d[k]
        d['ctype'] = self.__class__.__name__
        self.Factory.registry['ctype'] = self.__class__
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
            _cls = cls.registry.get("ctype")
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


    Factory = AttrFactory()