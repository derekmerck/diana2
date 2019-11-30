"""
Merck, Fall 2019

Sort single-foldered studies into patient/date/series folders
and filter by desired series description

dcm.uid.1
- ct.uid.11
- ct.uid.12...
dcm.uid.2
- ct.uid.21
- ct.uid.22...

to

patient_name
- study1-date
  - series1_protocol_name.zip
  - series2_protocol_name.zip
- study1-date
  - series1_protocol_name.zip

Requires an orthanc helper, used for only a single study at a time

Rough diana-cli equivalent for a single study:

$ diana-cli dgetall -b path:/input_dir/study \
            oput orthanc: \
            ofind -q "SeriesDescription: *W/O*" --level=series orthanc: \
            oget -b orthanc "" \
            put path:/output_dir
"""

import os
import logging
from pathlib import Path
from diana.apis import DcmDir, Orthanc
from diana.dixel import DixelView as DVw
from diana.utils.dicom import DicomLevel as DLv
from diana.utils.gateways.requesters import suppress_urllib_debug, USE_SESSIONS
from crud.utils import path_safe

# Script vars
# ----------------

# output filepath
fpo = "/tmp"

# unsorted source data
src_dir = "/Users/derek/Dropbox (UFL)/UFH ICH Heads"

handled_file = "handled.txt"
errors_file  = "errors.txt"

# queries =[ {"SeriesDescription": "*W/O*",
#             "BodyPartExamined": "Head"},
#            {"SeriesDescription": "*NON?CON*",
#             "BodyPartExamined": "Head"},
#            {"SeriesDescription": "*BRAIN*STEALTH*",
#             "BodyPartExamined": "Head"}
#          ]

# Include any heads, throw out any heads with contrast
includes = [{"BodyPartExamined": "Head",
             "ImageType": "ORIGINAL?PRIMARY?AXIAL"}]
filters = [{"ContrastBolusAgent": "CE"}]

anon_map = {"Remove": "RequestingPhysician"}


def ul_study(source: DcmDir, dest: Orthanc):
    """Grab a single study ad upload it"""

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


def dl_series(source: Orthanc):

    qitems = []

    for query in includes:
        _qitems = source.find(query, level=DLv.SERIES)

        if _qitems:
            qitems.extend( _qitems )

    logging.info(f"Found series: {qitems}")

    tagged_items = []
    for qitem in qitems:
        item = source.get(qitem, view=DVw.TAGS)

        for filt in filters:
            for k,v in filt.items():
                if item.tags.get(k) == v:
                    logging.debug(f"Discarding {item.tags['SeriesDescription']}")
                else:
                    tagged_items.append(item)
                    logging.debug(f"Including {item.tags['SeriesDescription']}")

    if not qitems:
        logging.warning("No valid series identified")

    logging.info(f"Found series: {qitems}")

    rv = []
    for item in tagged_items:
        item = source.get(item, view=DVw.FILE)
        rv.append(item)

    return rv


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


def handle_study(fpi, fpo):

    O = Orthanc()

    O.clear()
    D = DcmDir(path=fpi)
    ul_study(D, O)

    items = dl_series(O)

    if not items:
        logging.error(f"Could not find any appropriate series for {fpi}")
        with open(errors_file, "a") as f:
            f.write(f"{fpi}\n")
        return

    for item in items:
        write_item(item, fpo)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # Windows does not like request session objects
    USE_SESSIONS = False
    suppress_urllib_debug()

    if os.path.isfile(handled_file):
        with open(handled_file) as f:
            sorted_studies = f.readlines()
    else:
        sorted_studies = []

    study_dirs = os.listdir(src_dir)

    study_dirs = ["1.3.6.1.4.1.29565.1.4.67799414.108615.1538292283.543265"]

    for study_dir in study_dirs:
        if study_dir in sorted_studies:
            # Already handled this one
            continue
        fpi = os.path.join(src_dir, study_dir)
        handle_study(fpi, fpo)

        with open(handled_file, "a") as f:
            f.write(f"{study_dir}\n")
