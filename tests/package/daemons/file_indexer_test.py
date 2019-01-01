import logging
from pprint import pprint
from datetime import datetime

from diana.daemons import FileIndexer
from diana.apis import Orthanc, Redis

import pytest
from conftest import setup_orthanc, setup_redis


path = "/Users/derek/data/DICOM/Christianson"


@pytest.mark.skip(reason="Needs large dataset for indexing")
def test_index(setup_redis):

    R = Redis()
    R.clear()

    dcmfdx = FileIndexer(pool_size=10)

    tic = datetime.now()

    dcmfdx.index_path(
        basepath=path,
        registry=R,
        rex="*",
        recurse_style="ORTHANC"
    )

    toc = datetime.now()
    tictoc = (toc-tic).seconds

    print("Indexing elapsed: {}".format( tictoc ))

    """
    10x workers, debug: 180 seconds for 12k indexed, 24k checked
    10x workers, debug: 120 seconds for 12k indexed, 24k checked - skipped reading tags
    """

@pytest.mark.skip(reason="Needs large dataset for uploading")
def test_upload(setup_redis, setup_orthanc):

    R = Redis()
    O = Orthanc()
    O.clear()

    dcmfdx = FileIndexer(pool_size=10)

    tic = datetime.now()

    dcmfdx.upload_path(
        basepath=path,
        registry=R,
        dest=O
    )

    toc = datetime.now()
    tictoc = (toc-tic).seconds

    print("Upload elapsed: {}".format( tictoc ))

    pprint(O.gateway.statistics())

    """
    10x workers ~120 secs to upload 12k instances (100/sec!)
    """


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    for (i,j) in zip(setup_orthanc(), setup_redis()):
        #test_index(None)
        test_upload(None, None)