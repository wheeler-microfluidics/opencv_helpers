from time import sleep

from path_helpers import path

from recorder import Recorder, CVCaptureConfig


def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Copy n seconds from source video to destination.""",
                           )
    parser.add_argument('-s', '--seconds', dest='seconds', type=int, default=5)
    parser.add_argument(nargs=1, dest='in_file', type=str)
    parser.add_argument(nargs=1, dest='out_file', type=str)
    args = parser.parse_args()
    
    args.in_file = path(args.in_file[0])
    args.out_file = path(args.out_file[0])
    if args.in_file.abspath() == args.out_file.abspath():
        raise ValueError, 'Input path and output path must be different.'
    
    return args


if __name__ == '__main__':
    from safe_cv import cv

    args = parse_args()
    cap_config = CVCaptureConfig(args.in_file, type_='file')
    r = Recorder(cap_config, args.out_file)

    print 'start recording'
    r.record()

    sleep(args.seconds)

    print 'stop recording'
    r.stop()
