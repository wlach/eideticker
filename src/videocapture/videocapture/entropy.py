from itertools import repeat
from scipy import ndimage
import cPickle as pickle
import math
import multiprocessing
import numpy

DEFAULT_POOL_SIZE=8

def _get_frame_entropy((i, capture, sobelized)):
    frame = capture.get_frame(i, True).astype('float')
    if sobelized:
        frame = ndimage.median_filter(frame, 3)

        dx = ndimage.sobel(frame, 0)  # horizontal derivative
        dy = ndimage.sobel(frame, 1)  # vertical derivative
        frame = numpy.hypot(dx, dy)  # magnitude
        frame *= 255.0 / numpy.max(frame)  # normalize (Q&D)

    histogram = numpy.histogram(frame, bins=256)[0]
    histogram_length = sum(histogram)
    samples_probability = [float(h) / histogram_length for h in histogram]
    entropy = -sum([p * math.log(p, 2) for p in samples_probability if p != 0])

    return entropy

def get_frame_entropies(capture, sobelized=False):
    try:
        cache = pickle.load(open(capture.cache_filename, 'r'))
    except:
        cache = {}

    cachekey = 'frame_entropies'
    if sobelized:
        cachekey += '_sobel'

    if cache.get(cachekey):
        return cache[cachekey]

    pool = multiprocessing.Pool(processes=DEFAULT_POOL_SIZE)
    results = pool.map(_get_frame_entropy, zip(range(capture.num_frames+1),
                                               repeat(capture),
                                               repeat(sobelized)))
    cache[cachekey] = results
    pickle.dump(cache, open(capture.cache_filename, 'w'))

    return cache[cachekey]

def get_overall_entropy(capture, sobelized=False):
    return sum(get_frame_entropies(capture, sobelized=sobelized))

def get_entropy_diffs(capture, num_samples=5, sobelized=False):
    prev_samples = []
    entropies = get_frame_entropies(capture, sobelized=sobelized)
    entropy_diffs = [0]
    for i in range(1, len(entropies)):
        frame_entropy = entropies[i]
        if prev_samples:
            entropy_diff = 0
            for prev_sample in prev_samples:
                entropy_diff += abs(frame_entropy - prev_sample)
            entropy_diff /= (1 + len(prev_samples))
            entropy_diffs.append(entropy_diff)
        prev_samples.append(frame_entropy)
        if len(prev_samples) > num_samples:
            prev_samples = prev_samples[1:]

    return entropy_diffs
