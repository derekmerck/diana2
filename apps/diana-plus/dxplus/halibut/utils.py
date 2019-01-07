import numpy as np
from scipy.ndimage.interpolation import zoom
from scipy.ndimage.filters import gaussian_filter

from diana.dixel import Dixel

def resize_image(img, size, smooth=None, verbose=True):
    """
    Resizes image to new_length x new_length and pads with black.
    Only works with grayscale right now.

    Arguments:
    - smooth (float/None) : sigma value for Gaussian smoothing
    """
    resize_factor = float(size) / np.max(img.shape)
    if resize_factor > 1:
        # Cubic spline interpolation
        resized_img = zoom(img, resize_factor)
    else:
        # Linear interpolation
        resized_img = zoom(img, resize_factor, order=1, prefilter=False)
    if smooth is not None:
        resized_img = gaussian_filter(resized_img, sigma=smooth)
    l = resized_img.shape[0] ; w = resized_img.shape[1]
    if l != w:
        ldiff = (size-l) // 2
        wdiff = (size-w) // 2
        pad_list = [(ldiff, size-l-ldiff), (wdiff, size-w-wdiff)]
        resized_img = np.pad(resized_img, pad_list, "constant",
                             constant_values=0)
    assert size == resized_img.shape[0] == resized_img.shape[1]
    return resized_img.astype("uint8")

def get_pixels(dixel: Dixel, imsize=224):

    pixels = dixel.get_pixels()

    if dixel.meta.get("PhotometricInterpretation") == "MONOCHROME1":
        pixels = np.invert(pixels.astype("uint16"))

    pixels = pixels.astype("float32")
    pixels -= np.min(pixels)
    pixels /= np.max(pixels)
    pixels *= 255.
    pixels = resize_image(pixels, imsize, verbose=False)
    return pixels


from .MobileNetGray import MobileNet
# from keras.applications import MobileNet
from keras.layers import Dense, Dropout, GlobalMaxPooling2D, GlobalAveragePooling2D, Flatten
from keras.engine import Model
from keras import optimizers

def get_mobilenet(layer, lr=1e-3, input_shape=(224,224,1), dropout=None,
                  pooling="avg", weights=None):
    mnet = MobileNet(input_shape=input_shape,
                     include_top=False,
                     weights=weights,
                     channels="gray")
    if pooling == "avg":
        x = GlobalAveragePooling2D()(mnet.output)
    elif pooling == "max":
        x = GlobalMaxPooling2D()(mnet.output)
    elif pooling is None:
        x = Flatten()(mnet.output)
    if dropout is not None:
        x = Dropout(dropout)(x)
    x = Dense(1, activation="sigmoid")(x)
    model = Model(inputs=mnet.input, outputs=x)
    if weights is not None:
        model.load_weights(weights)
    for l in model.layers[:layer]:
        l.trainable = False
    model.compile(loss="binary_crossentropy", optimizer=optimizers.Adam(lr),
                  metrics=["accuracy"])
    return model


def get_prediction( dixel: Dixel, model ):
    pixels = get_pixels(dixel)
    return model.predict(np.expand_dims(np.expand_dims(pixels, axis=2), axis=0))[0][0]

Dixel.get_prediction = get_prediction