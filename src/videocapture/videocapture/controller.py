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
import re

import Image
import numpy
from zipfile import ZipFile

DECKLINK_DIR = os.path.join(os.path.dirname(__file__), 'decklink')

def _natural_key(str):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str)]

def _get_biggest_square(rgb, imagefile):
    image = numpy.array(Image.open(imagefile), dtype=numpy.int16)
    imagesquares = []

    # An array representing whether each pixel's RGB components are within
    # the box's threshold
    mask = numpy.array(rgb,dtype=numpy.int16)
    threshold = numpy.int16(30)

    thresharray = numpy.abs(image-mask)
    thresharray = ((thresharray[:,:,0]+thresharray[:,:,1]+thresharray[:,:,2]) < threshold)
    for y, row in enumerate(thresharray):
        scanline = None
        # assumption: there aren't several boxes on this same line
        where = numpy.nonzero(row)[0]
        if len(where):
            scanline = [where[0], where[-1]]

        if scanline:
            found_existing = False
            for square in imagesquares:
                if abs(square[0] - scanline[0]) < 1 and abs(square[2] - scanline[1]) < 1:
                    square[3] = y
                    found_existing = True
            if not found_existing:
                imagesquares.append([int(scanline[0]), y, int(scanline[1]), y])

    if imagesquares:
        return max(imagesquares, key=lambda box: (box[2]-box[0])*(box[3]-box[1]))
    else:
        return None

class CaptureController(object):

    def __init__(self, device_name):
        self.capture_proc = None
        self.null_read = file('/dev/null', 'r')
        self.null_write = file('/dev/null', 'w')
        self.output_filename = None
        self.output_raw_filename = None
        self.capture_time = None
        self.capture_name = None
        self.device_name = device_name

    def launch(self, capture_name, output_filename):
        print 'launch requested'
        if self.capture_proc:
            print 'capture already running'
            return
        print 'launching'
        self.output_raw_file = tempfile.NamedTemporaryFile()
        self.output_filename = output_filename
        self.capture_time = datetime.datetime.now()
        self.capture_name = capture_name
        args = (os.path.join(DECKLINK_DIR, 'decklink-capture'),
                '-m',
                '13',
                '-p',
                '0',
                '-f',
                self.output_raw_file.name)
        self.capture_proc = subprocess.Popen(args, close_fds=True)

    def running(self):
        if not self.capture_proc:
            return False
        running = self.capture_proc.poll()
        if running != None:
            self.capture_proc = None
        return running == None

    def terminate_capture(self):
        print 'terminate requested'
        if not self.capture_proc:
            print 'not running'
            return

        print 'terminating...'
        self.capture_proc.terminate()
        for i in range(0, 5):
            rc = self.capture_proc.poll()
            print 'rc: %s' % str(rc)
            if rc != None:
                print 'terminated'
                self.capture_proc.wait()  # necessary?
                self.capture_proc = None
                break
            time.sleep(1)
        if self.capture_proc:
            print 'still running!'
            # terminate failed; try forcibly killing it
            try:
                self.capture_proc.kill()
            except:
                pass
            self.capture_proc.wait()  # or poll and error out if still running?
            self.capture_proc = None

    def convert_capture(self):
        print 'Converting...'
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
        print "Getting start frame / capture dimensions ..."
        squares = []
        start_frame = 0
        capture_area = None
        for (i, imagefile) in enumerate(imagefiles):
            squares.append(_get_biggest_square((0,255,0), imagefile))

            if i > 1 and not squares[-1] and squares[-2]:
                start_frame = i
                capture_area = squares[-2]
                break

        # end frame
        print "Getting end frame ..."
        squares = []
        end_frame = num_frames
        for i in range(num_frames-1, 0, -1):
            squares.append(_get_biggest_square((255,0,0), imagefiles[i]))

            if len(squares) > 1 and not squares[-1] and squares[-2]:
                end_frame = i
                break

        print "Rewriting images ..."
        imagedir = tempfile.mkdtemp()

        def _rewrite_frame(framenum, dirname, imagefilename):
            os.rename(imagefilename, os.path.join(dirname, '%s.png' % framenum))

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
                         json.dumps({'name': self.capture_name,
                                     'device': self.device_name,
                                     'date': self.capture_time.isoformat(),
                                     'frameDimensions': frame_dimensions,
                                     'captureArea': capture_area,
                                     'version': 1 }))

        zipfile.writestr('movie.webm', moviefile.read())

        for imagefilename in os.listdir(imagedir):
            zipfile.writestr("images/%s" % imagefilename,
                             open(os.path.join(imagedir, imagefilename)).read())

        zipfile.close()

        self.output_filename = None
        self.output_raw_file = None
