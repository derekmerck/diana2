import attr
from ...endpoints import Redis as BaseRedis
from ..abc.distributed import DistributedMixin


@attr.s
class DistributedRedisKV(DistributedMixin, BaseRedis):
    """Redis with distributed handler functions"""
    pass


DistributedRedisKV.register(BaseRedis)
