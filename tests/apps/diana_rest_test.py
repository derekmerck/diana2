import json
import logging

import pytest
from conftest import setup_orthanc, setup_redis
from test_utils import find_resource

app = __import__('diana-rest').app

@pytest.fixture
def diana_rest():
    service_path = find_resource("resources/test_services.yml")
    app.app.load_services(service_path)
    client = app.app.test_client()
    yield client

def test_rest_check(diana_rest, setup_orthanc, setup_redis):

    expected = {
        "orthanc": "Ready",
        "orthanc_bad": "Not Ready",
        "redis": "Ready",
        "redis_bad": "Not Ready",
        "redis_p": "Not Ready"
    }

    resp = diana_rest.get("/v1.0/endpoint")
    print(resp.data)

    assert( json.loads( resp.data ) == expected )


def test_rest_guid(diana_rest):
    print("Running test")

    expected = {
        "birth_date": "19991218",
        "id": "QROJO4EWXIOM7HWDBSQG2XZJ2JET5WFG",
        "name": "QUAY^REY^O",
        "time_offset": "-15 days, 23:30:59"
    }

    resp = diana_rest.get("/v1.0/guid?name=MERCK^DEREK^L&birth_date=20000101")
    print(resp.data)

    assert( json.loads( resp.data ) == expected )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    for i in diana_rest():
        test_rest_guid(i)

    for i,j,k in zip( diana_rest(), setup_orthanc(), setup_redis() ):
        test_rest_check(i,j,k)
