from eideticker.test import B2GTest
import time
from gaiatest.gaia_test import GaiaApps

class Test(B2GTest):
    def __init__(self, appname=None, **kwargs):
        super(Test, self).__init__(**kwargs)

        self.appname = appname

    def run(self):
        apps = GaiaApps(self.device.marionette)

        self.start_capture()
        self.test_started()
        app = apps.launch(self.appname)
        assert app.frame_id is not None
        time.sleep(5)
        self.test_finished()
        self.end_capture()

        # cleanup: switch back to main frame
        self.device.marionette.switch_to_frame()
