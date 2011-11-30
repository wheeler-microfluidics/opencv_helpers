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

        with Silence():
            self.writer = cv.CreateVideoWriter(self.output_path, cv.CV_FOURCC('X', 'V', 'I', 'D'),
                                            self.fps, (self.props.width, self.props.height), True)
        self.state = self.STATES['STOPPED']

    def main(self):
        with Silence():
            while True:
                try:
                    command = self.conn.get_nowait()
                except Queue.Empty:
                    pass
                else:
                    if command == 'stop':
                        self.state = self.STATES['STOPPED']
                        break
                    elif command == 'record':
                        self.state = self.STATES['RECORDING']
                if self.state == self.STATES['RECORDING']:
                    sleep(1.0 / 24)
                    cv.GrabFrame(self.cap)
                    frame = cv.RetrieveFrame(self.cap)
                    if frame:
                        cv.WriteFrame(self.writer, frame)


class Recorder(object):
    def __init__(self, cap, output_path, fps=24):
        self.output_path = path(output_path)
        self.fps = fps
        self.cap = cap
        self.conn = multiprocessing.Queue()

        p = multiprocessing.Process(target=self._start_child)
        p.start()

    def _start_child(self):
        child = RecorderChild(self.conn, self.cap, self.output_path, self.fps)
        child.main()

    def record(self):
        self.conn.put('record')

    def stop(self):
        self.conn.put('stop')
