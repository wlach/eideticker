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
import capture
from square import get_biggest_square
import re
import multiprocessing
import shutil

from PIL import Image
import numpy
from zipfile import ZipFile

DECKLINK_DIR = os.path.join(os.path.dirname(__file__), 'decklink')

def _natural_key(str):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str)]

supported_formats = {
    "1080p": { "decklink_mode": 13 },
    "1080i": { "decklink_mode": 9 },
    "720p": { "decklink_mode": 16 },
    "720p@59.94": { "decklink_mode": 12 }
 }

class CaptureProcess(multiprocessing.Process):

    def __init__(self, output_raw_filename, video_format, frame_counter, finished_semaphore, custom_tempdir=None):
        multiprocessing.Process.__init__(self, args=(frame_counter,finished_semaphore,))
        self.frame_counter = frame_counter
        self.output_raw_filename = output_raw_filename
        self.video_format = video_format
        self.custom_tempdir = custom_tempdir
        self.finished_semaphore = finished_semaphore

    def stop(self):
        self.finished_semaphore.value = True

    def run(self):
        mode = supported_formats[self.video_format]["decklink_mode"]

        args = (os.path.join(DECKLINK_DIR, 'decklink-capture'),
                '-o',
                '-m',
                '%s' % mode,
                '-p',
                '0',
                '-n',
                '6000',
                '-f',
                self.output_raw_filename)

        self.capture_proc = subprocess.Popen(args, stdout=subprocess.PIPE)

        while not self.finished_semaphore.value:
            try:
                line = self.capture_proc.stdout.readline()
            except KeyboardInterrupt:
                break

            if not line:
                break

            self.frame_counter.value=int(line.rstrip())

        self.capture_proc.terminate()
        for i in range(2):
            rc = self.capture_proc.poll()
            if rc != None:
                print 'terminated'
                self.capture_proc.wait()  # necessary?
                return

        print 'still running!'
        # terminate failed; try forcibly killing it
        try:
            self.capture_proc.kill()
        except:
            pass
        self.capture_proc.wait()  # or poll and error out if still running?


class CaptureController(object):

    def __init__(self, custom_tempdir=None):
        self.capture_process = None
        self.null_read = file('/dev/null', 'r')
        self.null_write = file('/dev/null', 'w')
        self.output_filename = None
        self.output_raw_file = None
        self.capture_time = None
        self.capture_name = None
        self.custom_tempdir = custom_tempdir

    def log(self, msg):
        print "%s Capture Controller | %s" % (datetime.datetime.now().strftime("%b %d %H:%M:%S %Z"), msg)

    def start_capture(self, output_filename, mode, capture_metadata = {}, debug=False):
        # should not call this more than once
        assert not self.capture_process
        if mode not in supported_formats.keys():
            raise Exception("Unsupported video format %s" % mode)

        self.output_raw_file = tempfile.NamedTemporaryFile(dir=self.custom_tempdir)
        self.mode = mode
        self.output_filename = output_filename
        self.capture_time = datetime.datetime.now()
        self.capture_metadata = capture_metadata
        self.frame_counter = multiprocessing.RawValue('i', 0)
        self.finished_semaphore = multiprocessing.RawValue('b', False)
        self.capture_process = CaptureProcess(self.output_raw_file.name,
                                              mode,
                                              self.frame_counter,
                                              self.finished_semaphore,
                                              custom_tempdir=self.custom_tempdir)
        self.log("Starting capture...")
        self.capture_process.start()

    @property
    def capturing(self):
        return self.capture_process != None

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

    def convert_capture(self, start_frame, end_frame):
        self.log("Converting capture...")
        imagedir = tempfile.mkdtemp(dir=self.custom_tempdir)

        subprocess.Popen((os.path.join(DECKLINK_DIR, 'decklink-convert.sh'),
                          self.output_raw_file.name, imagedir, self.mode),
                         close_fds=True).wait()

        self.log("Gathering capture dimensions and cropping to start/end of capture...")
        imagefiles = [os.path.join(imagedir, path) for path in sorted(os.listdir(imagedir),
                                                                     key=_natural_key)]
        num_frames = len(imagefiles)

        # full image dimensions
        frame_dimensions = (0,0)
        if num_frames > 0:
            im = Image.open(imagefiles[0])
            frame_dimensions = im.size

        # start frame
        self.log("Searching for start of capture signal ...")
        squares = []
        capture_area = None
        for (i, imagefile) in enumerate(imagefiles):
            imgarray = numpy.array(Image.open(imagefile), dtype=numpy.int16)
            squares.append(get_biggest_square((0,255,0), imgarray))

            if i > 1 and not squares[-1] and squares[-2]:
                if not start_frame:
                    start_frame = i
                capture_area = squares[-2]
                break
        # If we still don't have a start frame, set it to 1
        if not start_frame:
            start_frame = 1

        # end frame
        self.log("Searching for end of capture signal ...")
        squares = []
        for i in range(num_frames-1, 0, -1):
            imgarray = numpy.array(Image.open(imagefiles[i]), dtype=numpy.int16)
            squares.append(get_biggest_square((255,0,0), imgarray))

            if len(squares) > 1 and not squares[-1] and squares[-2]:
                if not end_frame:
                    end_frame = (i-1)
                if not capture_area:
                    capture_area = squares[-2]
                break

        # still don't have an end frame? make it the entire length of the
        # capture
        if not end_frame:
            end_frame = num_frames


        self.log("Rewriting images ...")
        rewritten_imagedir = tempfile.mkdtemp(dir=self.custom_tempdir)

        def _rewrite_frame(framenum, dirname, imagefilename):
            im = Image.open(imagefilename)
            if capture_area:
                im = im.crop(capture_area)
            im.save(os.path.join(dirname, '%s.png' % framenum))

        # map the frame before the start frame to the zeroth frame (if possible)
        if start_frame > 1:
            _rewrite_frame(0, rewritten_imagedir, imagefiles[start_frame-1])
        else:
            # HACK: otherwise, create a copy of the start frame
            # (this duplicates a frame)
            _rewrite_frame(0, rewritten_imagedir, imagefiles[0])
        # last frame is the specified end frame or the first red frame if
        # no last frame specified, or the very last frame in the
        # sequence if there is no red frame and no specified last frame
        last_frame = min(num_frames-1, end_frame+2)

        # copy the remaining frames into numeric order starting from 1
        # (use multiprocessing to speed this up: there's probably a more
        # elegant way of doing this, but I'm not sure what it is)
        multiprocesses = []
        for (i,j) in enumerate(range(start_frame, last_frame)):
            p = multiprocessing.Process(target=_rewrite_frame, args=((i+1), rewritten_imagedir, imagefiles[j]))
            p.start()
            multiprocesses.append(p)
           # _rewrite_frame((i+1), rewritten_imagedir, imagefiles[j])
        for p in multiprocesses:
            p.join()

        self.log("Creating movie ...")
        moviefile = tempfile.NamedTemporaryFile(dir=self.custom_tempdir,
                                                suffix=".webm")
        subprocess.Popen(('ffmpeg', '-y', '-r', '60', '-i',
                          os.path.join(rewritten_imagedir, '%d.png'),
                          moviefile.name), close_fds=True).wait()

        self.log("Writing final capture '%s'..." % self.output_filename)
        zipfile = ZipFile(self.output_filename, 'a')

        zipfile.writestr('metadata.json',
                         json.dumps(dict({ 'date': self.capture_time.isoformat(),
                                           'frameDimensions': frame_dimensions,
                                           'version': 1 },
                                         **self.capture_metadata)))

        zipfile.writestr('movie.webm', moviefile.read())

        for imagefilename in os.listdir(rewritten_imagedir):
            zipfile.writestr("images/%s" % imagefilename,
                             open(os.path.join(rewritten_imagedir,
                                               imagefilename)).read())

        zipfile.close()

        shutil.rmtree(imagedir)
        shutil.rmtree(rewritten_imagedir)

        self.output_filename = None
        self.output_raw_file = None
