import logging
from diana.utils.dicom import DicomLevel


def test_dicom_levels():

    logging.debug("Checking dicom level syntax")

    patients_level = DicomLevel.PATIENTS
    studies_level = DicomLevel.STUDIES
    series_level = DicomLevel.SERIES
    instances_level = DicomLevel.INSTANCES

    assert( "{!s}".format(patients_level) == "patients" )
    assert( "{!s}".format(studies_level) == "studies" )
    assert( "{!s}".format(series_level) == "series" )
    assert( "{!s}".format(instances_level) == "instances" )

    assert( patients_level < studies_level < series_level < instances_level )

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_dicom_levels()