#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import subprocess
import tempfile
import time
import datetime
import os
from square import get_biggest_square
import re
import multiprocessing
import select
import shutil

from PIL import Image, ImageFilter
import numpy
from zipfile import ZipFile

DECKLINK_DIR = os.path.join(os.path.dirname(__file__), 'decklink')
POINTGREY_DIR = os.path.join(os.path.dirname(__file__), 'pointgrey')
MAX_VIDEO_FPS = 60
DEFAULT_WEBM_BIT_RATE = 1024

valid_capture_devices = ["decklink", "pointgrey"]
valid_decklink_modes = ["720p", "1080p"]


def _natural_key(str):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str)]

supported_formats = {
    "1080p": {"decklink_mode": 13},
    "1080i": {"decklink_mode": 9},
    "720p": {"decklink_mode": 16},
    "720p@59.94": {"decklink_mode": 12}
}

camera_configs = {
    "Flea3 FL3-U3-13Y3M": "FL3-U3-13Y3M.json",
    "Flea3 FL3-U3-13E4C": "FL3-U3-13E4C.json"
}


class CaptureProcess(multiprocessing.Process):

    def __init__(self, capture_device, video_format, frame_counter,
                 finished_semaphore, output_raw_filename=None,
                 outputdir=None, fps=None, camera_settings_file=None):
        multiprocessing.Process.__init__(self, args=(frame_counter,
                                                     finished_semaphore,))
        self.frame_counter = frame_counter
        self.output_raw_filename = output_raw_filename
        self.outputdir = outputdir
        self.capture_device = capture_device
        self.video_format = video_format
        self.finished_semaphore = finished_semaphore
        self.fps = fps
        self.camera_settings_file = camera_settings_file

    def stop(self):
        self.finished_semaphore.value = True

    def run(self):
        timeout = 10
        if self.capture_device == "decklink":
            mode = supported_formats[self.video_format]["decklink_mode"]
            args = [os.path.join(DECKLINK_DIR, 'decklink-capture'),
                    '-o',
                    '-m',
                    '%s' % mode,
                    '-p',
                    '0',
                    '-n',
                    '6000',
                    '-f',
                    self.output_raw_filename]
        elif self.capture_device == "pointgrey":
            # for debugging purposes, it might be useful to print out the
            # flycap version. the best way I could find to do this was to
            # try to look up the .soname
            flycap_lib = max([filename for filename in os.listdir('/usr/lib') \
                              if 'libflycapture.so' in filename], key=len)
            if flycap_lib:
                version_index = flycap_lib.find('.so') + 3
                self.log('Using PointGrey SDK version: %s' % flycap_lib[version_index])
            else:
                self.log("WARNING: Unable to determine PointGrey SDK version")

            # get the device type
            camera_id = subprocess.check_output([os.path.join(
                POINTGREY_DIR, "get-camera-id")]).strip()
            if self.camera_settings_file:
                camera_settings_file = self.camera_settings_file
            else:
                camera_config = camera_configs.get(camera_id)
                if not camera_config:
                    raise Exception("No camera configuration for model '%s'" %
                                    camera_id)
                camera_settings_file = os.path.join(POINTGREY_DIR, camera_config)
            args = [os.path.join(POINTGREY_DIR, 'pointgrey-capture'),
                    '-c',
                    camera_settings_file,
                    '-o',
                    '-n',
                    '1200',
                    '-f',
                    self.outputdir]
            if self.fps:
                args.extend(['-r', str(self.fps)])
            timeout = 300  # pointgrey devices need an extra long timeout
        else:
            raise Exception("Unknown capture device '%s'" %
                            self.capture_device)

        self.capture_proc = subprocess.Popen(args, stdout=subprocess.PIPE)

        # this loop keeps track of the frame counter while the capture is
        # ongoing
        while not self.finished_semaphore.value:
            try:
                ready, _, _ = select.select([self.capture_proc.stdout], [], [], .1)

                if self.capture_proc.stdout in ready:
                    line = self.capture_proc.stdout.readline()
                    if not line:
                        break # end of output, we're done
                    self.frame_counter.value = int(line.rstrip())
            except KeyboardInterrupt:
                break

        print "Terminating capture proc..."
        self.capture_proc.terminate()
        waitstart = time.time()
        while (time.time() - waitstart) < timeout:
            rc = self.capture_proc.poll()
            time.sleep(0.5)
            if rc is not None:
                print "Capture proc terminated"
                self.capture_proc.wait()  # necessary?
                return

        print "WARNING: Capture still running!"
        # terminate failed; try forcibly killing it
        try:
            self.capture_proc.kill()
        except:
            pass
        self.capture_proc.wait()  # or poll and error out if still running?

def _rewrite_frame(framenum, dirname, imagefilename, capture_area,
                   capture_device):
    im = Image.open(imagefilename)
    if capture_area:
        im = im.crop(capture_area)
    # pointgrey needs a median filter because it's so noisy
    if capture_device == "pointgrey":
        im = im.filter(ImageFilter.MedianFilter())
    im = im.convert("RGB")
    im.save(os.path.join(dirname, '%s.png' % framenum))

class CaptureController(object):

    def __init__(self, capture_device, capture_area=None,
                 find_start_signal=True, find_end_signal=True,
                 custom_tempdir=None, fps=None, use_vpxenc=False,
                 camera_settings_file=None):
        self.capture_process = None
        self.null_read = file('/dev/null', 'r')
        self.null_write = file('/dev/null', 'w')
        self.output_filename = None
        self.output_raw_file = None
        self.outputdir = None
        self.capture_time = None
        self.capture_name = None
        self.custom_tempdir = custom_tempdir
        self.capture_device = capture_device
        self.capture_area = capture_area
        self.find_start_signal = find_start_signal
        self.find_end_signal = find_end_signal
        self.fps = fps
        self.use_vpxenc = use_vpxenc
        self.camera_settings_file = camera_settings_file

    def log(self, msg):
        print "%s Capture Controller | %s" % (
            datetime.datetime.now().strftime("%b %d %H:%M:%S %Z"), msg)

    def start_capture(self, output_filename, mode=None,
                      capture_metadata={}, debug=False):
        # should not call this more than once
        assert not self.capture_process

        output_raw_filename = None

        if self.capture_device == 'decklink':
            if mode not in supported_formats.keys():
                raise Exception("Unsupported video format %s" % mode)
            self.output_raw_file = tempfile.NamedTemporaryFile(
                dir=self.custom_tempdir)
            output_raw_filename = self.output_raw_file.name

        self.outputdir = tempfile.mkdtemp(dir=self.custom_tempdir)
        self.mode = mode
        self.output_filename = output_filename
        self.capture_time = datetime.datetime.now()
        self.capture_metadata = capture_metadata
        self.frame_counter = multiprocessing.RawValue('i', 0)
        self.finished_semaphore = multiprocessing.RawValue('b', False)
        self.capture_process = CaptureProcess(
            self.capture_device, mode,
            self.frame_counter,
            self.finished_semaphore,
            output_raw_filename=output_raw_filename,
            outputdir=self.outputdir,
            fps=self.fps,
            camera_settings_file=self.camera_settings_file)
        self.log("Starting capture...")
        self.capture_process.start()

        # wait for capture to actually start...
        self.log("Waiting for first frame...")
        max_wait_for_frame = 5
        elapsed = 0
        interval = 0.1
        while self.capture_framenum() < 1:
            time.sleep(interval)
            elapsed += interval
            if elapsed > max_wait_for_frame:
                self.log("Timed out waiting for first frame! Capture prog "
                         "hung?")
                self.terminate_capture()
                raise Exception("Timed out waiting for first frame")

    @property
    def capturing(self):
        return self.capture_process is not None

    def capture_framenum(self):
        assert self.capture_process
        return self.frame_counter.value

    def terminate_capture(self):
        # should not call this when no capture is ongoing
        if not self.capturing:
            self.log("Terminated capture, but no capture ongoing")
            return

        self.capture_process.stop()
        self.capture_process.join()
        self.capture_process = None

    def convert_capture(self, start_frame, end_frame, create_webm=True):
        self.log("Converting capture...")
        # wait for capture to finish if it has not already
        if self.capturing:
            self.log("Capture not finished... waiting")
            while self.capturing:
                time.sleep(0.5)

        if self.capture_device == "decklink":
            subprocess.Popen((
                os.path.join(DECKLINK_DIR, 'decklink-convert.sh'),
                self.output_raw_file.name, self.outputdir, self.mode),
                close_fds=True).wait()

        self.log("Gathering capture dimensions and cropping to start/end of "
                 "capture...")
        imagefiles = [os.path.join(self.outputdir, path) for path in
                      sorted(os.listdir(self.outputdir), key=_natural_key)]
        num_frames = len(imagefiles)

        # full image dimensions
        frame_dimensions = (0, 0)
        if num_frames > 0:
            im = Image.open(imagefiles[0])
            frame_dimensions = im.size

        # searching for start/end frames and capture dimensions only really
        # makes sense on the decklink cards, which have a clean HDMI signal.
        # input from things like the pointgrey cameras is too noisy...
        if self.capture_device == "decklink":
            # start frame
            if self.find_start_signal:
                self.log("Searching for start of capture signal ...")
                squares = []
                for (i, imagefile) in enumerate(imagefiles):
                    imgarray = numpy.array(Image.open(imagefile),
                                           dtype=numpy.int16)
                    squares.append(get_biggest_square((0, 255, 0), imgarray))
                    if i > 1 and not squares[-1] and squares[-2]:
                        if not start_frame:
                            start_frame = i
                        self.capture_area = squares[-2]
                        self.log("Found start capture signal at frame %s. "
                                 "Area: %s" % (i, self.capture_area))
                        break

            # end frame
            if self.find_end_signal:
                self.log("Searching for end of capture signal ...")
                squares = []
                for i in range(num_frames - 1, 0, -1):
                    imgarray = numpy.array(Image.open(imagefiles[i]),
                                           dtype=numpy.int16)
                    squares.append(get_biggest_square((255, 0, 0), imgarray))

                    if len(squares) > 1 and not squares[-1] and squares[-2]:
                        if not end_frame:
                            end_frame = (i - 1)
                        if not self.capture_area:
                            self.capture_area = squares[-2]
                        self.log("Found end capture signal at frame %s. Area: "
                                 "%s" % (i - 1, self.capture_area))
                        break

        # If we don't have a start frame, set it to 1
        if not start_frame:
            start_frame = 1
        # Don't have an end frame? make it the entire length of the
        # capture
        if not end_frame:
            end_frame = num_frames

        self.log("Rewriting images in %s..." % self.outputdir)
        rewritten_imagedir = tempfile.mkdtemp(dir=self.custom_tempdir)

        pool = multiprocessing.Pool()

        # map the frame before the start frame to the zeroth frame (if
        # possible). HACK: otherwise, create a copy of the start
        # frame (this duplicates a frame).
        remapped_frame = 0
        if start_frame > 1:
            remapped_frame = start_frame - 1
        pool.apply_async(_rewrite_frame,
                         [0, rewritten_imagedir, imagefiles[remapped_frame],
                          self.capture_area, self.capture_device])

        # last frame is the specified end frame or the first red frame if
        # no last frame specified, or the very last frame in the
        # sequence if there is no red frame and no specified last frame
        last_frame = min(num_frames - 1, end_frame + 2)

        # copy the remaining frames into numeric order starting from 1
        for (i, j) in enumerate(range(start_frame, last_frame)):
            pool.apply_async(_rewrite_frame, [(i + 1),
                             rewritten_imagedir, imagefiles[j],
                             self.capture_area, self.capture_device])

        # wait for the rewriting of the images to complete
        pool.close()
        pool.join()

        capturefps = self.fps
        if not capturefps:
            capturefps = 60
        generated_video_fps = capturefps
        if generated_video_fps > MAX_VIDEO_FPS:
            generated_video_fps = MAX_VIDEO_FPS

        if create_webm:
            self.log("Creating movie ...")

            moviefile = tempfile.NamedTemporaryFile(dir=self.custom_tempdir,
                                                    suffix=".webm")
            # png2yuv is broken on Ubuntu 12.04 and earlier, so we can't use
            # vpxenc there by default
            if self.use_vpxenc:
                with tempfile.NamedTemporaryFile(dir=self.custom_tempdir) as yuvfile:
                    yuvconv = subprocess.Popen(('png2yuv', '-I',  'p', '-f',
                                                str(capturefps), '-n',
                                                str(last_frame-start_frame), '-j',
                                                '%s/%%d.png' % rewritten_imagedir),
                                               stdout=subprocess.PIPE)
                    while yuvconv.poll() == None:
                        yuvfile.write(yuvconv.stdout.read())
                    yuvfile.write(yuvconv.stdout.read())
                    yuvfile.flush()

                    subprocess.Popen(('vpxenc', '--good', '--cpu-used=0',
                                      '--end-usage=vbr', '--passes=2',
                                      '--threads=%s' % (multiprocessing.cpu_count() - 1),
                                      '--target-bitrate=%s' % DEFAULT_WEBM_BIT_RATE,
                                      '-o', moviefile.name, yuvfile.name)).wait()
            else:
                subprocess.Popen(('avconv', '-y', '-r', str(generated_video_fps), '-i',
                                  os.path.join(rewritten_imagedir, '%d.png'),
                                  moviefile.name), close_fds=True).wait()


        self.log("Writing final capture '%s'..." % self.output_filename)
        zipfile = ZipFile(self.output_filename, 'a')

        zipfile.writestr('metadata.json',
                         json.dumps(dict({ 'captureDevice': self.capture_device,
                                           'date': self.capture_time.isoformat(),
                                           'frameDimensions': frame_dimensions,
                                           'fps': capturefps,
                                           'generatedVideoFPS': generated_video_fps,
                                           'version': 1 },
                                         **self.capture_metadata)))
        if create_webm:
            zipfile.writestr('movie.webm', moviefile.read())

        for imagefilename in os.listdir(rewritten_imagedir):
            zipfile.writestr("images/%s" % imagefilename,
                             open(os.path.join(rewritten_imagedir,
                                               imagefilename)).read())

        zipfile.close()

        shutil.rmtree(self.outputdir)
        shutil.rmtree(rewritten_imagedir)

        self.output_filename = None
        self.outputdir = None
        self.output_raw_file = None
