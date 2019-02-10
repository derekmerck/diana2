import logging
from diana.utils.gateways import Orthanc


def test_orthanc_gateway(setup_orthanc0):

    O = Orthanc()
    assert( O.statistics().get('CountInstances') >= 0 )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    from conftest import mk_orthanc

    O = mk_orthanc()
    logging.debug(O.dkr_container.status)
    test_orthanc_gateway(None)

