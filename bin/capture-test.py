#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import optparse
import videocapture

usage = "usage: %prog [options] <capture name> <mode> <capture file>"
parser = optparse.OptionParser(usage)
options, args = parser.parse_args()
if len(args) != 3:
    parser.error("incorrect number of arguments")

(capture_name, mode, capture_file) = args

controller = videocapture.CaptureController()
controller.start_capture(capture_file, mode, capture_metadata={
    'name': capture_name})

print "Should be capturing. Press enter to stop!"
raw_input()
print "Done!"
controller.terminate_capture()

print "Converting capture..."
controller.convert_capture(None, None)
