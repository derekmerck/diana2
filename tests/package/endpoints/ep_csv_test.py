import logging
from pprint import pformat
from diana.endpoints import CsvFile
from diana.utils.dicom import DicomLevel

from diana.utils.guid.mint import GUIDMint


def skip_it():

    logging.basicConfig(level=logging.DEBUG)

    fpi = "/Users/derek/Desktop/uldrs.phi.csv"
    fpo = "/Users/derek/Desktop/uldrs.key.csv"

    C = CsvFile(fp=fpi, level=DicomLevel.SERIES)

    C.read()

    logging.debug(pformat(C.dixels))


    M = GUIDMint()

    for d in C.dixels:

        study_type = "HIGH" if "high" in d.tags['Format'] else "LOW"

        name = d.tags['PatientName'] + "^" + study_type
        dob = d.tags['PatientBirthDate']
        gender = d.tags['PatientSex']

        sham_id = M.get_sham_id(name=name, dob=dob, gender=gender)
        logging.debug(sham_id)

        d.tags['ShamPatientID'] = sham_id[0]
        d.tags['ShamPatientName'] = sham_id[1]
        d.tags['ShamPatientBirthDate'] = sham_id[2]

    logging.debug(C.fieldnames)
    C.fieldnames += ["ShamPatientID", "ShamPatientName", "ShamPatientBirthDate"]

    logging.debug(C.fieldnames)
    C.write(fp=fpo)