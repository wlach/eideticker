from eideticker.test import B2GAppStartupTest
from eideticker.b2gtestmixins import B2GMessagesTestMixin


class Test(B2GMessagesTestMixin, B2GAppStartupTest):
    pass
