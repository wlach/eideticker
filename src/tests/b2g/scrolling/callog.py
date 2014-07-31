import time

from gaiatest.apps.phone.app import Phone

from eideticker.test import B2GAppActionTest

from b2gpopulate import WORKLOADS


class Test(B2GAppActionTest):

    def __init__(self, testinfo, options, device, capture_controller):
        B2GAppActionTest.__init__(self, testinfo, options, device, capture_controller)
        self.scrolldown_amount = int(testinfo.get('scrolldown_amount'))

    def populate_databases(self):
        self.device.b2gpopulate.populate_calls(
            WORKLOADS['medium']['call'], restart=False)

    def launch_app(self):
        phone = Phone(self.device.marionette)
        phone.launch()
        phone.tap_call_log_toolbar_button()

        time.sleep(30)  # FIXME: wait for call log loading modal to be gone
        self.log('Done waiting for call log loading modal to be gone')

        call_log_container = self.device.marionette.find_element(
            'id', 'call-log-container')
        call_log_location = call_log_container.location
        call_log_swipe_padding = 8

        scroll_x1 = call_log_location['x'] + call_log_container.size['width'] / 2
        scroll_y1 = call_log_location['y'] + (call_log_container.size['height'] -
                                              call_log_swipe_padding)
        scroll_y2 = call_log_location['y'] + call_log_swipe_padding

        self.cmds = []

        for i in range(self.scrolldown_amount):
            self.cmds.append([
                'drag', scroll_x1, scroll_y1, scroll_x1, scroll_y2, 100, 10])
