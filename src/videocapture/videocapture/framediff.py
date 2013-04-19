# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import numpy
from PIL import Image
import cPickle as pickle

# Note: we consider frame differences to be the number of pixels with an rgb
# component > 5 components (out of 255) different from the previous frame.
# this probably doesn't catch all cases, but works well in the common case
# of eliminating frame differences due to "noise" in the HDMI capture
PIXEL_DIFF_THRESHOLD = 5.0

def get_framediff_imgarray(capture, framenum1, framenum2,
                           threshold = PIXEL_DIFF_THRESHOLD, cropped=False):
    if capture.metadata.get('ignoreAreas'):
        ignored_areas = capture.metadata['ignoreAreas']
    else:
        ignored_areas = []

    frame1 = capture.get_frame(framenum1, cropped)
    frame2 = capture.get_frame(framenum2, cropped)
    framediff = numpy.abs(frame1.astype('float') - frame2.astype('float'))
    for (y, row) in enumerate(framediff):
        for (x, px) in enumerate(row):
            skip = False
            for ignored_area in ignored_areas:
                if y >= ignored_area[1] and y < ignored_area[3] and \
                        x >= ignored_area[0] and x < ignored_area[2]:
                    print ignored_area
                    print "Skipped: %s %s" % (x, y)
                    skip = True
                    break

            if not skip and (px[0] >= threshold or \
                                 px[1] >= threshold or \
                                 px[2] >= threshold):
                px[0] = 255.0
                px[1] = 0.0
                px[2] = 0.0
            else:
                px[0] = px[1] = px[2] = 0.0

    return framediff

def get_framediff_image(capture, framenum1, framenum2, cropped=False):
    framediff = get_framediff_imgarray(capture, framenum1, framenum2, cropped=cropped)
    return Image.fromarray(framediff.astype(numpy.uint8))

def get_framediff_sums(capture, threshold = PIXEL_DIFF_THRESHOLD):
    try:
        cache = pickle.load(open(capture.cache_filename, 'r'))
    except:
        cache = {}

    if capture.metadata.get('ignoreAreas'):
        ignored_areas = capture.metadata['ignoreAreas']
    else:
        ignored_areas = []

    try:
        diffsums = cache['diffsums']
    except:
        # Frame differences
        diffsums = None
        prevframe = None
        diffsums = []
        for i in range(1, capture.num_frames+1):
            frame = capture.get_frame(i, True).astype('float')
            if prevframe != None:
                framediff = (frame - prevframe)
                for ignored_area in ignored_areas:
                    for x in range(ignored_area[0], ignored_area[2]):
                        for y in range(ignored_area[1], ignored_area[3]):
                            framediff[x][y] = 0.0
                framediff = framediff[framediff >= threshold]
                diffsums.append(len(framediff))
            prevframe = frame
        cache['diffsums'] = diffsums
        pickle.dump(cache, open(capture.cache_filename, 'w'))

    return diffsums

def get_num_unique_frames(capture):
    framediff_sums = get_framediff_sums(capture)
    return 1 + len([framediff for framediff in framediff_sums if framediff > 0])

def get_fps(capture):
    return get_num_unique_frames(capture) / capture.length

def get_stable_frame(capture, threshold = 2048):
    framediff_sums = get_framediff_sums(capture)
    for i in range(len(framediff_sums)-1, 0, -1):
        if framediff_sums[i] > threshold:
            return i+1
    return len(framediff_sums)-1

def get_stable_frame_time(capture, threshold = 2048):
    return get_stable_frame(capture, threshold) / 60.0
