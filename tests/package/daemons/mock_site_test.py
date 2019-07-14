import logging, random
from datetime import datetime
from pprint import pformat
import yaml
from diana.apis import Orthanc
from diana.daemons import MockSite
from diana.dixel.mock_dixel import reset_mock_seed

from interruptingcow import timeout


sample_site_desc = """
- name: Example Hospital
  services:
  - name: Main CT
    modality: CT
    devices: 3
    studies_per_hour: 30
  - name: Main MR
    modality: MR
    devices: 2
    studies_per_hour: 10
"""

ref_studies = [
    "cafb-01-001: 1.2.826.0.1.3680043.10.43.55.908786948015.186631867210.9883.9883 : IMG839 CT CHEST WIVC / Localizer 1",
    "a973-01-001: 1.2.826.0.1.3680043.10.43.55.645690578333.488786789619.9883.9883 : IMG763 CT PELVIS NC / Localizer 1",
    "ec17-01-001: 1.2.826.0.1.3680043.10.43.55.821881799968.932901781804.9883.9883 : IMG919 CT NECK WWOIVC / Localizer 1",
    "4984-01-001: 1.2.826.0.1.3680043.10.43.55.303160580365.803142399889.9883.9883 : IMG771 MR PELVIS NC / Localizer ",
    "acae-01-001: 1.2.826.0.1.3680043.10.43.55.601486131319.972125320799.9883.9883 : IMG806 MR ABDOMEN NC / Localizer "
]
ref_dt = datetime(year=2018, month=1, day=1)

def test_mock_site():
    reset_mock_seed()

    site_desc = yaml.load(sample_site_desc)
    logging.debug(pformat(site_desc))

    H = MockSite.Factory.create(desc=site_desc)[0]

    logging.debug(H)
    logging.debug(list(H.devices()))

    assert( len(list(H.devices())) == 5 )

    for device in H.devices():
        s = device.gen_study(study_datetime=ref_dt)
        # print("{!s}".format( next(s.instances()) ))
        assert( "{!s}".format( next(s.instances()) ) in ref_studies )


def test_site_submission(setup_orthanc0):
    reset_mock_seed()

    O = Orthanc()

    assert( O.check() )

    n_instances_init = O.gateway.statistics()["CountInstances"]

    logging.debug( O.gateway.statistics() )

    site_desc = yaml.load(sample_site_desc)

    H = MockSite.Factory.create(desc=site_desc)[0]

    try:
        with timeout(15):
            print("Starting mock site")
            H.run(pacs=O)
    except:
        print("Stopping mock site")

    n_instances = O.gateway.statistics()["CountInstances"]

    # At least 500 new instances arrived in the last 15 seconds
    assert( n_instances > n_instances_init + 500 )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    test_mock_site()

    from conftest import setup_orthanc0

    for i in setup_orthanc0():
        test_site_submission(None)