import logging
from test_utils import find_resource
from diana.apis import Orthanc, DcmDir
from diana.dixel import DixelView, ShamDixel
from diana.utils.dicom import DicomLevel

def test_orthanc_ep(setup_orthanc):

    logging.debug("Test Orthanc EP")

    O = Orthanc()
    print(O)
    O.check()

def test_orthanc_upload(setup_orthanc):

    O = Orthanc()

    dicom_dir = find_resource("resources/dcm")
    D = DcmDir(path=dicom_dir)
    d = D.get("IM2263", view=DixelView.FILE)

    O.put(d)

    q = {"PatientID": "AW15119516.678.1392297407"}
    result = O.find(q)

    if result:
        id = result[0]

    logging.debug( id )

    result = O.exists(id)
    assert( result )

    O.delete(d)

    result = O.exists(id)
    assert( not result )

def test_anon(setup_orthanc):
    O = Orthanc()
    dicom_dir = find_resource("resources/dcm")
    D = DcmDir(path=dicom_dir)
    d = D.get("IM2263", view=DixelView.FILE)
    O.put(d)

    d.tags["AccessionNumber"] = "123456"
    d.tags["PatientBirthDate"] = "20000101"
    d.tags["PatientID"] = "ABC"
    d.tags["PatientName"] ="XYZ"
    d.level=DicomLevel.STUDIES
    e = ShamDixel.from_dixel(d)
    rep = e.orthanc_sham_map()

    O.anonymize("959e4e9f-e954be4e-11917c87-09d0f98f-7cc39128",
                level=DicomLevel.STUDIES,
                replacement_map=rep)

def test_psend(setup_orthanc, setup_orthanc2):

    O = Orthanc()
    print(O)
    O.check()

    O2 = Orthanc(port=8043, name="Orthanc2")
    print(O2)
    O2.check()

    dicom_dir = find_resource("resources/dcm")
    D = DcmDir(path=dicom_dir)

    d = D.get("IM2263", view=DixelView.FILE)
    O2.put(d)
    O2.psend(d.oid(), O)

    e = O.get(d.oid(), level=DicomLevel.INSTANCES)

    logging.debug(e)

    assert d.oid() == e.oid()


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    from conftest import setup_orthanc, setup_orthanc2
    for (i,j) in zip(setup_orthanc(), setup_orthanc2()):
        # test_orthanc_ep(None)
        # test_orthanc_upload(None)
        # test_psend(None, None)
        test_anon(None)
        i.stop_container()
        j.stop_container()