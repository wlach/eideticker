from device import getDevice, getDevicePrefs
from test import get_test, get_testinfo, TestException, EIDETICKER_TEMP_DIR, SRC_DIR
import datetime
import json
import mozlog
import os
import videocapture
from marionette.errors import MarionetteException

CAPTURE_DIR = os.path.abspath(os.path.join(SRC_DIR, "../captures"))

logger = mozlog.getLogger('Eideticker')

def _connect_wifi(device, options):
    # we catch when the user requests synchronized time but doesn't
    # provide a wifi settings file when parsing options, but no
    # such luck if the test itself requires wifi; so throw an exception
    # in that case
    if not options.wifi_settings_file:
        raise TestException("WIFI required for this test but no settings "
                            "file (-w) provided!")
    wifi_settings = json.loads(open(options.wifi_settings_file).read())
    device.connectWIFI(wifi_settings)


def prepare_test(testkey, options):
    device_prefs = getDevicePrefs(options)
    device = getDevice(**device_prefs)

    # prepare test logic -- currently only done on b2g
    if device_prefs['devicetype'] == 'b2g':
        testinfo = get_testinfo(testkey)

        # HACK: we need to setup marionette here so we can instantiate a
        # b2gpopulate instance inside the device object (even though we
        # wind up deleting the same marionette instance in just a moment...
        # FIXME: find some less convoluted way of getting the same behaviour)
        device.setupMarionette()

        test = get_test(testinfo, options, device)

        # reset B2G device's state for test
        logger.info("Stopping B2G and cleaning up...")
        device.stopB2G()
        device.cleanup()

        if hasattr(test, 'populate_databases'):
            logger.info("Populating database...")
            test.populate_databases()

        device.startB2G()

        if test.requires_wifi:
            _connect_wifi(device, options)

        if hasattr(test, 'prepare_app'):
            logger.info("Doing initial setup on app for test")
            test.prepare_app()
    else:
        device.cleanup()

def run_test(testkey, options, capture_filename=None, profile_filename=None,
             capture_name=None):
    testinfo = get_testinfo(testkey)

    if options.devicetype == 'android' and not options.appname and \
            not testinfo.get('appname'):
        raise TestException("Must specify an appname (with --app-name) on "
                            "Android when not spec'd by test")

    if not os.path.exists(EIDETICKER_TEMP_DIR):
        os.mkdir(EIDETICKER_TEMP_DIR)
    if not os.path.isdir(EIDETICKER_TEMP_DIR):
        raise TestException("Could not open eideticker temporary directory")

    device_prefs = getDevicePrefs(options)
    device = getDevice(**device_prefs)

    appname = testinfo.get('appname') or options.appname

    capture_metadata = {
        'name': capture_name or testinfo['shortDesc'],
        'testpath': testinfo['relpath'],
        'app': appname,
        'device': device.model,
        'devicetype': options.devicetype,
        'startupTest': testinfo['type'] == 'startup'}

    # something of a hack. if profiling is enabled, carve off an area to
    # ignore in the capture
    if profile_filename:
        capture_metadata['ignoreAreas'] = [[0, 0, 3 * 64, 3]]

    if options.capture:
        if not capture_filename:
            capture_filename = os.path.join(CAPTURE_DIR,
                                            "capture-%s.zip" %
                                            datetime.datetime.now().isoformat())
        capture_controller = videocapture.CaptureController(capture_filename, options,
                                                            capture_metadata=capture_metadata,
                                                            custom_tempdir=EIDETICKER_TEMP_DIR)

    elif not options.capture:
        capture_controller = None

    test = get_test(testinfo, options, device,
                    capture_controller=capture_controller,
                    profile_filename=profile_filename)

    if device_prefs['devicetype'] == 'b2g':
        device.restartB2G()

        if options.sync_time or test.requires_wifi:
            _connect_wifi(device, options)

    elif device_prefs['devicetype'] == 'android':
        device.stopApplication(appname)

    # synchronize time unless instructed not to
    if options.sync_time:
        device.synchronizeTime()

    try:
        test.run()
    except MarionetteException, e:
        # there are many ways a test could throw a marionette exception, try
        # to catch them all here (we'll consider them non-fatal, so we'll retry
        # a few times before giving up)
        print "Marionette exception caught running test:\n%s" % e
        raise TestException("Marionette exception caught running test: %s" % e.msg,
                            can_retry=True)

    test.cleanup()

    if options.capture:
        try:
            capture_controller.convert_capture(
                test.start_frame, test.end_frame)
        except KeyboardInterrupt:
            raise TestException("Aborting because of keyboard interrupt")

    return test.testlog
