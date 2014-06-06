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
    parser.add_option("--app-name", action="store",
                      type="string", dest="appname",
                      help="Specify an application name (android only)")
    parser.add_option("--test-type", action="store", type="string",
                      dest="test_type", help="override test type")
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

    if len(args) != 1:
        parser.error("You must specify (only) a test key")
        sys.exit(1)
    testkey = args[0]


    if options.prepare_test:
        eideticker.prepare_test(testkey, options)

    testlog = eideticker.run_test(testkey, options,
                                  capture_filename=options.capture_file,
                                  profile_filename=options.profile_file)

    # save logs if applicable
    if options.request_log_file:
        open(options.request_log_file, 'w').write(json.dumps(testlog.http_request_log))
    if options.actions_log_file:
        open(options.actions_log_file, 'w').write(json.dumps(testlog.actions))

main()
