import random
from datetime import datetime, timedelta
import attr
from ...utils.dicom import DicomLevel
from ...dixel import MockDixel
from ...apis import Orthanc

sample_site_desc = """
---
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

@attr.s
class MockDevice(object):
    """Generates studies on a schedule"""

    pacs = attr.ib(type=Orthanc, default=None, repr=False)
    site_name = attr.ib(default="Mock Facility")
    station_name = attr.ib(default="Imaging Service")
    modality = attr.ib(default="CT")
    studies_per_hour = attr.ib(default=6)

    _next_study = attr.ib(init=False, factory=datetime.now)

    def gen_study(self):
        s = MockDixel(study_datetime=datetime.now(),
                      site_name = self.site_name,
                      station_name = self.station_name,
                      modality=self.modality,
                      study_description="Indicated Exam",
                      level=DicomLevel.STUDIES
                      )
        return s

    def poll(self):
        if datetime.now() > self._next_study:
            study = self.gen_study()
            for d in study.children:
                d.gen_file()
                self.pacs.put(d)
            delay = 60*60/self.studies_per_hour
            self._next_study = datetime.now() + timedelta(seconds=delay)


@attr.s
class MockService(object):
    """Set of similar modality imaging devices"""
    pacs = attr.ib(type=Orthanc, default=None)
    site_name = attr.ib(default="Mock Facility")
    name = attr.ib(default="Imaging Service")
    modality = attr.ib(default="CT")
    num_devices = attr.ib(default=1)
    studies_per_hour = attr.ib(default=6)

    devices = attr.ib(init=False)
    @devices.default
    def setup_devices(self):
        devices = []
        for i in range(self.num_devices):
            device = MockDevice(
                    site_name = self.site_name,
                    station_name = "{}_{}".format(
                        self.name.upper().replace(" ","_"),
                        len(devices)+1),
                    modality=self.modality,
                    studies_per_hour = self.studies_per_hour/self.num_devices,
                    pacs = self.pacs
                )
            devices.append(device)
        return devices

@attr.s
class MockSite(object):
    """Set of imaging services"""

    name = attr.ib(default="Mock Facility")
    services = attr.ib(init=False, factory=list)

    pacs = attr.ib(type=Orthanc, default=None, repr=False)

    seed = attr.ib( default=None )
    @seed.validator
    def set_seed(self, attribute, value):
        if value:
            random.seed(value)

    def add_service(self, name, modality, devices, studies_per_hour):
        self.services.append(
            MockService(
                name=name,
                modality=modality,
                num_devices=devices,
                studies_per_hour=studies_per_hour,
                site_name=self.name,
                pacs=self.pacs)
        )

    class Factory(object):

        @classmethod
        def create(cls, desc: dict):

            sites = []
            for site_desc in desc:
                site = MockSite(name=site_desc.get("name"))
                for service in site_desc.get("services"):
                    site.add_service(**service)
                sites.append(site)

            return sites
