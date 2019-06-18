import os, yaml
from diana.apis import DcmDir, Orthanc

D = DcmDir(path="/data")

svcs_t = os.environ.get("DIANA_SERVICES")
svcs = yaml.load(svcs_t)

print(svcs)

args = svcs.get("renalstone")
O = Orthanc(**args)

for d in D.files(rex="*.zip"):

    file_set = D.get_zipped(d)

    for f in file_set:

        O.put(f)
