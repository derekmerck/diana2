import os, logging

from diana.dixel import DixelView
from diana.apis import DcmDir
from diana.plus.halibut import get_mobilenet

from test_utils import find_resource

import pytest

# On Mac there is a duplicate MP library from compilers
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


@pytest.mark.skip(reason="Need to dl models")
def test_view_classifier():

    # These weights classify as AP (pos) or Lateral (neg)
    fp = find_resource("resources/models/pose/view_classifier.h5")

    _model = get_mobilenet(0, weights=None)
    _model.load_weights(fp)

    fp = find_resource("resources/scouts")
    D = DcmDir(path=fp)

    # This one is lateral
    d = D.get("ct_scout_01.dcm", view=DixelView.PIXELS)
    prediction = d.get_prediction(_model)

    logging.debug("Prediction is {}".format(prediction))
    assert( prediction < 0.5 )

    # prediction = get_prediction( model, image )

    # positive = "AP"
    # negative = "Lateral"
    # if prediction >= 0.5:
    #     logging.debug("Predicted: {} ({})".format( positive, round(prediction, 2) ))
    # else:
    #     logging.debug("Predicted: {} ({})".format( negative, round(1.0-prediction, 2) ))

    # This one is an AP
    d = D.get("ct_scout_02.dcm", view=DixelView.PIXELS)
    prediction = d.get_prediction(_model)

    logging.debug("Prediction is {}".format(prediction))
    assert( prediction >= 0.5 )


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_view_classifier()
