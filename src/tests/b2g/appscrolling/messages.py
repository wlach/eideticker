import time

from gaiatest.apps.messages.app import Messages
from marionette.by import By
from marionette.errors import NoSuchElementException
from marionette.errors import ElementNotVisibleException
from marionette.wait import Wait

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

    def populate_databases(self):
        self.device.b2gpopulate.populate_messages(200, restart=False)

    def prepare_app(self):
        # launch the messages app and wait for the messages to be displayed,
        # the first launch after populating the data takes a long time.
        messages = Messages(self.device.marionette)
        messages.launch()
        Wait(self.device.marionette, 120, ignored_exceptions=(NoSuchElementException, ElementNotVisibleException)).until(lambda m: m.find_element(By.CSS_SELECTOR, '#threads-container li').is_displayed())
