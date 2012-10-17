# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import optparse
import os

class OptionParser(optparse.OptionParser):
    '''Custom version of the optionparser class with a few eideticker-specific
       parameters to set device information'''

    def __init__(self, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
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
