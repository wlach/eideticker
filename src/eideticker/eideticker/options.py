# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import optparse
import os
import videocapture

class OptionParser(optparse.OptionParser):
    '''Custom version of the optionparser class with a few eideticker-specific
       parameters to set device information'''

    def _add_options(self):
        self.add_option("--host", action="store",
                        type = "string", dest = "host",
                        help = "Device hostname (only if using TCP/IP)", default=None)
        self.add_option("-p", "--port", action="store",
                        type = "int", dest = "port",
                        help = "Custom device port (if using SUTAgent or "
                        "adb-over-tcp)", default=None)
        self.add_option("-m", "--dm-type", action="store",
                        type = "string", dest = "dmtype",
                        default = os.environ.get('DM_TRANS', 'adb'),
                        help = "DeviceManager type (adb or sut, defaults to adb)")
        self.add_option("-d", "--device-type", action="store",
                        type = "string", dest = "devicetype",
                        default = os.environ.get('DEVICE_TYPE', 'android'),
                        help = "Device type (android or b2g, default to "
                        "android). If B2G, you do not need to pass in an "
                        "appname")
        self.add_option("--debug", action="store_true",
                        dest="debug", help="show verbose debugging information")

    def __init__(self, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        self._add_options()

class CaptureOptionParser(OptionParser, videocapture.OptionParser):
    '''Custom version of the optionparser with eideticker-specific parameters
    to set device information + video capture related settings'''

    def __init__(self, **kwargs):
        videocapture.OptionParser.__init__(self, **kwargs)
        OptionParser._add_options(self)

class TestOptionParser(CaptureOptionParser):
    '''Custom version of the optionparser with eideticker-specific parameters
    to set device information, video capture settings, and test-specific settings'''

    def __init__(self, **kwargs):
        CaptureOptionParser.__init__(self, **kwargs)

        self.add_option("--no-sync-time", action="store_true",
                        dest="no_sync_time",
                        help="don't synchronize time before running test",
                        default=False)
