import logging
from diana.utils.gateways import Orthanc

"""
$ docker run derekmerck/orthanc-confd -p 8042:8042
"""
#
# @pytest.fixture(scope="module")
# def setup_orthanc():
#
#     print("Standing up orthanc fixture")
#
#     S = Containerized(
#             dkr_service = "orthanc",
#             dkr_image = "derekmerck/orthanc-confd",
#             dkr_ports = {"8042/tcp": 8042}
#         )
#     S.start_servive()
#
#     client = docker.from_env()
#     c = client.containers.get("orthanc")
#     print(c.status)
#
#     yield S
#
#     print("Tearing down orthanc fixture")
#     S.stop_service()

def test_orthanc_gateway(setup_orthanc):

    O = Orthanc()
    assert( O.statistics().get('CountInstances') >= 0 )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    import sys
    sys.path.append('..')
    from conftest import setup_orthanc

    for i in setup_orthanc():
        logging.debug(i.dkr_container.status)
        test_orthanc_gateway(None)

