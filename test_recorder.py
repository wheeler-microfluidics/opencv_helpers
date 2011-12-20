#!/usr/bin/env python
from time import sleep

from path import path

from recorder import Recorder, CVCaptureConfig
from camera_capture import CameraCapture


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

    cam_cap = CameraCapture()
    info = cam_cap.get_framerate_info()
    target_fps = min(24., int(0.95 * info.mean_framerate))

    r = Recorder(args.out_file, cam_cap, fps=target_fps, auto_init=True)
    r.record()
    sleep(args.seconds)
    log = r.stop()

    log.print_summary()
    log.save(args.out_file.parent.joinpath('%s.dat' % args.out_file.namebase))
    print 'DONE'
    del cam_cap
