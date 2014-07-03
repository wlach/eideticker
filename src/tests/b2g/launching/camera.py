# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette import expected
from marionette import Wait
from marionette.by import By

from eideticker.test import B2GAppStartupTest


class Test(B2GAppStartupTest):

    def prepare_app(self):
        self.device.gaiaApps.set_permission('Camera', 'geolocation', 'deny')

    def wait_for_content_ready(self):
        viewfinder = Wait(self.device.marionette).until(
            expected.element_present(
                By.CSS_SELECTOR, 'video[class*=viewfinder]'))
        Wait(self.device.marionette).until(lambda m: m.execute_script(
            'return arguments[0].readyState > 0;', [viewfinder]))
