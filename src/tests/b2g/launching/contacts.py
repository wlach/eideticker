from eideticker.test import B2GAppStartupTest
from eideticker.b2gtestmixins import B2GContactsTestMixin


class Test(B2GContactsTestMixin, B2GAppStartupTest):
    pass
