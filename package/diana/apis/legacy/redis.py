import logging, hashlib, json, os
from typing import Any, Union, Mapping
from redis import Redis as RedisGateway, exceptions as RedisExceptions
import attr
from diana.dixel import Dixel
from diana.utils.dicom import DicomFormatError
from diana.utils.endpoint import Endpoint, Serializable
from diana.utils import SmartJSONEncoder

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
        return RedisGateway(host=self.host,
                            port=self.port,
                            password=self.password,
                            db=self.db)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CHECK")

        try:
            info = self.gateway.info()
            logger.debug(info)
            return info is not None
        except RedisExceptions.ConnectionError as e:
            logger.warning("Failed to connect to EP")
            logger.error(type(e))
            logger.error(e)
            return False

    @staticmethod
    def serialize(item):

        logging.debug(item)

        if isinstance(item, Serializable):
            # AttrsSerializable class
            data = item.json()
            key = item.epid
            return key, data

        if hasattr(item, "__dict__"):
            # Generic class
            _data = item.__dict__
        else:
            # Primitive
            _data = item

        data = json.dumps(_data, cls=SmartJSONEncoder)
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
        elif isinstance(item, Serializable) or hasattr(item, "sha1"):
            k = item.sha1
        else:
            raise ValueError("Item has no sid attribute, so it requires an explicit key")

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

    def clear(self):
        logger = logging.getLogger(self.name)
        logger.debug("EP CLEAR")

        self.gateway.flushdb()


    ### Collections

    def add_to_collection(self, item: Dixel, prefix: str="",
                                 collection_key: str = "AccessionNumber",
                                 item_key: str = "FilePath",
                                 path=None ):
        """
        It is non-obvious how to check the total number of objects across all sets.
        This works and its fast for even large data sets.

        > EVAL "local total = 0 for _, key in ipairs(redis.call('keys', ARGV[1])) do total = total + redis.call('scard', key) end return total" 0 prefix-*

        See <https://stackoverflow.com/questions/34563144/redis-multiple-key-set-counts>
        """

        if item_key == "FilePath" and path:
            value = os.path.join(path, item.meta.get("FileName"))
        elif item.tags.get(item_key):
            value = item.tags[item_key]
        elif item.meta.get(item_key):
            value = item.meta[item_key]
        else:
            raise ValueError("No item key found")

        if item.tags.get(collection_key):
            suffix = item.tags[collection_key]
        elif item.meta.get(collection_key):
            suffix =item.meta[collection_key]
        else:
            raise DicomFormatError("No collection key found")

        key = prefix + suffix

        logger = logging.getLogger(self.name)
        logger.info("Registering {} under {}".format(value, key))

        self.gateway.sadd(key, value)

    def collections(self, prefix: str=""):
        keys = self.gateway.keys(prefix+"*")
        result = []
        l = len(prefix)
        for k in keys:
            result.append( k[l:].decode("UTF-8") )
        return result

    def collected_items(self, collection: str, prefix: str=""):
        key = prefix + collection
        logger = logging.getLogger(self.name)
        logger.info("Collecting {}".format(key))
        data = self.gateway.smembers(key)
        result = []
        for d in data:
            result.append(d.decode("UTF-8"))
        return result
