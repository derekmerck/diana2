import logging, time
import docker
import pytest
from diana.utils.endpoint import Containerized


def test_containers():

    C = Containerized(
        dkr_name="testing",
        dkr_image="alpine",
        dkr_command="tail -f > /dev/null"
    )

    C.start_container()

    client = docker.from_env()
    c = client.containers.get("testing")
    assert( c.status == "running" )

    C.stop_container()
    time.sleep(1)

    with pytest.raises(Exception):
        c = client.containers.get("testing")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_containers()

