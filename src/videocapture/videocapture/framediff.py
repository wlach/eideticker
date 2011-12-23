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

from capture import *
import numpy

def get_framediff_image(capture, framenum1, framenum2, cropped=False):
    frame1 = capture.get_frame(framenum1, cropped)
    frame2 = capture.get_frame(framenum2, cropped)
    framediff = numpy.abs(frame1.astype('float') - frame2.astype('float'))
    return Image.fromarray(framediff.astype(numpy.uint8))

def get_framediff_sums(capture):
    try:
        cache = pickle.load(open(capture.cache_filename, 'r'))
    except:
        cache = {}

    try:
        diffsums = cache['diffsums']
    except:
        # Frame differences
        diffsums = None
        prevframe = None
        diffsums = []
        for i in range(capture.start_frame, capture.end_frame):
            frame = capture.get_frame(i, True).astype('float')
            if prevframe != None:
                diffsums.append(numpy.linalg.norm(frame - prevframe))
            prevframe = frame
        cache['diffsums'] = diffsums
        pickle.dump(cache, open(capture.cache_filename, 'w'))

    return diffsums
