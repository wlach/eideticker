import time

from gaiatest.apps.messages.app import Messages
from marionette.by import By
from marionette.errors import NoSuchElementException
from marionette.errors import StaleElementException
from marionette.errors import TimeoutException

from eideticker.test import B2GAppStartupTest


class Test(B2GAppStartupTest):

    def populate_databases(self):
        self.device.b2gpopulate.populate_messages(200, restart=False)

    def prepare_app(self):
        # launch the messages app and wait for the messages to be displayed,
        # the first launch after populating the data takes a long time.
        messages = Messages(self.device.marionette)
        messages.launch()
        end_time = time.time() + 120
        while time.time() < end_time:
            try:
                message = self.device.marionette.find_element(
                    By.CSS_SELECTOR, '#threads-container li')
                if message.is_displayed():
                    break
            except (NoSuchElementException, StaleElementException):
                pass
            time.sleep(0.5)
        else:
            raise TimeoutException('No messages displayed')
        self.device.gaiaApps.kill(messages.app)
