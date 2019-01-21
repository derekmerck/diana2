import logging

# currently missing keras-retinanet (and opencv dep) on travis
# import pytest
# predict = pytest.importorskip("diana.plus.halibut.predict")

# from diana.plus.halibut.predict import predict_ba

from test_utils import find_resource

import pytest


@pytest.mark.skip(reason="Needs big files")
def test_ba_estimator():

    # These weights classify as AP (pos) or Lateral (neg)
    model_path = find_resource("resources/models/bone_age")
    image_path = "/Users/derek/Data/DICOM/bone_age"

    predict_ba(dicom_folder=image_path, models_folder=model_path)


if __name__=="__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_ba_estimator()
