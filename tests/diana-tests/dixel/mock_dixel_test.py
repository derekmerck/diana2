import logging, random
from datetime import datetime
from io import BytesIO
import pydicom
from diana.dixel import MockStudy
from diana.dixel.mock_dixel import reset_mock_seed
from utils import find_resource


ref_inst_tags = {'AccessionNumber': 'cafb4188068b4af927b01699410de442', 'PatientName': 'RUSTON^SHERWOOD^L', 'PatientID': 'RSLWBBZPD5RZPRA7WNEIZCKWFD2MG5IY', 'PatientSex': 'M', 'PatientBirthDate': '20000207', 'StudyInstanceUID': '1.2.826.0.1.3680043.10.43.55.908786948015.186631867210', 'StudyDescription': 'IMG839 CT CHEST WIVC', 'StationName': 'Scanner', 'Manufacturer': 'Device Manufacturer', 'ManufacturerModelName': 'Device Model Name', 'Institution': 'Mock Site', 'Modality': 'CT', 'StudyDate': '20180101', 'StudyTime': '000000', 'SeriesDescription': 'Dose Report', 'SeriesNumber': 6, 'SeriesInstanceUID': '1.2.826.0.1.3680043.10.43.55.908786948015.186631867210.5128', 'SeriesDate': '20180101', 'SeriesTime': '001318', 'InstanceNumber': 1, 'SOPInstanceUID': '1.2.826.0.1.3680043.10.43.55.908786948015.186631867210.5128.9883', 'InstanceCreationDate': '20180101', 'InstanceCreationTime': '001319'}
ref_n_instances = 283
ref_dt = datetime(year=2018, month=1, day=1)


def test_mock_dixel():

    reset_mock_seed()
    d = MockStudy(study_datetime=ref_dt)
    inst = list(d.instances())[-1]

    # Check reproducibility
    reset_mock_seed()
    e = MockStudy(study_datetime=ref_dt)
    assert( inst.tags == list(e.instances())[-1].tags )

    # Check correctness
    logging.debug(inst.tags)
    assert( inst.tags == ref_inst_tags )

    logging.debug( len( list(d.instances()) ) )
    assert(len( list(d.instances()) ) == ref_n_instances )

    for item in d.instances():
        logging.debug("{!s}".format(item))

    # Check file creation
    inst.gen_file()
    inst_dcm = find_resource("resources/mock/inst.dcm")

    # Reset mock/inst.dcm with fresh data
    with open(inst_dcm, "wb") as f:
        f.write(inst.file)

    with open(inst_dcm, "rb") as f:
        data = f.read()
    assert( inst.file == data )

    # Test file legibility
    ds = pydicom.dcmread(BytesIO(inst.file))
    logging.debug(ds)
    assert( ds.AccessionNumber == d.tags["AccessionNumber"] )

    # Test new item is unique
    f = MockStudy(study_datetime=ref_dt)
    for item in f.instances():
        logging.debug("{!s}".format(item))

    assert( d.tags["AccessionNumber"] != f.tags["AccessionNumber"] )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_mock_dixel()