#!/usr/bin/env python
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
from time import sleep
from contextlib import closing
from StringIO import StringIO
import signal
import os

import numpy as np
import gtk
import gobject
from path_helpers import path

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

def array2cv(a):
    dtype2depth = {
            'uint8':   cv.IPL_DEPTH_8U,
            'int8':    cv.IPL_DEPTH_8S,
            'uint16':  cv.IPL_DEPTH_16U,
            'int16':   cv.IPL_DEPTH_16S,
            'int32':   cv.IPL_DEPTH_32S,
            'float32': cv.IPL_DEPTH_32F,
            'float64': cv.IPL_DEPTH_64F,
        }
    try:
        nChannels = a.shape[2]
    except:
        nChannels = 1
    cv_im = cv.CreateMat(a.shape[0], a.shape[1], cv.CV_8UC3)
    cv.SetData(cv_im, a.tostring(), a.shape[1] * nChannels)
    return cv_im


class FrameGrabberGUI:
    def __init__(self, fps_limit=5.):
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
        self.pixmap = None
        self.grabber.start()
        self.grabber.set_fps_limit(fps_limit)
        self.video_enabled = False

    def on_fps_limit_spinner_value_changed(self, button):
        self.grabber.set_fps_limit(button.get_value())

    def on_button_start_clicked(self, *args, **kwargs):
        self.video_enabled = True

    def on_button_stop_clicked(self, *args, **kwargs):
        self.video_enabled = False

    def on_drawing_area_expose_event(self, widget, event):
        if self.pixmap:
            x , y, width, height = event.area
            self.area.window.draw_drawable(gui.area.get_style().white_gc,
                        self.pixmap, x, y, x, y, width, height)
        return False

    def draw_state(self, cairo):
        # Draw two red boxes
        cairo.set_source_rgba(1, 0, 0, 0.5)
        cairo.rectangle(200, 100, 100, 100)
        cairo.fill()
        cairo.rectangle(200, 300, 100, 100)
        cairo.fill()
        # Draw two white boxes
        cairo.set_source_rgba(1, 1, 1, 0.5)
        cairo.rectangle(300, 100, 100, 100)
        cairo.fill()
        cairo.rectangle(300, 300, 100, 100)
        cairo.fill()

    def update_frame_data(self, frame, frame_time):
        cairo = None
        if self.video_enabled:
            # Process NumPy array frame data
            height, width, channels = frame.shape
            depth = {np.dtype('uint8'): 8}[frame.dtype]
            logging.debug('[update_frame_data] type(frame)=%s '\
                'height, width, channels, depth=(%s)'\
                % (type(frame), (height, width, channels, depth)))
            gtk_frame = array2cv(frame)
            cv.CvtColor(gtk_frame, gtk_frame, cv.CV_BGR2RGB)
            x, y, a_width, a_height = self.area.get_allocation()
            if a_width != width or a_height != height:
                resized = cv.CreateMat(width, height, cv.CV_8UC3)
                cv.Resize(gtk_frame, resized)
            else:
                resized = gtk_frame
            self.pixbuf = gtk.gdk.pixbuf_new_from_data(
                resized.tostring(), gtk.gdk.COLORSPACE_RGB, False,
                depth, width, height, height * 3) #resized.step)
            self.pixmap, mask = self.pixbuf.render_pixmap_and_mask()
            cairo = self.pixmap.cairo_create()
        elif self.pixmap is not None:
            x, y, width, height = self.area.get_allocation()
            cairo = self.pixmap.cairo_create()
            cairo.set_source_rgb(1, 1, 1)
            cairo.rectangle(0, 0, width, height)
            cairo.fill()
        if cairo:
            self.draw_state(cairo)
        self.area.queue_draw()
        return True

    def on_window_destroy(self, widget):
        gtk.main_quit()
        results = self.grabber.stop()

        logging.info(str(results))
        del self.cam_cap
    

def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Demo of interactive 4-point image registration.""",
                           )
    parser.add_argument(dest='fps_limit', nargs='?', type=float, default=5.,
            help='Max frames per second to grab (default=%(default)s)')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    import logging
    # ^C exits the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    logging.basicConfig(format='%(asctime)s %(message)s',
        level=logging.INFO)
    args = parse_args()

    gui = FrameGrabberGUI(args.fps_limit)

    gtk.main()
