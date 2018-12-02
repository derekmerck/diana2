import attr
from uuid import uuid4

@attr.s
class AttrSerializable(object):

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
        d['ctype'] = self.__class__.__name__
        return d

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
            return cls.registry[ctype](**kwargs)

    Factory = AttrFactory()