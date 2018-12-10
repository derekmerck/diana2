import logging
from pprint import pformat
import yaml
from diana.daemons.mock import MockSite
from diana.dixel import MockDixel

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

def test():

    site_desc = yaml.load(sample_site_desc)

    logging.debug(pformat(site_desc))

    H = MockSite.Factory.create(desc=site_desc)[0]

    logging.debug(H)

    logging.debug(MockDixel())
    logging.debug(MockDixel())


if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()