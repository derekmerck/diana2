# Simple remove/replace/keep sham map suitable for use with Orthanc

import logging
import random
from datetime import timedelta
from hashlib import sha224
from .dixel import Dixel
from diana.utils.dicom import DicomLevel, DicomHashUIDMint, dicom_date, dicom_time

MAX_STUDY_DAYS_OFFSET = 14           # 2 weeks
MAX_STUDY_SECONDS_OFFSET = 60*60*2   # 2 hours


def huid_sham_map(d: Dixel):
    if d.level > DicomLevel.INSTANCES:
        raise NotImplementedError("Can only create default hash sham maps for instances")

    logging.debug(d)

    patient_hash = sha224(d.tags["PatientID"].encode('utf8')).hexdigest()
    study_hash = sha224(d.tags["StudyInstanceUID"].encode('utf8')).hexdigest()
    series_hash = sha224(d.tags["SeriesInstanceUID"].encode('utf8')).hexdigest()
    inst_hash = sha224(d.tags["SOPInstanceUID"].encode('utf8')).hexdigest()

    random.seed(patient_hash)
    day_offset = random.randint(-14, 14)  # 2 weeks
    sec_offset = random.randint(-60 * 60 * 2, 60 * 60 * 2)  # 2 hours
    dt_offset = timedelta(days=day_offset, seconds=sec_offset)

    new_study_dt = d.meta["StudyDateTime"] + dt_offset
    new_series_dt = d.meta["SeriesDateTime"] + dt_offset
    new_inst_dt = d.meta["InstanceCreationDateTime"] + dt_offset

    m = {
        "Remove": [
            "PatientName",
            "PatientBirthDate",
        ],
        "Replace": {
            "PatientID": patient_hash[0:16],
            "AccessionNumber": study_hash[0:16],
            "StudyInstanceUID": DicomHashUIDMint().content_hash_uid(
                hex_hash=study_hash, dicom_level=DicomLevel.STUDIES),
            "StudyDate": dicom_date(new_study_dt),
            "StudyTime": dicom_time(new_study_dt),
            "SeriesInstanceUID": DicomHashUIDMint().content_hash_uid(
                hex_hash=series_hash, dicom_level=DicomLevel.SERIES),
            "SeriesDate": dicom_date(new_series_dt),
            "SeriesTime": dicom_time(new_series_dt),
            "SOPInstanceUID": DicomHashUIDMint().content_hash_uid(
                hex_hash=inst_hash, dicom_level=DicomLevel.SERIES),
            "InstanceCreationDate": dicom_date(new_inst_dt),
            "InstanceCreationTime": dicom_time(new_inst_dt),
        },
        "Keep": [
            "PatientAge",
            "PatientSex",
            'StudyDescription',
            'SeriesDescription',
            'InstanceNumber'
        ],
        "Force": True
    }
    return m
