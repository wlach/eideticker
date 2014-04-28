from framediff import get_framediff_sums
from entropy import get_frame_entropies
import scipy.stats

def _get_stable_frame_from_entropies(entropies, window_size=10, pvalue_threshold=0.000031):
    for i in range(len(entropies)-window_size, window_size, -1):
        previousrange = entropies[i-window_size:i]
        nextrange = entropies[i:i+window_size]
        # use welch's ttest, which does not assume equal variance between
        # populations
        pvalue = scipy.stats.ttest_ind(nextrange, previousrange, equal_var=False)[1]
        if pvalue < pvalue_threshold:
            return i
    return 0

def get_stable_frame(capture, method='framediff', sobelized=False,
                     threshold=4096):
    if method == 'framediff':
        framediff_sums = get_framediff_sums(capture)
        for i in range(len(framediff_sums) - 1, 0, -1):
            if framediff_sums[i] > threshold:
                return i + 1
        return len(framediff_sums) - 1
    elif method == 'entropy':
        return _get_stable_frame_from_entropies(
            get_frame_entropies(sobelized=sobelized))

def get_stable_frame_time(capture, method='framediff', threshold=4096,
                          sobelized=False):
    return get_stable_frame(capture, method=method, threshold=threshold,
                            sobelized=sobelized) / float(capture.fps)
