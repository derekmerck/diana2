import logging, datetime
from diana.dixel import Dixel, ShamDixel
from diana.utils.dicom import DicomLevel
from pprint import pformat

def test_dt_shams_at_levels():

    tags = {
        "PatientName": "FOOABC^BAR^Z",
        "PatientBirthDate": "20000101",
        "StudyDate": "20180102",
        "StudyTime": "120001",
        "AccessionNumber": "12345678"
    }

    expected_meta = {
         'ShamAccessionNumber': '25d55ad283aa400af464c76d713c07ad',
         'ShamBirthDate': '19991009',
         'ShamID': 'NTE3OTYH32XNES3LPNKR2U6CVOCZXDIL',
         'ShamName': 'NADERMAN^TRACY^E',

         'StudyDateTime': datetime.datetime(2018, 1, 2, 12, 0, 1),
         'ShamStudyDateTime': datetime.datetime(2017, 10, 10, 12, 15, 3)
    }

    d = ShamDixel(tags=tags, level=DicomLevel.STUDIES)
    logging.debug(pformat(d.meta))

    assert( expected_meta.items() <= d.meta.items() )

    # check for imputing missing series dt tags
    d = ShamDixel(tags=tags, level=DicomLevel.SERIES)
    logging.debug(pformat(d.meta))
    assert d.meta["ShamStudyDateTime"] == d.meta["ShamSeriesDateTime"]

    # check for imputing missing instance dt tags
    d = ShamDixel(tags=tags, level=DicomLevel.INSTANCES)
    logging.debug(pformat(d.meta))
    assert d.meta["ShamInstanceCreationDateTime"] == d.meta["ShamSeriesDateTime"] == d.meta["ShamStudyDateTime"]

    tags.update({
        "SeriesDate": "20180102",
        "SeriesTime": "120101"
    })

    expected_meta.update({
         'SeriesDateTime': datetime.datetime(2018, 1, 2, 12, 1, 1),
         'ShamSeriesDateTime': datetime.datetime(2017, 10, 10, 12, 16, 3)
    })

    d = ShamDixel(tags=tags, level=DicomLevel.SERIES)
    logging.debug(pformat(d.meta))

    assert( expected_meta.items() <= d.meta.items() )

    tags.update({
        "InstanceCreationDate": "20180102",
        "InstanceCreationTime": "120101"
    })

    expected_meta.update({
        'InstanceCreationDateTime': datetime.datetime(2018, 1, 2, 12, 1, 1),
        'ShamInstanceCreationDateTime': datetime.datetime(2017, 10, 10, 12, 16, 3)
    })

    d = ShamDixel(tags=tags, level=DicomLevel.INSTANCES)
    logging.debug(pformat(d.meta))

    assert( expected_meta.items() <= d.meta.items() )


def test_study_shams():

    tags = {
        "PatientName": "FOOABC^BAR^Z",
        "PatientBirthDate": "20000101",
        "StudyDate": "20180102",
        "StudyTime": "120001",
        "AccessionNumber": "12345678"
    }

    expected_meta = {
        'ShamID': 'NTE3OTYH32XNES3LPNKR2U6CVOCZXDIL',
        'ShamName': 'NADERMAN^TRACY^E',
        'ShamBirthDate': "19991009",
        'ShamStudyDateTime': datetime.datetime(2017, 10, 10, 12, 15, 3)
    }

    d = ShamDixel(tags=tags)
    logging.debug(d)

    assert( expected_meta.items() <= d.meta.items() )

    assert( d.meta["ShamName"] == "NADERMAN^TRACY^E" )
    assert( d.ShamStudyDate() == "20171010" )
    assert( d.meta["ShamAccessionNumber"] == "25d55ad283aa400af464c76d713c07ad")

    logging.debug( d.orthanc_sham_map() )

    expected_replacement_map = \
        {'Replace': {'PatientName': 'NADERMAN^TRACY^E', 'PatientID': 'NTE3OTYH32XNES3LPNKR2U6CVOCZXDIL',
                     'PatientBirthDate': '19991009', 'AccessionNumber': '25d55ad283aa400af464c76d713c07ad',
                     'StudyInstanceUID': '1.2.826.0.1.3680043.10.43.62.716180617702.336145899646',
                     'StudyDate': '20171010', 'StudyTime': '121503'}, 'Keep': ['PatientSex', 'StudyDescription'],
         'Force': True}

    assert( d.orthanc_sham_map() == expected_replacement_map )

    c = Dixel(tags=tags)
    e = ShamDixel.from_dixel(c)
    assert( d.meta["ShamName"] == e.meta["ShamName"] )

    f = ShamDixel.from_dixel(c, salt="FOO")
    logging.debug(f.meta["ShamName"])
    assert( d.meta["ShamName"] != f.meta["ShamName"] )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_study_shams()
    test_dt_shams_at_levels()
