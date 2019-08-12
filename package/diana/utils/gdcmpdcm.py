import pydicom
from scipy.misc import imsave
import sys

ba_image = sys.argv[1]
an = sys.argv[2]
ds = pydicom.dcmread(ba_image)
imsave("/opt/diana/{}.png".format(an), ds.pixel_array)
