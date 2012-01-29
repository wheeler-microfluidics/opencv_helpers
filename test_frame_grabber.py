#!/usr/bin/env python
from time import sleep
from contextlib import closing
from StringIO import StringIO
import signal
import os

import numpy as np
import gtk
import gobject
from path import path

from safe_cv import cv
from frame_grabber import FrameGrabber, CVCaptureConfig
from camera_capture import CameraCapture


def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Grab frames from webcam and asynchronously display to Gtk DrawingArea.""",
                           )
    parser.add_argument('-i', '--camera_id', dest='camera_id', type=int, default=-1)
    args = parser.parse_args()

    return args


class FrameGrabberGUI:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('glade', 'frame_grabber.glade'))
        self.window = self.builder.get_object('window')
        self.area = self.builder.get_object('drawing_area')
        # connect signals from glade to python
        self.builder.connect_signals(self)
        # show window and contents
        self.window.show_all()
        self.cam_cap = CameraCapture(auto_init=False)
        self.grabber = FrameGrabber(self.cam_cap, auto_init=True)
        self.grabber.frame_callback = self.update_frame_data
        self.pixbuf = None
        self.grabber.start()
        self.last_frame = None

    def update_frame_data(self, frame):
        # Process NumPy array frame data
        height, width, channels = frame.shape
        self.last_frame = frame
        depth = {np.dtype('uint8'): 8}[frame.dtype]
        logging.debug('[update_frame_data] type(frame)=%s '\
            'height, width, channels, depth=(%s)'\
            % (type(frame), (height, width, channels, depth)))
        gtk_frame = cv.fromarray(frame)
        cv.CvtColor(gtk_frame, gtk_frame, cv.CV_BGR2RGB)
        self.pixbuf = gtk.gdk.pixbuf_new_from_data(
            gtk_frame.tostring(), gtk.gdk.COLORSPACE_RGB, False,
            depth, width, height, gtk_frame.step)
        if self.pixbuf:
            self.area.window.draw_pixbuf(gui.window.get_style().white_gc,
                                        self.pixbuf, 0, 0, 0, 0)
        return True

    def on_window_destroy(self, widget):
        gtk.main_quit()
        results = self.grabber.stop()

        logging.info(str(results))
        del self.cam_cap
    

if __name__ == '__main__':
    import logging
    # ^C exits the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    logging.basicConfig(format='%(asctime)s %(message)s',
        level=logging.INFO)
    args = parse_args()

    gui = FrameGrabberGUI()

    gtk.main()
