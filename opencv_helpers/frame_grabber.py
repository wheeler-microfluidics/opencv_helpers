"""
Copyright 2012 Ryan Fobel and Christian Fobel

This file is part of Microdrop.

Microdrop is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
Foundation, either version 3 of the License, or
(at your option) any later version.

Microdrop is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Microdrop.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division
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
import gobject

from path_helpers import path, pickle
import numpy as np

from video import cv


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


class FrameGrabberChild(object):
    STATES = dict(RECORDING=10, STOPPED=20)

    def __init__(self, conn, cam_cap):
        self.conn = conn
        self.cam_cap = cam_cap
        try:
            self.cam_cap.init_capture()
        except:
            self.cam_cap = None
        self.fps_limit = 10.
        self.state = self.STATES['STOPPED']
        
    def main(self):
        import numpy as np

        prev_frame = None

        self.conn.send('ready')

        frames_captured = 0
        start_time = None
        stop_time = None
        watch_time = datetime.now()
        while True:
            now = datetime.now()
            """
            if (now - watch_time).total_seconds() > 5:
                # No watchdog reset in the last 5 seconds.  Assume that main
                # thread is gone.
                print '''
                 No watchdog reset in the last 5 seconds.  Assume that main
                 thread is gone.
                 '''
                return
            """
            if self.conn.poll():
                command = self.conn.recv()
                if command == 'reset_watchdog':
                    watch_time = now
                elif command == 'stop':
                    logging.getLogger('opencv.frame_grabber')\
                            .info('stop recording')
                    self.state = self.STATES['STOPPED']
                    stop_time = datetime.now()
                    break
                elif command == 'start':
                    logging.getLogger('opencv.frame_grabber').info('recording')
                    self.state = self.STATES['RECORDING']
                    start_time = datetime.now()
                elif len(command) == 2 and command[0] == 'set_fps_limit':
                    logging.getLogger('opencv.frame_grabber')\
                            .debug('setting fps_limit: %s' % command[1])
                    if self.fps_limit >= 1:
                        self.fps_limit = command[1]
            if self.cam_cap is not None\
                    and self.state == self.STATES['RECORDING']:
                grab_time = datetime.now()
                frame = self.cam_cap.get_frame()
                if frame:
                    # Convert frame to NumPy array so it can be pickled/sent
                    # to parent process.
                    mat = cv.GetMat(frame)
                    np_frame = np.asarray(mat)
                    self.conn.send(['frame', np_frame, grab_time])
                    frames_captured += 1
            sleep(1 / self.fps_limit)
        self.conn.send(('results', dict(frames_captured=frames_captured,
                                start_time=start_time,
                                stop_time=stop_time)))


class FrameGrabber(object):
    def __init__(self, cam_cap, auto_init=False):
        self.cam_cap = cam_cap
        self.conn, self.child_conn = multiprocessing.Pipe()
        if auto_init:
            self.child = self._launch_child()
        else:
            self.child = None
        self.timer_id = None
        self.watchdog_timer = None
        self.enabled = False
        self.last_result = None
        self.current_frame = None
        self.current_time = None
        self.frame_callback = None

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
                raise Exception('Invalid response from FrameGrabberChild')
        logging.getLogger('opencv.frame_grabber').info('FrameGrabberChild is ready')
        return p

    def _start_child(self):
        child = FrameGrabberChild(self.child_conn, self.cam_cap)
        child.main()

    def _reset_watchdog(self):
        if self.child is None:
            return
        self.conn.send('reset_watchdog')
        return True

    def _grab_frame(self):
        frame = None
        while self.enabled and self.conn.poll():
            frame = self.conn.recv()
            if len(frame) > 0 and frame:
                self.current_frame, self.current_time = frame[1:]
        if frame is not None:
            if self.frame_callback:
                self.frame_callback(self.current_frame, self.current_time)
        return self.enabled

    def set_fps_limit(self, fps_limit):
        if self.child is None:
            return
        self.conn.send(('set_fps_limit', fps_limit))

    def start(self):
        if self.child is None:
            self.child = self._launch_child()
        logging.getLogger('opencv.frame_grabber').info('request start: %s' % datetime.now())
        self.watchdog_timer = gobject.timeout_add(2500, self._reset_watchdog)
        self.conn.send('start')
        self.enabled = True
        self.timer_id = gobject.timeout_add(10, self._grab_frame)

    def stop(self):
        if self.watchdog_timer is not None:
            gobject.source_remove(self.watchdog_timer)
        if self.timer_id is not None:
            gobject.source_remove(self.timer_id)
        self.enabled = False
        logging.getLogger('opencv.frame_grabber').info('request stop: %s' % datetime.now())
        self.conn.send('stop')
        if self.child:
            log = self._pipe_pull()
            while log:
                if log[0] == 'results':
                    break
                log = self._pipe_pull()
            self.child.join()
        else:
            log = None
        del self.child
        self.last_result = log
        return self.last_result
