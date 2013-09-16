import videocapture

INPUT_RESPONSE_THRESHOLD = 4096

def get_standard_metrics(capture, actions, difference_threshold=0):
    metrics = {}
    metrics['uniqueframes'] = videocapture.get_num_unique_frames(capture, threshold=difference_threshold)
    metrics['fps'] = videocapture.get_fps(capture, threshold=difference_threshold)
    metrics['checkerboard'] = videocapture.get_checkerboarding_area_duration(capture)
    if actions:
        # get the delta between the first non-sleep action being fired and
        # there being a visible change
        first_non_sleep_action = None
        for action in actions:
            if action['type'] != 'sleep':
                first_non_sleep_action = action
                break
        if first_non_sleep_action:
            framediffs = videocapture.get_framediff_sums(
                capture, threshold=difference_threshold)
            for (i, framediff) in enumerate(framediffs):
                t = i/float(capture.fps)
                if first_non_sleep_action['start'] < t and \
                        framediff >= INPUT_RESPONSE_THRESHOLD:
                    metrics['timetoresponse'] = (t - first_non_sleep_action['start'])
                    return metrics

    return metrics
