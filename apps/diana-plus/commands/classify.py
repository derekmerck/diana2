#! python3
"""
halibut.py
Ian Pan, Summer 2018

Wrapper command-line tool for Halibut MobileNetGray classification.

$ python3 classify-it.py -m pose_weights.h5 -d CR00.dcm -p frontal -n lateral

"""

import argparse, os, logging
from packages.halibut import get_mobilenet, get_image_from_dicom, get_prediction


def parse_args():

    parser = argparse.ArgumentParser(prog="Halibut",
                                     description="Binary DICOM image classification with MobileNetGray")
    parser.add_argument("--model", "-m", type=str,
                        help="Path to model weights")
    parser.add_argument("--dicom", "-d", type=str,
                        help="Path DICOM file")
    parser.add_argument("--positive", "-p", help="Positive class", default="positive")
    parser.add_argument("--negative", "-n", help="Negative class", default="negative")
    return parser.parse_args()


if __name__ == "__main__":

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    logging.basicConfig(level=logging.DEBUG)

    opts = parse_args()

    model = get_mobilenet(0, weights=None)
    model.load_weights(opts.model)
    # model = get_mobilenet(0, weights=args.model)
    image = get_image_from_dicom(opts.dicom)

    prediction = get_prediction( model, image )

    if prediction >= 0.5:
        logging.info("Predicted: {} ({})<<".format( opts.positive, round(prediction, 2) ))
    else:
        logging.info("Predicted: {} ({})<<".format( opts.negative, round(1.0-prediction, 2) ))
