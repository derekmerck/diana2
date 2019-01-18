import logging

from diana.dixel import DixelView
from diana.apis import DcmDir
import plus.measure_scout

from test_utils import find_resource

# TODO: Need to test after pulling directly from orthanc rather than reading from disk


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
