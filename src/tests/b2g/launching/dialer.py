# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette import Wait

from eideticker.test import B2GAppStartupTest

from gaiatest.apps.phone.app import Phone

class Test(B2GAppStartupTest):

    def wait_for_content_ready(self):
        Wait(self.device.marionette).until(lambda m: self.device.gaiaApps.displayed_app.name == 'Phone')
        self.device.gaiaApps.switch_to_displayed_app()
        keypad_toolbar_button = self.device.marionette.find_element(*Phone._keypad_toolbar_button_locator)
        Wait(self.device.marionette).until(lambda m: 'toolbar-option-selected' in keypad_toolbar_button.get_attribute('class'))
