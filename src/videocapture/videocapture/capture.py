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

import Image
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

class CaptureDimensionsLgPortrait(CaptureDimensions):
    def __init__(self):
        CaptureDimensions.__init__(self, (613, 158, 1307, 1080))

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
        if not self.metadata or not self.metadata['version']:
            raise CaptureException("Capture file '%s' does not appear to be an "
                                   "Eideticker capture file" % filename)

        self.num_frames = len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                                     self.archive.namelist()))

        self.dimensions = None
        if self.metadata['device'] == 'LG-P999':
            self.dimensions = CaptureDimensionsLgPortrait()

        # If we don't have any preset dimensions, infer them from the size of frames
        if not self.dimensions:
            frame = self.get_frame(0)
            self.dimensions = CaptureDimensions(0, 0, frame.size[0], frame.size[1])

        # A cache file for storing hard-to-generate data about the capture
        self.cache_filename = filename + '.cache'

    def write_video(self, outputfile):
        outputfile.write(self.archive.open('movie.avi').read())

    def get_frame_image(self, framenum, cropped=False):
        return self._get_frame_image('images/%s.png' % framenum, cropped)

    def _get_frame_image(self, filename, cropped=False):
        buf = StringIO.StringIO()
        buf.write(self.archive.read(filename))
        buf.seek(0)
        im = Image.open(buf)
        if self.dimensions and cropped:
            return im.crop(self.dimensions.bbox)
        else:
            return im

    def get_frame(self, framenum, cropped=False):
        return numpy.array(self.get_frame_image(framenum, cropped))

    def get_num_frames(self, cropped = False):
        return len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                          self.archive.namelist()))

    def get_framediff_image(self, framenum1, framenum2, cropped=False):
        frame1 = self.get_frame(framenum1, cropped)
        frame2 = self.get_frame(framenum2, cropped)
        framediff = numpy.abs(frame1.astype('float') - frame2.astype('float'))
        return Image.fromarray(framediff.astype(numpy.uint8))

    def get_framediff_sums(self):
        diffsums = None
        try:
            cache = pickle.load(open(self.cache_filename, 'r'))
            # FIXME: throw an exception if the pickled file doesn't have
            # what we need in it
            diffsums = cache['diffsums']
        except:
            prevframe = None
            diffsums = []
            for i in range(1, self.get_num_frames()):
                frame = self.get_frame(i, True).astype('float')
                print "Processing frame %s" % i
                if i > 1:
                    diffsums.append(numpy.linalg.norm(frame - prevframe))
                prevframe = frame
            pickle.dump({'diffsums': diffsums}, open(self.cache_filename, 'w'))

        return diffsums
