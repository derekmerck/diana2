import logging
import yaml
from multiprocessing import Process
from diana.apis import Orthanc, ObservableProxiedDicom
from diana.daemons.mock_site import MockSite
from diana.dixel.mock_dixel import reset_mock_seed
from diana.utils.dicom import DicomEventType
from diana.utils.endpoint import Watcher, Trigger

from conftest import setup_orthanc, setup_orthanc2
from interruptingcow import timeout

from diana.utils.gateways.requesters import supress_urllib_debug


site_desc = """
---
- services:
  - name: imaging
    modality: CR
    devices: 1
    studies_per_hour: 1
"""

def mock_runner():

    reset_mock_seed()
    print("Starting mock site")
    O = Orthanc()
    desc = yaml.load(site_desc)
    H = MockSite.Factory.create(desc=desc)[0]
    H.run(pacs=O)
    print("Stopping mock site")


def test_mock_watcher(setup_orthanc, setup_orthanc2, capsys):

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

    p.terminate()

    if capsys:
        captured = capsys.readouterr()
        assert "AccessionNumber" in captured.out
        assert "SeriesInstanceUID" not in captured.out

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    supress_urllib_debug()

    for (i,j) in zip(setup_orthanc(), setup_orthanc2()):
        test_mock_watcher(None, None, None)
        i.stop_service()
        j.stop_service()

