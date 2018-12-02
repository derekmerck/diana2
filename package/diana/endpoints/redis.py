import logging, hashlib, json
from typing import Any, Union, Mapping
import redis
import attr
from ..dixel import Dixel
from ..utils import Endpoint, Serializable

@attr.s
class Redis(Endpoint, Serializable):

    name = attr.ib(default="Redis")

    host = attr.ib(default="localhost")
    port = attr.ib(default=6379)
    db = attr.ib(default=0)

    password = attr.ib(default=None)

    gateway = attr.ib(init=False, repr=False)

    @gateway.default
    def set_gateway(self):
        return redis.Redis(host=self.host,
                           port=self.port,
                           db=self.db)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CHECK")

        try:
            info = self.gateway.info()
            logger.debug(info)
            return info is not None
        except redis.exceptions.ConnectionError as e:
            logger.warning("Failed to connect to EP")
            logger.error(type(e))
            logger.error(e)
            return False



    @staticmethod
    def serialize(item):

        logging.debug(item)

        if isinstance(item, Serializable):
            # AttrsSerializable class
            _data = item.asdict()
            data = json.dumps(_data)
            key = item.sid()
            return key, data

        if hasattr(item, "__dict__"):
            # Generic class
            _data = item.__dict__
        else:
            # Primitive
            _data = item

        data = json.dumps(_data)
        key = hashlib.md5(data.encode("UTF8")).hexdigest()

        return key, data


    def put(self, item: Union[str, Serializable, Any], **kwargs) -> str:
        logger = logging.getLogger(self.name)
        logger.debug("EP PUT")

        k, v = self.serialize(item)

        logger.debug("{}: {}".format(k[0:4], v))
        self.gateway.set(k, v)
        return k

    def update(self, item: Union[str, Serializable], data: Union[Any, Dixel], **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP UPDATE")

        _, v = self.serialize(data)
        k = item

        logger.debug("{}: {}".format(k[0:4], v))
        self.gateway.set(k, v)

    def get(self, item: Union[str, Serializable], **kwargs) -> Any:
        logger = logging.getLogger(self.name)
        logger.debug("EP GET")

        if isinstance(item, str):
            k = item
        elif isinstance(item, Serializable):
            k = item.sid
        else:
            raise ValueError("Item is not explicitly Serializable, so it requires an explicit key")

        result = self.gateway.get(k)
        logging.debug(result)
        if not result:
            return None

        data = json.loads(result)
        if hasattr(data, "get") and data.get('ctype'):
            new_item = Serializable.Factory.create(**data)
            return new_item
        else:
            return data


    def find(self, query: Mapping, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP FIND")

        raise NotImplementedError


    def delete(self, item: Union[str, Dixel], **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("EP DELETE")

        self.gateway.delete(item)


Serializable.Factory.register(Redis)