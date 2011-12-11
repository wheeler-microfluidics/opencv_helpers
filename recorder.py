import sys
from time import sleep
import Queue
import multiprocessing
from collections import namedtuple

from path import path

from video import cv, CVCaptureProperties
from silence import Silence


class CVCaptureConfig(object):
    type_names = ('camera', 'file')
    types = namedtuple('CVCaptureTypes', type_names)(**dict([(n, i) for i, n in enumerate(type_names)]))

    def __init__(self, source, type_=None):
        self.source = source
        if type_ is None:
            type_ = self.types.camera
        elif type_ not in self.types:
            type_ = type_.strip()
            if not type_ in self.types._fields:
                raise ValueError, 'Invalid type: %s' % type_
            else:
                type_ = getattr(self.types, type_)
        self.type_ = type_

    def create_capture(self):
        if self.type_ == self.types.camera:
            cap = cv.CaptureFromCAM(self.source)
        elif self.type_ == self.types.file:
            source_path = path(self.source).abspath()
            if not source_path.exists():
                raise IOError, 'Capture source path is not accessible: %s' % source_path.abspath()
            cap = cv.CaptureFromFile(self.source)
        else:
            raise ValueError, 'Unsupported capture type: %s' % self.type_
        return cap

    def test_capture(self):
        cap = self.create_capture()
        result = cv.GrabFrame(cap)
        del cap
        return (result == 0)


class RecorderChild(object):
    STATES = dict(RECORDING=10, STOPPED=20)

    def __init__(self, conn, cap_config, output_path, fps=24):
        self.conn = conn
        self.output_path = path(output_path)
        self.fps = fps
        self.cap_config = cap_config
        self.cap = self.cap_config.create_capture()
        self.props = CVCaptureProperties(self.cap)
        self.writer = self._get_writer()
        self.state = self.STATES['STOPPED']

    def _get_writer(self):
        with Silence():
            writer = cv.CreateVideoWriter(self.output_path, cv.CV_FOURCC('X', 'V', 'I', 'D'),
                                            self.fps, (self.props.width, self.props.height), True)
        return writer

    def main(self):
        with Silence():
            while True:
                if self.conn.poll():
                    command = self.conn.recv()
                    if command == 'stop':
                        print 'stop recording'
                        self.state = self.STATES['STOPPED']
                        break
                    elif command == 'record':
                        print 'recording'
                        self.state = self.STATES['RECORDING']
                if self.state == self.STATES['RECORDING']:
                    cv.GrabFrame(self.cap)
                    frame = cv.RetrieveFrame(self.cap)
                    if frame:
                        cv.WriteFrame(self.writer, frame)
                    sleep(1.0 / 24)


class Recorder(object):
    def __init__(self, cap_config, output_path, fps=24, auto_init=False):
        self.output_path = path(output_path)
        self.fps = fps
        # Create a CVCaptureConfig object, since a Capture instance cannot
        # be pickled.  The RecorderChild will create a Capture instance.
        self.cap_config = cap_config
        self.conn, self.child_conn = multiprocessing.Pipe()
        if auto_init:
            self.child = self._launch_child()
        else:
            self.child = None

    def _launch_child(self):
        p = multiprocessing.Process(target=self._start_child)
        p.start()
        return p

    def _start_child(self):
        child = RecorderChild(self.child_conn, self.cap_config, self.output_path, self.fps)
        child.main()

    def record(self):
        if self.child is None:
            self.child = self._launch_child()
        self.conn.send('record')

    def stop(self):
        self.conn.send('stop')
        if self.child:
            self.child.join()
        self.child = None
