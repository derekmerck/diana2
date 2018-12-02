import logging, os
from diana.endpoints import DcmDir
import pytest

@pytest.mark.parametrize('base_path', ["."])
def test(base_path):

    D = DcmDir(path=os.path.join(base_path, "resources/dcm"))
    logging.debug(D)
    print(D)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

    D = DcmDir(path=os.path.join(base_path, "resources/dcm"),
               subpath_width=3, subpath_depth=2)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

if __name__=="__main__":

    logging. basicConfig(level=logging.DEBUG)
    test("../../")