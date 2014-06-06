from eideticker.test import B2GAppStartupTest
from eideticker.b2gtestmixins import B2GMarketplaceTestMixin


class Test(B2GMarketplaceTestMixin, B2GAppStartupTest):
    pass
