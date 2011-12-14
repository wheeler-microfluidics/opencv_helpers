#!/usr/bin/env python
from time import sleep

from path import path

from recorder import Recorder, CVCaptureConfig
from camera_capture import CAMVideoCapture, CVCameraCapture


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

    cam_cap = CAMVideoCapture()
    #cam_cap = CVCameraCapture()
    r = Recorder(args.out_file, cam_cap, fps=24, auto_init=True)
    sleep(3.)
    r.record()
    sleep(args.seconds)
    r.stop()
    print 'DONE'
    del cam_cap
