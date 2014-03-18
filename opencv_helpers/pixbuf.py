#!/usr/bin/env python
import gtk
from safe_cv import cv
import numpy as np
from path_helpers import path


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
    rows, cols, channels = a.shape

    cv_im = cv.CreateImageHeader((cols, rows),
                                dtype2depth[str(a.dtype)],
                                channels)
    cv.SetData(cv_im, a.tostring(),
                a.dtype.itemsize * channels * cols)
    return cv_im


def cv2pixbuf(img):
    dtype2depth = {
        cv.IPL_DEPTH_8U: 8,
        cv.IPL_DEPTH_16U: 16,
    }
    rows, cols, depth, channels = img.height, img.width, dtype2depth[img.depth], img.channels
    row_stride = channels * cols
    pixbuf = gtk.gdk.pixbuf_new_from_data(img.tostring(), 
                                       gtk.gdk.COLORSPACE_RGB, 
                                       False, 
                                       depth,
                                       cols, 
                                       rows, 
                                       row_stride)
    return pixbuf 


def array2pixbuf(a):
    dtype2depth = {
        'uint8':   cv.IPL_DEPTH_8U,
        'int8':    cv.IPL_DEPTH_8S,
        'uint16':  cv.IPL_DEPTH_16U,
        'int16':   cv.IPL_DEPTH_16S,
        'int32':   cv.IPL_DEPTH_32S,
        'float32': cv.IPL_DEPTH_32F,
        'float64': cv.IPL_DEPTH_64F,
    }
    return gtk.gdk.pixbuf_new_from_array(a, gtk.gdk.COLORSPACE_RGB, dtype2depth[str(a.dtype)])


def pixbuf2cv(p):
    dtype2depth = {
        8:   cv.IPL_DEPTH_8U,
        16:  cv.IPL_DEPTH_16U,
        32:   cv.IPL_DEPTH_32S,
    }
    rows, cols, depth, channels = p.get_height(), p.get_width(), p.get_bits_per_sample(), p.get_n_channels()

    cv_im = cv.CreateImageHeader((cols, rows), dtype2depth[depth], channels)
    print 'depth, channels, cols:', depth, channels, cols
    data = p.get_pixels()
    print len(data)
    cv.SetData(cv_im, p.get_pixels(), channels * cols)
    return cv_im


if __name__ == '__main__':
    args = parse_args()
    img = cv.LoadImage(args.in_file)

    # Convert CV image to numpy.array
    a = cv2array(img)

    # Convert numpy.array to CV image
    cv_im = array2cv(a)
    p = cv2pixbuf(cv_im)

    cv_im2 = pixbuf2cv(p)

    cv.SaveImage(args.out_file, cv_im2)
