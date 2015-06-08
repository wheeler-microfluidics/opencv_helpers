from .safe_cv import cv, cv2
import matplotlib.pyplot as plt
import numpy as np


def imshow(im, axis=None, show_axis=False, swap_channels=True, **kwargs):
    '''
    Arguments
    ---------

     - `im`: OpenCV image.
    '''
    if axis is None:
        fig, axis = plt.subplots(**kwargs)
    if swap_channels:
        cv.CvtColor(im, im, cv.CV_BGR2RGB)
    im_array = (np.fromstring(im.tostring(), dtype='uint8')
                .reshape(im.height, im.width, -1))
    if swap_channels:
        cv.CvtColor(im, im, cv.CV_RGB2BGR)
    axis.imshow(im_array)
    if not show_axis:
        axis.axis('off')
    return axis


def resize(im, width, height):
    '''
    Arguments
    ---------

     - `im`: OpenCV image.
     - `width`: Image width.
     - `height`: Image width.
    '''
    resized = cv.CreateImage((width, height), 8, im.channels)
    cv.Resize(im, resized)
    cv.CvtColor(resized, resized, cv.CV_BGR2RGB)
    return resized


def convert_color(im):
    '''
    Arguments
    ---------

     - `im`: OpenCV image.
    '''
    converted = cv.CreateImage((im.width, im.height), 8, im.channels)
    cv.CvtColor(im, converted, cv.CV_BGR2RGB)
    return converted


def get_map_array(df_a, df_b):
    map_mat = cv.CreateMat(3, 3, cv.CV_32FC1)
    cv.GetPerspectiveTransform(map(tuple, df_a.values),
                               map(tuple, df_b.values), map_mat)
    return np.fromstring(map_mat.tostring(), dtype='f32').reshape(3, 3)


def find_homography_array(df_a, df_b):
    map_arr, mask = cv2.findHomography(df_a.astype(float), df_b.astype(float))
    return map_arr


def cvwarp_mat_to_4x4(warp_arr):
    warp_arr4x4 = np.identity(4, dtype='f32')
    warp_arr4x4[:2, :2] = warp_arr[:2, :2]
    warp_arr4x4[-1, :2] = warp_arr[-1, :2]
    warp_arr4x4[:2, -1] = warp_arr[:2, -1]
    return warp_arr4x4
