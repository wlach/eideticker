from eideticker.test import B2GAppActionTest
from eideticker.b2gtestmixins import B2GMessagesTestMixin


class Test(B2GMessagesTestMixin, B2GAppActionTest):
    def __init__(self, testinfo, options, device, capture_controller):
        B2GAppActionTest.__init__(self, testinfo, options, device,
                                  capture_controller)

        self.cmds = []
        # there aren't as many messages to scroll through, so we'll do a
        # bunch of scroll ups/scroll downs here (need a bit of extra padding
        # to make sure events go through correctly, at least on the
        # unagi/inari). this is all pretty lame but there you go ;)
        scroll_x1 = int(self.device.dimensions[0] / 2)
        scroll_y1 = (self.device.deviceProperties['swipePadding'][0] + 40)
        scroll_y2 = (self.device.dimensions[1] -
                     self.device.deviceProperties['swipePadding'][2])

        for i in range(10):
            self.cmds.append(['drag', scroll_x1, scroll_y1, scroll_x1, scroll_y2, 100, 10])
            self.cmds.append(['drag', scroll_x1, scroll_y1, scroll_x1, scroll_y2, 100, 10])
            self.cmds.append(['drag', scroll_x1, scroll_y2, scroll_x1, scroll_y1, 100, 10])
            self.cmds.append(['drag', scroll_x1, scroll_y2, scroll_x1, scroll_y1, 100, 10])
