# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest.apps.contacts.app import Contacts
from marionette import expected
from marionette.errors import NoSuchElementException
from marionette.errors import ElementNotVisibleException
from marionette.wait import Wait
from marionette.by import By
from gaiatest.gaia_test import GaiaApps


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
        self.wait_for_content_ready()

    def wait_for_content_ready(self):
        apps = GaiaApps(self.device.marionette)
        contacts = Contacts(self.device.marionette)

        Wait(self.device.marionette).until(
            lambda m: apps.displayed_app.name.lower() == 'contacts')
        apps.switch_to_displayed_app()

        Wait(self.device.marionette, 120, ignored_exceptions=(
            NoSuchElementException, ElementNotVisibleException)).until(
            lambda m: m.find_element(
                *contacts._contact_locator).is_displayed())

    def prepare_app(self):
        self.launch_app()


class B2GMarketplaceTestMixin(object):

    requires_wifi = True

    def launch_app(self):
        apps = GaiaApps(self.device.marionette)
        apps.launch('Marketplace')
        self.wait_for_content_ready()

    def wait_for_content_ready(self):
        apps = GaiaApps(self.device.marionette)
        Wait(self.device.marionette).until(
            lambda m: apps.displayed_app.name.lower() == 'marketplace')
        apps.switch_to_displayed_app()
        iframe = Wait(self.device.marionette).until(
            expected.element_present(
                By.CSS_SELECTOR, 'iframe[src*="marketplace"]'))
        self.device.marionette.switch_to_frame(iframe)
        Wait(self.device.marionette).until(
            lambda m: 'loaded' in m.find_element(
                By.TAG_NAME, 'body').get_attribute('class').split())

    def prepare_app(self):
        self.launch_app()
