from imageio import imwrite
import pydicom
import sys

ba_image = sys.argv[1]
an = sys.argv[2]
ds = pydicom.dcmread(ba_image)
imwrite("/opt/diana/{}.png".format(an), ds.pixel_array)
