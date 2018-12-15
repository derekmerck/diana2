import logging
from datetime import datetime

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
    d = dt.strftime("%Y%m%d")
    t = dt.strftime("%H%M%S")
    return d, t

def parse_dicom_datetime(dts: str, tms: str=None) -> datetime:

    if tms:
        dts = dts + tms

    try:
        # GE Scanner dt format
        ts = datetime.strptime( dts, "%Y%m%d%H%M%S")
        return ts
    except ValueError:
        # Wrong format
        pass

    try:
        # Siemens scanners use a slightly different aggregated format with fractional seconds
        ts = datetime.strptime( dts, "%Y%m%d%H%M%S.%f")
        return ts
    except ValueError:
        # Wrong format
        pass

    logger = logging.getLogger("DcmStrings")
    logger.error("Failed to parse date time string: {0}".format( dts ))