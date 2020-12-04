from os import listdir
from os.path import join
import sys
import logging
import pydicom
sys.path.insert(0, r"D:\Git\diana2\package")
from diana.apis import DcmDir
from diana.utils.dicom import DicomLevel
from diana.dixel import Dixel
from crud.manager import EndpointManager

services_path = r"@D:\Brown\Research\test_service.yml"
D = DcmDir(path=r"D:\Brown\Research\Raw_Data\image_anonymization\Disc_1\7501")

epman = EndpointManager()
epman.serialized_ep_descs = services_path
epman.ep_descs = epman.set_descs()
# source = get_service(services_path, "legion", True)
source = epman.get("legion")

for i, subd in enumerate(D.subdirs()):
    if i == 0:
        continue

    for f in listdir(subd):
        try:
            fp = join(subd, f)
            ds = pydicom.dcmread(fp, stop_before_pixels=True)
            d = Dixel.from_pydicom(ds, fn=fp, file=open(fp, "rb"))
            result = source.gateway.put(d.file)
        except pydicom.errors.InvalidDicomError as e:
            logging.warning("Failed to parse with {}".format(e))

oid = result["ParentPatient"]
# oid = "c3c8cffc-a88625cd-db6acd2d-0e5d3785-b020c9b0"

# replace = {
#         "PatientName": "",
#         "PatientID": "",
#         "PatientBirthDate": "",
#         "AccessionNumber": "",
#         "StudyInstanceUID": "",
#         "StudyDate": "",
#         "StudyTime": "",
#     }
replace = {}
keep = []
query = {
    "Replace": replace,
    "Keep": keep,
    "Force": True
}
source.gateway.anonymize(oid, level=DicomLevel.PATIENTS, replacement_map=query)
# resource = "studies/{}/modify".format(oid)
# source.gateway._post(resource, json=query)

# DELETE original study here as _post duplicates
source.gateway.delete(oid=oid, level=DicomLevel.PATIENTS)
print("Anonymized: {}".format(oid))
