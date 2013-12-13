import time

from marionette.by import By
from marionette.errors import NoSuchElementException
from marionette.errors import StaleElementException
from marionette.errors import TimeoutException

from eideticker.test import B2GAppStartupTest


class Test(B2GAppStartupTest):

    def __init__(self, testinfo, appname, **kwargs):
        B2GAppStartupTest.__init__(self, testinfo, appname, **kwargs)

    def prepare_app(self):
        music_count = 100
        tracks_per_album = 10
        album_count = music_count / tracks_per_album
        self.device.b2gpopulate.populate_music(
            music_count, tracks_per_album=tracks_per_album)

        # launch the music app and wait for the tracks to be displayed,
        # the first launch after populating the data takes a long time.
        music = self.device.gaiaApps.launch('Music')
        time.sleep(5)
        end_time = time.time() + 120
        while time.time() < end_time:
            try:
                progress = self.device.marionette.find_element(
                    By.ID, 'scan-progress')
                if not progress.is_displayed():
                    break
            except (NoSuchElementException, StaleElementException):
                pass
            time.sleep(0.5)
        else:
            raise TimeoutException('No music displayed')
        self.device.gaiaApps.kill(music)
