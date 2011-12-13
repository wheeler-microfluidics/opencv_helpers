#!/usr/bin/env python
from time import sleep

from path import path

from recorder import Recorder, CVCaptureConfig


def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Copy n seconds from webcam to destination.""",
                           )
    parser.add_argument('-s', '--seconds', dest='seconds', type=float, default=5)
    parser.add_argument('-c', '--camera_id', dest='camera_id', type=int, default=-1)
    parser.add_argument(nargs=1, dest='out_file', type=str)
    args = parser.parse_args()
    
    args.out_file = path(args.out_file[0])
    
    return args


if __name__ == '__main__':
    args = parse_args()

    cap_config = CVCaptureConfig(args.camera_id, type_='camera')
    r = Recorder(cap_config, args.out_file, auto_init=True)
    r.record()
    sleep(args.seconds)
    r.stop()
