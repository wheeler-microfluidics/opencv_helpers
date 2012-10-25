import numpy as np


class FrameRateInfo(object):
    def __init__(self, cam_cap):
        self.cam_cap = cam_cap
        self.times, self.frame_lengths = self.test_framerate()

    def test_framerate(self, frame_count=50):
        raise NotImplementedError

    def get_summary(self):
        print 'captured %d frames' % len(self.times)
        print '  first frame: %s' % self.times[0]
        print '  last frame:  %s' % self.times[-1]
        print '  recording length: %s' % (self.times[-1] - self.times[0]).total_seconds()

        print '  Frame rate info:'
        print '    mean: %s' % self.mean_framerate
        print '    max:  %s' % self.max_framerate
        print '    min:  %s' % self.min_framerate

    @property
    def mean_framerate(self):
        return 1. / self.frame_lengths.mean()

    @property
    def min_framerate(self):
        return 1. / self.frame_lengths.max()

    @property
    def max_framerate(self):
        return 1. / self.frame_lengths.min()
