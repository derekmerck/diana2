import logging
import docker
from diana.utils.endpoint import Containerized





def test_swarm():
    client = Containerized.api_client()
    logging.debug(client.services())
    Containerized.clean_swarm()
    logging.debug(client.services())

    assert( len(client.services()) == 0 )

    C = Containerized(
        dkr_name="testing",
        dkr_image="alpine",
        dkr_command="tail -f > /dev/null"
    )
    C.start_service()

    assert( len(client.services()) == 1 )

    logging.debug(client.services())

    assert( "testing" in client.services()[0]["Spec"]["Name"] )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_swarm()