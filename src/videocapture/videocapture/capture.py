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
# The Original Code is Mozilla Eideticker.
#
# The Initial Developer of the Original Code is
# Mozilla foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
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

from PIL import Image
import StringIO
import os
from zipfile import ZipFile
import json
import numpy
import tempfile
import cPickle as pickle

class CaptureDimensions(object):
    def __init__(self, bbox):
        self.bbox = bbox
        self.size = (self.bbox[2] - self.bbox[0], self.bbox[3] - self.bbox[1])

class CaptureException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class Capture(object):
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise CaptureException("Capture file '%s' does not exist!" %
                                   filename)
        self.archive = ZipFile(filename, 'r')
        self.metadata = json.loads(self.archive.open('metadata.json').read())
        # A cache file for storing hard-to-generate data about the capture
        self.cache_filename = filename + '.cache'
        if not self.metadata or not self.metadata['version']:
            raise CaptureException("Capture file '%s' does not appear to be an "
                                   "Eideticker capture file" % filename)

        self.num_frames = max(0, len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                                            self.archive.namelist())) - 2)

        # Name of capture filename (in case we need to modify it)
        self.filename = filename

    @property
    def length(self):
        return self.num_frames / 60.0

    def get_video(self):
        buf = StringIO.StringIO()
        buf.write(self.archive.read('movie.webm'))
        return buf

    def get_frame_image(self, framenum, grayscale=False):
        return self._get_frame_image('images/%s.png' % framenum, grayscale)

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
