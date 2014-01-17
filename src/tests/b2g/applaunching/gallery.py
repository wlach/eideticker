import time

from gaiatest.apps.gallery.app import Gallery
from marionette.errors import NoSuchElementException
from marionette.errors import StaleElementException
from marionette.errors import TimeoutException

from eideticker.test import B2GAppStartupTest


class Test(B2GAppStartupTest):
    def __init__(self, testinfo, appname, **kwargs):
        B2GAppStartupTest.__init__(self, testinfo, appname, **kwargs)

    def prepare_app(self):
        picture_count = 100
        self.device.b2gpopulate.populate_pictures(picture_count)

        # launch the gallery app and wait for the thumbnails to be displayed,
        # the first launch after populating the data takes a long time.
        gallery = Gallery(self.device.marionette)
        gallery.app = self.device.gaiaApps.launch('Gallery')
        time.sleep(5)
        end_time = time.time() + 120
        while time.time() < end_time:
            try:
                items = self.device.marionette.find_elements(
                    *gallery._gallery_items_locator)
                progress = self.device.marionette.find_element(
                    *gallery._progress_bar_locator)
                if len(items) == picture_count and not progress.is_displayed():
                    break
            except (NoSuchElementException, StaleElementException):
                pass
            time.sleep(0.5)
        else:
            raise TimeoutException('Gallery items not displayed')
        self.device.gaiaApps.kill(gallery.app)
