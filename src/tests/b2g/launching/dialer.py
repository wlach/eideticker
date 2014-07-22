# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette import Wait

from eideticker.test import B2GAppStartupTest

from gaiatest.apps.phone.app import Phone

class Test(B2GAppStartupTest):

    # The dialer app does not load content after launching.
    # Thus it is safe to have a no-op for wait_for_content
    def wait_for_content_ready(self):
        pass
