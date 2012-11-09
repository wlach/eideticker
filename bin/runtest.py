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

BINDIR = os.path.dirname(__file__)
CAPTURE_DIR = os.path.abspath(os.path.join(BINDIR, "../captures"))
TEST_DIR = os.path.abspath(os.path.join(BINDIR, "../src/tests"))
EIDETICKER_TEMP_DIR = "/tmp/eideticker"
GECKO_PROFILER_ADDON_DIR = os.path.join(os.path.dirname(__file__), "../src/GeckoProfilerAddon")

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] [appname] <test path>"
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
    parser.add_option("--checkerboard-log-file", action="store",
                      type = "string", dest = "checkerboard_log_file",
                      help = "name to give checkerboarding stats file")
    parser.add_option("--startup-test", action="store_true",
                      dest="startup_test",
                      help="do a startup test: full capture, no actions")
    parser.add_option("--extra-prefs", action="store", dest="extra_prefs",
                      default="{}",
                      help="Extra profile preference for Firefox browsers. " \
                          "Must be passed in as a JSON dictionary")
    parser.add_option("--profile-file", action="store",
                      type="string", dest = "profile_file",
                      help="Collect a performance profile using the built in profiler.")

    options, args = parser.parse_args()
    testpath, appname = None, None
    if options.devicetype == 'b2g':
        if len(args) != 1:
            parser.error("You must specify (only) a test path on b2g")
            sys.exit(1)
        testpath = args[0]
    else:
        if len(args) != 2:
            parser.error("You must specify (only) an application name "
                         "(e.g. org.mozilla.fennec) and a test path")
            sys.exit(1)

        (appname, testpath) = args

    try:
        extra_prefs = json.loads(options.extra_prefs)
    except ValueError:
        parser.error("Error processing extra preferences: not valid JSON!")
        raise

    # Tests must be in src/tests/... unless it is a startup test and the
    # path is about:home (indicating we want to measure startup to the
    # home screen)
    if options.startup_test and testpath == "about:home":
        testpath_rel = testpath
        capture_timeout = 5 # 5 seconds to wait for fennec to start after it claims to have started
    else:
        capture_timeout = None
        try:
            testpath_rel = os.path.abspath(testpath).split(TEST_DIR)[1][1:]
        except:
            print "Test must be relative to %s" % TEST_DIR
            sys.exit(1)

    if not os.path.exists(EIDETICKER_TEMP_DIR):
        os.mkdir(EIDETICKER_TEMP_DIR)
    if not os.path.isdir(EIDETICKER_TEMP_DIR):
        print "Could not open eideticker temporary directory"
        sys.exit(1)

    capture_name = options.capture_name
    if not capture_name:
        capture_name = testpath_rel
    capture_file = options.capture_file
    if not capture_file and not options.no_capture:
        capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                         datetime.datetime.now().isoformat())

    # Create a device object to interface with the phone
    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)

    print "Creating webserver..."
    capture_metadata = {
        'name': capture_name,
        'testpath': testpath_rel,
        'app': appname,
        'device': device.model,
        'devicetype': options.devicetype,
        'startupTest': options.startup_test
        }

    # note: url params for startup tests currently not supported
    if options.url_params:
        testpath_rel += "?%s" % urllib.quote_plus(options.url_params)

    capture_controller = videocapture.CaptureController(custom_tempdir=EIDETICKER_TEMP_DIR)

    if options.startup_test:
        testtype = 'startup'
    elif options.devicetype == 'b2g' and testpath.endswith('.py'):
        testtype = 'b2g'
    else:
        testtype = 'web'

    # get actions for web tests
    actions = None
    if testtype == 'web':
        actions_path = os.path.join(os.path.dirname(testpath), "actions.json")
        try:
            with open(actions_path) as f:
                actions = json.loads(f.read())
        except EnvironmentError:
            print "Couldn't open actions file '%s'" % actions_path
            sys.exit(1)

    test = eideticker.get_test(devicetype = options.devicetype, testtype = testtype,
                               testpath = testpath,
                               testpath_rel = testpath_rel, device = device,
                               actions = actions, extra_prefs = extra_prefs,
                               capture_file = capture_file,
                               capture_controller = capture_controller,
                               capture_metadata = capture_metadata,
                               capture_timeout = capture_timeout,
                               appname = appname,
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
