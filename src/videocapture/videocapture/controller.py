#!/usr/bin/python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Eideticker.
#
# The Initial Developer of the Original Code is
# Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Mark Cote <mcote@mozilla.com>
#   William Lachance <wlachance@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import json
import subprocess
import tempfile
import time
import datetime
import os
import capture
from square import get_biggest_square
import re
import threading

import Image
import numpy
from zipfile import ZipFile

DECKLINK_DIR = os.path.join(os.path.dirname(__file__), 'decklink')

def _natural_key(str):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str)]

class CaptureThread(threading.Thread):
    framenum = 0
    finished = False
    capture_proc = None
    debug = False

    def __init__(self, output_raw_filename, debug=False):
        threading.Thread.__init__(self)
        self.output_raw_filename = output_raw_filename
        self.debug = debug

    def stop(self):
        self.finished = True
        self.capture_proc.terminate()
        for i in range(2):
            rc = self.capture_proc.poll()
            print 'rc: %s' % str(rc)
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

    def run(self):
        args = (os.path.join(DECKLINK_DIR, 'decklink-capture'),
                '-o',
                '-m',
                '13',
                '-p',
                '0',
                '-f',
                self.output_raw_filename)

        self.capture_proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        print "Opening!"
        while not self.finished:
            try:
                line = self.capture_proc.stdout.readline()
            except KeyboardInterrupt:
                break

            if not line:
                break

            self.framenum=int(line.rstrip())

class CaptureController(object):

    def __init__(self):
        self.capture_thread = None
        self.null_read = file('/dev/null', 'r')
        self.null_write = file('/dev/null', 'w')
        self.output_filename = None
        self.output_raw_file = None
        self.capture_time = None
        self.capture_name = None

    def start_capture(self, output_filename, capture_metadata = {}, debug=False):
        # should not call this more than once
        assert not self.capture_thread

        self.output_raw_file = tempfile.NamedTemporaryFile()
        self.output_filename = output_filename
        self.capture_time = datetime.datetime.now()
        self.capture_metadata = capture_metadata
        self.capture_thread = CaptureThread(self.output_raw_file.name, debug=debug)
        self.capture_thread.start()

    def capture_framenum(self):
        assert self.capture_thread
        return self.capture_thread.framenum

    def terminate_capture(self):
        # should not call this when no capture is ongoing
        assert self.capture_thread

        self.capture_thread.stop()
        self.capture_thread.join()
        self.capture_thread = None

    def convert_capture(self, start_frame, end_frame):
        tempdir = tempfile.mkdtemp()

        subprocess.Popen((os.path.join(DECKLINK_DIR, 'decklink-convert.sh'),
                          self.output_raw_file.name, tempdir),
                         close_fds=True).wait()

        print "Cropping to start/end of capture..."
        imagefiles = [os.path.join(tempdir, path) for path in sorted(os.listdir(tempdir),
                                                                     key=_natural_key)]
        num_frames = len(imagefiles)

        # full image dimensions
        frame_dimensions = (0,0)
        if num_frames > 0:
            im = Image.open(imagefiles[0])
            frame_dimensions = im.size

        # start frame
        print "Getting capture dimensions (and maybe start frame)..."
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
        if not end_frame:
            print "Getting end frame ..."
            squares = []
            end_frame = num_frames
            for i in range(num_frames-1, 0, -1):
                imgarray = numpy.array(Image.open(imagefiles[i]), dtype=numpy.int16)
                squares.append(get_biggest_square((255,0,0), imgarray))

                if len(squares) > 1 and not squares[-1] and squares[-2]:
                    end_frame = i
                    break

        print "Rewriting images ..."
        imagedir = tempfile.mkdtemp()

        def _rewrite_frame(framenum, dirname, imagefilename):
            im = Image.open(imagefilename)
            if capture_area:
                im = im.crop(capture_area)
            im.save(os.path.join(dirname, '%s.png' % framenum))

        # map the frame before the start frame to the zeroth frame (if possible)
        if start_frame > 1:
            _rewrite_frame(0, imagedir, imagefiles[start_frame-1])

        # last frame is the first red frame, or the very last frame in the
        # sequence (for the edge case where there is no red frame)
        last_frame = min(num_frames-1, end_frame+2)

        # copy the remaining frames into numeric order starting from 1
        for (i,j) in enumerate(range(start_frame, last_frame)):
            _rewrite_frame((i+1), imagedir, imagefiles[j])

        print "Creating movie ..."
        moviefile = tempfile.NamedTemporaryFile(suffix=".webm")
        subprocess.Popen(('ffmpeg', '-y', '-r', '60', '-i',
                          os.path.join(imagedir, '%d.png'),
                          moviefile.name), close_fds=True).wait()

        print "Writing final capture..."
        zipfile = ZipFile(self.output_filename, 'a')

        zipfile.writestr('metadata.json',
                         json.dumps(dict({ 'date': self.capture_time.isoformat(),
                                           'frameDimensions': frame_dimensions,
                                           'version': 1 },
                                         **self.capture_metadata)))

        zipfile.writestr('movie.webm', moviefile.read())

        for imagefilename in os.listdir(imagedir):
            zipfile.writestr("images/%s" % imagefilename,
                             open(os.path.join(imagedir, imagefilename)).read())

        zipfile.close()

        self.output_filename = None
        self.output_raw_file = None
