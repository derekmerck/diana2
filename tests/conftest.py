import logging
from diana.utils.endpoint import Containerized
import pytest
import docker
import sys

sys.path.append('test_utils')

@pytest.fixture(scope="module")
def setup_orthanc():

    print("Standing up orthanc fixture")

    S = Containerized(
            dkr_service = "orthanc",
            dkr_image = "derekmerck/orthanc-confd",
            dkr_ports = {"8042/tcp": 8042}
        )
    S.start_servive()

    client = docker.from_env()
    c = client.containers.get("orthanc")
    print("{}: {}".format(S.dkr_service, c.status))

    yield S

    print("Tearing down orthanc fixture")
    S.stop_service()

@pytest.fixture(scope="module")
def setup_redis():

    print("Standing up redis fixture")

    S = Containerized(
            dkr_service = "redis",
            dkr_image = "redis",
            dkr_ports = {"6379/tcp": 6379}
        )
    S.start_servive()

    client = docker.from_env()
    c = client.containers.get("redis")
    print("{}: {}".format(S.dkr_service, c.status))

    yield S

    print("Tearing down redis fixture")
    S.stop_service()