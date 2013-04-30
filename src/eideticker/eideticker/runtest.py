from device import getDevice
from test import get_test, TestException
import datetime
import json
import manifestparser
import os
import urllib
import videocapture

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CAPTURE_DIR = os.path.abspath(os.path.join(SRC_DIR, "../captures"))
TEST_DIR = os.path.abspath(os.path.join(SRC_DIR, "tests"))
GECKO_PROFILER_ADDON_DIR = os.path.join(SRC_DIR, "../src/GeckoProfilerAddon")
EIDETICKER_TEMP_DIR = "/tmp/eideticker"

def run_test(testkey, capture_device, appname, capture_name,
             device_prefs, extra_prefs={}, test_type=None, profile_file=None,
             request_log_file=None, checkerboard_log_file=None,
             capture_area=None, no_capture=False, capture_file=None):
    manifest = manifestparser.TestManifest(manifests=[os.path.join(
                TEST_DIR, 'manifest.ini')])

    # sanity check... does the test match a known test key?
    testkeys = [test["key"] for test in manifest.active_tests()]
    if testkey not in testkeys:
        raise TestException("No tests matching '%s' (options: %s)" % (testkey, ", ".join(testkeys)))

    testinfo = [test for test in manifest.active_tests() if test['key'] == testkey][0]
    print "Testinfo: %s" % testinfo

    if device_prefs['devicetype'] == 'android' and not appname and \
            not testinfo.get('appname'):
        raise TestException("Must specify an appname (with --app-name) on Android "
                            "when not spec'd by test")

    if not os.path.exists(EIDETICKER_TEMP_DIR):
        os.mkdir(EIDETICKER_TEMP_DIR)
    if not os.path.isdir(EIDETICKER_TEMP_DIR):
        raise TestException("Could not open eideticker temporary directory")

    appname = testinfo.get('appname') or appname

    capture_name = capture_name
    if not capture_name:
        capture_name = testinfo['shortDesc']
    if not capture_file and not no_capture:
        capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                    datetime.datetime.now().isoformat())

    # Create a device object to interface with the phone
    device = getDevice(**device_prefs)

    capture_metadata = {
        'name': capture_name,
        'testpath': testinfo['relpath'],
        'app': appname,
        'device': device.model,
        'devicetype': device_prefs['devicetype'],
        'startupTest': testinfo['type'] == 'startup'
        }

    # note: url params for startup tests currently not supported
    if testinfo.get('urlOverride'):
        testpath_rel = testinfo['urlOverride']
    else:
        testpath_rel = testinfo['relpath']
    if testinfo.get('urlParams'):
        testpath_rel += "?%s" % urllib.quote_plus(testinfo.get('urlParams'))

    capture_controller = videocapture.CaptureController(capture_device, capture_area,
                                                        custom_tempdir=EIDETICKER_TEMP_DIR)

    testtype = test_type or testinfo['type']

    # get actions for web tests
    actions = None
    if testtype == 'web':
        actions_path = os.path.join(testinfo['here'], "actions.json")
        try:
            with open(actions_path) as f:
                actions = json.loads(f.read())
        except EnvironmentError:
            raise TestException("Couldn't open actions file '%s'" % actions_path)

    test = get_test(devicetype = device_prefs['devicetype'],
                    testtype = testtype,
                    testpath = testinfo['path'],
                    testpath_rel = testpath_rel, device = device,
                    actions = actions, extra_prefs = extra_prefs,
                    capture_file = capture_file,
                    capture_controller = capture_controller,
                    capture_metadata = capture_metadata,
                    capture_timeout = int(testinfo['captureTimeout']),
                    appname = appname,
                    activity = testinfo.get('activity'),
                    intent = testinfo.get('intent'),
                    preinitialize_user_profile = int(testinfo.get('preInitializeProfile', 0)),
                    open_url_after_launch = bool(testinfo.get('openURLAfterLaunch')),
                    checkerboard_log_file = checkerboard_log_file,
                    profile_file = profile_file,
                    gecko_profiler_addon_dir=GECKO_PROFILER_ADDON_DIR,
                    docroot = TEST_DIR,
                    tempdir = EIDETICKER_TEMP_DIR)

    test.run()
    test.cleanup()

    if capture_file:
        try:
            capture_controller.convert_capture(test.start_frame, test.end_frame)
        except KeyboardInterrupt:
            raise TestException("Aborting because of keyboard interrupt")
