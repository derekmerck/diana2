from datetime import date

def dicom_name(names: list) -> str:
    s = "^".join(names).upper()
    return s

def dicom_date(dt: date) -> str:
    s = dt.strftime("%Y%m%d")
    return s