# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import optparse
import os
from controller import valid_capture_devices, valid_decklink_modes

class OptionParser(optparse.OptionParser):
    '''Custom version of the optionparser class with a few videocapture-specific
       parameters'''

    def _add_options(self):
        self.add_option("--capture-device", action="store",
                          type = "string", dest = "capture_device",
                          default = os.environ.get('CAPTURE_DEVICE', 'decklink'),
                          help = "type of capture device (%s)" % " or ".join(valid_capture_devices))
        self.add_option("--mode", action="store",
                        type = "string", dest = "mode",
                        default = None,
                        help = "mode to use with decklink cards (%s)" % " or ".join(valid_decklink_modes))

    def __init__(self, require_mode=False, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        OptionParser._add_options(self)
        self.require_mode = require_mode

    def validate_options(self, options):
        if options.capture_device not in valid_capture_devices:
            self.error("Capture device must be %s" % " or ".join(valid_capture_devices))
        if self.require_mode and options.mode not in valid_decklink_modes:
            self.error("Mode must be %s" % " or ".join(valid_decklink_modes))
