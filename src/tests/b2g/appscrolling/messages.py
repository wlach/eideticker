from eideticker.test import B2GAppActionTest

class Test(B2GAppActionTest):
    def __init__(self, testinfo, appname, **kwargs):
        B2GAppActionTest.__init__(self, testinfo, appname, **kwargs)

        self.cmds = []
        # there aren't as many messages to scroll through, so we'll do a
        # bunch of scroll ups/scroll downs here (need a bit of extra padding
        # to make sure events go through correctly, at least on the
        # unagi/inari). this is all pretty lame but there you go ;)
        scroll_x1 = int(self.device.dimensions[0] / 2)
        scroll_y1 = (self.device.deviceProperties['swipePadding'][0] + 40)
        scroll_y2 = (self.device.dimensions[1] - \
                         self.device.deviceProperties['swipePadding'][2])

        for i in range(10):
            self.cmds.append(['drag', scroll_x1, scroll_y1, scroll_x1, scroll_y2, 100, 10])
            self.cmds.append(['drag', scroll_x1, scroll_y1, scroll_x1, scroll_y2, 100, 10])
            self.cmds.append(['drag', scroll_x1, scroll_y2, scroll_x1, scroll_y1, 100, 10])
            self.cmds.append(['drag', scroll_x1, scroll_y2, scroll_x1, scroll_y1, 100, 10])
