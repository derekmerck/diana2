# Script to anonymize and re-save a directory of DICOM data

import logging
import os
from diana.apis import Orthanc, DcmDir, ImageDir
from diana.dixel import DixelView as DVW, ShamDixel

OUTPUT_FOLDER = "/Users/me/output"
INPUT_FOLDER = "/Users/me/incoming"

# logging.basicConfig(level=logging.DEBUG)

# Handle for a default Orthanc helper, e.g.,
# $ docker run -p 8042:8042 derekmerck/orthanc
O = Orthanc()
O.clear()
E = DcmDir(path=OUTPUT_FOLDER)

# Recursively upload all available files, regardless of folder structure
for path, root, files in os.walk(INPUT_FOLDER):
    D = DcmDir(path=path)
    for f in D.files():
        d = D.get(f, file=True)
        O.put(d)

# Anonymize and download every available study
for study in O.studies():

    e = O.get(study)
    # Create whatever sort of sham map you like here
    e_sham = ShamDixel().from_dixel(e).orthanc_sham_map()
    anon_id = O.anonymize(e, replacement_map=e_sham)
    O.delete(e)
    f = O.get(anon_id, view = DVW.TAGS)  # TODO: Bug, should be able to get tags & file in one call
    f = O.get(f, view = DVW.FILE)
    # Use whatever output filename you like here
    f.meta["FileName"] = "{}.zip".format(f.tags["AccessionNumber"][0:7])
    E.put(f)
