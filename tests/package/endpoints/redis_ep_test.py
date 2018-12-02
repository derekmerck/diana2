import logging
from diana.endpoints import Redis
from diana.utils import Serializable
import attr

"""
$ docker run -p 6379:6379 -d redis
"""

def test_redis_ep():

    logging.debug("Test Redis EP")

    R = Redis()
    logging.debug(R)
    R.check()

    @attr.s
    class Test(Serializable):
        data = attr.ib(default=None)
        def __cmp__(self, other):
            return self.sid() == other.sid() and \
                   self.data == other.data

    t = Test(data={"dog": 2, "foo": {'bar': 3}})
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




if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_redis_ep()