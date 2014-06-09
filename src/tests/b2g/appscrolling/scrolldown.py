from eideticker.test import B2GAppActionTest


class Test(B2GAppActionTest):
    def __init__(self, testinfo, options, device, capture_controller):
        B2GAppActionTest.__init__(self, testinfo, options, device, capture_controller)

        self.cmds = []
        for i in range(int(testinfo.get('scrolldown_amount'))):
            self.cmds.append(['scroll_down'])
