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

        self.num_frames = len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                                     self.archive.namelist()))

        # Name of capture filename (in case we need to modify it)
        self.filename = filename

    @property
    def start_frame(self):
        return self.metadata.get('start_frame')

    @property
    def end_frame(self):
        return self.metadata.get('end_frame')

    @property
    def capture_dimensions(self):
        return CaptureDimensions(self.metadata.get('capture_dimensions'))

    def get_video(self):
        buf = StringIO.StringIO()
        buf.write(self.archive.read('movie.webm'))
        return buf

    def get_frame_image(self, framenum, cropped=False, grayscale=False):
        return self._get_frame_image('images/%s.png' % framenum, cropped, grayscale)

    def _get_frame_image(self, filename, cropped=False, grayscale=False):
        buf = StringIO.StringIO()
        buf.write(self.archive.read(filename))
        buf.seek(0)
        im = Image.open(buf)
        if grayscale:
            im = im.convert("L")
        if self.metadata.get('capture_dimensions') and cropped:
            return im.crop(self.metadata['capture_dimensions'])
        else:
            return im

    def get_frame(self, framenum, cropped=False, grayscale=False):
        return numpy.array(self.get_frame_image(framenum, cropped, grayscale))

    def get_framediff_image(self, framenum1, framenum2, cropped=False):
        frame1 = self.get_frame(framenum1, cropped)
        frame2 = self.get_frame(framenum2, cropped)
        framediff = numpy.abs(frame1.astype('float') - frame2.astype('float'))
        return Image.fromarray(framediff.astype(numpy.uint8))

    def get_framediff_sums(self):
        try:
            cache = pickle.load(open(self.cache_filename, 'r'))
        except:
            cache = {}

        try:
            diffsums = cache['diffsums']
        except:
            # Frame differences
            diffsums = None
            prevframe = None
            diffsums = []
            print "Getting diffsums %s <-> %s" % (self.start_frame, self.end_frame)
            for i in range(self.start_frame, self.end_frame):
                frame = self.get_frame(i, True).astype('float')
                if prevframe != None:
                    diffsums.append(numpy.linalg.norm(frame - prevframe))
                prevframe = frame
            cache['diffsums'] = diffsums
            pickle.dump(cache, open(self.cache_filename, 'w'))

        return diffsums

    def _get_biggest_square(self, rgb, framenum):
        frame = self.get_frame(framenum, False).astype('int16')
        framesquares = []

        # An array representing whether each pixel's RGB components are within
        # the box's threshold
        mask = numpy.array(rgb,dtype=numpy.int16)
        threshold = numpy.int16(30)

        thresharray = numpy.abs(frame-mask)
        thresharray = ((thresharray[:,:,0]+thresharray[:,:,1]+thresharray[:,:,2]) < threshold)
        for y, row in enumerate(thresharray):
            scanline = None
            # assumption: there aren't several boxes on this same line
            where = numpy.nonzero(row)[0]
            if len(where):
                scanline = [where[0], where[-1]]

            if scanline:
                found_existing = False
                for square in framesquares:
                    if abs(square[0] - scanline[0]) < 1 and abs(square[2] - scanline[1]) < 1:
                        square[3] = y
                        found_existing = True
                if not found_existing:
                    framesquares.append([int(scanline[0]), y, int(scanline[1]), y])

        if framesquares:
            return max(framesquares, key=lambda box: (box[2]-box[0])*(box[3]-box[1]))
        else:
            return None

    def generate_metadata(self):
        # full image dimensions
        (width, height) = (0,0)
        if self.num_frames > 0:
            im = self.get_frame_image(1)
            (self.metadata['width'], self.metadata['height']) = im.size

        # start frame
        print "Getting start frame"
        squares = []
        self.metadata['start_frame'] = self.metadata['capture_dimensions'] = None
        for i in range(1, self.num_frames):
            squares.append(self._get_biggest_square((0,255,0), i))

            if len(squares) > 2 and not squares[-1] and squares[-2]:
                self.metadata['start_frame'] = len(squares) # +1 b/c frames start at 1
                self.metadata['capture_dimensions'] = squares[-2]
                break

        # end frame
        print "Getting end frame"
        squares = []
        self.metadata['end_frame'] = None
        for i in range(self.num_frames-1, 0, -1):
            squares.append(self._get_biggest_square((255,0,0), i))

            if len(squares) > 2 and not squares[-1] and squares[-2]:
                self.metadata['end_frame'] = self.num_frames-len(squares)
                break

        # rewrite metadata (unfortunately we have to do this ridiculous song
        # and dance because ZipFile does not currently support rewriting
        # files)
        newzipfname = tempfile.NamedTemporaryFile(delete=False)
        newzip = ZipFile(newzipfname, 'a')
        for filename in self.archive.namelist():
            if filename != 'metadata.json':
                newzip.writestr(filename, self.archive.read(filename))
        newzip.writestr('metadata.json', json.dumps(self.metadata))
        newzip.close()
        os.rename(newzipfname.name, self.filename)

        # reopen archive after rewriting
        self.archive = ZipFile(self.filename, 'r')
