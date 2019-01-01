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

    dcmfdx = FileIndexer(basepath=path,
                         recurse_style="ORTHANC",
                         registry=R,
                         pool_size=10)

    tic = datetime.now()

    dcmfdx.run_indexer(rex="*")

    toc = datetime.now()
    tictoc = (toc-tic).seconds

    print("Indexing elapsed: {}".format( tictoc ))

    """
    No MT, debug: 465 seconds
    """

@pytest.mark.skip(reason="Needs large dataset for uploading")
def test_upload(setup_redis, setup_orthanc):

    R = Redis()
    O = Orthanc()

    dcmfdx = FileIndexer(basepath=path,
                         recurse_style="ORTHANC",
                         registry=R,
                         dest=O,
                         pool_size=10)

    tic = datetime.now()

    dcmfdx.run_uploader()

    toc = datetime.now()
    tictoc = (toc-tic).seconds

    print("Upload elapsed: {}".format( tictoc ))

    pprint(O.gateway.statistics())

    """
    59 secs to upload 5800 instances (100/sec!)
    """




if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    for (i,j) in zip(setup_orthanc(), setup_redis()):
        # test_index(None)
        test_upload(None, None)