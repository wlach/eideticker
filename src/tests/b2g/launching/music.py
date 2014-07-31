import time

from gaiatest.apps.music.app import Music
from marionette import By
from marionette import Wait
from marionette import expected

from eideticker.test import B2GAppStartupTest

from b2gpopulate import WORKLOADS


class Test(B2GAppStartupTest):

    def prepare_app(self):
        music_count = WORKLOADS['heavy']['music']
        tracks_per_album = 10
        self.device.b2gpopulate.populate_music(
            music_count, tracks_per_album=tracks_per_album)

        app = Music(self.device.marionette)
        app.launch()
        # Bug 922610 - Wait for the music app to finish scanning
        time.sleep(5)
        self.wait_for_content_ready()

    def wait_for_content_ready(self):
        Wait(self.device.marionette, timeout=240).until(
            expected.element_not_displayed(
                self.device.marionette.find_element(By.ID, 'scan-progress')))
