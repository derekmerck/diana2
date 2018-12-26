import logging, random
from datetime import datetime
from io import BytesIO
import pydicom
from diana.dixel import MockStudy
from test_utils import find_resource


def test_mock_dixel():

    random.seed("diana-mock")
    ref_dt = datetime(year=2018, month=1, day=1)
    d = MockStudy(study_datetime=ref_dt)

    ref_inst_tags = {'AccessionNumber': '72fa1bdc4cecf4aca0540fbbb2398e80', 'PatientName': 'IRETON^OTHA^L', 'PatientID': 'IOLRVX62SA4IENBRAHKQTDXPM7AKFYC7', 'PatientSex': 'F', 'PatientBirthDate': '20000109', 'StudyInstanceUID': '1.2.826.0.1.3680043.10.43.55.347931617183.363541089775', 'StudyDescription': 'IMG1011 CT EXTREMITY NC', 'StationName': 'Scanner', 'Manufacturer': 'Device Manufacturer', 'ManufacturerModelName': 'Device Model Name', 'Institution': 'Mock Site', 'Modality': 'CT', 'StudyDate': '20180101', 'StudyTime': '000000', 'SeriesDescription': 'Dose Report', 'SeriesNumber': 6, 'SeriesInstanceUID': '1.2.826.0.1.3680043.10.43.55.347931617183.363541089775.5128', 'SeriesDate': '20180101', 'SeriesTime': '001259', 'InstanceNumber': 1, 'SOPInstanceUID': '1.2.826.0.1.3680043.10.43.55.347931617183.363541089775.5128.9883', 'InstanceCreationDate': '20180101', 'InstanceCreationTime': '001301'}

    ref_n_instances = 251

    for item in d.instances():
        logging.debug("{!s}".format(item))

    logging.debug( len( list(d.instances()) ) )

    assert(len( list(d.instances()) ) == ref_n_instances )

    inst = d.children[-1].children[-1]

    logging.debug( inst.tags )

    assert( inst.tags == ref_inst_tags )

    inst.gen_file()

    inst_dcm = find_resource("resources/mock/inst.dcm")

    # Reset mock/inst.dcm with fresh data
    # with open(inst_dcm, "wb") as f:
    #     f.write(inst.file)

    with open(inst_dcm, "rb") as f:
        data = f.read()

    assert( inst.file == data )

    ds = pydicom.dcmread(BytesIO(inst.file))

    logging.debug(ds)

    assert( ds.AccessionNumber == ref_inst_tags["AccessionNumber"] )


    e = MockStudy(study_datetime=ref_dt, modality="US")
    for item in e.instances():
        logging.debug("{!s}".format(item))


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_mock_dixel()