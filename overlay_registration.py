from collections import namedtuple

# Import state machine package
import statepy.state
from safe_cv import cv


CANCEL = statepy.state.declareEventType('on_cancel')
IMAGE_CLICK = statepy.state.declareEventType('on_image_click')
OVERLAY_CLICK = statepy.state.declareEventType('on_image_click')
END = statepy.state.declareEventType('on_end')


class StateWithCallback(statepy.state.State):
    def callback(self, event, *args):
        # Call callback function (if there is one)
        if hasattr(self, 'callback'):
            self.callback(*args)


class WaitCairoClick(StateWithCallback):
    colour = (0, 1, 0)
    def on_image_click(self, event):
        if not hasattr(event, 'cairo_context'):
            return
        # Draw label on image at point
        event.cairo_context.rectangle(event.cairo_point.x, event.cairo_point.y,
                10, 10)
        event.cairo_context.set_source_rgb(*self.colour)
        event.cairo_context.fill_preserve()
        event.cairo_context.set_source_rgb(1, 1, 1)
        event.cairo_context.stroke()


class WaitOverlayClick(WaitCairoClick):
    def on_image_click(self, event):
        super(WaitOverlayClick, self).on_image_click(event)
        self.overlay_points += [event.point]

    def enter(self):
        if self.on_overlay_point:
            self.on_overlay_point('Please click a new point on the overlay.')


class WaitImageClick(WaitCairoClick):
    def on_image_click(self, event):
        super(WaitImageClick, self).on_image_click(event)
        self.image_points += [event.point]

    def enter(self):
        if self.on_image_point:
            self.on_image_point('Please click a new point on the image.')


class WaitOverlayClickA(WaitOverlayClick):
    colour = (0, 1, 0)
    label = 'A'
    def enter(self):
        del self.overlay_points[:]
        del self.image_points[:]
        super(WaitOverlayClickA, self).enter()

    @staticmethod
    def transitions():
        return {
            OVERLAY_CLICK : WaitImageClickA, 
            CANCEL : Canceled
        }


class WaitImageClickA(WaitImageClick):
    colour = (0, 1, 0)
    label = 'A'
    @staticmethod
    def transitions():
        return {
            IMAGE_CLICK : WaitOverlayClickB,
            CANCEL : Canceled
        }


class WaitOverlayClickB(WaitOverlayClick):
    colour = (1, 0, 0)
    @staticmethod
    def transitions():
        return {
            OVERLAY_CLICK : WaitImageClickB, 
            CANCEL : Canceled
        }


class WaitImageClickB(WaitImageClick):
    colour = (1, 0, 0)
    @staticmethod
    def transitions():
        return {
            IMAGE_CLICK : WaitOverlayClickC,
            CANCEL : Canceled
        }


class WaitOverlayClickC(WaitOverlayClick):
    colour = (0, 0, 1)
    @staticmethod
    def transitions():
        return {
            OVERLAY_CLICK : WaitImageClickC, 
            CANCEL : Canceled
        }


class WaitImageClickC(WaitImageClick):
    colour = (0, 0, 1)
    @staticmethod
    def transitions():
        return {
            IMAGE_CLICK : WaitOverlayClickD,
            CANCEL : Canceled
        }


class WaitOverlayClickD(WaitOverlayClick):
    colour = (1, 0, 1)
    @staticmethod
    def transitions():
        return {
            OVERLAY_CLICK : WaitImageClickD, 
            CANCEL : Canceled
        }


class WaitImageClickD(WaitImageClick):
    colour = (1, 0, 1)
    def on_image_click(self, event):
        super(WaitImageClickD, self).on_image_click(event)
        cv.GetPerspectiveTransform(self.overlay_points, self.image_points, self.map_mat)
        if self.on_registered:
            self.on_registered()

    @staticmethod
    def transitions():
        return {
            IMAGE_CLICK : Done,
            CANCEL : Canceled
        }


class Canceled(statepy.state.State):
    def enter(self):
        if self.on_canceled:
            self.on_canceled()


class Done(statepy.state.State):
    pass


Point = namedtuple('Point', 'x y')


class ImageRegistrationTask(object):
    def __init__(self,
            on_overlay_point=None,
            on_image_point=None,
            on_registered=None,
            on_canceled=None):
        # Need to use an array for current_point or changes from a State
        # would not persist.
        self.map_mat = cv.CreateMat(3, 3, cv.CV_32FC1)
        # Initialize map_mat with identity transformation matrix.
        cv.GetPerspectiveTransform(4 * [Point(0,0)], 4 * [Point(0,0)], self.map_mat)
        self.state = dict(overlay_points=[], image_points=[],
            map_mat=self.map_mat,
            on_overlay_point=on_overlay_point,
            on_image_point=on_image_point,
            on_registered=on_registered,
            on_canceled=on_canceled)
        self.machine = statepy.state.Machine(statevars=self.state)

    def cancel(self):
        self.trigger_event(CANCEL)

    def start(self, start_state=WaitOverlayClickA):
        self.machine.start(startState=start_state)

    def get_corrected_image(self, in_image):
        assert(self.machine.currentState() is None)
        map_mat = self.state['map_mat']
        warped = cv.CreateImage((in_image.width, in_image.height), 8,
                                in_image.channels)
        cv.WarpPerspective(in_image, warped, map_mat, flags=cv.CV_WARP_INVERSE_MAP)
        return warped

    def simulate(self):
        self.start()
        for i in range(4):
            self.trigger_event(OVERLAY_CLICK, point=Point(i, i))
            self.trigger_event(IMAGE_CLICK, point=Point(i, i))

        current_state = self.machine.currentState()
        assert(current_state is None)

    def trigger_event(self, etype, **kwargs):
        if self.machine.currentState() is None:
            return None
        event = statepy.state.Event(etype)
        for key, value in kwargs.iteritems():
            setattr(event, key, value)
        self.machine.injectEvent(event)
        return event


if __name__ == '__main__':
    with open('overlay_registration.dot', 'wb') as in_file:
        statepy.state.Machine.writeStateGraph(fileobj=in_file, startState=WaitOverlayClickA)

    registration_task = ImageRegistrationTask()
