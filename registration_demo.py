import os
import random

import gtk
import numpy as np
from path import path

from safe_cv import cv


class TransformTest(object):
    def __init__(self, in_file):
        self.in_file = path(in_file)

    def get_rotated_image(self, in_image, rotate_degrees):
        rotated = cv.CreateImage((in_image.width, in_image.height), 8, in_image.channels)
        map_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetRotationMatrix2D((rotated.width * 0.5, rotated.height * 0.5),
                                rotate_degrees, 1., map_mat)
        cv.WarpAffine(in_image, rotated, map_mat)
        return rotated, map_mat

    def get_affine_image(self, in_image, map_mat):
        warped = cv.CreateImage((in_image.width, in_image.height), 8,
                                in_image.channels)
        a = [(0, 0), (in_image.width, in_image.height), (in_image.width, 0)]
        b = self.transform(a, map_mat)
        warped_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetAffineTransform(a, b, warped_mat)
        cv.WarpAffine(in_image, warped, warped_mat, flags=cv.CV_WARP_INVERSE_MAP)
        return warped, warped_mat

    def transform(self, points, map_mat):
        np_map = np.asarray(map_mat)
        get_transform_point = lambda x:\
            tuple(np_map.dot(np.array((points[x][0], points[x][1], 1))\
            .transpose()))
        return map(get_transform_point, range(len(points)))

    def get_perspective_image(self, in_image, map_mat):
        warped = cv.CreateImage((in_image.width, in_image.height), 8,
                                in_image.channels)
        a = [(0,0), (in_image.width, in_image.height), (in_image.width, 0),
                (0, in_image.height)]
        b = self.transform(a, map_mat)
        warped_mat = cv.CreateMat(3, 3, cv.CV_32FC1)
        cv.GetPerspectiveTransform(a, b, warped_mat)
        cv.WarpPerspective(in_image, warped, warped_mat, flags=cv.CV_WARP_INVERSE_MAP)
        return warped, warped_mat

    def test_affine_transform(self, rotate_degrees, out_file_prefix=None):
        if out_file_prefix is None:
            out_file_prefix = self.in_file.parent.joinpath(self.in_file.namebase)
        original = cv.LoadImageM(self.in_file)
        rotated, map_mat = self.get_rotated_image(original, rotate_degrees)
        cv.SaveImage('%s-affine_rotated%s' % (out_file_prefix, self.in_file.ext),
                        rotated)

        warped, warped_mat = self.get_affine_image(rotated, map_mat)
        cv.SaveImage('%s-affine_warped%s' % (out_file_prefix, self.in_file.ext),
                        warped)

    def test_perspective_transform(self, rotate_degrees, out_file_prefix=None):
        if out_file_prefix is None:
            out_file_prefix = self.in_file.parent.joinpath(self.in_file.namebase)
        original = cv.LoadImageM(self.in_file)
        rotated, map_mat = self.get_rotated_image(original, rotate_degrees)
        cv.SaveImage('%s-perspective_rotated%s' % (out_file_prefix, self.in_file.ext),
                        rotated)

        warped = cv.CreateImage((original.width, original.height), 8, original.channels)
        warped, warped_mat = self.get_perspective_image(rotated, map_mat)
        cv.SaveImage('%s-perspective_warped%s' % (out_file_prefix, self.in_file.ext),
                        warped)


class States(object):
    OFF=object()
    LEARN_ORIGINAL_POINTS=object()
    LEARN_ROTATED_POINTS=object()


class RegistrationDemoGUI:
    def __init__(self, in_file, in_file2=None):
        self.in_file = path(in_file)
        if in_file2:
            self.in_file2 = path(in_file2)
        else:
            self.in_file2 = None
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('glade', 'registration_demo.glade'))
        self.window = self.builder.get_object('window')
        self.label_info = self.builder.get_object('label_info')
        self.areas = dict(
            original=self.builder.get_object('original'),
            rotated=self.builder.get_object('rotated'),
            result=self.builder.get_object('result'))
        # connect signals from glade to python
        self.builder.connect_signals(self)
        self.window.show_all()
        # show window and contents
        self.images = {}
        self.pixmaps = {}
        self.pixbufs = {}
        self.reset()

    def _get_warped_image(self, width=None, height=None):
        if self.in_file2 is None:
            # Rotate the original image by a random number of degrees
            degrees = random.randint(0, 360)
            image, map_mat = self.get_rotated(self.images['original'], degrees)
        else:
            image = cv.LoadImageM(self.in_file2)
            cv.CvtColor(image, image, cv.CV_BGR2RGB)
        if width and height:
            image = self.get_resized(image, int(width), int(height))
        return image

    def reset(self):
        im_original = cv.LoadImageM(self.in_file)
        cv.CvtColor(im_original, im_original, cv.CV_BGR2RGB)
        x, y, width, height = self.areas['original'].get_allocation()
        self.images['original'] = self.get_resized(im_original, width, height)
        self.draw_cv_to_pixmap('original')

        x, y, width, height = self.areas['rotated'].get_allocation()
        self.images['rotated'] = self._get_warped_image(width, height)
        self.draw_cv_to_pixmap('rotated')

        #self.draw_cv_to_pixmap('rotated')
        self.areas['original'].queue_draw()
        self.areas['rotated'].queue_draw()
        self.points = dict(original=[], rotated=[])
        self.state = States.OFF

    def get_rotated(self, in_image, rotate_degrees):
        rotated = cv.CreateImage((in_image.width, in_image.height), 8, in_image.channels)
        map_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetRotationMatrix2D((rotated.width * 0.5, rotated.height * 0.5),
                                rotate_degrees, 1., map_mat)
        cv.WarpAffine(in_image, rotated, map_mat)
        return rotated, map_mat

    def draw_cv_to_pixmap(self, image_name):
        image = self.images[image_name]
        x, y, width, height = self.areas[image_name].get_allocation()
        self.pixbufs[image_name] = gtk.gdk.pixbuf_new_from_data(
            image.tostring(), gtk.gdk.COLORSPACE_RGB, False,
            8, width, height, width * 3)
        self.pixmaps[image_name], mask =\
            self.pixbufs[image_name].render_pixmap_and_mask()
    
    def get_resized(self, in_image, width, height):
        #print 'get_resized width=%s height=%s'\
            #% (width, height)
        resized = cv.CreateImage((width, height), 8, in_image.channels)
        cv.Resize(in_image, resized)
        return cv.GetMat(resized)

    def on_original_expose_event(self, widget, event):
        x , y, width, height = event.area
        if 'original' not in self.pixmaps:
            return False
        self.areas['original'].window\
            .draw_drawable(self.areas['original'].get_style().white_gc,
                    self.pixmaps['original'], x, y, x, y, width, height)
        return False

    def on_rotated_expose_event(self, widget, event):
        if 'rotated' not in self.pixmaps:
            return False
        x , y, width, height = event.area
        self.areas['rotated'].window\
            .draw_drawable(self.areas['rotated'].get_style().white_gc,
                    self.pixmaps['rotated'], x, y, x, y, width, height)
        return False

    def on_result_expose_event(self, widget, event):
        if 'result' not in self.pixmaps:
            return False
        x , y, width, height = event.area
        self.areas['result'].window\
            .draw_drawable(self.areas['result'].get_style().white_gc,
                    self.pixmaps['result'], x, y, x, y, width, height)
        return False

    def on_button_reset_clicked(self, *args, **kwargs):
        self.reset()

    def get_perspective_image(self, in_image, map_mat):
        warped = cv.CreateImage((in_image.width, in_image.height), 8,
                                in_image.channels)
        cv.WarpPerspective(in_image, warped, map_mat, flags=cv.CV_WARP_INVERSE_MAP)
        return warped

    def on_rotated_button_press_event(self, widget, event):
        if not self.state == States.LEARN_ROTATED_POINTS:
            return False
        point_count = len(self.points['rotated']) 
        self.points['rotated'].append(event.get_coords())
        point_count += 1
        self.label_info.set_text('Click on point %d in rotated image' % (point_count))
        if point_count >= 4:
            self.state = States.OFF
            self.label_info.set_text('original: %s\nrotated: %s'\
                % (self.points['original'], self.points['rotated']))
            #import pudb; pudb.set_trace()
            map_mat = cv.CreateMat(3, 3, cv.CV_32FC1)
            cv.GetPerspectiveTransform(self.points['original'], self.points['rotated'], map_mat)
            self.images['result'] = self.get_perspective_image(self.images['rotated'], map_mat)
            self.draw_cv_to_pixmap('result')
            self.areas['result'].queue_draw()
            self.points = dict(original=[], rotated=[])
        return False

    def on_original_button_press_event(self, widget, event):
        if not self.state == States.LEARN_ORIGINAL_POINTS:
            return False
        point_count = len(self.points['original']) 
        self.points['original'].append(event.get_coords())
        point_count += 1
        self.label_info.set_text('Click on point %d in original image' % (point_count))
        if point_count >= 4:
            self.state = States.LEARN_ROTATED_POINTS
            self.label_info.set_text('Click on point 0 in rotated image')
        return False

    def on_button_perspective_clicked(self, *args, **kwargs):
        if self.state == States.OFF:
            self.label_info.set_text('Click on point 0 in original image')
            self.state = States.LEARN_ORIGINAL_POINTS

    def on_window_destroy(self, *args, **kwargs):
        gtk.main_quit()

    def info(self, message, title=""):
        dialog = gtk.MessageDialog(self.window, 
                                   gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_INFO, 
                                   gtk.BUTTONS_CLOSE, message)
        dialog.set_title(title)
        result = dialog.run()
        dialog.destroy()
        return result

def parse_args():
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Demo of interactive 4-point image registration.""",
                           )
    parser.add_argument(dest='input_image', nargs=1, type=str)
    parser.add_argument(dest='warped_image', nargs='?', type=str)
    args = parser.parse_args()

    if args.input_image:
        args.input_image = path(args.input_image[0])
    if args.warped_image:
        args.warped_image = path(args.warped_image)

    for f in (args.input_image, args.warped_image):
        if f and not f.isfile():
            parser.error('Could not open file: %s' % f)

    return args

if __name__ == '__main__':
    import logging
    import signal
    # ^C exits the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = parse_args()
    logging.basicConfig(format='%(asctime)s %(message)s',
        level=logging.INFO)

    gui = RegistrationDemoGUI(args.input_image, args.warped_image)

    gtk.main()
