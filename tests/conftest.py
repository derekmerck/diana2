import sys
import pytest
import docker
from diana.utils.endpoint import Containerized

sys.path.append('test_utils')

@pytest.fixture(scope="session")
def setup_orthanc():

    print("Standing up orthanc fixture")

    S = Containerized(
            dkr_name  = "orthanc",
            dkr_image = "derekmerck/orthanc-confd",
            dkr_ports = {"8042/tcp": 8042, "4242/tcp": 4242},
            dkr_env={"ORTHANC_MOD_0": "remote,ORTHANC,localhost,4243"}
    )
    S.start_container()

    client = docker.from_env()
    c = client.containers.get("orthanc")
    print("{}: {}".format(S.dkr_name, c.status))

    yield S

    print("Tearing down orthanc fixture")
    S.stop_container()


@pytest.fixture(scope="session")
def setup_orthanc2():

    print("Standing up orthanc2 fixture")

    S = Containerized(
            dkr_name  = "orthanc2",
            dkr_image = "derekmerck/orthanc-confd",
            dkr_ports = {"8042/tcp": 8043, "4242/tcp": 4243},
            dkr_links = {"orthanc": None},
            dkr_env = {"ORTHANC_PEER_0": "orthanc,http://orthanc:8042,orthanc,passw0rd!",
                       "ORTHANC_MOD_0":  "remote,ORTHANC,orthanc,4242"},
            # dkr_remove = False,
            # dkr_command="tail -f > /dev/null"
        )
    S.start_container()

    client = docker.from_env()
    c = client.containers.get("orthanc2")
    print("{}: {}".format(S.dkr_name, c.status))

    yield S

    print("Tearing down orthanc2 fixture")
    S.stop_container()

@pytest.fixture(scope="session")
def setup_redis():

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

    yield S

    print("Tearing down redis fixture")
    S.stop_container()

