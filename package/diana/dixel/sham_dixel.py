from datetime import datetime, timedelta
import logging
import hashlib
from dateutil import parser as DateTimeParser
import attr
from . import Dixel
from ..utils.guid import GUIDMint
from ..utils.dicom import dicom_date, dicom_name, dicom_datetime, DicomLevel, DicomUIDMint


@attr.s(cmp=False)
class ShamDixel(Dixel):

    REFERENCE_DATE = None
    ShamUID = DicomUIDMint()

    @classmethod
    def from_dixel(cls, dixel: Dixel, salt: str=None):
        # Force the new instance to keep its own copy of any data
        _meta = dict(dixel.meta)
        _tags = dict(dixel.tags)
        sh = ShamDixel(
            meta=_meta,
            tags=_tags,
            salt=salt,
            level=dixel.level
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
        Dixel.update_meta(self)
        self.update_shams()


    def update_shams(self):

        self.meta["ShamID"] = self.sham_info["ID"]
        self.meta["ShamName"] = dicom_name(self.sham_info["Name"])
        self.meta["ShamBirthDate"] = dicom_date(self.sham_info["BirthDate"])

        if self.tags.get("AccessionNumber"):
            self.meta["ShamAccessionNumber"] = \
                hashlib.md5(self.tags["AccessionNumber"].encode("UTF-8")).hexdigest()

        if self.meta.get("StudyDateTime"):
           self.meta["ShamStudyDateTime"] = self.meta.get("StudyDateTime") + self.sham_info['TimeOffset']

        if self.level >= DicomLevel.SERIES and \
                self.meta.get("SeriesDatetime"):
            self.meta["ShamSeriesDateTime"] = self.meta.get("SeriesDatetime") + self.sham_info['TimeOffset']

        if self.level >= DicomLevel.INSTANCES and \
                self.tags.get("InstanceDateTime"):
            self.meta["ShamInstanceCreationDateTime"] = self.tags.get("InstanceDateTime") + \
                                                        self.sham_info['TimeOffset']
    def ShamStudyDate(self):
        if self.meta.get("ShamStudyDateTime"):
            return dicom_datetime(self.meta["ShamStudyDateTime"])[0]

    def ShamStudyTime(self):
        if self.meta.get("ShamStudyDateTime"):
            return dicom_datetime(self.meta["ShamStudyDateTime"])[1]

    def ShamSeriesDate(self):
        if self.meta.get("ShamSeriesDateTime"):
            return dicom_datetime(self.meta["ShamSeriesDateTime"])[0]

    def ShamSeriesTime(self):
        if self.meta.get("ShamStudyDateTime"):
            return dicom_datetime(self.meta["ShamSeriesDateTime"])[1]

    def ShamStudyUID(self):
        return ShamDixel.ShamUID.uid(PatientID=self.meta["ShamID"],
                         StudyInstanceUID=self.meta["ShamAccessionNumber"])

    def ShamSeriesUID(self):
        return ShamDixel.ShamUID.uid(PatientID=self.meta["ShamID"],
                         StudyInstanceUID=self.meta["ShamAccessionNumber"],
                         SeriesInstanceUID=self.meta["ShamSeriesNumber"])

    def ShamInstanceUID(self):
        return ShamDixel.ShamUID.uid(PatientID=self.meta["ShamID"],
                         StudyInstanceUID=self.meta["ShamAccessionNumber"],
                         SeriesInstanceUID=self.meta["ShamSeriesNumber"],
                         SOPInstanceUID=self.tags["InstanceNumber"])

    def orthanc_sham_map(self):

        if self.level >= DicomLevel.INSTANCES:
            raise NotImplementedError

        replace = {
                "PatientName": self.meta["ShamName"],
                "PatientID": self.meta["ShamID"],
                "PatientBirthDate": self.meta["ShamBirthDate"],
                "AccessionNumber": self.meta["ShamAccessionNumber"],
                "StudyInstanceUID": ShamDixel.ShamStudyUID(self),
                "StudyDate": ShamDixel.ShamStudyDate(self),
                "StudyTime": ShamDixel.ShamStudyTime(self),
            }
        keep = ['PatientSex']

        if self.meta.get('ShamStudyDescription'):
            replace['StudyDescription'] = self.meta.get('ShamStudyDescription')
        else:
            keep.append('StudyDescription')

        if self.level >= DicomLevel.SERIES:
            replace['SeriesInstanceUID'] = ShamDixel.ShamSeriesUID(self)
            replace['SeriesTime'] = ShamDixel.ShamSeriesTime(self)
            replace['SeriesDate'] = ShamDixel.ShamSeriesDate(self)
            if self.meta.get('ShamSeriesDescription'):
                replace['SeriesDescription'] = self.meta.get('ShamSeriesDescription')
            else:
                keep.append('SeriesDescription')
            if self.meta.get('ShamSeriesNumber'):
                replace['SeriesNumber'] = self.meta.get('ShamSeriesNumber')
            else:
                keep.append('SeriesNumber')

        if self.level >= DicomLevel.INSTANCES:
            replace['SOPInstanceUID'] = ShamDixel.ShamInstanceUID(self)
            replace['InstanceCreationTime'] = ShamDixel.ShamInstanceTime(self)
            replace['InstanceCreationDate'] = ShamDixel.ShamInstanceDate(self)

        return {
            "Replace": replace,
            "Keep": keep,
            "Force": True
        }

