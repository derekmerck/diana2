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
    S = mk_orthanc(8043,4243,8042,4242)
    yield S
    print("Tearing down orthanc fixture")
    S.stop_container()


def mk_orthanc(http_port=8042, dcm_port=4242, remote_peer=8043, remote_mod=4243):

    print("Standing up orthanc fixture")
    dkr_name = "orthanc-{}".format(http_port)

    import socket
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)

    S = Containerized(
            dkr_name  = dkr_name,
            dkr_image = "derekmerck/orthanc-confd",
            dkr_ports = {"8042/tcp": http_port, "4242/tcp": dcm_port},
            dkr_env = {"ORTHANC_MOD_0": "mod0,ORTHANC{},{},{}".format(remote_mod, host_ip, remote_mod),
                       "ORTHANC_PEER_0": "peer0,http://{}:{},orthanc,passw0rd!".format(host_ip, remote_peer),
                       "ORTHANC_AET": "ORTHANC{}".format(dcm_port),
                       "ORTHANC_VERBOSE": "true"}
    )
    S.start_container()

    client = docker.from_env()
    c = client.containers.get(dkr_name)
    print("{}: {}".format(S.dkr_name, c.status))

    return S


@pytest.fixture(scope="session")
def setup_redis():
    S = mk_redis()
    yield S
    print("Tearing down redis fixture")
    S.stop_container()


def mk_redis():

    print("Standing up redis fixture")
    dkr_name = "redis"

    S = Containerized(
            dkr_name  = dkr_name,
            dkr_image = "redis",
            dkr_ports = {"6379/tcp": 6379}
        )
    S.start_container()

    client = docker.from_env()
    c = client.containers.get(dkr_name)
    print("{}: {}".format(S.dkr_name, c.status))

    return S
