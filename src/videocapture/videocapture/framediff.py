# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import math
import numpy
from PIL import Image
import cPickle as pickle

# Note: we consider frame differences to be the number of pixels with an rgb
# component > 5 components (out of 255) different from the previous frame.
# this probably doesn't catch all cases, but works well in the common case
# of eliminating frame differences due to "noise" in the capture
PIXEL_DIFF_THRESHOLD = 5.0

def get_framediff_imgarray(capture, framenum1, framenum2,
                           filter_low_differences=True, cropped=False):
    filter_threshold = 0
    if filter_low_differences:
        filter_threshold = PIXEL_DIFF_THRESHOLD

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

            if not skip and (px[0] >= filter_threshold or \
                                 px[1] >= filter_threshold or \
                                 px[2] >= filter_threshold):
                px[0] = 255.0
                px[1] = 0.0
                px[2] = 0.0
            else:
                px[0] = px[1] = px[2] = 0.0

    return framediff

def get_framediff_image(capture, framenum1, framenum2, cropped=False):
    framediff = get_framediff_imgarray(capture, framenum1, framenum2, cropped=cropped)
    return Image.fromarray(framediff.astype(numpy.uint8))

def get_framediff_sums(capture, filter_low_differences=True):
    filter_threshold = 0
    if filter_low_differences:
        filter_threshold = PIXEL_DIFF_THRESHOLD

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
        diffsums = [0]
        for i in range(1, capture.num_frames+1):
            frame = capture.get_frame(i, True).astype('float')
            if prevframe != None:
                framediff = abs(frame - prevframe)
                for ignored_area in ignored_areas:
                    for x in range(ignored_area[0], ignored_area[2]):
                        for y in range(ignored_area[1], ignored_area[3]):
                            framediff[x][y] = 0.0
                framediff = framediff[framediff >= filter_threshold]
                diffsums.append(len(framediff))
            prevframe = frame
        cache['diffsums'] = diffsums
        pickle.dump(cache, open(capture.cache_filename, 'w'))

    return diffsums

def image_entropy(img):
    """calculate the entropy of an image"""
    # based on: http://brainacle.com/calculating-image-entropy-with-python-how-and-why.html
    # this could be made more efficient using numpy
    histogram = img.histogram()
    histogram_length = sum(histogram)
    samples_probability = [float(h) / histogram_length for h in histogram]
    return -sum([p * math.log(p, 2) for p in samples_probability if p != 0])

def get_entropy_diffs(capture, num_samples=5):
    prev_samples = []
    entropy_diffs = [0]
    for i in range(1, capture.num_frames+1):
        frame = capture.get_frame_image(i)
        frame_entropy = image_entropy(frame)
        if prev_samples:
            entropy_diff = 0
            for prev_sample in prev_samples:
                entropy_diff += abs(frame_entropy-prev_sample)
            entropy_diff /= (1 + len(prev_samples))
            entropy_diffs.append(entropy_diff)
        prev_samples.append(frame_entropy)
        if len(prev_samples) > num_samples:
            prev_samples = prev_samples[1:]
    return entropy_diffs

def get_num_unique_frames(capture, threshold=0):
    framediff_sums = get_framediff_sums(capture)
    num_uniques = len([framediff for framediff in framediff_sums if framediff > threshold])
    if threshold > 0:
        num_uniques += 1 # first frame not included if threshold is greater than 0

def get_fps(capture, threshold=0):
    return get_num_unique_frames(capture, threshold=threshold) / capture.length

def get_stable_frame(capture, method='framediff', threshold=4096):
    if method == 'framediff':
        framediff_sums = get_framediff_sums(capture)
        for i in range(len(framediff_sums)-1, 0, -1):
            if framediff_sums[i] > threshold:
                return i+1
        return len(framediff_sums)-1
    elif method == 'entropy':
        entropy_diffs = get_entropy_diffs(capture)
        for i in range(len(entropy_diffs)-1, 0, -1):
            if abs(entropy_diffs[i]) > threshold:
                return i+1
        return len(entropy_diffs)-1

def get_stable_frame_time(capture, method='framediff', threshold = 4096):
    return get_stable_frame(capture, method=method, threshold=threshold) / float(capture.fps)
