import logging, json
from diana.apis import DcmDir
from diana.utils import Serializable

from test_utils import find_resource


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


def test_subdirs():

    D = DcmDir(recurse_style="ORTHANC")

    # for fp in D.recurse():
    #     logging.debug(fp)

    subdirs = list( D.subdirs() )

    assert( len( subdirs )  == 256*256 )
    assert( "./ff/ff" in subdirs )
    assert( "./00/00" in subdirs )

    p = find_resource("resources")
    D = DcmDir(path=p)

    subdirs = list( D.subdirs() )
    logging.debug(subdirs)

    assert( len(subdirs) >= 8 )



if __name__=="__main__":

    logging. basicConfig(level=logging.DEBUG)
    test_exists()
    test_subdirs()