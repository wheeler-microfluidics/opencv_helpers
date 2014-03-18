import sys
from time import sleep
import Queue
import multiprocessing
from collections import namedtuple
from contextlib import closing
from StringIO import StringIO
from datetime import datetime, timedelta
import os
import tempfile
import logging

from path_helpers import path, pickle
import numpy as np

from video import cv, CVCaptureProperties
from frame_rate import FrameRateInfo
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


class RecorderLog(object):
    def __init__(self, fps):
        self.fps = fps
        self.times = [datetime.now()]
        self.sleep_times = []
        self.record_times = []
        self.frame_lengths = []

    def print_summary(self):
        from pprint import pprint

        print 'captured %d frames' % len(self.times)
        print '  first frame: %s' % self.times[0]
        print '  last frame:  %s' % self.times[-1]
        print '  recording length: %s' % (self.times[-1] - self.times[0]).total_seconds()

        print '  Frame rate info:'
        print '    mean: %s' % (1.0 / self.frame_lengths.mean())
        print '    max:  %s' % (1.0 / self.frame_lengths.min())
        print '    min:  %s' % (1.0 / self.frame_lengths.max())

        pprint(self.frame_lengths)

    def save(self, out_file):
        out_path = path(out_file)
        out_path.pickle_dump([self.fps, self.frame_lengths, self.times, self.sleep_times, self.record_times], protocol=pickle.HIGHEST_PROTOCOL)

    def finish(self):
        import numpy as np

        del self.times[0]

        self.frame_lengths = np.array([(self.times[i + 1] - self.times[i]).total_seconds()  for i in range(len(self.times) - 1)])


class RecorderChild(object):
    STATES = dict(RECORDING=10, STOPPED=20)

    def __init__(self, conn, output_path, cam_cap, fps=24, codec=None):
        self.conn = conn
        self.output_path = path(output_path)
        self.fps = fps
        if codec is None and not os.name == 'nt':
            codec = 'XVID'
        self.codec = codec
        logging.getLogger('opencv.recorder').info('[RecorderChild] Using codec: %s' % self.codec)
        self.cam_cap = cam_cap
        self.cam_cap.init_capture()
        self.writer = self._get_writer()
        self.state = self.STATES['STOPPED']
        self.frame_period = 1.0 / self.fps
        
    def _get_writer(self):
        if self.codec is None:
            fourcc = -1
        else:
            fourcc = cv.CV_FOURCC(*self.codec)
        writer = cv.CreateVideoWriter(self.output_path, fourcc, self.fps,
                                            self.cam_cap.dimensions, True)
        return writer

    def main(self):
        import numpy as np

        prev_frame = None

        self.cam_cap.get_framerate_info()
        frame_count = 0
        record_id = 0
        avg_count = 1
        record_times_smooth = np.array(avg_count * [0.1 * self.frame_period])
        frame_periods = np.array(avg_count * [0.95 * self.frame_period])
        logging.getLogger('opencv.recorder').info('Target FPS: %.4f' % (self.fps))

        log = RecorderLog(self.fps)

        iter_count = 1000
        extra_start = datetime.now()
        for i in range(iter_count):
            log.sleep_times.append(1)
            log.record_times.append(1)
            log.times.append(1)
            frame_count += 1
            record_id = (record_id + 1) % avg_count
        log.sleep_times = []
        log.record_times = []
        del log.times[1:]
        record_id = 0
        frame_count = 0
        extra_time = (datetime.now() - extra_start).total_seconds() / float(iter_count)

        self.conn.send('ready')

        while True:
            if self.conn.poll():
                command = self.conn.recv()
                if command == 'stop':
                    logging.getLogger('opencv.recorder').info('stop recording')
                    self.state = self.STATES['STOPPED']
                    break
                elif command == 'record':
                    logging.getLogger('opencv.recorder').info('recording')
                    self.state = self.STATES['RECORDING']
            if self.state == self.STATES['RECORDING']:
                log.times.append(datetime.now())
                frame_periods[record_id] = (log.times[-1] - log.times[-2]).total_seconds()
                frame = self.cam_cap.get_frame()
                if frame:
                    cv.WriteFrame(self.writer, frame)
                    prev_frame = frame
                else:
                    cv.WriteFrame(self.writer, prev_frame)
                record_times_smooth[record_id] = (datetime.now() - log.times[-1]).total_seconds()
                if frame_count > 10:
                    sleep_time = self.frame_period - record_times_smooth[record_id]\
                                    + 0.5 * (self.frame_period - frame_periods.mean())\
                                    - extra_time
                else:
                    sleep_time = self.frame_period - record_times_smooth[record_id]\
                                    - extra_time

                log.sleep_times.append(sleep_time)
                log.record_times.append(record_times_smooth[record_id])
                record_id = (record_id + 1) % avg_count

                if sleep_time > 0:
                    sleep(sleep_time)
                else:
                    logging.getLogger('opencv.recorder').info('warning: recording is lagging')
                frame_count += 1


        log.finish()

        # Report log back to parent process
        self.conn.send(log)

        return


class RecordFrameRateInfo(FrameRateInfo):
    def __init__(self, cam_cap, codec=None):
        self.codec = codec
        super(RecordFrameRateInfo, self).__init__(cam_cap)

    def test_framerate(self, frame_count=100):
        with Silence():
            if self.codec is None:
                fourcc = -1
            else:
                fourcc = cv.CV_FOURCC(*self.codec)
            f_handle, output_path = tempfile.mkstemp(suffix='.avi') 
            output_path = path(output_path)
            os.close(f_handle)
            times = []
            writer = None
            try:
                writer = cv.CreateVideoWriter(output_path, fourcc, 24,
                                                    self.cam_cap.dimensions, True)
                prev_frame = None
                # Grab and write frames as fast as possible (no delay between
                # frames) and record times of frame grabs.
                for i in range(frame_count):
                    frame = self.cam_cap.get_frame()
                    if frame:
                        cv.WriteFrame(writer, frame)
                        prev_frame = frame
                    else:
                        cv.WriteFrame(writer, prev_frame)
                    self.cam_cap.get_frame()
                    times.append(datetime.now())

                frame_lengths = np.array([(times[i + 1] - times[i]).total_seconds()  for i in range(len(times) - 1)])
            finally:
                if writer:
                    del writer
                output_path.remove()

        return np.array(times), frame_lengths


class Recorder(object):
    def __init__(self, output_path, cam_cap, fps=24, codec=None, auto_init=False):
        self.output_path = path(output_path)
        self.fps = fps
        self.cam_cap = cam_cap
        self.codec = codec
        self.conn, self.child_conn = multiprocessing.Pipe()
        if auto_init:
            self.child = self._launch_child()
        else:
            self.child = None

    def _pipe_pull(self):
        while True:
            if self.conn.poll():
                return self.conn.recv()
            sleep(1. / 100)
    
    def _launch_child(self):
        p = multiprocessing.Process(target=self._start_child)
        p.start()
        while True:
            response = self._pipe_pull()
            if response == 'ready':
                break
            else:
                raise Exception('Invalid response from RecorderChild')
        logging.getLogger('opencv.recorder').info('RecorderChild is ready')
        return p

    def _start_child(self):
        child = RecorderChild(self.child_conn, self.output_path, self.cam_cap, self.fps, self.codec)
        child.main()

    def record(self):
        if self.child is None:
            self.child = self._launch_child()
        logging.getLogger('opencv.recorder').info('request recording: %s' % datetime.now())
        self.conn.send('record')

    def stop(self):
        logging.getLogger('opencv.recorder').info('request stop: %s' % datetime.now())
        self.conn.send('stop')
        if self.child:
            log = self._pipe_pull()
            self.child.join()
        else:
            log = None
        del self.child
        return log
