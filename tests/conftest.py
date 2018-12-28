import sys
import pytest
import docker
from diana.utils.endpoint import Containerized

sys.path.append('test_utils')

@pytest.fixture(scope="module")
def setup_orthanc():

    print("Standing up orthanc fixture")

    S = Containerized(
            dkr_service = "orthanc",
            dkr_image = "derekmerck/orthanc-confd",
            dkr_env={"ORTHANC_MOD_0": "remote,ORTHANC,localhost,4243"}
    )
    S.start_service()

    client = docker.from_env()
    c = client.containers.get("orthanc")
    print("{}: {}".format(S.dkr_service, c.status))

    yield S

    print("Tearing down orthanc fixture")
    S.stop_service()


@pytest.fixture(scope="module")
def setup_orthanc2():

    print("Standing up orthanc2 fixture")

    S = Containerized(
            dkr_service = "orthanc2",
            dkr_image = "derekmerck/orthanc-confd",
            dkr_links = {"orthanc": None},
            dkr_env = {"ORTHANC_PEER_0": "orthanc,http://orthanc:8042,orthanc,passw0rd!",
                       "ORTHANC_MOD_0":  "remote,ORTHANC,orthanc,4242"},
            # dkr_remove = False,
            # dkr_command="tail -f > /dev/null"
        )
    S.start_service()

    client = docker.from_env()
    c = client.containers.get("orthanc2")
    print("{}: {}".format(S.dkr_service, c.status))

    yield S

    print("Tearing down orthanc2 fixture")
    S.stop_service()

@pytest.fixture(scope="module")
def setup_redis():

    print("Standing up redis fixture")

    S = Containerized(
            dkr_service = "redis",
            dkr_image = "redis",
            dkr_ports = {"6379/tcp": 6379}
        )
    S.start_service()

    client = docker.from_env()
    c = client.containers.get("redis")
    print("{}: {}".format(S.dkr_service, c.status))

    yield S

    print("Tearing down redis fixture")
    S.stop_service()