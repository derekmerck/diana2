import logging, sys
import yaml
from multiprocessing import Process
from diana.apis import Orthanc, ObservableProxiedDicom
from diana.daemons.mock_site import MockSite
from diana.dixel.mock_dixel import reset_mock_seed
from diana.utils.dicom import DicomEventType
from diana.utils.endpoint import Watcher, Trigger

from interruptingcow import timeout
from diana.utils.gateways.requesters import suppress_urllib_debug


site_desc = """
---
- services:
  - name: imaging
    modality: CR
    devices: 1
    studies_per_hour: 1
"""


def mock_runner():
    """Generates a single CR study and sends to the mock pacs"""

    reset_mock_seed()
    print("Starting mock site")
    O = Orthanc()
    desc = yaml.load(site_desc)
    H = MockSite.Factory.create(desc=desc)[0]
    H.run(pacs=O)
    print("Stopping mock site")


def test_mock_watcher(setup_orthanc0, setup_orthanc1, capfd):

    obs = ObservableProxiedDicom(proxy_desc={"port": 8043})
    watcher = Watcher()

    trigger0 = Trigger(
        evtype=DicomEventType.STUDY_ADDED,
        source=obs,
        action=obs.say
    )
    watcher.add_trigger(trigger0)

    p = Process(target=mock_runner)
    p.start()

    try:
        with timeout(10):
            print("Starting watcher")
            watcher.run()
    except:
        print("Stopping watcher")

    # Force p to flush stdout
    sys.stdout.flush()
    p.terminate()

    if capfd:
        captured = capfd.readouterr()
        print(captured.out)
        assert "AccessionNumber" in captured.out
        assert "SeriesInstanceUID" not in captured.out


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    suppress_urllib_debug()

    from conftest import setup_orthanc0, setup_orthanc1

    setup_orthanc0()
    setup_orthanc1()

    test_mock_watcher(None, None, None)

