from eideticker.test import B2GTest
import time
from gaiatest.gaia_test import GaiaApps
from gaiatest.apps.homescreen.app import Homescreen

class Test(B2GTest):
    def __init__(self, testinfo, **kwargs):
        super(Test, self).__init__(testinfo, **kwargs)

        self.appname = testinfo['appname']

    def run(self):
        apps = GaiaApps(self.device.marionette)

        # theoretically it would be cleaner to set this specifically for the
        # camera test, but that seemed additional complication for no real
        # gain
        apps.set_permission('Camera', 'geolocation', 'deny')

        homescreen = Homescreen(self.device.marionette)
        homescreen.switch_to_homescreen_frame()
        appicon = None

        while homescreen.homescreen_has_more_pages:
            # skip the everything.me page by going to the next page at the
            # beginning of this loop
            homescreen.go_to_next_page()
            appicon = self.device.marionette.find_element(
                homescreen._homescreen_icon_locator[0],
                homescreen._homescreen_icon_locator[1] % self.appname)
            if appicon.is_displayed():
                break

        tap_x = appicon.location['x'] + (appicon.size['width'] / 2)
        tap_y = appicon.location['y'] + (appicon.size['height'] / 2)

        self.start_capture()
        self.execute_actions([['tap', tap_x, tap_y]],
                             test_finished_after_actions=False)
        self.log("Waiting %s seconds for app to finish starting" %
                 self.capture_timeout)
        time.sleep(self.capture_timeout)

        self.test_finished()
        self.end_capture()
