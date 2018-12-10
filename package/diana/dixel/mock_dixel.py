from datetime import datetime
from itertools import count
import random
import attr
from . import Dixel
from ..utils.dicom import DicomLevel, dicom_datetime
from ..utils.guid import GUIDMint


@attr.s
class MockDixel(Dixel):
    """This is a study-level root dixel"""
    n_dixels = count(0)
    dxid = attr.ib(init=False, factory=n_dixels.__next__)

    study_datetime=attr.ib(factory=datetime.now, type=datetime)
    site_name=attr.ib(default="Mock Site", type=str)
    station_name=attr.ib(default="Scanner", type=str)
    modality=attr.ib(default="CT", type=str)

    gender = attr.ib(init=False)
    @gender.default
    def setup_gender(self):
        return random.choice(["M", "F"])

    level = attr.ib(init=False, default=DicomLevel.STUDIES)

    study_description=attr.ib(init=False)
    @study_description.default
    def set_study_description(self):
        anatomy = random.choice(["HEAD",
                                 "NECK",
                                 "EXTREMITY",
                                 "PELVIS",
                                 "CHEST",
                                 "ABDOMEN"])
        contrast = random.choice(["NC", "WIVC", "WWOIVC"])
        code = 0
        for c in self.modality + anatomy + contrast:
            code += ord(c)

        result = "IMG{} {} {} {}".format(code, self.modality, anatomy, contrast)
        return result

    def __attrs_post_init__(self):
        patient_info = GUIDMint.get_sham_id(
                name=self.dxid,
                age=random.randint(18, 85),
                gender=self.gender,
                reference_date=datetime.now()
            )

        self.meta = {
            "StudyDateTime": self.study_datetime
        }
        self.tags = {
            "PatientName": patient_info["Name"],
            "PatientID": patient_info["ID"],
            "PatientSex": str(self.gender),
            "PatientBirthDate": patient_info["BirthDate"].isoformat(),
            "StudyDescription": self.study_description,
            "StationName": self.station_name,
            "Institution": self.site_name,
            "Modality": self.modality,
            "StudyDate": dicom_datetime(self.study_datetime)[0],
            "StudyTime": dicom_datetime(self.study_datetime)[1]
        }

