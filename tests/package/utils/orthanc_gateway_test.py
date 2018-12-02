import logging
from diana.utils.gateways import Orthanc

"""
$ docker run derekmerck/orthanc-confd -p 8042:8042
"""

def test_orthanc_gateway():

    O = Orthanc()
    assert( O.statistics().get('CountInstances') >= 0 )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_orthanc_gateway()