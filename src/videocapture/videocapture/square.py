# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import numpy

# how far outside the bounds of the square a scanline can be and still be
# considered part of the frame
X_TOLERANCE_MIN = 192 + 1 # ignore frame counter on left for fennec
X_TOLERANCE_MAX = 1

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
                if abs(square[0] - scanline[0]) < X_TOLERANCE_MIN and \
                        abs(square[2] - scanline[1]) < X_TOLERANCE_MAX:
                    square[3] = y
                    found_existing = True
                    # expand the square if the scanline is bigger
                    if square[0] > scanline[0]:
                        square[0] = scanline[0]
                    if square[2] < scanline[1]:
                        square[2] = scanline[1]

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
