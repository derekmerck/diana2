import logging
from pprint import pprint

from diana.daemons import FileIndexer
from diana.apis import Orthanc, Redis

import pytest
from conftest import setup_orthanc0, setup_redis


# path = "/Users/derek/data/DICOM/Christianson"
# recursion_style = "ORTHANC"

path = "/Users/derek/data/Protect3D/Protect3"
recursion_style = "UNSTRUCTURED"


@pytest.mark.skip(reason="Needs large dataset for indexing")
def test_index(setup_redis):

    print("Testing indexing speed")

    R = Redis()
    R.clear()

    dcmfdx = FileIndexer(pool_size=15)

    dcmfdx.index_path(
        basepath=path,
        registry=R,
        rex="*",
        recurse_style=recursion_style
    )

    """
    240 fps checking over 24k | 120 fps registration over 12k (Christianson)
    """

@pytest.mark.skip(reason="Needs large dataset for uploading")
def test_upload(setup_redis, setup_orthanc0):

    print("Testing upload speed")

    R = Redis()
    O = Orthanc()
    O.clear()

    dcmfdx = FileIndexer(pool_size=15)

    dcmfdx.upload_path(
        basepath=path,
        registry=R,
        dest=O
    )

    pprint(O.gateway.statistics())

    """
    130 fps uploaded over 24k
    """


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    from conftest import mk_orthanc, mk_redis

    O = mk_orthanc()
    R = mk_redis

    test_index(None)
    #test_upload(None, None)

    O.stop()
    R.stop()

"""
Overall fps about 120 for each part

40,000,000 files / 120 files ps = 300k seconds = 90 hours = 4 days
"""