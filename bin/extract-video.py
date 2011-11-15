#!/usr/bin/env python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Eideticker.
#
# The Initial Developer of the Original Code is
# Mozilla foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   William Lachance <wlachance@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import optparse
import os
import subprocess
import sys
import tempfile
import videocapture

usage = "usage: %prog [options] <capture file> <output movie>"
parser = optparse.OptionParser(usage)
options, args = parser.parse_args()

if len(args) <> 2:
    parser.error("incorrect number of arguments")

capture_file = args[0]
output_file = args[1]

extension = os.path.splitext(output_file)[1]
capture = videocapture.Capture(args[0])

if extension == ".avi":
    with open(output_file, 'w') as f:
        capture.write_video(f)
elif extension == ".webm":
    with tempfile.NamedTemporaryFile() as tf:
        capture.write_video(tf)
        if subprocess.call("ffmpeg -i %s -acodec libvorbis -ac 2 -ab 96k "
                           "-ar 44100 -b 345k %s" % (tf.name, output_file),
                           shell=True) != 0:
            print >> sys.stderr, "ERROR: Couldn't write webm file"
else:
    print >> sys.stderr, "ERROR: Extension '%s' not recognized! Try avi or webm." % extension



