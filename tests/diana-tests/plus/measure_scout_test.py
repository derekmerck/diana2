import logging

from diana.dixel import DixelView
from diana.apis import DcmDir
# import diana.plus.measure_scout  # Monkey patch

from utils import find_resource

import pytest

# TODO: Need to test after pulling directly from orthanc as well as reading from disk

@pytest.mark.skip(reason="Needs scipy")
def test_measurement():

    path = find_resource("resources/scouts")
    D = DcmDir(path=path)

    fn_s1 = "ct_scout_01.dcm"
    d_s1 = D.get(fn_s1, view=DixelView.PIXELS)
    ret = d_s1.measure_scout()
    logging.debug(ret)

    assert( ret[0] == 'AP' and
            round(ret[1]) == 28 )

    fn_s2 = "ct_scout_02.dcm"
    d_s2 = D.get(fn_s2, view=DixelView.PIXELS)
    ret = d_s2.measure_scout()
    logging.debug(ret)

    assert( ret[0] == 'LATERAL' and
            round(ret[1]) == 43 )


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_measurement()
