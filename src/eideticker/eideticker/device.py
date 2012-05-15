# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import StringIO
import mozdevice
import os
import re
import tempfile
import time

# I know specifying resolution manually like this is ugly, but as far as I
# can tell there is no good, device-independant way of getting this
# information universally (we can get the resolution with SUT, but not the
# required HDMI mode)
DEVICE_PROPERTIES = {
    "Galaxy Nexus": {
        "hdmiResolution": "720p",
        "dimensions": (1180, 720)
    },
    "LG-P999": {
        "hdmiResolution": "720p",
        "dimensions": (480, 800)
    },
}

class EidetickerMixin(object):
    """Mixin to extend DeviceManager with functionality to allow it to be
       remotely controlled and other related things"""

    @property
    def hdmiResolution(self):
        return DEVICE_PROPERTIES[self.model]['hdmiResolution']

    def _init(self):
        self.model = self._shellCheckOutput(["getprop", "ro.product.model"])

        # Hack: this gets rid of the "finished charging" modal dialog that the
        # LG G2X sometimes brings up
        self.tap(240, 617)

    # FIXME: make this part of devicemanager
    def _shellCheckOutput(dm, args):
        buf = StringIO.StringIO()
        dm.shell(args, buf)
        return str(buf.getvalue()[0:-1]).rstrip()

    def _executeScript(self, script):
        '''Executes a set of monkey commands on the device'''
        f = tempfile.NamedTemporaryFile()
        f.write("type= raw events\ncount= %s\nspeed= 0.0\nstart data >>\n" % len(script.split('\n')))
        f.write(script)
        f.flush()
        remotefilename = os.path.join(self.getDeviceRoot(),
                                      os.path.basename(f.name))
        self.pushFile(f.name, remotefilename)
        buf = StringIO.StringIO()
        self.shell(["su", "-c", "LD_LIBRARY_PATH=/vendor/lib:/system/lib monkey -f %s 1" % remotefilename], buf)

    def drag(self, touch_start, touch_end, duration=1.0, num_steps=5):
        script = ""
        script += ("createDispatchPointer(0,0,0,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                   "0)\n" % touch_start)
        delta = ((touch_end[0] - touch_start[0]) / num_steps,
                 (touch_end[1] - touch_start[1]) / num_steps)
        for i in range(num_steps):
            current = (touch_start[0] + delta[0]*i,
                       touch_start[1] + delta[1]*i)
            script += ("createDispatchPointer(0,0,2,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                       "0)\n" % current)
            script += ("UserWait(%s)\n" % int((duration / num_steps) * 1000.0))
        script += ("createDispatchPointer(0,0,1,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                   "0)\n" % touch_end)
        self._executeScript(script)

    def tap(self, x, y, times=1):
        script = ""
        for i in range(0, times):
            script += ("createDispatchPointer(0,0,0,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                          "0)\n" % (x,y))
            script += ("createDispatchPointer(0,0,1,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                       "0)\n" % (x,y))
        self._executeScript(script)

    def scrollDown(self):
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - 100
        ytop = 200
        self.drag((x,ybottom), (x,ytop), 0.1, 10)

    def scrollUp(self):
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - 100
        ytop = 200
        self.drag((x,ytop), (x,ybottom), 0.1, 10)

    def executeCommand(self, cmd, args):
        if cmd == "quit":
            pass # for backwards compatibility only
        elif cmd == "scroll_down":
            self.scrollDown()
        elif cmd == "scroll_up":
            self.scrollUp()
        elif cmd == "tap":
            self.tap(*args)
        elif cmd == "double_tap":
            self.tap(*args, times=2)
        elif cmd == "sleep":
            sleeptime = 1
            if len(args) > 0:
                sleeptime = int(args[0])
            time.sleep(sleeptime)
        else:
            raise Exception("Unknown command")

    def executeCommands(self, cmds):
        for cmd in cmds:
            (cmd, args) = (cmd[0], cmd[1:])
            self.executeCommand(cmd, args)


class DroidADB(mozdevice.DroidADB, EidetickerMixin):

    def __init__(self, **kwargs):
        mozdevice.DroidADB.__init__(self, **kwargs)
        self._init() # custom eideticker init steps

    @property
    def dimensions(self):
        return DEVICE_PROPERTIES[self.model]['dimensions']

class DroidSUT(mozdevice.DroidSUT, EidetickerMixin):

    cached_dimensions = None
    def __init__(self, **kwargs):
        mozdevice.DroidSUT.__init__(self, **kwargs)
        self._init() # custom eideticker init steps

    @property
    def dimensions(self):
        if self.cached_dimensions:
            return self.cached_dimensions

        res_string = self.getInfo('screen')['screen'][0]
        m = re.match('X:([0-9]+) Y:([0-9]+)', res_string)
        self. cached_dimensions = (int(m.group(1)), int(m.group(2)))
        return self.cached_dimensions

    def updateApp(self, appBundlePath, processName=None, destPath=None, ipAddr=None, port=30000):
        '''Replacement for SUT version of updateApp which operates more like the ADB version'''
        '''(FIXME: TOTAL HACK ETC ETC)'''
        basename = os.path.basename(appBundlePath)
        pathOnDevice = os.path.join(self.getDeviceRoot(), basename)
        self.pushFile(appBundlePath, pathOnDevice)
        self.installApp(pathOnDevice)
        self.removeFile(pathOnDevice)

def addDeviceOptionsToParser(parser):
    parser.add_option("--host", action="store",
                      type = "string", dest = "host",
                      help = "Device hostname (only if using TCP/IP)", default=None)
    parser.add_option("-p", "--port", action="store",
                      type = "int", dest = "port",
                      help = "Custom device port (if using SUTAgent or "
                      "adb-over-tcp)", default=None)
    parser.add_option("-m", "--dm-type", action="store",
                      type = "string", dest = "dmtype",
                      help = "DeviceManager type (adb or sut, defaults to adb)")


def getDeviceParams(options):
    ''' Convert command line options and environment variables into
        parameters for getDevice()'''
    params = {}

    if options.dmtype:
        params['dmtype'] = options.dmtype
    else:
        params['dmtype'] = os.environ.get('DM_TRANS', 'adb')

    params['host']=options.host
    if not params['host'] and params['dmtype'] == "sut":
        params['host'] = os.environ.get('TEST_DEVICE')

    return params

def getDevice(dmtype="adb", host=None, port=None):
    '''Gets an eideticker device according to parameters'''
    print "Using %s interface (host: %s, port: %s)" % (dmtype, host, port)
    if dmtype == "adb":
        if host and not port:
            port = 5555
        return DroidADB(host=host, port=port)
    elif dmtype == "sut":
        if not host:
            raise Exception("Must specify host with SUT!")
        if not port:
            port = 20701
        return DroidSUT(host=host, port=port)
    else:
        raise Exception("Unknown device manager type: %s" % type)
