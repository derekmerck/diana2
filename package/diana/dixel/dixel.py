import logging
from typing import Mapping
from pprint import pformat
from dateutil import parser as DatetimeParser
import attr
import pydicom
from .report import RadiologyReport
from ..utils.dicom import DicomLevel
from ..utils import Serializable
from ..utils.gateways import orthanc_id, Montage


def mktime(datestr, timestr):
    dt_str = datestr + timestr
    dt = DatetimeParser.parse(dt_str)
    return dt


@attr.s(cmp=False, hash=None)
class Dixel(Serializable):

    meta = attr.ib(factory=dict)
    tags = attr.ib(factory=dict)
    level = attr.ib(default=DicomLevel.STUDIES, converter=DicomLevel)

    # Making this init=False removes it from the serializer
    # Use a "from" constructor or add "file" manually after creation
    file = attr.ib(default=None, repr=False, init=False)
    pixels = attr.ib(default=None, repr=False, init=False)
    report = attr.ib(default=None, repr=False, init=False)
    children = attr.ib(init=False, factory=list)

    def __attrs_post_init__(self):
        self.update_meta()

    def update_meta(self):
        if self.tags.get("StudyDate"):
            self.meta["StudyDateTime"] = mktime(self.tags.get("StudyDate"), self.tags.get("StudyTime"))
        if self.tags.get("SeriesDate") and self.level >= DicomLevel.SERIES:
            self.meta["SeriesDateTime"] = mktime(self.tags.get("SeriesDate"), self.tags.get("SeriesTime"))
        if self.tags.get("InstanceCreationDate") and self.level >= DicomLevel.INSTANCES:
            self.meta["InstanceDateTime"] = mktime(self.tags.get("InstanceCreationDate"),
                                                   self.tags.get("InstanceCreationTime"))

    @staticmethod
    def from_pydicom(ds: pydicom.Dataset, fn: str, file=None):

        meta = {
            'FileName': fn,
            'TransferSyntaxUID': ds.file_meta.TransferSyntaxUID,
            'TransferSyntax': str(ds.file_meta.TransferSyntaxUID),
            'MediaStorage': str(ds.file_meta.MediaStorageSOPClassUID),
        }

        # Most relevant tags for indexing
        tags = {
            'AccessionNumber': ds.AccessionNumber,
            'PatientName': str(ds.PatientName),  # Odd unserializing type
            'PatientID': ds.PatientID,
            'PatientBirthDate': ds.PatientBirthDate,
            'StudyInstanceUID': ds.StudyInstanceUID,
            'StudyDescription': ds.StudyDescription,
            'StudyDate': ds.StudyDate,
            'StudyTime': ds.StudyTime,
            'SeriesDescription': ds.SeriesDescription,
            'SeriesNumber': ds.SeriesNumber,
            'SeriesInstanceUID': ds.SeriesInstanceUID,
            'SeriesDate': ds.SeriesDate,
            'SeriesTime': ds.SeriesTime,
            'SOPInstanceUID': ds.SOPInstanceUID,
            'InstanceCreationDate': ds.InstanceCreationDate,
            'InstanceCreationTime': ds.InstanceCreationTime,
            'PhotometricInterpretation': ds[0x0028, 0x0004].value,  # MONOCHROME, RGB etc.
        }

        d = Dixel(meta=meta,
                  tags=tags,
                  level=DicomLevel.INSTANCES)
        if file:
            d.file = file

        if hasattr(ds, "PixelData"):
            d.pixels = ds.pixel_array

        return d

    @staticmethod
    def from_montage_csv(data: Mapping):

        tags = {
            "AccessionNumber": data["Accession Number"],
            "PatientID": data["Patient MRN"],
            'StudyDescription': data['Exam Description'],
            'ReferringPhysicianName': data['Ordered By'],
            'PatientSex': data['Patient Sex'],
            "StudyDate": data['Exam Completed Date'],
            'Organization': data['Organization'],
        }

        meta = {
            'PatientName': "{}^{}".format(
                data["Patient Last Name"].upper(),
                data["Patient First Name"].upper()),
            'PatientAge': data['Patient Age'],
            "OrderCode": data["Exam Code"],
            "PatientStatus": data["Patient Status"],
            "ReportText": data["Report Text"],
        }

        d = Dixel(meta=meta,
                  tags=tags,
                  level=DicomLevel.STUDIES)
        d.report = RadiologyReport(meta['ReportText'])

        return d

    @staticmethod
    def from_montage_json(data: Mapping):
        """Tracks Montage-mappedd CPT codes, to dereference them to
        real CPT codes and body parts, call Montage().get_meta(dixel)"""

        # logging.debug(pformat(data['exam_type']))

        referring_physician = data['events'][0].get('provider')
        if referring_physician:
            referring_physician = referring_physician.get('name')

        study_datetime = None
        if len(data['events']) > 2:
            study_datetime = DatetimeParser.parse(data['events'][2]['date'])

        montage_cpts = []
        for resource in data["exam_type"]["cpts"]:
            code = resource.split("/")[-2]
            montage_cpts.append(code)

        # TODO: Check event flags for various event types to get ordering and reading

        tags = {
            "AccessionNumber": data["accession_number"],
            "PatientID": data["patient_mrn"],
            'StudyDescription': data['exam_type']['description'],
            'ReferringPhysicianName': referring_physician,
            'PatientSex': data['patient_sex'],
            'Organization': data['organization']['label'],
            "Modality": data['exam_type']['modality']['label']
        }

        meta = {
            'BodyPart': None,
            'PatientName': "{}^{}".format(
                data["patient_last_name"].upper(),
                data["patient_first_name"].upper()),
            'PatientAge': data['patient_age'],
            "OrderCode": data["exam_type"]["code"],
            "PatientStatus": data["patient_status"],
            "ReportText": Montage.clean_text(data['text']),
            "ReadingPhysiciansName": data['events'][-1]['provider']['name'],
            'StudyDateTime': study_datetime,
            "MontageCPTCodes": montage_cpts
        }

        d = Dixel(meta=meta,
                  tags=tags,
                  level=DicomLevel.STUDIES)
        d.report = RadiologyReport(meta['ReportText'])

        return d

    @staticmethod
    def from_orthanc(meta: Mapping=None, tags: Mapping=None,
                     level: DicomLevel=DicomLevel.STUDIES, file=None):

        d = Dixel(meta=meta,
                  tags=tags,
                  level=level)
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

    def get_pixels(self):
        if not self.pixels:
            raise TypeError

        if self.meta.get('PhotometricInterpretation') == "RGB":
            pixels = self.pixels.reshape([self.pixels.shape[1], self.pixels.shape[2], 3])
        else:
            pixels = self.pixels

        return pixels