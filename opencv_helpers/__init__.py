from .safe_cv import cv
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
