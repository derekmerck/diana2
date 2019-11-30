"""
Merck, Fall 2019

Given single-foldered studies
- Filter non-primary-head series
- Filter any series with contrast
- Delete RequestingPhysician tag
- Save remaining series (nc primary head) as patient/date/series_desc.zip

dcm.uid.1
- ct.uid.11
- ct.uid.12...
dcm.uid.2
- ct.uid.21
- ct.uid.22...

to

patient_name
- study1-date
  - series1_desc.zip
  - series2_desc.zip
- study1-date
  - series1_desc.zip

Requires an orthanc helper, used for only a single study at a time
"""

import os
import logging
from pathlib import Path
from diana.apis import DcmDir, Orthanc
from diana.dixel import DixelView as DVw
from diana.utils.dicom import DicomLevel as DLv
from diana.utils.gateways.requesters import suppress_urllib_debug
from diana.utils.gateways.requesters import requester
from crud.utils import path_safe

# Script vars
# --------------------------------

# output filepath
fpo = "/tmp"

# unsorted source data
src_dir = "/Users/derek/Dropbox (UFL)/UFH ICH Heads"

handled_file = "handled.txt"
errors_file  = "errors.txt"

replacement_map = {"Remove": ["RequestingPhysician"]}

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
            # logging.debug(f"Found {fn}")
            files.append(fn)

    logging.info(f"Found {len(files)} files")

    for f in files:
        _item = source.get(f, file=True)
        if _item:
            dest.put(_item)


def get_int(s: str):
    digits = filter(str.isdigit, s)
    as_str = ''.join(digits)
    num = int(as_str)
    return num


def dl_series(source: Orthanc, pull=True):

    query = {"BodyPartExamined": "Head",
            "ImageType": "ORIGINAL?PRIMARY?AXIAL"}

    qitems = source.find(query, level=DLv.SERIES)

    if not qitems:
        logging.warning("No candidate series available")
        return

    logging.debug(f"Found {len(qitems)} candidate series")

    items = []
    for qitem in qitems:
        item = source.get(qitem, view=DVw.TAGS)

        logging.debug(f"Testing: {item.tags.get('SeriesDescription')}")

        if item.tags.get("ContrastBolusAgent"):
            logging.debug(f"Discarding {item.tags['SeriesDescription']}")
            continue

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
    dt = path_safe( item.tags["StudyDate"] )
    fp = os.path.join(fpo, pn, dt)

    Path(fp).mkdir(parents=True, exist_ok=True)

    sn = path_safe( item.tags["SeriesDescription"] )
    fp = os.path.join(fpo, pn, dt, f"{sn}.zip")

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

    logging.basicConfig(level=logging.INFO)

    suppress_urllib_debug()
    DcmDir.suppress_debug_logging()

    if os.path.isfile(handled_file):
        with open(handled_file) as f:
            sorted_studies = f.readlines()
    else:
        sorted_studies = []

    study_dirs = os.listdir(src_dir)

    # # study_dirs = ["1.3.6.1.4.1.29565.1.4.67799414.108615.1538292283.543265",
    #              # "1.3.6.1.4.1.29565.1.4.67799414.2635.1530202664.221926",
    # study_dirs = ["1.3.6.1.4.1.29565.1.4.67799414.14323.1561904796.589380"]

    for study_dir in study_dirs:
        if study_dir in sorted_studies:
            # Already handled this one
            continue
        fpi = os.path.join(src_dir, study_dir)
        handle_study(fpi, fpo, clear=clear, pull=pull)

        with open(handled_file, "a") as f:
            f.write(f"{study_dir}\n")
