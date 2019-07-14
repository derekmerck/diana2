import logging
from datetime import datetime
from diana.utils.dicom import dicom_date, dicom_datetime, dicom_time, \
    date_str_to_dicom, parse_dicom_datetime, dicom_name

testv = [
    {"dt": datetime(2000, 1, 1, 1, 1, 1),
     "dcm_tm": "010101",
     "dcm_dt": "20000101",
     "dt_str": "January 1, 2000"},
    {"dt": datetime(1935, 10, 11, 21, 31, 41),
     "dcm_tm": "213141",
     "dcm_dt": "19351011",
     "dt_str": "1935-10-11"},
    {"dt": datetime(2015, 5, 11, 7, 8, 59),
     "dcm_tm": "070859",
     "dcm_dt": "20150511",
     "dt_str": datetime(2015, 5, 11, 7, 8, 59).date().isoformat()},
    {"dt": datetime(2015, 5, 11, 7, 8, 59, 100),
     "dcm_tm": "070859.000100",
     "dcm_dt": "20150511",
     "dt_str": datetime(2015, 5, 11, 7, 8, 59, 100).date().isoformat()
    }
]


def test_dcm_to_dt():

    for _t in testv:

        assert parse_dicom_datetime(_t["dcm_dt"] + _t["dcm_tm"]) == _t["dt"]


def test_dt_parser():

    for _t in testv:

        # logging.debug(date_str_to_dicom(_t["dt_str"]))
        assert date_str_to_dicom(_t["dt_str"]) == _t["dcm_dt"]


def test_dcm_dt_strings():

    for _t in testv:

        assert dicom_time(_t["dt"]) == _t["dcm_tm"].split(".")[0]
        assert dicom_date(_t["dt"]) == _t["dcm_dt"]
        assert dicom_datetime(_t["dt"]) == (_t["dcm_dt"], _t["dcm_tm"].split(".")[0])


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    test_dcm_dt_strings()
    test_dt_parser()
    test_dcm_to_dt()