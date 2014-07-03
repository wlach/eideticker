from itertools import repeat
from scipy import ndimage
import cPickle as pickle
import cv2
import math
import concurrent.futures
import numpy

def _get_frame_entropy((i, capture, edge_detection)):
    """ Function calculates and returns the entropy of a single frame.
        Values for edge_detection can be 'sobel', 'canny' and None. """

    frame = capture.get_frame(i, True).astype('uint8') #ndarray is float64 by default

    if edge_detection=='sobel':
        frame = ndimage.median_filter(frame, 3)

        dx = ndimage.sobel(frame, 0)  # horizontal derivative
        dy = ndimage.sobel(frame, 1)  # vertical derivative
        frame = numpy.hypot(dx, dy)  # magnitude
        frame *= 255.0 / numpy.max(frame)  # normalize (Q&D)
    elif edge_detection=='canny':
        frame = cv2.Canny(frame,100,200) # Using set params at the moment

    histogram = numpy.histogram(frame, bins=256)[0]
    histogram_length = sum(histogram)
    samples_probability = [float(h) / histogram_length for h in histogram]
    entropy = -sum([p * math.log(p, 2) for p in samples_probability if p != 0])

    return entropy

def get_frame_entropies(capture, edge_detection=None):
    try:
        cache = pickle.load(open(capture.cache_filename, 'r'))
    except:
        cache = {}

    cachekey = 'frame_entropies'
    if edge_detection=='sobel':
        cachekey += '_sobel'
    elif edge_detection=='canny':
        cachekey += '_canny'

    if cache.get(cachekey):
        return cache[cachekey]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        entropies = list(executor.map(_get_frame_entropy,
                                      zip(range(capture.num_frames+1),
                                          repeat(capture),
                                          repeat(edge_detection))))
        cache[cachekey] = entropies
    pickle.dump(cache, open(capture.cache_filename, 'w'))
    return cache[cachekey]

def get_overall_entropy(capture, edge_detection=None):
    return sum(get_frame_entropies(capture, edge_detection))
