import os
import random

import gtk
import numpy as np
from path_helpers import path

from safe_cv import cv
from overlay_registration import ImageRegistrationTask, Point, OVERLAY_CLICK,\
                                IMAGE_CLICK, CANCEL
from registration_dialog import RegistrationDialog


class RegistrationDemoGUI(RegistrationDialog):
    def __init__(self, in_file, in_file2=None, *args, **kwargs):
        super(RegistrationDemoGUI, self).__init__(*args, **kwargs)
        self.in_file = path(in_file)
        if in_file2:
            self.in_file2 = path(in_file2)
        else:
            self.in_file2 = None

    def get_original_image(self):
        im_original = cv.LoadImageM(self.in_file)
        cv.CvtColor(im_original, im_original, cv.CV_BGR2RGB)
        return im_original

    def get_rotated_image(self):
        original = self.images['original']
        return self._get_warped_image(original.width, original.height)

    def _get_warped_image(self, width, height):
        if self.in_file2 is None:
            # Rotate the original image by a random number of degrees
            degrees = random.randint(0, 360)
            image, map_mat = self.get_rotated(self.images['original'], degrees)
        else:
            image = cv.LoadImageM(self.in_file2)
            cv.CvtColor(image, image, cv.CV_BGR2RGB)
        if image.width != width or image.height != height:
            image = self.get_resized(image, int(width), int(height))
        return image

    def get_rotated(self, in_image, rotate_degrees):
        rotated = cv.CreateImage((in_image.width, in_image.height), 8, in_image.channels)
        map_mat = cv.CreateMat(2, 3, cv.CV_32FC1)
        cv.GetRotationMatrix2D((rotated.width * 0.5, rotated.height * 0.5),
                                rotate_degrees, 1., map_mat)
        cv.WarpAffine(in_image, rotated, map_mat)
        return rotated, map_mat


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

    import numpy as np
    print np.asarray(gui.run())
