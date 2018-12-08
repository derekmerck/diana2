from datetime import datetime, date

def dicom_name(names: list) -> str:
    s = "^".join(names).upper()
    return s

def dicom_date(dt: date) -> str:
    s = dt.strftime("%Y%m%d")
    return s

def dicom_datetime(dt: datetime) -> (str, str):
    d = dt.strftime("%Y%m%d")
    t = dt.strftime("%H%M%S")
    return d, t
