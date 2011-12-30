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
            lines = get_checkerboard_lines(capture, i)
            percents.append(float((lines == 1).sum()) / len(lines))
        cache['checkerboard_percents'] = percents
        pickle.dump(cache, open(capture.cache_filename, 'w'))


    return percents

def get_checkerboard_image(capture, framenum):
    lines = get_checkerboard_lines(capture, framenum)
    size = capture.capture_area.size
    imgarray = numpy.zeros((size[0], size[1]),
                           dtype=numpy.uint32)
    imgarray.shape = size[1],size[0]
    for (y, line) in enumerate(lines):
        imgarray[y:y+1,0:size[0]] = 0xFF000000 + line*0xFF0000FF
    return Image.frombuffer('RGBA',(size[0],size[1]),imgarray,'raw','RGBA',0,1)

def get_checkerboard_lines(capture, framenum):
    imgarray = capture.get_frame(framenum, True, True).astype('float')
    lines = numpy.zeros(shape=capture.capture_area.size[1])
    for (y, row) in enumerate(imgarray):
        runs = []
        currentrun = None
        for pixval in [int(pixval) for pixval in row]:
            if currentrun:
                if abs(currentrun[0] - pixval) < 5:
                    currentrun[1] += 1
                #elif currentrun[1] > 5:
                else:
                    runs.append(currentrun)
                    currentrun = [pixval, 1]
            else:
                currentrun = [pixval, 1]
        lastrun = None
        numchecks = 0
        for run in runs:
            if run[1] > 1:
                if lastrun:
                    # if length is ~ the same and the colours are different,
                    # assume a check pattern
                    if abs(lastrun[1]-run[1]) < 2 and abs(lastrun[0]-run[0]) > 10:
                       numchecks+=1
                lastrun = run

        # the magical "proportion" of # checks to line length is between 0.05 and 0.09
        # (FIXME: may need to refine this later ... although really we should probably
        # just modify Gecko to just show the background colour when it's checkerboarding
        # ... all these heuristics are complicated and ridiculous)
        percent = float(numchecks)/len(row)
        if percent >= 0.05 and percent <= 0.09:
            lines[y] = 1
        else:
            lines[y] = 0

    return lines


