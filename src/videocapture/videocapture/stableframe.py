from framediff import get_framediff_sums
from entropy import get_entropy_diffs

def get_stable_frame(capture, method='framediff', threshold=4096):
    if method == 'framediff':
        framediff_sums = get_framediff_sums(capture)
        for i in range(len(framediff_sums) - 1, 0, -1):
            if framediff_sums[i] > threshold:
                return i + 1
        return len(framediff_sums) - 1
    elif method == 'entropy':
        entropy_diffs = get_entropy_diffs(capture)
        for i in range(len(entropy_diffs) - 1, 0, -1):
            if abs(entropy_diffs[i]) > threshold:
                return i + 1
        return len(entropy_diffs) - 1


def get_stable_frame_time(capture, method='framediff', threshold=4096):
    return get_stable_frame(capture, method=method,
                            threshold=threshold) / float(capture.fps)
