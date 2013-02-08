#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import sys
import eideticker
import mozdevice

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

    device_prefs = eideticker.getDevicePrefs(options)

    if options.debug:
        mozdevice.DeviceManagerSUT.debug = 4

    eideticker.run_test(testkey, options.devicetype, options.appname,
                        options.capture_name, device_prefs,
                        extra_prefs=extra_prefs,
                        profile_file=options.profile_file,
                        checkerboard_log_file=options.checkerboard_log_file,
                        no_capture=options.no_capture,
                        capture_file=options.capture_file)

main()
