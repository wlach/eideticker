from device import getDevice
from test import get_test, get_testinfo, TestException, SRC_DIR, TEST_DIR
import datetime
import json
import os
import urllib
import videocapture
from log import logger

CAPTURE_DIR = os.path.abspath(os.path.join(SRC_DIR, "../captures"))
GECKO_PROFILER_ADDON_DIR = os.path.join(SRC_DIR, "../src/GeckoProfilerAddon")
EIDETICKER_TEMP_DIR = "/tmp/eideticker"


def prepare_test(testkey, device_prefs, wifi_settings_file=None):
    # prepare test logic -- currently only done on b2g
    if device_prefs['devicetype'] == 'b2g':
        testinfo = get_testinfo(testkey)

        device = getDevice(**device_prefs)
        # HACK: we need to setup marionette here so we can instantiate a
        # b2gpopulate instance inside the device object (even though we
        # wind up deleting the same marionette instance in just a moment...
        # FIXME: find some less convoluted way of getting the same behaviour)
        device.setupMarionette()

        test = get_test(testinfo, devicetype=device_prefs['devicetype'],
                        device=device, appname=testinfo.get('appname'))

        # reset B2G device's state for test
        logger.info("Stopping B2G and cleaning up...")
        device.stopB2G()
        device.cleanup()

        if hasattr(test, 'populate_databases'):
            logger.info("Populating database...")
            test.populate_databases()

        device.startB2G()

        if test.requires_wifi:
            if not wifi_settings_file:
                raise Exception("WIFI required for this test but no settings "
                                "file (-w) provided!")
            wifi_settings = json.loads(open(wifi_settings_file).read())
            device.connectWIFI(wifi_settings)

        if hasattr(test, 'prepare_app'):
            logger.info("Doing initial setup on app for test")
            test.prepare_app()


def run_test(testkey, capture_device, appname, capture_name,
             device_prefs, extra_prefs={}, test_type=None, profile_file=None,
             wifi_settings_file=None, request_log_file=None,
             actions_log_file=None, log_checkerboard_stats=False,
             extra_env_vars={}, capture_area=None, camera_settings_file=None,
             capture=True, capture_file=None, sync_time=True, fps=None,
             use_vpxenc=False):
    testinfo = get_testinfo(testkey)

    if device_prefs['devicetype'] == 'android' and not appname and \
            not testinfo.get('appname'):
        raise TestException("Must specify an appname (with --app-name) on "
                            "Android when not spec'd by test")

    if not os.path.exists(EIDETICKER_TEMP_DIR):
        os.mkdir(EIDETICKER_TEMP_DIR)
    if not os.path.isdir(EIDETICKER_TEMP_DIR):
        raise TestException("Could not open eideticker temporary directory")

    appname = testinfo.get('appname') or appname

    capture_name = capture_name
    if not capture_name:
        capture_name = testinfo['shortDesc']
    if capture and not capture_file:
        capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                    datetime.datetime.now().isoformat())
    elif not capture:
        capture_file = None

    device = getDevice(**device_prefs)

    capture_metadata = {
        'name': capture_name,
        'testpath': testinfo['relpath'],
        'app': appname,
        'device': device.model,
        'devicetype': device_prefs['devicetype'],
        'startupTest': testinfo['type'] == 'startup'}

    # note: url params for startup tests currently not supported
    if testinfo.get('urlOverride'):
        testpath_rel = testinfo['urlOverride']
    else:
        testpath_rel = testinfo['relpath']
    if testinfo.get('urlParams'):
        testpath_rel += "?%s" % urllib.quote_plus(testinfo.get('urlParams'))

    capture_controller = videocapture.CaptureController(
        capture_device, capture_area, custom_tempdir=EIDETICKER_TEMP_DIR,
        fps=fps, use_vpxenc=use_vpxenc,
        camera_settings_file=camera_settings_file)

    testtype = test_type or testinfo['type']

    # get actions for web tests
    actions = None
    if testtype == 'web':
        actions_path = os.path.join(testinfo['here'], "actions.json")
        try:
            with open(actions_path) as f:
                actions = json.loads(f.read())
        except EnvironmentError:
            raise TestException("Couldn't open actions file '%s'" %
                                actions_path)

    test = get_test(testinfo, devicetype=device_prefs['devicetype'],
                    testtype=testtype,
                    testpath_rel=testpath_rel, device=device,
                    actions=actions, extra_prefs=extra_prefs,
                    extra_env_vars=extra_env_vars,
                    capture_file=capture_file,
                    capture_controller=capture_controller,
                    capture_metadata=capture_metadata,
                    appname=appname,
                    request_log_file=request_log_file,
                    actions_log_file=actions_log_file,
                    log_checkerboard_stats=log_checkerboard_stats,
                    profile_file=profile_file,
                    gecko_profiler_addon_dir=GECKO_PROFILER_ADDON_DIR,
                    docroot=TEST_DIR,
                    tempdir=EIDETICKER_TEMP_DIR)

    if device_prefs['devicetype'] == 'b2g':
        device.restartB2G()

        if sync_time or test.requires_wifi:
            # we catch when the user requests synchronized time but doesn't
            # provide a wifi settings file when parsing options, but no
            # such luck if the test itself requires wifi; so throw an exception
            # in that case
            if not wifi_settings_file:
                raise Exception("WIFI required for this test but no settings "
                                "file (-w) provided!")
            wifi_settings = json.loads(open(wifi_settings_file).read())
            device.connectWIFI(wifi_settings)
    elif device_prefs['devicetype'] == 'android':
        num_tries = 0
        max_tries = 5
        while device.processExist(appname):
            if num_tries > max_tries:
                raise Exception("Couldn't successfully kill %s after %s "
                                "tries" % (appname, max_tries))
            device.killProcess(appname)
            num_tries+=1

    # synchronize time unless instructed not to
    if sync_time:
        device.synchronizeTime()

    test.run()
    test.cleanup()

    if capture_file:
        try:
            capture_controller.convert_capture(
                test.start_frame, test.end_frame)
        except KeyboardInterrupt:
            raise TestException("Aborting because of keyboard interrupt")

    return test.testlog
