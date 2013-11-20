from eideticker.test import B2GAppActionTest
from marionette.by import By

class Test(B2GAppActionTest):
    def prepare_app(self):

        settings_container = self.device.marionette.find_element(
            By.CSS_SELECTOR, '#root > div')
        settings_location = settings_container.location
        settings_swipe_padding = 16

        scroll_x1 = settings_location['x'] + settings_container.size['width'] / 2
        scroll_y1 = settings_location['y'] + (settings_container.size['height'] -
                                              settings_swipe_padding)
        scroll_y2 = settings_location['y'] + settings_swipe_padding

        self.cmds = []
        for i in range(5):
            self.cmds.append(['drag', scroll_x1, scroll_y1, scroll_x1, scroll_y2, 100, 10])
            self.cmds.append(['sleep', 0.5])
            self.cmds.append(['drag', scroll_x1, scroll_y2, scroll_x1, scroll_y1, 100, 10])
            self.cmds.append(['sleep', 0.5])
