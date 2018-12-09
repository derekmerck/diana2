import attr
from abc import ABC


@attr.s
class Event(object):

    etype = attr.ib()
    source = attr.ib()
    data = attr.ib(default=None)


class ObservableMixin(ABC):

    def changes(self, **kwargs) -> list:
        raise NotImplementedError