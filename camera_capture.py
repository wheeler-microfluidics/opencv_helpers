from video import CVCaptureProperties
from recorder import CVCaptureConfig, cv
from videocapture.VideoCapture import Device


class CameraCapture(object):
    def __init__(self, auto_init=False):
        if auto_init:
            self.init_capture()
        self._dimensions = None

    def init_capture(self):
        raise NotImplementedError

    def get_frame(self):
        raise NotImplementedError

    @property
    def dimensions(self):
        raise NotImplementedError


class CVCameraCapture(CameraCapture):
    def __init__(self, id=None, auto_init=False):
        if id is None:
            self.id = -1
        else:
            self.id = id
        self.cap_config = CVCaptureConfig(self.id, type_='camera')
        self.cap = None
        self.props = None
        super(CVCameraCapture, self).__init__(auto_init=auto_init)

    def init_capture(self):
        self.cap = self.cap_config.create_capture()
        for i in range(100):
            cv.GrabFrame(self.cap)

    def get_frame(self):
        cv.GrabFrame(self.cap)
        frame = cv.RetrieveFrame(self.cap)
        if frame:
            return frame
        else:
            return None

    @property
    def dimensions(self):
        if self._dimensions is None:
            self.props = CVCaptureProperties(self.cap)
            self._dimensions = (self.props.width, self.props.height)
        return self._dimensions


class CAMVideoCapture(CameraCapture):
    def __init__(self, id=None, auto_init=False):
        if id is None:
            self.id = 0
        else:
            self.id = id
        self.device = None
        super(CAMVideoCapture, self).__init__(auto_init=auto_init)

    def init_capture(self):
        self.device = Device()
        for i in range(100):
            self.device.getImage()

    def get_frame(self):
        pi = self.device.getImage()
        frame = cv.CreateImageHeader(pi.size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(frame, pi.tostring())
        return frame

    @property
    def dimensions(self):
        if self._dimensions is None:
            pi = self.device.getImage()
            self._dimensions = pi.size
        return self._dimensions
