from imageio import imwrite
import numpy as np
import pydicom
import sys


ba_image = sys.argv[1]
an = sys.argv[2]
ds = pydicom.dcmread(ba_image)
im = ds.pixel_array
if ds.PhotometricInterpretation == "MONOCHROME1":
    im = np.full((ds.pixel_array.shape), 255.0) - (ds.pixel_array / ds.pixel_array.max() * 255.0)
imwrite("/opt/diana/{}.png".format(an), im)
