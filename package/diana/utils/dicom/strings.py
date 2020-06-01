import logging
from datetime import datetime
from dateutil import parser as DatetimeParser


def dicom_name(names: list) -> str:
    s = "^".join(names).upper()
    return s


def dicom_date(dt: datetime) -> str:
    s = dt.strftime("%Y%m%d")
    return s


def dicom_time(dt: datetime) -> str:
    s = dt.strftime("%H%M%S")
    return s


def dicom_datetime(dt: datetime) -> (str, str):
    d = dicom_date(dt)
    t = dicom_time(dt)
    return d, t


def parse_dicom_datetime(dts: str, tms: str = None) -> datetime:

    if tms:
        dts = dts + tms

    # GE Scanner dt format
    try:
        ts = datetime.strptime( dts, "%Y%m%d%H%M%S")
        return ts
    except ValueError:
        # Wrong format
        pass

    # Siemens scanners use fractional seconds
    try:
        ts = datetime.strptime( dts, "%Y%m%d%H%M%S.%f")
        return ts
    except ValueError:
        # Wrong format
        pass

    # Unknown format, fall back on guessing
    try:
        # Parser does _not_ like fractional seconds
        dts = dts.split(".")[0]
        ts = DatetimeParser.parse(dts)
        return ts
    except (ValueError, OverflowError) as e:
        # Wrong format
        print(e)
        pass

    logger = logging.getLogger("DcmStrings")
    logger.error("Failed to parse date time string: {0}".format( dts ))


def date_str_to_dicom(dstr):
    dt = DatetimeParser.parse(dstr)
    dcm_dt = dicom_date(dt)
    return dcm_dt
