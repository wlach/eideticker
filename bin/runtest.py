#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import sys
import eideticker


def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <test key>"
    parser = eideticker.TestOptionParser(usage=usage)
    parser.add_option("--url-params", action="store",
                      dest="url_params",
                      help="additional url parameters for test")
    parser.add_option("--name", action="store",
                      type="string", dest="capture_name",
                      help="name to give capture")
    parser.add_option("--capture-file", action="store",
                      type="string", dest="capture_file",
                      help="name to give to capture file")
    parser.add_option("--no-capture", action="store_true",
                      dest="no_capture",
                      help="run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--app-name", action="store",
                      type="string", dest="appname",
                      help="Specify an application name (android only)")
    parser.add_option("--test-type", action="store", type="string",
                      dest="test_type", help="override test type")
    parser.add_option("--checkerboard-log-file", action="store",
                      type="string", dest="checkerboard_log_file",
                      help="name to give checkerboarding stats file (fennec "
                      "only)")
    parser.add_option("--profile-file", action="store",
                      type="string", dest="profile_file",
                      help="Collect a performance profile using the built in "
                      "profiler (fennec only).")
    parser.add_option("--request-log-file", action="store",
                      type="string", dest="request_log_file",
                      help="Collect a log of HTTP requests during test")
    parser.add_option("--actions-log-file", action="store",
                      type="string", dest="actions_log_file",
                      help="Collect a log of actions requests during test")

    options, args = parser.parse_args()

    parser.validate_options(options)

    if len(args) != 1:
        parser.error("You must specify (only) a test key")
        sys.exit(1)
    testkey = args[0]

    capture_area = None
    if options.capture_area:
        # we validated this previously...
        capture_area = json.loads(options.capture_area)
    device_prefs = eideticker.getDevicePrefs(options)

    eideticker.run_test(testkey, options.capture_device,
                        options.appname,
                        options.capture_name, device_prefs,
                        extra_prefs=options.extra_prefs,
                        extra_env_vars=options.extra_env_vars,
                        test_type=options.test_type,
                        profile_file=options.profile_file,
                        request_log_file=options.request_log_file,
                        actions_log_file=options.actions_log_file,
                        checkerboard_log_file=options.checkerboard_log_file,
                        no_capture=options.no_capture,
                        capture_area=capture_area,
                        capture_file=options.capture_file,
                        sync_time=options.sync_time)

main()
