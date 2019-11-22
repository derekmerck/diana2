import logging
from datetime import datetime
from crud.endpoints import Redis

from utils import SimpleItem
import pytest


def test_redis_ep(setup_redis):

    logging.debug("Test Redis EP")

    R = Redis(clear=True)
    logging.debug(R)
    R.check()

    t = SimpleItem(data={"myDateTime": datetime.now(), "foo": {'bar': 3}})
    key = R.put(t)
    s = R.get(key)

    logging.debug(f"key={key}")

    logging.debug(f"t={t}")
    logging.debug(f"s={s}")
    assert( t == s )

    u = SimpleItem(data=42)
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

    R = Redis(clear=True)

    d = SimpleItem(meta={"FileName": "my_file"},
                   data=[1,2,3,4])

    R.sput(d, skey="test")
    logging.debug( R.skeys() )
    assert("test" in R.skeys() )

    logging.debug( R.sget("test") )
    items = R.sget("test")
    assert(items[0].meta["FileName"] == "my_file")


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)

    from conftest import mk_redis
    mk_redis()

    test_redis_ep(None)
    test_redis_index(None)
