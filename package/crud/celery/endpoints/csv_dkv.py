import attr
from ...endpoints import Csv as BaseCsvKV
from ...gateways import CsvGateway as BaseCsvGateway
from ..abc.distributed import DistributedMixin, LockingGatewayMixin


@attr.s
class LockingCsvGateway(BaseCsvGateway, LockingGatewayMixin):
    pass


@attr.s
class LockingCsvKV(BaseCsvKV):
    """Csv with a lock-on-read/write gateway"""
    gateway = attr.ib(init=False)

    @gateway.default
    def set_gateway(self):
        return LockingCsvGateway(fp=self.fp)


@attr.s
class DistributedCsvKV(DistributedMixin, LockingCsvKV):
    """Csv with locking gateway and distributed handler functions"""
    pass


DistributedCsvKV.register(LockingCsvKV)
