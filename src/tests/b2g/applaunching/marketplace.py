from eideticker.test import B2GAppStartupTest
from eideticker.b2gtestmixins import B2GMarketplaceTestMixin


class Test(B2GMarketplaceTestMixin, B2GAppStartupTest):

    requires_wifi = True

    def __init__(self, testinfo, appname, **kwargs):
        B2GAppStartupTest.__init__(self, testinfo, appname, **kwargs)
