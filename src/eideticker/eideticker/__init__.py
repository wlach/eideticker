# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from dashboard import add_dashboard_options, copy_dashboard_files, update_dashboard_device_list, update_dashboard_test_list, update_dashboard_testdata, upload_dashboard
from runner import AndroidBrowserRunner
from options import OptionParser, CaptureOptionParser, TestOptionParser
from device import getDevicePrefs, getDevice
from metadata import get_fennec_appinfo, get_appinfo
from products import get_product, products, BuildRetriever
from test import get_test_manifest, get_testinfo, get_test
from runtest import run_test, prepare_test, TestException
from metrics import get_standard_metrics, get_stable_frame_time, get_standard_metric_metadata
from log import logger
