#!/usr/bin/env python
from safe_cv import cv
import numpy as np
from path_helpers import path


def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Convert image from one format to another.""",
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
    img = cv.LoadImageM(args.in_file)
    print type(img)
    cv.SaveImage(args.out_file, img)
