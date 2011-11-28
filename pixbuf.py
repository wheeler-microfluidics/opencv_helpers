#!/usr/bin/env python
import gtk
import cv
import numpy as np
from path import path


def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Overlay sub-rectangle of image onto image.""",
                           )
    parser.add_argument(nargs=1, dest='in_file', type=str)
    parser.add_argument(nargs=1, dest='out_file', type=str)
    args = parser.parse_args()
    
    args.in_file = path(args.in_file[0])
    args.out_file = path(args.out_file[0])
    if args.in_file.abspath() == args.out_file.abspath():
        raise ValueError, 'Input path and output path must be different.'
    
    return args


def cv2array(im):
  depth2dtype = {
        cv.IPL_DEPTH_8U: 'uint8',
        cv.IPL_DEPTH_8S: 'int8',
        cv.IPL_DEPTH_16U: 'uint16',
        cv.IPL_DEPTH_16S: 'int16',
        cv.IPL_DEPTH_32S: 'int32',
        cv.IPL_DEPTH_32F: 'float32',
        cv.IPL_DEPTH_64F: 'float64',
    }

  arrdtype=im.depth
  a = np.fromstring(
         im.tostring(),
         dtype=depth2dtype[im.depth],
         count=im.width*im.height*im.nChannels)
  a.shape = (im.height,im.width,im.nChannels)
  return a


def array2cv(a):
    dtype2depth = {
        'uint8':   cv.IPL_DEPTH_8U,
        'int8':    cv.IPL_DEPTH_8S,
        'uint16':  cv.IPL_DEPTH_16U,
        'int16':   cv.IPL_DEPTH_16S,
        'int32':   cv.IPL_DEPTH_32S,
        'float32': cv.IPL_DEPTH_32F,
        'float64': cv.IPL_DEPTH_64F,
    }
    rows, cols, depth = a.shape

    cv_im = cv.CreateImageHeader((cols, rows),
                                dtype2depth[str(a.dtype)],
                                depth)
    cv.SetData(cv_im, a.tostring(),
                a.dtype.itemsize * depth * cols)
    return cv_im


if __name__ == '__main__':
    args = parse_args()
    img = cv.LoadImage(args.in_file)

    # Convert CV image to numpy.array
    a = cv2array(img)

    # Convert numpy.array to CV image
    cv_im = array2cv(a)

    cv.SaveImage(args.out_file, cv_im)
