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
# Portions created by the Initial Developer are Copyright (C) 2012
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

import numpy

def get_squares(rgb, imgarray):
    ''' Get contiguous square regions within a certain threshold of an RGB
        color inside an image '''
    squares = []

    # An array representing whether each pixel's RGB components are within
    # the box's threshold
    mask = numpy.array(rgb, dtype=numpy.int16)
    threshold = imgarray.dtype.type(30)

    thresharray = numpy.abs(imgarray-mask)
    thresharray = ((thresharray[:,:,0]+thresharray[:,:,1]+thresharray[:,:,2]) < threshold)
    for y, row in enumerate(thresharray):
        scanline = None
        # assumption: there aren't several boxes on this same line
        where = numpy.nonzero(row)[0]
        if len(where):
            scanline = [where[0], where[-1]]

        if scanline:
            found_existing = False
            for square in squares:
                if abs(square[0] - scanline[0]) < 1 and abs(square[2] - scanline[1]) < 1:
                    square[3] = y
                    found_existing = True
            if not found_existing:
               squares.append([int(scanline[0]), y, int(scanline[1]), y])

    return squares

def get_biggest_square(rgb, imgarray):
    '''Get the biggest contiguous square region within a certain threshold
       of an RGB color inside an image'''
    squares = get_squares(rgb, imgarray)

    if squares:
        return max(squares, key=lambda box: (box[2]-box[0])*(box[3]-box[1]))
    else:
        return None
