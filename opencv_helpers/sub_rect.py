#!/usr/bin/env python
from safe_cv import cv
import numpy as np
from path_helpers import path


def overlay_subrect(in_file):
    img = cv.LoadImageM(in_file)
    sub_width = img.cols / 5
    sub_height = img.rows / 5

    sub_dims = [sub_width, sub_height]

    sub_offset = sub_dims[:]
    sub = cv.GetSubRect(img, tuple(sub_offset + sub_dims))

    sub_offset = [3 * sub_width, 3 * sub_height]
    sub2 = cv.GetSubRect(img, tuple(sub_offset + sub_dims))

    cv.AddWeighted(sub2, 0.8, sub, 0.2, 0, sub)
    return img


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


if __name__ == '__main__':
    args = parse_args()
    img = overlay_subrect(args.in_file)
    cv.SaveImage(args.out_file, img)
