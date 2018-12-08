from datetime import datetime, timedelta
import logging
import hashlib
from dateutil import parser as DateTimeParser
import attr
from . import Dixel
from ..utils.guid import GUIDMint
from ..utils.dicom import dicom_date, dicom_name, dicom_datetime, DicomLevel


@attr.s(cmp=False)
class ShamDixel(Dixel):

    REFERENCE_DATE = None

    @classmethod
    def from_dixel(cls, dixel: Dixel, salt: str=None):
        # Force the new instance to keep its own copy of any data
        _meta = dict(dixel.meta)
        _tags = dict(dixel.tags)
        sh = ShamDixel(
            meta=_meta,
            tags=_tags,
            salt=salt
        )
        if dixel.file:
            sh.file = dixel.file
        return sh


    salt = attr.ib(default=None, type=str)
    sham_info = attr.ib(init=False, repr=False)

    @sham_info.default
    def set_sham_info(self):

        logging.debug(self)

        name = self.tags.get("PatientName")
        if self.salt:
            name = "{}+{}".format(name, self.salt)

        sham_info = GUIDMint.get_sham_id(
            name=name,
            dob=self.tags.get("PatientBirthDate"),
            age=self.meta.get("Age"),
            gender=self.tags.get("PatientSex", "U"),
            reference_date=self.REFERENCE_DATE
        )

        return sham_info


    def __attrs_post_init__(self):
        self.update_shams()


    def update_shams(self, force=False):

        logging.debug(self)

        self.meta["ShamID"] = self.sham_info["ID"]

        self.meta["ShamName"] = dicom_name(self.sham_info["Name"])

        self.meta["ShamBirthDate"] = dicom_date(self.sham_info["BirthDate"])

        if self.tags.get("AccessionNumber"):
            self.meta["ShamAccessionNumber"] = \
                hashlib.md5(self.tags["AccessionNumber"].encode("UTF-8")).hexdigest()

        if self.tags.get("StudyDate") and self.tags.get("StudyTime"):
            dt = DateTimeParser.parse(self.tags['StudyDate'] + self.tags['StudyTime'])
            new_dt = dt + self.sham_info['TimeOffset']
            self.meta["ShamStudyDateTime"] = new_dt

        if self.level > DicomLevel.STUDIES and \
                self.tags.get("SeriesDate") and self.tags.get("SeriesTime"):
            dt = DateTimeParser.parse(self.tags['SeriesDate'] + self.tags['SeriesTime'])
            new_dt = dt + self.sham_info['TimeOffset']
            self.meta["ShamSeriesDateTime"] = new_dt

        if self.level > DicomLevel.SERIES and \
                self.tags.get("InstanceCreationDate") and self.tags.get("InstanceCreationTime"):
            dt = DateTimeParser.parse(self.tags['InstanceCreationDate'] + self.tags['InstanceCretionTime'])
            new_dt = dt + self.sham_info['TimeOffset']
            self.meta["ShamInstanceCreationDateTime"] = new_dt

    @property
    def ShamStudyDate(self):
        return dicom_datetime(self.meta["ShamStudyDateTime"])[0]

    @property
    def ShamStudyTime(self):
        return dicom_datetime(self.meta["ShamStudyDateTime"])[1]

    @property
    def ShamSeriesDate(self):
        return dicom_datetime(self.meta["ShamSeriesDateTime"])[0]

    @property
    def ShamSeriesTime(self):
        return dicom_datetime(self.meta["ShamSeriesDateTime"])[1]
