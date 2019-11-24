import logging
from typing import Mapping
import attr
from crud.abc import Endpoint, Serializable

import pytest


@attr.s
class SimpleEP(Endpoint, Serializable):

    cache = attr.ib(factory=dict, init=False)
    dummy1 = attr.ib(default=42)
    dummy2 = attr.ib(default=43)

    def check(self):
        return True

    def get(self, id: str, **kwargs):
        return self.cache.get(id)

    def find(self, query: Mapping, **kwargs):
        val = query.get('q')
        for k, v in self.cache.items():
            if v == val:
                return k

    def put(self, item, **kwargs):
        id = hash(item)
        self.cache[id] = item
        return id

    def update(self, id, new_data, **kwargs):
        self.cache[id] = new_data


@pytest.mark.parametrize("item1,item2", [
    ("abcd", 123),
    ("abcd", {"key":"efgh"})
])
def test_ep(item1, item2):
    """Set an item, find it, replace it"""

    logging.debug("Testing ep accessors")

    ep = SimpleEP()
    assert(ep.check())

    id = ep.put(item1)
    assert(ep.get(id) == item1)
    assert(ep.find({'q': item1}) == id)
    assert(ep.exists({'q': item1}) is True)
    assert(ep.exists(id) is True)
    assert(ep.exists({'q': item2}) is False)

    ep.update(id, item2)
    assert(ep.get(id) == item2)
    assert(ep.find({'q': item2}) == id)
    assert(ep.exists({'q': item2}) is True)
    assert(ep.exists(id) is True)
    assert(ep.exists({'q': item1}) is False)


def test_ep_factory():

    logging.debug("Testing ep factory")

    ep = SimpleEP(name="test", dummy1=10)
    kwargs = ep.asdict()
    logging.debug(kwargs)

    assert(kwargs.get('dummy1'))
    assert(not kwargs.get('dummy2'))
    assert(not kwargs.get('cache'))

    ep2 = Serializable.Factory.create(**kwargs)
    assert( ep2.name == "test" )
    assert( ep2.check() )
    assert( ep2.dummy1 == 10 )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    test_ep("abcd", 123 )
    test_ep("abcd", {"key":"efgh"} )
    test_ep_factory()
