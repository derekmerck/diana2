import logging, os, json
from diana.endpoints import DcmDir
import pytest
from diana.utils import Serializable


@pytest.mark.parametrize('base_path', ["."])
def test(base_path):

    D = DcmDir(path=os.path.join(base_path, "resources/dcm"))
    logging.debug(D)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

    D = DcmDir(path=os.path.join(base_path, "resources/dcm"),
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


if __name__=="__main__":

    logging. basicConfig(level=logging.DEBUG)
    test("../../")