# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from runner import AndroidBrowserRunner
from options import OptionParser, CaptureOptionParser, TestOptionParser
from device import getDevicePrefs, getDevice
from metadata import get_fennec_appinfo, get_appinfo
from products import get_product, products, BuildRetriever
from test import get_test
from runtest import get_test_manifest, run_test, TestException
from metrics import get_standard_metrics
