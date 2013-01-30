#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import os
import sys
import urllib
import videocapture
import eideticker
import manifestparser
import mozdevice

BINDIR = os.path.dirname(__file__)
CAPTURE_DIR = os.path.abspath(os.path.join(BINDIR, "../captures"))
TEST_DIR = os.path.abspath(os.path.join(BINDIR, "../src/tests"))
EIDETICKER_TEMP_DIR = "/tmp/eideticker"
GECKO_PROFILER_ADDON_DIR = os.path.join(os.path.dirname(__file__), "../src/GeckoProfilerAddon")

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <test key>"
    parser = eideticker.OptionParser(usage=usage)
    parser.add_option("--url-params", action="store",
                      dest="url_params",
                      help="additional url parameters for test")
    parser.add_option("--name", action="store",
                      type = "string", dest = "capture_name",
                      help = "name to give capture")
    parser.add_option("--capture-file", action="store",
                      type = "string", dest = "capture_file",
                      help = "name to give to capture file")
    parser.add_option("--no-capture", action="store_true",
                      dest = "no_capture",
                      help = "run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--app-name", action="store",
                      type="string", dest="appname",
                      help="Specify an application name (android only)")
    parser.add_option("--checkerboard-log-file", action="store",
                      type = "string", dest = "checkerboard_log_file",
                      help = "name to give checkerboarding stats file (fennec only)")
    parser.add_option("--extra-prefs", action="store", dest="extra_prefs",
                      default="{}",
                      help="Extra profile preference for Firefox browsers. " \
                          "Must be passed in as a JSON dictionary")
    parser.add_option("--profile-file", action="store",
                      type="string", dest = "profile_file",
                      help="Collect a performance profile using the built in "
                      "profiler (fennec only).")
    parser.add_option("--debug", action="store_true",
                      dest="debug", help="show verbose debugging information")

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("You must specify (only) a test key")
        sys.exit(1)
    testkey = args[0]

    try:
        extra_prefs = json.loads(options.extra_prefs)
    except ValueError:
        parser.error("Error processing extra preferences: not valid JSON!")
        raise

    manifest = manifestparser.TestManifest(manifests=[os.path.join(
                BINDIR, '../src/tests/manifest.ini')])

    # sanity check... does the test match a known test key?
    testkeys = [test["key"] for test in manifest.active_tests()]
    if testkey not in testkeys:
        print "ERROR: No tests matching '%s' (options: %s)" % (testkey, ", ".join(testkeys))
        sys.exit(1)

    testinfo = [test for test in manifest.active_tests() if test['key'] == testkey][0]
    print "Testinfo: %s" % testinfo

    if options.devicetype == 'android' and not options.appname and \
            not testinfo.get('appname'):
        print "ERROR: Must specify an appname (with --app-name) on Android " \
                     "when not spec'd by test"
        sys.exit(1)

    if not os.path.exists(EIDETICKER_TEMP_DIR):
        os.mkdir(EIDETICKER_TEMP_DIR)
    if not os.path.isdir(EIDETICKER_TEMP_DIR):
        print "Could not open eideticker temporary directory"
        sys.exit(1)

    appname = testinfo.get('appname') or options.appname

    capture_name = options.capture_name
    if not capture_name:
        capture_name = testinfo['shortDesc']
    capture_file = options.capture_file
    if not capture_file and not options.no_capture:
        capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                         datetime.datetime.now().isoformat())

    # Create a device object to interface with the phone
    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)
    if options.debug:
        mozdevice.DeviceManagerSUT.debug = 4

    capture_metadata = {
        'name': capture_name,
        'testpath': testinfo['relpath'],
        'app': appname,
        'device': device.model,
        'devicetype': options.devicetype,
        'startupTest': testinfo['type'] == 'startup'
        }

    # note: url params for startup tests currently not supported
    if testinfo.get('urlOverride'):
        testpath_rel = testinfo['urlOverride']
    else:
        testpath_rel = testinfo['relpath']
    if testinfo.get('urlParams'):
        testpath_rel += "?%s" % urllib.quote_plus(testinfo.get('urlParams'))

    capture_controller = videocapture.CaptureController(custom_tempdir=EIDETICKER_TEMP_DIR)

    testtype = testinfo['type']

    # get actions for web tests
    actions = None
    if testtype == 'web':
        actions_path = os.path.join(testinfo['here'], "actions.json")
        try:
            with open(actions_path) as f:
                actions = json.loads(f.read())
        except EnvironmentError:
            print "Couldn't open actions file '%s'" % actions_path
            sys.exit(1)

    test = eideticker.get_test(devicetype = options.devicetype, testtype = testinfo['type'],
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
                               checkerboard_log_file = options.checkerboard_log_file,
                               profile_file = options.profile_file,
                               gecko_profiler_addon_dir=GECKO_PROFILER_ADDON_DIR,
                               docroot = TEST_DIR,
                               tempdir = EIDETICKER_TEMP_DIR)
    test.run()
    test.cleanup()

    if capture_file:
        print "Converting capture..."
        try:
            capture_controller.convert_capture(test.start_frame, test.end_frame)
        except KeyboardInterrupt:
            print "Aborting"
            sys.exit(1)

main()
