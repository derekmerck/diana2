from abc import ABC
import attr
from uuid import uuid4
import json
from datetime import datetime
from dateutil import parser as DateTimeParser

@attr.s
class AttrSerializable(ABC):

    uuid = attr.ib(repr=False)
    @uuid.default
    def set_uuid(self):
        return str(uuid4())

    def sid(self):
        """Overload in sub-classes to assign specific id fields for serializers"""
        return str(self.uuid)

    # It can be useful for a sub-class member to self-register if the
    # sub-class is not explicitly registered.
    def __attrs_post_init__(self):
        self.Factory.register(self.__class__)

    def asdict(self):
        # Remove non-init and default variables
        d = attr.asdict(self,
                        filter=lambda attr, val: attr.init and val != attr.default)
        for k, v in d.items():
            if k.startswith("_"):
                d[k[1:]] = v
                del d[k]
        d['ctype'] = self.__class__.__name__
        return d

    def json(self):

        class DatetimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return json.JSONEncoder.default(obj)

        map = self.asdict()
        data = json.dumps(map, cls=DatetimeEncoder)
        return data


    class AttrFactory(object):
        registry = {}

        @classmethod
        def register(cls, new_class):
            cls.registry[new_class.__name__] = new_class

        @classmethod
        def create(cls, **kwargs):
            ctype = kwargs.pop('ctype')
            if not ctype:
                raise TypeError("No ctype, cannot instantiate")
            if not ctype in cls.registry.keys():
                raise TypeError("No class for ctype {} is registered, cannot instantiate".format(ctype))
            for k, v in kwargs.items():
                if hasattr(v, "keys"):
                    for kk, vv in v.items():
                        if "DateTime" in kk:
                            v[kk] = DateTimeParser.parse(vv)
            return cls.registry[ctype](**kwargs)

    Factory = AttrFactory()