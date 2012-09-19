# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from PIL import Image
import StringIO
import os
from zipfile import ZipFile, BadZipfile
import json
import numpy
import tempfile
import cPickle as pickle

class CaptureException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class BadCapture(CaptureException):
    pass

class Capture(object):
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise CaptureException("Capture file '%s' does not exist!" %
                                   filename)
        try:
            self.archive = ZipFile(filename, 'r')
        except BadZipfile:
            raise BadCapture("Capture file '%s' not a .zip file")

        if 'metadata.json' not in self.archive.namelist():
            raise BadCapture("No metadata in capture")

        self.metadata = json.loads(self.archive.open('metadata.json').read())
        # A cache file for storing hard-to-generate data about the capture
        self.cache_filename = filename + '.cache'
        if not self.metadata or not self.metadata['version']:
            raise BadCapture("Capture file '%s' does not appear to be an "
                                   "Eideticker capture file" % filename)

        self.num_frames = max(0, len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                                            self.archive.namelist())) - 2)
        if self.num_frames > 0:
            im = self.get_frame_image(0)
            self.dimensions = im.size

        # Name of capture filename (in case we need to modify it)
        self.filename = filename

    @property
    def length(self):
        return self.num_frames / 60.0

    def get_video(self):
        buf = StringIO.StringIO()
        buf.write(self.archive.read('movie.webm'))
        buf.seek(0)
        return buf

    def get_frame_image(self, framenum, grayscale=False):
        if int(framenum) > self.num_frames:
            raise CaptureException("Frame number '%s' is greater than the number of frames " \
                                   "(%s)" % (framenum, self.num_frames))

        filename = 'images/%s.png' % framenum
        if filename not in self.archive.namelist():
            raise BadCapture("Frame image '%s' not in capture" % filename)

        return self._get_frame_image(filename, grayscale)

    def _get_frame_image(self, filename, grayscale=False):
        buf = StringIO.StringIO()
        buf.write(self.archive.read(filename))
        buf.seek(0)
        im = Image.open(buf)
        if grayscale:
            im = im.convert("L")

        return im

    def get_frame(self, framenum, grayscale=False, type=numpy.float):
        return numpy.array(self.get_frame_image(framenum, grayscale), dtype=type)
