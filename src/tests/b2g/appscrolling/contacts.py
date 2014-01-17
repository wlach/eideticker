from eideticker.test import B2GAppActionTest
from eideticker.b2gtestmixins import B2GContactsTestMixin


class Test(B2GContactsTestMixin, B2GAppActionTest):

    def __init__(self, testinfo, appname, **kwargs):
        B2GAppActionTest.__init__(self, testinfo, appname, **kwargs)
        self.cmds = []
        for i in range(int(testinfo.get('scrolldown_amount'))):
            self.cmds.append(['scroll_down'])
