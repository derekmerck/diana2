import logging, os, time
import subprocess
from diana.apis import Orthanc
from diana.utils.endpoint import Containerized as C
from test_utils import find_resource
import pytest


# TODO: Broken and needs attention...
@pytest.mark.skip(reason="Unknown change to swarm manager?")
def test_mock_svcs():

    C.start_swarm()
    C.clean_swarm()

    c = C.api_client()

    admin_stack = find_resource("platform/docker-stacks/admin/admin-stack.yml")
    cmd = ["docker", "stack", "deploy", "-c", admin_stack, "admin"]
    subprocess.run(cmd)

    service_names = [x['Spec']['Name'] for x in c.services()]

    assert( "admin_portainer" in service_names )
    assert( "admin_traefik" in service_names )

    mock_stack = find_resource("platform/docker-stacks/diana-workers/mock-stack.yml")
    cmd = ["docker", "stack", "deploy", "-c", mock_stack, "mock"]

    # Don't forget to set the password, or docker-compose will
    # interpret it as empty rather than default
    os.environ["ORTHANC_PASSWORD"] = "passw0rd!"
    subprocess.run(cmd)

    service_names = [x['Spec']['Name'] for x in c.services()]

    assert ("mock_diana-mock" in service_names)
    assert ("mock_orthanc-mock" in service_names)

    # Pause to generate some data
    time.sleep(20)

    O = Orthanc(path="orthanc-mock", port=80)
    info = O.gateway._get("statistics")

    # At least 100 new images in the PACS
    assert( info['CountInstances'] > 100 )

    C.clean_swarm()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_mock_svcs()
