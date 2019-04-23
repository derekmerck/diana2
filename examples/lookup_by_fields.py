"""
Discovery accession nums for paired MR and USbx images

Merck, Spring 2019

input:

project.data.csv

input format:

MR    Date of MRI     Date of Biopsy
----  ------------    ---------------
abc   1/2/34          1/2/34

outputs:

project-us.studies.txt
project-mr.studies.txt

Suitable for use as input to diana-collector

One point of weakness is that some studies violate the
unique accession number for each study UID constraint,
but this is untracked.

"""

import os, logging
from pprint import pformat
from diana.apis import *
from diana.utils.dicom import DicomLevel, dicom_date, date_str_to_dicom
from diana.utils.endpoint import get_endpoint

# Set script vars

services_path = ".secrets/lifespan_services.yml"
pacs_key = "pacs"
csv_file = "/Users/derek/Desktop/grand.mr_fat.data.csv"

# Processing

logging.basicConfig(level=logging.DEBUG)

pacs = get_endpoint(services_path, pacs_key, check=True)

data = CsvFile()
data.read(csv_file)

us_results = []
mr_results = []

for item in data.dixels:
    patient_id = item.tags.get("MR")

    mr_study_date = item.tags.get("Date of MRI")
    us_study_date = item.tags.get("Date of Biopsy")

    q = {
        "AccessionNumber": "",
        "PatientID": patient_id,
        "StudyDate": date_str_to_dicom(us_study_date),
        "ModalitiesInStudy": "US"
    }

    result = pacs.find(q, level=DicomLevel.STUDIES)

    # pprint(result)

    if len(result) > 1:
        logging.warning(pformat(result))

    if result:
        # Possible point of error - only takes _first_ candidate
        us_results.append(result[0].get("AccessionNumber"))

    q = {
        "AccessionNumber": "",
        "PatientID": patient_id,
        "StudyDate": date_str_to_dicom(mr_study_date),
        "ModalitiesInStudy": "MR"
    }

    result = pacs.find(q, level=DicomLevel.STUDIES)

    if len(result) > 1:
        logging.warning(pformat(result))

    if result:
        # Possible point of error - only takes _first_ candidate
        mr_results.append(result[0].get("AccessionNumber"))


data_dir = os.path.dirname(csv_file)
base_name = os.path.basename(csv_file)
project = os.path.splitext(base_name)[0][:-5]

logging.debug(project)

fn_mr = os.path.join(data_dir, "{}-mr.studies.txt".format(project))
fn_us = os.path.join(data_dir, "{}-us.studies.txt".format(project))

logging.debug(fn_mr)
logging.debug(fn_us)

with open(fn_mr, "w") as f:
    f.writelines("\n".join(mr_results))

with open(fn_us, "w") as f:
    f.writelines("\n".join(us_results))
