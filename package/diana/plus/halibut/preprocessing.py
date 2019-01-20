import scipy.misc
# import cv2
import os
import numpy as np

from scipy.ndimage.interpolation import zoom
from scipy.ndimage.filters import gaussian_filter
# from skimage.exposure import equalize_adapthist
from PIL import Image

# def apply_clahe(image):
#     clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
#     return clahe.apply(image)


def resize_single_image(img, new_length, clahe=False, smooth=None, verbose=True):
    """
    Resizes image (L x W) length-wise while maintaining aspect ratio.

    Arguments:
      - smooth (float/None) : sigma value for Gaussian smoothing
    """
    # if clahe:
    #     img = apply_clahe(img)
    resize_factor = float(new_length) / img.shape[0]
    if resize_factor > 1:
        # Cubic spline interpolation
        resized_img = zoom(img, resize_factor)
    else:
        # Linear interpolation
        resized_img = zoom(img, resize_factor, order=1, prefilter=False)
    if smooth is not None:
        resized_img = gaussian_filter(resized_img, sigma=smooth)
    return resized_img.astype("uint8")

def resize_images(image_file_paths, input_dir, output_dir, new_length,
    clahe=False, smooth=None, verbose=True):
    """
    Resizes images (L x W) length-wise while maintaining aspect ratio.
    Assumes images are PNG file format.
    Saves resized image in <output_dir> with original file name.

    Arguments:
      - smooth (float/None) : sigma value for Gaussian smoothing
    """
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    for each_image in image_file_paths:
        pid = each_image.split(".png")[0]
        if verbose:
            print("Resizing pid {} ...".format(pid) )
        full_img_path = os.path.join(input_dir, each_image)
        outp_img_path = os.path.join(output_dir, each_image)
        img = scipy.misc.imread(full_img_path)
        img = resize_single_image(img, new_length, clahe, smooth, verbose)
        img = Image.fromarray(img)
        img.save(outp_img_path)

def grid_patches(img, patch_size=224, num_rows=7, num_cols=7, return_coords=False):
    """
    Generates <num_rows> * <num_cols> patches from an image.
    Centers of patches gridded evenly length-/width-wise.
    """
    # This typically doesn't happen, but if one of your original image
    # dimensions is smaller than the patch size, the image will be resized
    # (aspect ratio maintained) such that the smaller dimension is equal
    # to the patch size. (Maybe it should be padded instead?)
    if np.min(img.shape) < patch_size:
        resize_factor = patch_size / float(np.min(img.shape))
        new_h = int(np.round(resize_factor*img.shape[0]))
        new_w = int(np.round(resize_factor*img.shape[1]))
        img = scipy.misc.imresize(img, (new_h, new_w))
    row_start = patch_size // 2
    row_end = img.shape[0] - patch_size // 2
    col_start = patch_size // 2
    col_end = img.shape[1] - patch_size // 2
    row_inc = (row_end - row_start) // (num_rows - 1)
    col_inc = (col_end - col_start) // (num_cols - 1)
    if row_inc == 0: row_inc = 1
    if col_inc == 0: col_inc = 1
    patch_list = []
    coord_list = []
    for i in range(row_start, row_end+1, row_inc):
        for j in range(col_start, col_end+1, col_inc):
            x0 = i-patch_size//2 ; x1 = i+patch_size//2
            y0 = j-patch_size//2 ; y1 = j+patch_size//2
            patch = img[x0:x1, y0:y1]
            assert patch.shape == (patch_size, patch_size)
            patch_list.append(patch)
            coord_list.append([x0,x1,y0,y1])
    if return_coords:
        return patch_list, coord_list
    else:
        return patch_list


def get_patches(image_file_paths, input_dir, patch_dir, patch_size=224,
    num_rows=7, num_cols=7, verbose=True):
    """
    Basically a wrapper function to generate patches from a list of images.
    Saves patches as numpy arrays because they load faster.
    """
    if not os.path.exists(patch_dir): os.makedirs(patch_dir)
    for each_image in image_file_paths:
        pid = each_image.split(".png")[0]
        if verbose:
            print("Extracting patches from pid {} ...".format(pid) )
        full_img_path = os.path.join(input_dir, each_image)
        outp_img_path = os.path.join(patch_dir, each_image)
        img = scipy.misc.imread(full_img_path)
        patch_list = grid_patches(img, patch_size=patch_size,
            num_rows=num_rows, num_cols=num_cols)
        for index, each_patch in enumerate(patch_list):
            patch_name = pid + "_" + str(index).zfill(3)
            np.save(os.path.join(patch_dir, patch_name), each_patch)
