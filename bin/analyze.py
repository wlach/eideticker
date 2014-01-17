#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import optparse
import videocapture

usage = "usage: %prog [options] <capture file>"
parser = optparse.OptionParser(usage)
options, args = parser.parse_args()
if len(args) != 1:
    parser.error("incorrect number of arguments")

capture = videocapture.Capture(args[0])
(uniques, processed) = videocapture.get_unique_frames(
    capture, thresehold=25000)

print "Unique frames: %s/%s" % (uniques, processed)
