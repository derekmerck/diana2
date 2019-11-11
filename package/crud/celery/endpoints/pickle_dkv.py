import attr
from ...endpoints import Pickle as BasePickle
from ...gateways import PickleGateway as BasePickleGateway
from ..abc.distributed import DistributedMixin, LockingGatewayMixin


@attr.s
class LockingPickleGateway(BasePickleGateway, LockingGatewayMixin):
    pass


@attr.s
class LockingPickler(BasePickle):
    """Pickler with a lock-on-read/write gateway"""
    gateway = attr.ib(init=False)

    @gateway.default
    def set_gateway(self):
        return LockingPickleGateway(fp=self.fp)


@attr.s
class DistributedPickleKV(DistributedMixin, LockingPickler):
    """Pickler with locking gateway and distributed handler functions"""
    pass


DistributedPickleKV.register(LockingPickler)
