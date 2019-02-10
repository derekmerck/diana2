import logging
from datetime import datetime
import attr
from diana.apis import Redis
from diana.dixel import Dixel
from diana.utils import Serializable

"""
$ docker run -p 6379:6379 -d redis
"""

@attr.s
class Test(Serializable):
    data = attr.ib(default=None)
    #
    # def __cmp__(self, other):
    #     return self.sid() == other.sid() and \
    #            self.data == other.data

Redis.test = Test


def test_redis_ep(setup_redis):

    logging.debug("Test Redis EP")

    R = Redis()
    logging.debug(R)
    R.check()

    t = Test(data={"myDateTime": datetime.now(), "foo": {'bar': 3}})
    id = R.put(t)
    s = R.get(id)

    logging.debug(t)
    logging.debug(s)
    assert( t == s )

    u = Test(data=42)
    id2 = R.put(u)
    v = R.get(id2)

    logging.debug(u)
    logging.debug(v)
    assert( u == v )

    R.update(id, u)
    w = R.get(id)

    assert( w == v )
    assert( w != s )

    assert( R.exists(id) )
    R.delete(id)
    assert( not R.exists(id) )

    a = "one two three"
    id2 = R.put(a)
    b = R.get(id2)
    assert( a == b )


def test_redis_index(setup_redis):

    R = Redis()

    d = Dixel(meta={"FileName": "my_file"},
              tags={"AccessionNumber": "100"})

    R.add_to_collection(d, item_key="FileName")
    logging.debug( R.collections() )
    assert("100" in R.collections() )

    logging.debug( R.collected_items("100") )
    assert("my_file" in R.collected_items("100") )


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    from conftest import setup_redis
    for i in setup_redis():
        test_redis_ep(None)
        test_redis_index(None)
