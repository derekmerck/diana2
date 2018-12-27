import logging, random
from datetime import datetime
from pprint import pformat
import yaml
from diana.daemons import MockSite
from diana.dixel import MockStudy

sample_site_desc = """
- name: Example Hospital
  services:
  - name: Main CT
    modality: CT
    devices: 3
    studies_per_hour: 15
  - name: Main MR
    modality: MR
    devices: 2
    studies_per_hour: 4
"""

def test_mock_site():

    site_desc = yaml.load(sample_site_desc)

    logging.debug(pformat(site_desc))

    H = MockSite.Factory.create(desc=site_desc)[0]

    logging.debug(H)

    logging.debug(list(H.devices()))

    assert( len(list(H.devices())) == 5 )

    random.seed("diana-mock")
    ref_dt = datetime(year=2018, month=1, day=1)

    expected = [
        "72fa-01-001: 1.2.826.0.1.3680043.10.43.55.347931617183.363541089775.9883.9883 : IMG1011 CT EXTREMITY NC / Localizer 1",
        "9a3d-01-001: 1.2.826.0.1.3680043.10.43.55.751496470813.875193017942.9883.9883 : IMG1132 CT ABDOMEN WWOIVC / Localizer 1",
        "8235-01-001: 1.2.826.0.1.3680043.10.43.55.419758937095.455555102843.9883.9883 : IMG1345 CT EXTREMITY WWOIVC / Localizer 1",
        "3ce3-01-001: 1.2.826.0.1.3680043.10.43.55.841019304337.990560417635.9883.9883 : IMG847 MR CHEST WIVC / Localizer 1",
        "a122-01-001: 1.2.826.0.1.3680043.10.43.55.497131879750.627653313782.9883.9883 : IMG593 MR NECK NC / Localizer 1"
    ]

    for device in H.devices():
        s = device.gen_study(study_datetime=ref_dt)
        assert( "{!s}".format( next(s.instances()) ) in expected )


if __name__=="__main__":
    logging.basicConfig(level=logging.WARNING)
    test_mock_site()