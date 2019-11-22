import logging
from datetime import datetime
import attr

# TODO: No collections or key by a/n yet
# from crud.endpoints import Redis

# from diana.apis import Redis
from crud.abc import Serializable
from crud.endpoints import Redis
from diana.dixel import Dixel


@attr.s(cmp=False)
class Test(Serializable):
    data = attr.ib(default=None)

    # Force epid to update for comparison
    def __cmp__(self, other):
        return self.epid == other.epid and \
               self.data == other.data

Redis.test = Test


def test_redis_ep(setup_redis):

    logging.debug("Test Redis EP")

    R = Redis()
    logging.debug(R)
    R.check()

    t = Test(data={"myDateTime": datetime.now(), "foo": {'bar': 3}})
    key = R.put(t)
    s = R.get(key)

    logging.debug(f"key={key}")

    logging.debug(f"t={t}")
    logging.debug(f"s={s}")
    assert( t == s )

    u = Test(data=42)
    id2 = R.put(u)
    v = R.get(id2)

    logging.debug(f"u={u}")
    logging.debug(f"v={v}")
    assert( u == v )

    assert( R.exists(key) )
    R.delete(key)
    assert( not R.exists(key) )

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

    from conftest import mk_redis
    S0 = mk_redis()

    test_redis_ep(None)
    # test_redis_index(None)
