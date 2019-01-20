###########
# IMPORTS #
###########

import sys
sys.path.insert(0, "../models/")
from .models.mobilenet_v2_gray import MobileNetV2
from .models.densenet_gray import DenseNet121
from .preprocessing import *

import keras
from keras_retinanet.models import load_model

from keras.layers import Dropout, Flatten, Dense
from keras.layers import GlobalAveragePooling2D, GlobalMaxPooling2D
from keras.engine import Model
from keras.callbacks import CSVLogger, ModelCheckpoint
from keras import backend as K
from keras import optimizers, layers

# import pandas as pd
import numpy as np
# import scipy.misc
import pydicom
import glob
import os
import re

# from scipy.ndimage.interpolation import zoom, rotate
# from scipy.ndimage.filters import gaussian_filter
#
# from skimage import exposure

################
# KERAS MODELS #
################

def get_model(base_model,
              layer,
              lr=1e-3,
              input_shape=(224,224,1),
              dropout=None,
              pooling="avg",
              weights=None,
              pretrained=None):
    base = base_model(input_shape=input_shape,
                      include_top=False,
                      weights=pretrained,
                      channels="gray")
    if pooling == "avg":
        x = GlobalAveragePooling2D()(base.output)
    elif pooling == "max":
        x = GlobalMaxPooling2D()(base.output)
    elif pooling is None:
        x = Flatten()(base.output)
    if dropout is not None:
        x = Dropout(dropout)(x)
    x = Dense(1, activation="relu")(x)
    model = Model(inputs=base.input, outputs=x)
    if weights is not None:
        model.load_weights(weights)
    for l in model.layers[:layer]:
        l.trainable = False
    model.compile(loss="mean_absolute_error",
                  optimizer=optimizers.Adam(lr))
    return model

##########
## DATA ##
##########

# == PREPROCESSING == #
def preprocess_input(x, model):
    x = x.astype("float32")
    if model in ("inception","xception","mobilenet"):
        x /= 255.
        x -= 0.5
        x *= 2.
    if model in ("densenet"):
        x /= 255.
        if x.shape[-1] == 3:
            x[..., 0] -= 0.485
            x[..., 1] -= 0.456
            x[..., 2] -= 0.406
            x[..., 0] /= 0.229
            x[..., 1] /= 0.224
            x[..., 2] /= 0.225
        elif x.shape[-1] == 1:
            x[..., 0] -= 0.449
            x[..., 0] /= 0.226
    elif model in ("resnet","vgg"):
        if x.shape[-1] == 3:
            x[..., 0] -= 103.939
            x[..., 1] -= 116.779
            x[..., 2] -= 123.680
        elif x.shape[-1] == 1:
            x[..., 0] -= 115.799
    return x

#############
# FUNCTIONS #
#############
def get_array_from_dicom(dicom_file):
    dicom_array = dicom_file.pixel_array
    dicom_array = dicom_array - np.min(dicom_array)
    dicom_array = dicom_array / float(np.max(dicom_array))
    dicom_array *= 255.
    assert np.min(dicom_array) >= 0
    assert np.max(dicom_array) <= 255
    if dicom_file.PhotometricInterpretation == "MONOCHROME1":
        dicom_array = 255. - dicom_array
    return dicom_array

import logging

##########
# SCRIPT #
##########
def predict_ba(dicom_folder, models_folder):

    # Get all DICOM images in folder
    dicom_files = []
    for root, dirs, files in os.walk(dicom_folder):
        for name in files:
            if re.search(".dcm", name):
                dicom_files.append(os.path.join(root,name))

    logging.debug(dicom_files)

    # Load, apply hand cropper, take the one with the highest score
    hand_cropper = load_model( os.path.join(models_folder, "hand_roi.h5"), backbone_name="resnet50")

    hand_scores = []
    hand_arrays = []
    hand_bboxes = []
    for dicom_fi in dicom_files:
        try:
            hand_arr = get_array_from_dicom(pydicom.read_file(dicom_fi))
        except:
            continue
        hand_arrays.append(hand_arr.copy())
        hand_arr = preprocess_input(hand_arr, "resnet")
        hand_arr = resize_single_image(hand_arr, 512)
        hand_arr_rgb = np.empty((hand_arr.shape[0], hand_arr.shape[1], 3))
        for ch in range(3):
            hand_arr_rgb[:,:,ch] = hand_arr
        predictions = hand_cropper.predict_on_batch(np.expand_dims(hand_arr_rgb, axis=0))
        scores = predictions[1][0]
        bboxes = predictions[0][0]
        hand_scores.append(scores[0])
        hand_bboxes.append(bboxes[0])

    best_hand_index = hand_scores.index(np.max(hand_scores))
    best_hand_score = hand_scores[best_hand_index]
    best_hand_array = hand_arrays[best_hand_index]
    best_hand_bbox  = hand_bboxes[best_hand_index]

    if best_hand_score < 0:
        Exception("No hand detected. Please verify that at least one DICOM file contains frontal view of hand.")

    scale = np.max(best_hand_array.shape) / 512.
    best_hand_bbox = [int(_ * scale) for _ in best_hand_bbox]
    hand = best_hand_array[best_hand_bbox[1]:best_hand_bbox[3],best_hand_bbox[0]:best_hand_bbox[2]]

    # Get the sex
    patientSex = pydicom.read_file(dicom_files[best_hand_index]).PatientSex

    model_weights_dir = "../trained_models/"

    list_of_model_weights = glob.glob(os.path.join(model_weights_dir, "*.hdf5"))

    if patientSex == "M":
        model_weights = [_ for _ in list_of_model_weights if re.search("_M_", _)]
    elif patientSex == "F":
        model_weights = [_ for _ in list_of_model_weights if re.search("_F_", _)]

    # Load each model
    model_names = []
    model_percentiles = []
    list_of_models = []
    for model_index, each_model in enumerate(model_weights):
        print ("Loading model {}/{} ...".format(model_index+1, len(model_weights)))
        #K.clear_session()
        if re.search("densenet", each_model):
            list_of_models.append(get_model(DenseNet121, 0, weights=each_model, input_shape=(224,224,1)))
            model_names.append("densenet")
        elif re.search("mobilenet", each_model):
            list_of_models.append(get_model(MobileNetV2, 0, weights=each_model, input_shape=(448,448,1)))
            model_names.append("mobilenet")
        model_percentiles.append(int(each_model.split("_")[-3]))

    big_hand  = resize_single_image(hand, 1120)
    tiny_hand = resize_single_image(hand, 560)

    hand_patches_448 = np.asarray(grid_patches(big_hand, 448))
    hand_patches_224 = np.asarray(grid_patches(tiny_hand, 224))

    hand_predictions = []
    for index, model in enumerate(list_of_models):
        if model_names[index] == "densenet":
            tmp_prediction = np.percentile(model.predict(np.expand_dims(hand_patches_224, axis=-1)), model_percentiles[index])
        elif model_names[index] == "mobilenet":
            tmp_prediction = np.percentile(model.predict(np.expand_dims(hand_patches_448, axis=-1)), model_percentiles[index])
        hand_predictions.append(tmp_prediction)

    final_hand_prediction = np.mean(hand_predictions)
    round_hand_prediction = np.round(final_hand_prediction)

    print(">>RECORDED SEX: {}".format(patientSex))
    print(">>PREDICTED BONE AGE: {} months".format(round(final_hand_prediction, 2)))
    print(">>PREDICTED BONE AGE: {} years {} months".format(int(round_hand_prediction / 12),
                                int(round_hand_prediction % 12)))



