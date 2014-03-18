import re
import sys
import os
import tempfile

from path_helpers import path

from safe_cv import cv
from silence import Silence


class CVCaptureProperties(object):
    captureprop_name2code = dict([(v, getattr(cv, v)) for v in dir(cv) if re.search(r'^CV_CAP_PROP_', v)])

    def __init__(self, cap):
        self.cap = cap
        self.props = self._get_props()
        for k, v in self.captureprop_name2code.iteritems():
            setattr(self, k, self.props[k])

    def _get_props(self):
        with Silence():
            values = dict([(k, cv.GetCaptureProperty(self.cap, v)) for k, v in self.captureprop_name2code.iteritems()])
        return values

    @property
    def frame_count(self):
        return int(self.CV_CAP_PROP_FRAME_COUNT)

    @property
    def height(self):
        return int(self.CV_CAP_PROP_FRAME_HEIGHT)

    @property
    def width(self):
        return int(self.CV_CAP_PROP_FRAME_WIDTH)

    @property
    def fps(self):
        return self.CV_CAP_PROP_FPS

    @property
    def fourcc(self):
        fourcc = int(self.CV_CAP_PROP_FOURCC)
        chars = (fourcc & 0XFF,
                    (fourcc & 0XFF00) >> 8,
                    (fourcc & 0XFF0000) >> 16,
                    int((fourcc & 0XFF000000) >> 24))
        return ''.join([chr(v) for v in chars])


def copy_image_to_video(in_file, out_file, frame_count, fourcc='XVID', fps=24):
    # standard RGB png file
    cap = cv.CaptureFromFile(in_file)
    width = int(cv.GetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_WIDTH))
    height = int(cv.GetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_HEIGHT))

    # uncompressed YUV 4:2:0 chroma subsampled
    cv_fourcc = cv.CV_FOURCC(*fourcc)
    writer = cv.CreateVideoWriter(out_file, cv_fourcc, fps, (width, height), 1)

    for i in range(frame_count):
        cv.GrabFrame(cap)
        frame = cv.RetrieveFrame(cap)
        cv.WriteFrame(writer, frame)


def copy_video(cap, output_path, frame_count=None, offset=0):
    props = CVCaptureProperties(cap)
    if frame_count is None:
        frame_count = props.frame_count
    frame_count = min(props.frame_count, frame_count)
    skip_frames = min(offset, frame_count)
    print 'frame_count, skip_frames:', frame_count, skip_frames

    writer = cv.CreateVideoWriter(output_path, cv.CV_FOURCC(*props.fourcc),
                                    props.fps, (props.width, props.height), True)

    for skip_frames in range(offset):
        cv.GrabFrame(cap)

    for i in range(frame_count):
        cv.GrabFrame(cap)
        frame = cv.RetrieveFrame(cap)
        cv.WriteFrame(writer, frame)


if __name__ == '__main__':
    pass
