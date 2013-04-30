# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import numpy

# how far outside the bounds of the square a scanline can be and still be
# considered part of the frame
X_TOLERANCE_MIN = 192 + 1 # ignore frame counter on left for fennec
X_TOLERANCE_MAX = 1

def get_squares(rgb, imgarray, x_tolerance_min=X_TOLERANCE_MIN,
                x_tolerance_max=X_TOLERANCE_MAX,
                handle_multiple_scanlines=False):
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
        where = numpy.nonzero(row)[0]
        if len(where):
            if handle_multiple_scanlines:
                scanlines = []
                current_scanline = [where[0], where[0]]
                last = where[0]
                for pos in where[1:]:
                    if (pos - last) > 2:
                        if (current_scanline[1] - current_scanline[0]) > 0:
                            scanlines.append(current_scanline)
                        current_scanline = [pos, pos]
                    else:
                        current_scanline[1] = pos
                    last = pos
                if current_scanline not in scanlines and (current_scanline[1]-current_scanline[0]) > 0:
                    scanlines.append(current_scanline)
                if len(scanlines):
                    scanline = max(scanlines, key=lambda s: s[1]-s[0])
            else:
                scanline = [where[0], where[-1]]

        if scanline:
            found_existing = False
            for square in squares:

                if square[3] == (y-1) and abs(square[0] - scanline[0]) < x_tolerance_min and \
                        abs(square[2] - scanline[1]) < x_tolerance_max:
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

def get_area(square):
    return (square[2]-square[0])*(square[3]-square[1])

def get_biggest_square(rgb, imgarray, x_tolerance_min=X_TOLERANCE_MIN,
                       x_tolerance_max=X_TOLERANCE_MAX,
                       handle_multiple_scanlines=False):
    '''Get the biggest contiguous square region within a certain threshold
       of an RGB color inside an image'''
    squares = get_squares(rgb, imgarray, x_tolerance_min=x_tolerance_min,
                          x_tolerance_max=x_tolerance_max,
                          handle_multiple_scanlines=handle_multiple_scanlines)

    if squares:
        biggest_square = max(squares, key=get_area)
        if get_area(biggest_square) > 0:
            return biggest_square

    return None
