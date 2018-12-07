import logging
from diana.endpoints.dcmdir import DcmFileHandler


def test_paths():

    D = DcmFileHandler()
    fn = "abcdefghijk.dcm"
    fp = D.make_path(fn)
    logging.debug(fp)
    assert(fp=="./{}".format(fn))

    D = DcmFileHandler(subpath_depth=2)
    fp = D.make_path(fn)
    logging.debug(fp)
    assert(fp=="./ab/cd/{}".format(fn))

    D = DcmFileHandler(subpath_depth=3, subpath_width=1)
    fp = D.make_path(fn)
    logging.debug(fp)
    assert(fp=="./a/b/c/{}".format(fn))


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_paths()