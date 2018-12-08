import logging, datetime
from diana.dixel import Dixel, ShamDixel

def test_shams():

    tags = {
        "PatientName": "FOOABC^BAR^Z",
        "PatientBirthDate": "20000101",
        "StudyDate": "20180102",
        "StudyTime": "120001",
        "AccessionNumber": "12345678"
    }

    expected = {
        'ID': 'NTE3OTYH32XNES3LPNKR2U6CVOCZXDIL',
        'Name': ['NADERMAN', 'TRACY', 'E'],
        'BirthDate': datetime.date(1999, 10, 9),
        'TimeOffset': datetime.timedelta(-84, 902)
    }


    d = ShamDixel(tags=tags)
    logging.debug(d)

    assert( d.sham_info == expected )

    assert( d.meta["ShamName"] == "NADERMAN^TRACY^E" )
    assert( d.ShamStudyDate == "20171010" )
    assert( d.meta["ShamAccessionNumber"] == "25d55ad283aa400af464c76d713c07ad")

    c = Dixel(tags=tags)
    e = ShamDixel.from_dixel(c)
    assert( d.meta["ShamName"] == e.meta["ShamName"] )

    f = ShamDixel.from_dixel(c, salt="FOO")
    logging.debug(f.meta["ShamName"])
    assert( d.meta["ShamName"] != f.meta["ShamName"] )



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_shams()