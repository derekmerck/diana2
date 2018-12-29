import logging
from pprint import pformat
from distutils.version import LooseVersion
from diana.utils.endpoint import Containerized

def test_swarm():
    client = Containerized.api_client()
    logging.debug(client.services())
    Containerized.clean_swarm()
    logging.debug(client.services())

    logging.debug(pformat(client.version()))

    api_vers = client.version()["ApiVersion"]
    logging.debug(api_vers)

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

    C.stop_service()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_swarm()