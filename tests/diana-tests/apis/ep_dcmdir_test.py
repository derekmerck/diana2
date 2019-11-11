import logging, json
from pprint import pformat
from crud.abc import Serializable
from diana.apis import DcmDir
from diana.dixel import DixelView

from utils import find_resource


def test_exists():

    resources_dir = find_resource("resources/dcm")

    D = DcmDir(path=resources_dir)
    logging.debug(D)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

    D = DcmDir(path=resources_dir,
               subpath_width=3, subpath_depth=2)
    assert( D.check() )
    assert( D.exists("IM2263") )
    assert( not D.exists("abcd") )

    logging.debug("Checking round-trip")

    d = D.get("IM2263")

    logging.debug(pformat(d.tags))

    dd = d.json()
    ee = json.loads(dd)
    e = Serializable.Factory.create(**ee)

    logging.debug(d)
    logging.debug(e)

    assert( d.tags == e.tags )


def test_subdirs():

    D = DcmDir(recurse_style="ORTHANC")

    # for fp in D.recurse():
    #     logging.debug(fp)

    subdirs = list( D.subdirs() )

    assert( len( subdirs )  == 256*256 )
    assert( "./ff/ff" in subdirs )
    assert( "./00/00" in subdirs )

    p = find_resource("resources")
    D = DcmDir(path=p)

    subdirs = list( D.subdirs() )
    logging.debug(subdirs)

    assert( len(subdirs) >= 8 )


def test_zip_reader():

    p = find_resource("resources")
    D = DcmDir(path=p)

    f = D.get("dcm/IM2263", view=DixelView.TAGS_FILE)

    gs = D.get_zipped("dcm_zip/test.zip")

    for _g in gs:
        if "2263" in _g.meta["FileName"]:
            g = _g
            break

    logging.debug(f)
    logging.debug(g)

    assert(f.tags["StudyInstanceUID"] == g.tags["StudyInstanceUID"])

    from binascii import hexlify

    logging.debug("f file:")
    logging.debug( hexlify(f.file[1024:2048]) )
    logging.debug("g file:")
    logging.debug( hexlify(g.file[1024:2048]) )

    assert f.file == g.file


if __name__=="__main__":

    logging. basicConfig(level=logging.DEBUG)
    # test_exists()
    # test_subdirs()
    test_zip_reader()