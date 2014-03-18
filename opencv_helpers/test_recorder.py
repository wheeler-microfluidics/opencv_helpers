#!/usr/bin/env python
from time import sleep
from contextlib import closing
from StringIO import StringIO

from path_helpers import path

from silence import Silence
from recorder import Recorder, CVCaptureConfig, RecordFrameRateInfo
from camera_capture import CameraCapture
from codec import CodecTest, get_supported_codecs


def print_codec_list(msg=None):
    if msg is None:
        msg = 'Please choose from:'
    print '%s\n   ' % msg,
    print '\n    '.join(sorted([c.fourcc for c in get_supported_codecs()]))


def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Copy n seconds from webcam to destination.""",
                           )
    parser.add_argument('-s', '--seconds', dest='seconds', type=float, default=5)
    parser.add_argument('-i', '--camera_id', dest='camera_id', type=int, default=-1)
    parser.add_argument('-c', '--codec_fourcc', dest='fourcc', type=str, default=None)
    parser.add_argument('-f', '--fps', dest='fps', type=float, default=25)
    parser.add_argument('-l', '--list_codecs', dest='list_codecs', action='store_true')
    parser.add_argument(nargs=1, dest='out_file', type=str)
    args = parser.parse_args()

    if args.list_codecs:
        parser.print_help()
        print ''
        print_codec_list('Available codecs:')
        raise SystemExit

    args.out_file = path(args.out_file[0])
    
    return args


preferred_codecs = ['XVID', 'I420']


if __name__ == '__main__':
    args = parse_args()

    if args.fourcc is None:
        for c in preferred_codecs:
            if CodecTest.test_codec(c):
                args.fourcc = c
                break
        if args.fourcc is None:
            print 'Default codecs not supported on this system.'
            print_codec_list()
            raise SystemExit
    elif not CodecTest.test_codec(args.fourcc):
        print 'Unsupported codec: %s\n' % args.fourcc
        raise SystemExit

    cam_cap = CameraCapture()
    info = cam_cap.get_record_framerate_info(args.fourcc)
    target_fps = min(args.fps, int(0.95 * info.mean_framerate))

    r = Recorder(args.out_file, cam_cap, fps=target_fps, codec=args.fourcc, auto_init=True)
    r.record()
    sleep(args.seconds)

    log = r.stop()

    log.print_summary()
    log.save(args.out_file.parent.joinpath('%s.dat' % args.out_file.namebase))
    print 'DONE'
    del cam_cap
