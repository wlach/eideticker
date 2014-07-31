# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest.apps.contacts.app import Contacts
from marionette import expected
from marionette import Wait
from marionette.by import By

from b2gpopulate import WORKLOADS


class B2GContactsTestMixin(object):

    def launch_app(self):
        app = Contacts(self.device.marionette)
        app.launch()
        self.wait_for_content_ready()

    def populate_databases(self):
        self.device.b2gpopulate.populate_contacts(
            WORKLOADS['light']['contact'],
            include_pictures=False, restart=False)

    def prepare_app(self):
        self.launch_app()

    def wait_for_content_ready(self):
        app = Contacts(self.device.marionette)
        contact = Wait(self.device.marionette, timeout=240).until(
            expected.element_present(*app._contact_locator))
        Wait(self.device.marionette, timeout=30).until(
            expected.element_displayed(contact))


class B2GMarketplaceTestMixin(object):

    def launch_app(self):
        self.device.gaiaApps.launch('Marketplace')
        self.wait_for_content_ready()

    def prepare_app(self):
        self.launch_app()

    def wait_for_content_ready(self):
        if 'index.html' in self.device.marionette.get_url():
            # only switch to iframe if Marketplace is not packaged
            iframe = Wait(self.device.marionette).until(
                expected.element_present(
                    By.CSS_SELECTOR, 'iframe[src*="marketplace"]'))
            self.device.marionette.switch_to_frame(iframe)
        Wait(self.device.marionette, timeout=30).until(
            lambda m: 'loaded' in m.find_element(
                By.TAG_NAME, 'body').get_attribute('class').split())


class B2GMessagesTestMixin(object):

    def launch_app(self):
        self.device.gaiaApps.launch('Messages')
        self.wait_for_content_ready()

    def prepare_app(self):
        self.launch_app()

    def populate_databases(self):
        self.device.b2gpopulate.populate_messages(
            WORKLOADS['light']['message'],
            restart=False)

    def wait_for_content_ready(self):
        # the 200 message workload contains 37 threads (36 on v1.3)
        Wait(self.device.marionette, timeout=60).until(
            lambda m: len(m.find_elements(
                By.CSS_SELECTOR, '#threads-container li')) >= 36)


class B2GSettingsTestMixin(object):

    def wait_for_content_ready(self):
        # _currentPanel is set after all handlers are set
        Wait(self.device.marionette).until(
            lambda m: m.execute_script(
                "return window.wrappedJSObject.Settings && "
                "window.wrappedJSObject.Settings._currentPanel === '#root'"))
