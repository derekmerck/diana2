import logging, os
from pathlib import Path
from diana.dixel import DixelView
from diana.apis import DcmDir, ImageDir

from test_utils import find_resource


def test_conversion(tmp_path):

    resources_dir = find_resource("resources/dcm")

    D = DcmDir(path=resources_dir)
    logging.debug(D)

    d = D.get("IM2263", view=DixelView.PIXELS)

    E = ImageDir(path=tmp_path)
    E.put(d)

    fn = "1.2.840.113619.2.181.90581140298.2577.1392297407726.4-0004-0002.png"
    fp = Path( tmp_path / fn )
    assert( fp.is_file() )
    os.remove(fp)

    F = ImageDir(path=tmp_path, anonymizing=True)
    F.put(d)

    fn = "6ee6f414e4c779c8bb1f90baf45c000c-0004-0002.png"
    fp = Path( tmp_path / fn )
    assert( fp.is_file() )
    os.remove(fp)


def test_unzip(tmp_path):

    resources_dir = find_resource("resources/dcm_zip")
    fp = resources_dir / "test.zip"

    E = ImageDir(path=tmp_path, anonymizing=True)

    with open(fp, 'rb') as f:
        E.put_zipped(f)

    fn = "6ee6f414e4c779c8bb1f90baf45c000c-0004-0002.png"
    fp = Path( tmp_path / fn )
    assert( fp.is_file() )
    os.remove(fp)

    fn = "78496388f522585b71b90f374051f552-0016-0001.png"
    fp = Path( tmp_path / fn )
    assert( fp.is_file() )
    os.remove(fp)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    tmp_path = Path("/Users/derek/tmp")

    test_conversion(tmp_path)
    test_unzip(tmp_path)
