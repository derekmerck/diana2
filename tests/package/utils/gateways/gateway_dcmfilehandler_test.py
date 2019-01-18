import logging
from diana.utils.dicom import DicomFormatError
from diana.utils.gateways import DcmFileHandler
import pytest

from test_utils import find_resource


def test_paths():

    D = DcmFileHandler()
    fn = "abcdefghijk.dcm"
    fp = D.get_path(fn)
    logging.debug(fp)
    assert(fp=="./{}".format(fn))

    D = DcmFileHandler(subpath_depth=2)
    fp = D.get_path(fn)
    logging.debug(fp)
    assert(fp=="./ab/cd/{}".format(fn))

    D = DcmFileHandler(subpath_depth=3, subpath_width=1)
    fp = D.get_path(fn)
    logging.debug(fp)
    assert(fp=="./a/b/c/{}".format(fn))

def test_reader():

    dcm_file = find_resource("resources/dcm/IM2263")
    json_file = find_resource("resources/reports/screening_rpt_anon.txt")

    DcmFileHandler().get(dcm_file)

    with pytest.raises(DicomFormatError):
        DcmFileHandler().get(json_file)



if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_paths()
    test_reader()