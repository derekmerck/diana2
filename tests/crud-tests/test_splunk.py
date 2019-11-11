import os
import logging
from crud.endpoints import Splunk
import sys
sys.path.append('utils')
from utils import SimpleItem

"""
$ docker run -d -p 8000:8000 -p 8088:8088 -p 8089:8089 \
   -e SPLUNK_START_ARGS=--accept-license \
   -e SPLUNK_PASSWORD=$SPLUNK_PASSWORD \
   -e SPLUNK_HEC_TOKEN=$SPLUNK_HEC_TOKEN \
   --name splunk splunk/splunk:latest
   
- create index "testing"
- turn off ssl
- change default index for token to "testing"
"""

import pytest

@pytest.mark.skip(reason="No splunk fixture")
def test_splunk():

    S = Splunk(
        host="debian-testing",
        password=os.environ.get("TEST_SPLUNK_PASSWORD"),
        hec_token=os.environ.get("TEST_SPLUNK_HEC_TOKEN"),
        index="testing"
    )

    d = SimpleItem(
        data=123
    )

    S.put(d)

    items = S.find("search index=testing")

    print(items)

    # TODO: Need a pause or something here until Splunk can handle it
    assert d in items


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_splunk()
