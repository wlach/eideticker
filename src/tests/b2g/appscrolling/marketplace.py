from eideticker.test import B2GAppActionTest
from eideticker.b2gtestmixins import B2GMarketplaceTestMixin


class Test(B2GMarketplaceTestMixin, B2GAppActionTest):

    requires_wifi = True

    def __init__(self, testinfo, appname, **kwargs):
        B2GAppActionTest.__init__(self, testinfo, appname, **kwargs)
        self.cmds = []
        num_swipes = 5
        for i in range(num_swipes):
            self.cmds.append(['scroll_down'])
        for i in range(num_swipes):
            self.cmds.append(['scroll_up'])
