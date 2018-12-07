import logging
from diana.endpoints import Orthanc

def test_orthanc_ep():

    logging.debug("Test Orthanc EP")

    O = Orthanc()
    print(O)

    O.check()
    q = {"PatientName": "YELLOCK*"}
    result = O.find(q)

    if result:
        id = result[0]

    print( id )

    result = O.get(id)

    print(result)


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_orthanc_ep()