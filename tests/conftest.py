import sys
import pytest
import docker
from diana.utils.endpoint import Containerized

sys.path.append('test_utils')


@pytest.fixture(scope="session")
def setup_orthanc0():
    S = mk_orthanc()
    yield S
    print("Tearing down orthanc fixture")
    S.stop_container()


@pytest.fixture(scope="session")
def setup_orthanc1():
    S = mk_orthanc(8043,4243,4242)
    yield S
    print("Tearing down orthanc fixture")
    S.stop_container()


def setup_redis():
    S = mk_redis()
    yield S
    print("Tearing down redis fixture")
    S.stop_container()


def mk_orthanc(http_port=8042, dcm_port=4242, remote_port=4243):

    print("Standing up orthanc fixture")

    S = Containerized(
            dkr_name  = "orthanc:{}".format(http_port),
            dkr_image = "derekmerck/orthanc-confd",
            dkr_ports = {"8042/tcp": http_port, "4242/tcp": dcm_port},
            dkr_env={"ORTHANC_MOD_0": "remote,ORTHANC,localhost,{}".format(remote_port)}
    )
    S.start_container()

    client = docker.from_env()
    c = client.containers.get("orthanc")
    print("{}: {}".format(S.dkr_name, c.status))

    return S


def mk_redis():

    print("Standing up redis fixture")

    S = Containerized(
            dkr_name  = "redis",
            dkr_image = "redis",
            dkr_ports = {"6379/tcp": 6379}
        )
    S.start_container()

    client = docker.from_env()
    c = client.containers.get("redis")
    print("{}: {}".format(S.dkr_name, c.status))

    return S
