# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest.apps.contacts.app import Contacts
from marionette.errors import NoSuchElementException
from marionette.errors import ElementNotVisibleException
from marionette.wait import Wait


class B2GContactsTestMixin(object):

    def populate_databases(self):
        self.device.b2gpopulate.populate_contacts(
            200, include_pictures=False, restart=False)

    def launch_app(self):

        self.log("Launching app and waiting for it to be ready!")

        # launch the contacts app and wait for the contacts to be displayed,
        # the first launch after populating the data takes a long time.
        contacts = Contacts(self.device.marionette)
        contacts.launch()
        Wait(self.device.marionette, 120, ignored_exceptions=(NoSuchElementException, ElementNotVisibleException)).until(lambda m: m.find_element(*contacts._contact_locator).is_displayed())

    def prepare_app(self):
        self.launch_app()
