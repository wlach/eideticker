from eideticker.test import B2GTest
import time
from gaiatest.gaia_test import GaiaApps


class Test(B2GTest):

    def run(self):
        apps = GaiaApps(self.device.marionette)
        # open two apps
        for name in ['Contacts', 'Clock', 'Music']:
            app = apps.launch(name)
            assert app.frame_id is not None

        # switch back to main frame
        self.device.marionette.switch_to_frame()

        # open cards view
        self.device.marionette.execute_script(
            "window.dispatchEvent(new Event('holdhome'));")

        # launching apps can reset orientation to the wrong value, since some
        # apps only support portrait mode. reset it here.
        self.device.resetOrientation()

        self.start_capture()
        self.test_started()
        for i in range(3):
            for command in ['swipe_left', 'swipe_left', 'swipe_right',
                            'swipe_right']:
                self.device.executeCommand(command, [])
                time.sleep(0.5)
        self.test_finished()
        self.end_capture()
