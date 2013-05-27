from eideticker.test import B2GTest
import time
from gaiatest.gaia_test import GaiaApps

class Test(B2GTest):
    def __init__(self, testinfo, **kwargs):
        super(Test, self).__init__(testinfo, **kwargs)

        self.appname = testinfo['appname']

    def run(self):
        apps = GaiaApps(self.device.marionette)

        self.start_capture()
        self.test_started()
        app = apps.launch(self.appname)
        assert app.frame_id is not None
        self.log("Waiting %s seconds for app to finish starting" %
                 self.capture_timeout)
        time.sleep(self.capture_timeout)
        self.test_finished()
        self.end_capture()

        # cleanup: switch back to main frame
        self.device.marionette.switch_to_frame()
