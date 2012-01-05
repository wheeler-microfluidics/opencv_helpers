import os
from datetime import datetime, timedelta

import numpy as np

from video import CVCaptureProperties
from recorder import CVCaptureConfig, cv, RecordFrameRateInfo
from frame_rate import FrameRateInfo


class CaptureError(Exception):
    pass


class CaptureFrameRateInfo(FrameRateInfo):
    def test_framerate(self, frame_count=50):
        times = [datetime.now()]
        for i in range(frame_count):
            self.cam_cap.get_frame()
            times.append(datetime.now())
        del times[0]

        frame_lengths = np.array([(times[i + 1] - times[i]).total_seconds()  for i in range(len(times) - 1)])

        return np.array(times), frame_lengths


class CameraCaptureBase(object):
    def __init__(self, auto_init=False):
        self.initialized = False
        if auto_init:
            self.init_capture()
        self._dimensions = None

    def release_capture(self):
        if self.initialized:
            result = self._release_capture()
            self.initialized = False
            return result
        return False

    def _release_capture(self):
        raise NotImplementedError

    def init_capture(self):
        result = self._init_capture()
        if self.get_frame() is None:
            raise CaptureError, 'could not initialize capture device.'
        self.initialized = True
        return result

    def _init_capture(self):
        raise NotImplementedError

    def get_frame(self):
        raise NotImplementedError

    @property
    def dimensions(self):
        raise NotImplementedError

    def get_record_framerate_info(self, codec):
        if not self.initialized:
            cleanup_required = True
            self.init_capture()
        else:
            cleanup_required = False

        info = RecordFrameRateInfo(self, codec)

        if cleanup_required:
            self.release_capture()
        return info

    def get_framerate_info(self):
        if not self.initialized:
            cleanup_required = True
            self.init_capture()
        else:
            cleanup_required = False

        info = CaptureFrameRateInfo(self)

        if cleanup_required:
            self.release_capture()
        return info

    def __del__(self):
        self.release_capture()


class CVCameraCapture(CameraCaptureBase):
    def __init__(self, id=None, auto_init=False):
        if id is None:
            self.id = -1
        else:
            self.id = id
        self.cap_config = CVCaptureConfig(self.id, type_='camera')
        self.cap = None
        self.props = None
        super(CVCameraCapture, self).__init__(auto_init=auto_init)

    def _release_capture(self):
        if self.cap is not None:
            del self.cap
        if self.props is not None:
            del self.props

    def _init_capture(self):
        self.cap = self.cap_config.create_capture()

    def get_frame(self):
        cv.GrabFrame(self.cap)
        frame = cv.RetrieveFrame(self.cap)
        if frame:
            return frame
        else:
            return None

    def _set_dimensions(self, dimensions):
        cv.SetCaptureProperty(self.cap, cv.CV_CAP_PROP_FRAME_WIDTH, dimensions[0])
        cv.SetCaptureProperty(self.cap, cv.CV_CAP_PROP_FRAME_HEIGHT, dimensions[1])
        self._dimensions = dimensions

    @property
    def dimensions(self):
        if self._dimensions is None:
            self.props = CVCaptureProperties(self.cap)
            self._dimensions = (self.props.width, self.props.height)
        return self._dimensions


class CAMVideoCapture(CameraCaptureBase):
    def __init__(self, id=None, auto_init=False):
        if id is None:
            self.id = 0
        else:
            self.id = id
        self.device = None
        super(CAMVideoCapture, self).__init__(auto_init=auto_init)

    def _init_capture(self):
        from videocapture.VideoCapture import Device

        try:
            self.device = Device()
        except Exception, why:
            raise CaptureError, 'could not initialize capture device'
        for i in range(100):
            self.device.getImage()

    def _release_capture(self):
        if self.device:
            del self.device

    def get_frame(self):
        pi = self.device.getImage()
        frame = cv.CreateImageHeader(pi.size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(frame, pi.tostring())
        cv.CvtColor(frame, frame, cv.CV_RGB2BGR)
        return frame

    @property
    def dimensions(self):
        if self._dimensions is None:
            pi = self.device.getImage()
            self._dimensions = pi.size
        return self._dimensions

if os.name == 'nt':
    CameraCapture = CAMVideoCapture
else:
    CameraCapture = CVCameraCapture
