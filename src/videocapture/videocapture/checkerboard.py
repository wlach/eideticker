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
import square

def get_checkerboarding_percents(capture):
    try:
        cache = pickle.load(open(capture.cache_filename, 'r'))
    except:
        cache = {}

    try:
        percents = cache['checkerboard_percents']
    except:
        percents = []
        for i in range(1, capture.num_frames+1):
            frame = capture.get_frame(i, True, False, numpy.int16)
            percent = 0.0
            checkerboard_box = square.get_biggest_square((255,0,255), frame)
            if checkerboard_box:
                checkerboard_size = (checkerboard_box[2]-checkerboard_box[0])*(checkerboard_box[3]-checkerboard_box[1])
                percent = float(checkerboard_size) / (capture.capture_area.size[0]*capture.capture_area.size[1])
            percents.append(percent)
        cache['checkerboard_percents'] = percents
        pickle.dump(cache, open(capture.cache_filename, 'w'))

    return percents

def get_checkerboard_image(capture, framenum):

    frame = capture.get_frame(framenum, True, False, numpy.int16)
    checkerboard_box = square.get_biggest_square((255,0,255), frame)

    size = capture.capture_area.size
    imgarray = 0xFF000000 * numpy.ones((size[0], size[1]), dtype=numpy.uint32)
    imgarray.shape = size[1],size[0]

    if checkerboard_box:
        imgarray[checkerboard_box[1]:checkerboard_box[3],checkerboard_box[0]:checkerboard_box[2]] = 0xFF0000FF

    return Image.frombuffer('RGBA',(size[0],size[1]),imgarray,'raw','RGBA',0,1)
