from typing import Mapping
# import logging
from dateutil import parser as DatetimeParser
import attr
import pydicom
from ..utils.dicom import DicomLevel
from ..utils import Serializable
from ..utils.gateways.orthanc import orthanc_id


@attr.s(cmp=False)
class Dixel(Serializable):

    meta = attr.ib(factory=dict)
    tags = attr.ib(factory=dict)
    level = attr.ib(default=DicomLevel.STUDIES, convert=DicomLevel)

    # Making this init=False removes it from the serializer
    file = attr.ib(default=None, repr=False, init=False)

    def __hash__(self):
        # return hash(self.oid())
        return hash(self.tags.values())

    def __cmp__(self, other):
        return self.sid() == other.sid() and \
               self.tags == other.tags and \
               self.meta == other.meta and \
               self.level == other.level

    @staticmethod
    def from_pydicom(ds: pydicom.Dataset, fn: str, file=None):

        def mktime(datestr, timestr):
            dt_str = datestr + timestr
            dt = DatetimeParser.parse(dt_str)
            return dt

        meta = {
            'FileName': fn
        }

        # Most relevant tags for indexing
        tags = {
            'AccessionNumber': ds.AccessionNumber,
            'PatientName': str(ds.PatientName),  # Odd unserializing type
            'PatientID': ds.PatientID,
            'PatientBirthDate': ds.PatientBirthDate,

            'StudyInstanceUID': ds.StudyInstanceUID,
            'StudyDescription': ds.StudyDescription,
            'StudyDateTime': mktime(
                ds.StudyDate,
                ds.StudyTime),

            'SeriesDescription': ds.SeriesDescription,
            'SeriesNumber': ds.SeriesNumber,
            'SeriesInstanceUID': ds.SeriesInstanceUID,
            'SeriesDateTime': mktime(
                ds.SeriesDate,
                ds.SeriesTime),

            'SOPInstanceUID': ds.SOPInstanceUID,
            'InstanceCreationDateTime': mktime(
                ds.InstanceCreationDate,
                ds.InstanceCreationTime),

        }
        level = DicomLevel.INSTANCES
        d = Dixel(meta=meta,
                  tags=tags,
                  level=level)
        if file:
            d.file = file

        return d

    @staticmethod
    def from_montage(ds: Mapping):
        meta = {}
        tags = ds
        level = DicomLevel.STUDIES
        return Dixel(meta=meta,
                     tags=tags,
                     level=level)

    @staticmethod
    def from_orthanc(meta: Mapping, tags: Mapping=None, file=None):
        d = Dixel(meta=meta,
                  tags=tags)
        if file:
            d.file = file

    # orthanc id
    def oid(self):
        if not self.meta.get('ID'):
            if self.level == DicomLevel.PATIENTS:
                self.meta['ID'] = orthanc_id(self.tags.get('PatientID'))
            elif self.level == DicomLevel.STUDIES:
                self.meta['ID'] = orthanc_id(self.tags.get('PatientID'),
                                             self.tags.get('StudyInstanceUID'))
            elif self.level == DicomLevel.SERIES:
                self.meta['ID'] = orthanc_id(self.tags.get('PatientID'),
                                             self.tags.get('StudyInstanceUID'),
                                             self.tags.get('SeriesInstanceUID'))
            elif self.level == DicomLevel.INSTANCES:
                self.meta['ID'] = orthanc_id(self.tags.get('PatientID'),
                                             self.tags.get('StudyInstanceUID'),
                                             self.tags.get('SeriesInstanceUID'),
                                             self.tags.get('SOPInstanceUID'))
            else:
                raise ValueError("Unknown DicomLevel for oid")
        return self.meta.get('ID')

    # serializer id
    def sid(self):
        return self.tags.get('AccessionNumber')

    # filename
    def fn(self):
        return self.meta.get('FileName')


Serializable.Factory.register(Dixel)
