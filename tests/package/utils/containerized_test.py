import logging
import docker
from diana.utils.endpoint import Containerized

def test():

    C = Containerized(
        dkr_service="testing",
        dkr_image="alpine",
        dkr_command="tail -f > /dev/null"
    )

    C.start_servive()

    client = docker.from_env()
    c = client.containers.get("testing")
    assert( c.status == "running" )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

