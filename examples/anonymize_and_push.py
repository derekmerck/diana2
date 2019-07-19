import logging
from diana.dixel import ShamDixel
from diana.apis import get_service

services_path = "my_services.yml"
oid = "802d6dcb-baf06419-375e594c-yyyyyyyy-xxxxxxxx"

logging.basicConfig(level=logging.DEBUG)

source = get_service(services_path, "internal", True)
dest = get_service(services_path, "external", True)

# q = {
#     "PatientName": patient_name
# }
#
# result = source.find(q)
# for oid in result:

d = source.get(oid)
dd = ShamDixel.from_dixel(d)
map = ShamDixel.orthanc_sham_map(dd)
e = source.anonymize(d, replacement_map=map)

source.psend(e, dest)
source.delete(e)
