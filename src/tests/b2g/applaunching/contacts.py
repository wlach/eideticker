from eideticker.test import B2GAppStartupTest
from eideticker.b2gtestmixins import B2GContactsTestMixin


class Test(B2GAppStartupTest, B2GContactsTestMixin):

    def __init__(self, testinfo, appname, **kwargs):
        B2GAppStartupTest.__init__(self, testinfo, appname, **kwargs)
