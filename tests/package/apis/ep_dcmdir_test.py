import logging, os, json

from conftest import *
from test_utils import find_resource

from diana.apis import DcmDir
from diana.utils import Serializable


def test_exists():

    resources_dir = find_resource("resources/dcm")

    D = DcmDir(path=resources_dir)
    logging.debug(D)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

    D = DcmDir(path=resources_dir,
               subpath_width=3, subpath_depth=2)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

    logging.debug("Checking round-trip")

    d = D.get("IM2263")
    dd = d.json()
    ee = json.loads(dd)
    e = Serializable.Factory.create(**ee)

    logging.debug(d)
    logging.debug(e)

    assert( d == e )

def test_indexer(setup_redis, setup_orthanc):
    return

    from diana.apis import Redis, Orthanc
    R = Redis()
    O = Orthanc()

    path = "/Users/derek/data/dicom/christianson"
    D = DcmDir(path=path, subpath_depth=2, subpath_width=2)
    # D.index_to(R)

    studies = D.indexed_studies(R)
    print(studies)

    for s in studies:
        worklist = D.get_indexed_study(s, R)
        print(worklist)

        for fn in worklist:
            d = D.get(fn, get_file=True)
            print(d)
            O.put(d)


if __name__=="__main__":

    logging. basicConfig(level=logging.DEBUG)
    test_exists()
    test_indexer()