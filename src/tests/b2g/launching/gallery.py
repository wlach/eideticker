import time

from gaiatest.apps.gallery.app import Gallery
from marionette import By
from marionette import Wait
from marionette import expected

from eideticker.test import B2GAppStartupTest

from b2gpopulate import WORKLOADS


class Test(B2GAppStartupTest):
    picture_count = WORKLOADS['heavy']['picture']

    def prepare_app(self):
        self.device.b2gpopulate.populate_pictures(self.picture_count)
        self.device.gaiaApps.launch(self.appname)
        # Bug 922608 - Wait for the gallery app to finish scanning
        time.sleep(5)
        self.wait_for_content_ready()

    def wait_for_content_ready(self):
        app = Gallery(self.device.marionette)
        Wait(self.device.marionette, timeout=240).until(
            lambda m: len(m.find_elements(
                By.CSS_SELECTOR, '.thumbnail')) == self.picture_count)
        Wait(self.device.marionette, timeout=60).until(
            expected.element_not_displayed(self.device.marionette.find_element(
                *app._progress_bar_locator)))
