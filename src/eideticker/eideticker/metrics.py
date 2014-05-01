import videocapture

_hdmi_props = {
    'input_threshold': 4096,
    'stable_frame_analysis_method': 'framediff',
    'stable_frame_threshold': 4096,
    'sobelize': False,
    'animation_threshold': 2048,
    'valid_measures': [ 'uniqueframes', 'fps', 'checkerboard',
                        'overallentropy' ]
}

# even with median filtering, pointgrey captures tend to have a
# bunch of visual noise -- try to compensate for this by setting
# a higher threshold for frames to be considered different and use
# different methods for determining load/startup finishing.
_camera_props = {
    'input_threshold': 4096,
    'stable_frame_analysis_method': 'entropy',
    'stable_frame_threshold': 3, # 3 times standard deviation, standard
    'sobelize': True,
    'animation_threshold': 4096,
    'valid_measures': [ 'overallentropy' ]
}


def _get_analysis_props(capture_device):
    if capture_device == 'decklink':
        return _hdmi_props
    elif capture_device == 'pointgrey':
        return _camera_props
    else:
        raise Exception("ERROR: Unknown capture device '%s' -- don't know how "
                        "to calculate metrics" % capture_device)


def get_stable_frame_time(capture):
    analysis_props = _get_analysis_props(capture.metadata['captureDevice'])
    return videocapture.get_stable_frame_time(
        capture, method=analysis_props['stable_frame_analysis_method'],
        threshold=analysis_props['stable_frame_threshold'],
        sobelized=analysis_props['sobelize'])

def get_standard_metrics(capture, actions):
    analysis_props = _get_analysis_props(capture.metadata['captureDevice'])

    metrics = {}
    if 'unique_frames' in analysis_props['valid_measures']:
        metrics['uniqueframes'] = videocapture.get_num_unique_frames(
            capture, threshold=analysis_props['animation_threshold'])
    if 'fps' in analysis_props['valid_measures']:
        metrics['fps'] = videocapture.get_fps(
            capture, threshold=analysis_props['animation_threshold'])
    if 'checkerboard' in analysis_props['valid_measures']:
        metrics['checkerboard'] = videocapture.get_checkerboarding_area_duration(
            capture)
    if 'overallentropy' in analysis_props['valid_measures']:
        metrics['overallentropy'] = \
                                    videocapture.get_overall_entropy(capture,
                                         sobelized=analysis_props['sobelize'])

    if actions:
        # get the delta between the first non-sleep action being fired and
        # there being a visible change
        first_non_sleep_action = None
        for action in actions:
            if action['type'] != 'sleep':
                first_non_sleep_action = action
                break
        if first_non_sleep_action:
            framediffs = videocapture.get_framediff_sums(capture)
            for (i, framediff) in enumerate(framediffs):
                t = i / float(capture.fps)
                if first_non_sleep_action['start'] < t and \
                        framediff >= analysis_props['input_threshold']:
                    metrics['timetoresponse'] = (
                        t - first_non_sleep_action['start'])
                    return metrics

    return metrics

def get_standard_metric_metadata(capture):
    return { 'framediffsums': videocapture.get_framediff_sums(capture),
             'framesobelentropies': videocapture.get_frame_entropies(
            capture, sobelized=True) }
