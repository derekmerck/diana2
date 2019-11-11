import logging
from pprint import pformat

from utils import SimpleItem
from crud.endpoints import Pickle, Redis, Csv

# from crud.celery.endpoints import Pickle as DistPickle, Redis as DistRedis, Csv as DistCsv
# from crud.celery import app
# app.config_from_object("celeryconfig")

import pytest

@pytest.mark.skip(reason="No celery testing")
def check_for_endpoint(ep):
    """
    Generate a few items, stash them, and make sure they are
    persistent.
    """

    logging.debug(pformat(ep.asdict()))

    expected = []

    for i in range(5):

        item = SimpleItem(i)
        ep.put(item)
        expected.append(item.epid)

    assert( len(expected) == 5 )

    logging.debug(expected)
    logging.debug(ep.keys())
    assert( len(ep.keys()) == 5 )

    for key in ep.keys():
        item = ep.get(key)
        assert( item.epid in expected )

@pytest.mark.skip(reason="No celery testing")
def test_persistence():

    logging.basicConfig(level=logging.DEBUG)

    endpoints = [Pickle(),
                 Redis(clear=True, db=1),
                 Csv(item_ctype="SimpleItem")]
    for ep in endpoints:
        check_for_endpoint(ep)

    Redis(clear=True, db=1)

    endpoints = [DistPickle(),
                 DistRedis(db=1),
                 DistCsv(exclusive=False, item_ctype="SimpleItem")]
    for ep in endpoints:
        check_for_endpoint(ep)


if __name__ == "__main__":
    test_persistence()
