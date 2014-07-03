from eideticker.test import B2GAppActionTest
from eideticker.b2gtestmixins import B2GMarketplaceTestMixin


class Test(B2GMarketplaceTestMixin, B2GAppActionTest):
    pass

Test.cmds = []
num_swipes = 5
for i in range(num_swipes):
    Test.cmds.append(['scroll_down'])
for i in range(num_swipes):
    Test.cmds.append(['scroll_up'])
