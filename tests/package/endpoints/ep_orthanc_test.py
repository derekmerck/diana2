import logging
from test_utils import find_resource
from diana.endpoints import Orthanc, DcmDir

def test_orthanc_ep(setup_orthanc):

    logging.debug("Test Orthanc EP")

    O = Orthanc()
    print(O)
    O.check()

def test_orthanc_upload(setup_orthanc):

    O = Orthanc()

    dicom_dir = find_resource("resources/dcm")
    D = DcmDir(path=dicom_dir)
    d = D.get("IM2263", get_file=True)

    O.put(d)

    q = {"PatientID": "AW15119516.678.1392297407"}
    result = O.find(q)

    if result:
        id = result[0]

    logging.debug( id )

    result = O.exists(id)

    assert( result )


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    from conftest import setup_orthanc
    for i in setup_orthanc():
        test_orthanc_ep(None)
        test_orthanc_upload(None)