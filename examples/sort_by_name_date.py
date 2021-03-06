"""
Merck, Fall 2019

Given single-foldered studies
- Filter non-primary-head series
- Optionally filter any series with or with-out contrast
- Delete RequestingPhysician tag
- Save remaining series as patient/date/series_desc.zip

dcm.uid.1
- ct.uid.11
- ct.uid.12...
dcm.uid.2
- ct.uid.21
- ct.uid.22...

to

patient_name
- study1_date-study1_desc
  - 1-series1_desc.zip
  - 2-series2_desc.zip
- study1_date-study1_desc
  - 1-series1_desc.zip

Requires an orthanc helper, used for only a single study at a time
"""

import os
import logging
from pprint import pformat
from pathlib import Path
from diana.apis import DcmDir, Orthanc
from diana.dixel import DixelView as DVw
from diana.utils.dicom import DicomLevel as DLv
from diana.utils.gateways.requesters import suppress_urllib_debug
from diana.utils.gateways.requesters import requester
from crud.utils import path_safe

# Filters
# --------------------------------

def contrasted(item):
    logging.debug("Checking for contrast")
    if item.tags.get("ContrastBolusAgent"):
        return True
    return False

def not_contrasted(item):
    return not contrasted(item)


# Script vars
# --------------------------------

UPDATE_ID = True
id_prefix = "IRB201800011"

# unsorted source data
source_dir = "/mnt/imrsch/Exams_Sorted"

# sorted and filtered data
# target_dir = "/Users/derek/Dropbox (UFL)/UFH ICH Heads"
target_dir = "/home/derek/Dropbox/UFH Perfusion Heads"

handled_file = "handled.txt"
errors_file  = "errors.txt"

series_query = {"BodyPartExamined": "Head",
                "ImageType": "ORIGINAL?PRIMARY?AXIAL"}

# filters = [not_contrasted]
filters = []

# Requesting physician was overlooked in initial anonymization
replacement_map = { "Remove": ["RequestingPhysician"] }

# Windows does not like request session objects
requester.USE_SESSIONS = False

clear = True
pull = True


# --------------------------------

def ul_study(source: DcmDir, dest: Orthanc):
    """Grab a single study and upload it"""

    files = []
    for root, dirs, _files in os.walk(source.path):

        for file in _files:
            fn = os.path.join(root, file)
            files.append(fn)

    logging.info(f"Found {len(files)} files in {source.path}")

    for f in files:
        _item = source.get(f, file=True)
        if _item:
            dest.put(_item)


# For comparing convolution kernel sizes
# def get_int(s: str):
#     digits = filter(str.isdigit, s)
#     as_str = ''.join(digits)
#     num = int(as_str)
#     return num
#

def dl_series(source: Orthanc, pull=True):

    # Have to create new pt before collecting series or the oid will change
    if UPDATE_ID and id_prefix:
        patient_id = source.patients()[0]
        patient = source.get(patient_id, level=DLv.PATIENTS, view=DVw.TAGS)

        id_suffix = patient.tags["PatientID"].split("-")[1]
        new_id = f"{id_prefix}-{id_suffix}"
        logging.info(f"Replacing name and id: {new_id}")
        _replacement_map = {
            "Replace": {"PatientName": new_id,
                        "PatientID":   new_id},
            "Force": True
        }
        source.modify(patient, replacement_map=_replacement_map)
        source.delete(patient)

    qitems = source.find(series_query, level=DLv.SERIES)

    if not qitems:
        logging.warning("No candidate series available")
        return

    logging.debug(f"Found {len(qitems)} candidate series")

    items = []
    for qitem in qitems:
        item = source.get(qitem, view=DVw.TAGS)

        logging.debug(f"Testing: {item.tags.get('SeriesDescription')}")

        include_item = True
        for filt in filters:
            if not filt(item):
                logging.debug(f"Discarding {item.tags['SeriesDescription']}")
                include_item = False
                break

        if include_item:
                logging.debug(f"Including {item.tags['SeriesDescription']}")
                items.append(item)

    if not items:
        logging.warning("No valid series identified")

    logging.info(f"Found {len(items)} valid series:")
    for item in items:
        logging.info(f"  {item.tags['SeriesDescription']} w kernel: {item.tags['ConvolutionKernel']}")

    if pull:
        rv = []
        for item in items:
            if replacement_map:
                logging.info("Running replacement map")
                item_id = source.modify(item, replacement_map=replacement_map)
                item = source.get(item_id, view=DVw.TAGS)
            item = source.get(item, view=DVw.FILE)
            rv.append(item)

        return rv

    else:
        return items


def write_item(item, fpo):

    if not item.file:
        raise ValueError("No file to write")

    pn = path_safe( item.tags["PatientName"] )
    study_dt = path_safe( item.tags["StudyDate"] )
    study_desc = path_safe( item.tags["StudyDescription"])
    study_dir_o = f"{study_dt}-{study_desc}"
    fp = os.path.join(fpo, pn, study_dir_o)

    Path(fp).mkdir(parents=True, exist_ok=True)

    ser_num = item.tags["SeriesNumber"]
    ser_desc = path_safe( item.tags["SeriesDescription"] )
    ser_file = f"{ser_num}-{ser_desc}.zip"
    fp = os.path.join(fpo, pn, study_dir_o, ser_file)

    with open(fp, "wb") as f:
        f.write(item.file)


def handle_study(fpi, fpo, clear=True, pull=True):

    O = Orthanc()

    if clear:
        O.clear()
        D = DcmDir(path=fpi)
        ul_study(D, O)

    items = dl_series(O, pull)

    if not items:
        logging.error(f"Could not find any appropriate series for {fpi}")
        with open(errors_file, "a") as f:
            f.write(f"{fpi}\n")
        return

    if pull:
        for item in items:
            write_item(item, fpo)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    suppress_urllib_debug()
    DcmDir.suppress_debug_logging()

    if os.path.isfile(handled_file):
        with open(handled_file) as f:
            sorted_studies = f.read()
            sorted_studies = sorted_studies.split("\n")
            logging.info("Found already handled studies:")
            logging.info(pformat(sorted_studies))
    else:
        sorted_studies = []

    # Should use a glob here
    study_dirs = os.listdir(source_dir)

    # study_dirs = [
    #     # "IRB201901039-120",
    #     "IRB201901039-121",
    # ]

    for study_dir in study_dirs:
        if study_dir in sorted_studies:
            # Already handled this one
            continue
        fpi = os.path.join(source_dir, study_dir)
        handle_study(fpi, target_dir, clear=clear, pull=pull)

        with open(handled_file, "a") as f:
            f.write(f"{study_dir}\n")
