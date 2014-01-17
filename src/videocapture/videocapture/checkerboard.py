# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import numpy
import square
import cPickle as pickle
from PIL import Image


def get_checkerboarding_percents(capture):
    try:
        cache = pickle.load(open(capture.cache_filename, 'r'))
    except:
        cache = {}

    try:
        percents = cache['checkerboard_percents']
    except:
        percents = []
        for i in range(1, capture.num_frames + 1):
            frame = capture.get_frame(i, type=numpy.int16)
            percent = 0.0
            checkerboard_box = square.get_biggest_square((255, 0, 255), frame)
            if checkerboard_box:
                checkerboard_size = (checkerboard_box[2] - checkerboard_box[0]) * (checkerboard_box[3] - checkerboard_box[1])
                percent = float(checkerboard_size) / (capture.dimensions[0] * capture.dimensions[1])
            percents.append(percent)
        cache['checkerboard_percents'] = percents
        pickle.dump(cache, open(capture.cache_filename, 'w'))

    return percents


def get_checkerboarding_area_duration(capture):
    percents = get_checkerboarding_percents(capture)
    total = 0
    for percent in percents:
        total += percent

    return total


def get_checkerboard_image(capture, framenum):

    frame = capture.get_frame(framenum, type=numpy.int16)
    checkerboard_box = square.get_biggest_square((255, 0, 255), frame)

    dimensions = capture.dimensions
    imgarray = 0xFF000000 * numpy.ones((dimensions[0], dimensions[1]),
                                       dtype=numpy.uint32)
    imgarray.shape = dimensions[1], dimensions[0]

    if checkerboard_box:
        imgarray[checkerboard_box[1]:checkerboard_box[3],
                 checkerboard_box[0]:checkerboard_box[2]] = 0xFF0000FF

    return Image.frombuffer('RGBA', (dimensions[0], dimensions[1]), imgarray,
                            'raw', 'RGBA', 0, 1)
