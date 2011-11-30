from time import sleep
import Queue
import multiprocessing

from path import path

from video import cv, CVCaptureProperties
from silence import Silence


class RecorderChild(object):
    STATES = dict(RECORDING=10, STOPPED=20)

    def __init__(self, conn, cap, output_path, fps=24):
        self.conn = conn
        self.output_path = path(output_path)
        self.fps = fps
        self.cap = cap
        self.props = CVCaptureProperties(cap)
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
                        self.state = self.STATES['STOPPED']
                    elif command == 'record':
                        self.state = self.STATES['RECORDING']
                if self.state == self.STATES['RECORDING']:
                    cv.GrabFrame(self.cap)
                    frame = cv.RetrieveFrame(self.cap)
                    if frame:
                        cv.WriteFrame(self.writer, frame)
                    sleep(1.0 / 24)


class Recorder(object):
    def __init__(self, cap, output_path, fps=24):
        self.output_path = path(output_path)
        self.fps = fps
        self.cap = cap
        #self.conn = multiprocessing.Queue()
        self.conn, self.child_conn = multiprocessing.Pipe()

        p = multiprocessing.Process(target=self._start_child)
        p.start()

    def _start_child(self):
        child = RecorderChild(self.child_conn, self.cap, self.output_path, self.fps)
        child.main()

    def record(self):
        self.conn.send('record')

    def stop(self):
        self.conn.send('stop')
