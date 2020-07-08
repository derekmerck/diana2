import logging
import hashlib
from pprint import pprint
from diana.utils.dicom import DicomHashUIDMint
from diana.dixel import huid_sham_map

from utils import find_resource
from diana.apis import DcmDir


def test_dicom_huid():

    logging.debug("Checking dicom huid mint")

    h = hashlib.sha224(b"test_str").hexdigest()
    u = DicomHashUIDMint().content_hash_uid(hex_hash=h)
    hh = DicomHashUIDMint().hashes_from_uid(u)

    assert(h == hh[0])


def test_huid_sham_map():

    resources_dir = find_resource("resources/dcm")

    D = DcmDir(path=resources_dir)
    d = D.get("IM2263")

    m = huid_sham_map(d)

    pprint(m)

    assert(m["Replace"]["AccessionNumber"] == "0fd7bb93e958add7")
    assert(m["Replace"]["SOPInstanceUID"] == "1.2.826.0.1.3680043.10.43.62.4.3.2992367831700837762904696709542635840549944649331682818720273067376")
    assert(m["Replace"]["StudyTime"] == "094850")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_huid_sham_map()
