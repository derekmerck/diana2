import logging, time
from multiprocessing import Process
from diana.utils.gateways import PicklePMap, PickleArrayPMap, CSVArrayPMap, CSVPMap

import pytest


@pytest.mark.parametrize("cache_class", (PicklePMap, CSVPMap), ids=("pickle", "csv"))
def test_cache(tmp_path, cache_class):

    cache = cache_class(fn="{}/cache".format(tmp_path))
    assert (not cache.get("key1"))

    cache.put("key1", {"value": 100})
    assert( int( cache.get("key1").get("value") ) == 100)
    assert (not cache.get("key2"))
    cache.put("key1", {"value": 101})
    cache.put("key2", {"value": 200})
    assert( int( cache.get("key1").get("value") ) == 101)
    assert( int( cache.get("key2").get("value") ) == 200)
    assert( not cache.get("key3") )

    cache.clear()

@pytest.mark.parametrize("cache_class",
                         (PicklePMap, CSVPMap),
                         ids=("pickle_array", "csv_array"))
def test_polling_cache(tmp_path, cache_class):

    cache = cache_class(fn="{}/cache-{{}}".format(tmp_path))
    assert (not cache.get("key1"))

    p = Process(target=cache.run)
    p.start()
    cache.queue.put( ("key1", {"value": 100}) )
    cache.queue.put( ("key1", {"value": 101}) )
    cache.queue.put( ("key2", {"value": 200}) )
    time.sleep(2)
    p.terminate()

    assert( int( cache.get("key1").get("value") ) == 101)
    assert( int( cache.get("key2").get("value") ) == 200)
    assert( not cache.get("key3") )

    cache.clear()


def test_keyfield(tmp_path):

    cache = CSVPMap(fn="{}/cache.csv".format(tmp_path),
                    keyfield="my_key",
                    fieldnames=["my_key", "value"])
    cache.clear()
    assert (not cache.get("key1"))

    cache.put("key1", {"value": 101})

    with open("{}/cache.csv".format(tmp_path), 'r') as f:
        content = f.read()
    logging.debug(content)
    assert( content == 'my_key,value\nc2add694bf942dc77b376592d9c862cd,101\n' )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    cache_class = PicklePMap
    test_cache("/tmp", cache_class)
    test_polling_cache("/tmp", cache_class)

    cache_class = PickleArrayPMap
    test_cache("/tmp", cache_class)
    test_polling_cache("/tmp", cache_class)

    cache_class = CSVPMap
    test_cache("/tmp", cache_class)
    test_polling_cache("/tmp", cache_class)

    cache_class = CSVArrayPMap
    test_cache("/tmp", cache_class)
    test_polling_cache("/tmp", cache_class)

    test_keyfield("/tmp")
