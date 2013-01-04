# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import StringIO
import mozdevice
import mozb2g
import os
import posixpath
import re
import tempfile
import time

# I know specifying resolution manually like this is ugly, but as far as I
# can tell there is no good, device-independant way of getting this
# information universally (we can get the resolution with SUT, but not the
# required HDMI mode)
DEVICE_PROPERTIES = {
    "android": {
        "Galaxy Nexus": {
            "hdmiResolution": "720p",
            "inputDevice": "/dev/input/event1",
            "dimensions": (1180, 720),
            "swipePadding": (240, 40, 100, 40)
            },
        "Panda": {
            "hdmiResolution": "720p",
            "inputDevice": "/dev/input/event0",
            "dimensions": (1280, 672),
            "swipePadding": (240, 40, 100, 40)
            },
        "LG-P999": {
            "hdmiResolution": "1080p",
            "inputDevice": "/dev/input/event1",
            "dimensions": (480, 800),
            "swipePadding": (240, 40, 100, 40)
            },
        "MID": {
            "hdmiResolution": None,
            "inputDevice": "/dev/input/event2",
            "dimensions": (480, 800),
            "swipePadding": (240, 40, 100, 40)
            },
        },
    "b2g": {
        "Panda": {
            "hdmiResolution": "720p",
            "inputDevice": "/dev/input/event2",
            "defaultOrientation": "landscape",
            "dimensions": (1280, 720),
            "swipePadding": (40, 40, 40, 40)
            },
        "unagi1": {
            "hdmiResolution": None,
            "inputDevice": "/dev/input/event0",
            "defaultOrientation": "portrait",
            "dimensions": (320, 480),
            "swipePadding": (40, 40, 40, 40)
            }
        }
}

class EidetickerMixin(object):
    """Mixin to extend DeviceManager with functionality to allow it to be
       remotely controlled and other related things"""

    @property
    def hdmiResolution(self):
        return self.deviceProperties['hdmiResolution']

    @property
    def inputDevice(self):
        return self.deviceProperties['inputDevice']

    def _init(self):
        self.model = self.getprop("ro.product.model")
        self.orngLocation = None

        if not DEVICE_PROPERTIES.get(self.type) or \
                not DEVICE_PROPERTIES[self.type].get(self.model):
            raise mozdevice.DMError("Unsupported device '%s' for type '%s'" % (
                    self.model, self.type))
        self.deviceProperties = DEVICE_PROPERTIES[self.type][self.model]

        # we support two locations for the orng executable: /data/local
        # and /system/xbin
        for dir in ["/data/local", "/system/xbin", "/system/bin"]:
            potentialLocation = posixpath.join(dir, "orng")
            if self.fileExists(potentialLocation):
                self.orngLocation = potentialLocation
                break

        if not self.orngLocation:
            raise mozdevice.DMError("Could not find a copy of Orangutan (orng) to run")

        # Hack: this gets rid of the "finished charging" modal dialog that the
        # LG G2X sometimes brings up
        if self.model == 'LG-P999':
            self.executeCommand("tap", [240, 617])

    # FIXME: make this part of devicemanager
    def _executeScript(self, events, executeCallback=None):
        '''Executes a set of monkey commands on the device'''
        with tempfile.NamedTemporaryFile() as f:
            f.write("\n".join(events) + "\n")
            f.flush()
            remotefilename = os.path.join(self.getDeviceRoot(),
                                          os.path.basename(f.name))
            self.pushFile(f.name, remotefilename)
            if executeCallback:
                executeCallback()
            self.shellCheckOutput([self.orngLocation, self.inputDevice,
                                   remotefilename], root=self._logcatNeedsRoot)
            self.removeFile(remotefilename)

    def getPIDs(self, appname):
        '''FIXME: Total hack, put this in devicemanagerADB instead'''
        procs = self.getProcessList()
        pids = []
        for (pid, name, user) in procs:
            if name == appname:
                pids.append(pid)
        return pids

    def sendSaveProfileSignal(self, appName):
        pids = self.getPIDs(appName)
        if pids:
            self.shellCheckOutput(['kill', '-s', '12', str(pids[0])])

    def fileExists(self, filepath):
        ret = self.shellCheckOutput(['sh', '-c', 'ls -a %s || true' % filepath])
        return ret.strip() == filepath

    def getAPK(self, appname, localfile):
        remote_tempfile = posixpath.join(self.getDeviceRoot(),
                                         'apk-tmp-%s' % time.time())
        for remote_apk_path in [ '/data/app/%s-1.apk' % appname,
                                 '/data/app/%s-2.apk' % appname ]:
            if self.fileExists(remote_apk_path):
                self.shellCheckOutput(['dd', 'if=%s' % remote_apk_path,
                                       'of=%s' % remote_tempfile], root=True)
                self.shellCheckOutput(['chmod', '0666', remote_tempfile],
                                      root=True)
                self.getFile(remote_tempfile, localfile)
                self.removeFile(remote_tempfile)
                return

        raise mozdevice.DMError("Unable to get APK for %s" % appname)

    def getprop(self, prop):
        return self.shellCheckOutput(["getprop", str(prop)])

    def setprop(self, prop, value):
        if not value:
            value = "\"\""
        self.shellCheckOutput(["setprop", str(prop), str(value)])

    def _transformXY(self, coords):
        # FIXME: Only handling 90 degrees for now, everything else falls back
        # to default
        if hasattr(self, "rotation") and self.rotation == 90:
            return (self.dimensions[1] - int(coords[1]), int(coords[0]))

        return coords

    def _getDragEvents(self, touch_start, touch_end, duration=1000, num_steps=5):
        touch_start = self._transformXY(touch_start)
        touch_end = self._transformXY(touch_end)

        return "drag %s %s %s %s %s %s" % (int(touch_start[0]), int(touch_start[1]),
                                           int(touch_end[0]), int(touch_end[1]),
                                           num_steps, duration)

    def _getSleepEvent(self, duration=1.0):
        return "sleep %s" % int(float(duration) * 1000.0)

    def _getTapEvent(self, x, y, times=1):
        coords = self._transformXY((x,y))
        return "tap %s %s %s" % (int(coords[0]), int(coords[1]), times)

    def _getScrollEvents(self, direction, numtimes=1, numsteps=10, duration=100):
        events = []
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - self.deviceProperties['swipePadding'][2]
        ytop = self.deviceProperties['swipePadding'][0]
        (p1, p2) = ((x, ybottom), (x, ytop))
        if direction == "up":
            (p1, p2) = (p2, p1)
        for i in range(int(numtimes)):
            events.append(self._getDragEvents(p1, p2, duration,
                                              int(numsteps)))
        return events

    def _getSwipeEvents(self, direction, numtimes=1, numsteps=10, duration=100):
        events = []
        y = (self.dimensions[1] / 2)
        (x1, x2) = (self.deviceProperties['swipePadding'][3],
                    self.dimensions[0] - self.deviceProperties['swipePadding'][2])
        if direction == "left":
            (x1, x2) = (x2, x1)
        for i in range(int(numtimes)):
            events.append(self._getDragEvents((x1, y), (x2, y), duration,
                                              int(numsteps)))
        return events

    def _getPinchEvent(self, touch1_x1, touch1_y1, touch1_x2, touch1_y2,
                       touch2_x1, touch2_y1, touch2_x2, touch2_y2,
                       numsteps=10, duration=1000):
        return "pinch %s %s %s %s %s %s %s %s %s %s" % (touch1_x1, touch1_y1,
                                                        touch1_x2, touch1_y2,
                                                        touch2_x1, touch2_y1,
                                                        touch2_x2, touch2_y2,
                                                        numsteps,
                                                        duration)
    def _getCmdEvents(self, cmd, args):
        if cmd == "scroll_down":
            cmdevents = self._getScrollEvents("down", *args)
        elif cmd == "scroll_up":
            cmdevents = self._getScrollEvents("up", *args)
        elif cmd == "swipe_left":
            cmdevents = self._getSwipeEvents("left", *args)
        elif cmd == "swipe_right":
            cmdevents = self._getSwipeEvents("right", *args)
        elif cmd == "tap":
            cmdevents = [self._getTapEvent(*args)]
        elif cmd == "double_tap":
            cmdevents = [self._getTapEvent(*args, times=2)]
        elif cmd == "pinch":
            cmdevents = [self._getPinchEvent(*args)]
        elif cmd == "sleep":
            if len(args):
                cmdevents = [self._getSleepEvent(duration=args[0])]
            else:
                cmdevents = [self._getSleepEvent()]
        else:
            raise Exception("Unknown command")

        return cmdevents

    def executeCommand(self, cmd, args, executeCallback=None):
        cmdevents = self._getCmdEvents(cmd, args)
        if cmdevents:
            self._executeScript(cmdevents, executeCallback=executeCallback)

    def executeCommands(self, cmds, executeCallback=None):
        cmdevents = []
        for cmd in cmds:
            (cmd, args) = (cmd[0], cmd[1:])
            cmdevents.extend(self._getCmdEvents(cmd, args))
        self._executeScript(cmdevents, executeCallback=executeCallback)

class DroidADB(EidetickerMixin, mozdevice.DroidADB):

    def __init__(self, **kwargs):
        mozdevice.DroidADB.__init__(self, **kwargs)
        self._init() # custom eideticker init steps

    @property
    def type(self):
        return "android"

    def killProcess(self, appname, forceKill=False):
        '''FIXME: Total hack, put this in devicemanagerADB instead'''
        procs = self.getProcessList()
        didKillProcess = False
        for (pid, name, user) in procs:
            if name == appname:
                self._runCmd(["shell", "echo kill %s | su" % pid])
                didKillProcess = True
        return didKillProcess

    @property
    def dimensions(self):
        return self.deviceProperties['dimensions']

    @property
    def rotation(self):
        return 0 # No way to find real rotation, assume 0

class DroidSUT(EidetickerMixin, mozdevice.DroidSUT):

    cached_dimensions = None
    cached_rotation = None
    def __init__(self, **kwargs):
        mozdevice.DroidSUT.__init__(self, **kwargs)
        self._init() # custom eideticker init steps

    @property
    def type(self):
        return "android"

    @property
    def dimensions(self):
        if self.cached_dimensions:
            return self.cached_dimensions

        res_string = self.getInfo('screen')['screen'][0]
        m = re.match('X:([0-9]+) Y:([0-9]+)', res_string)
        self.cached_dimensions = (int(m.group(1)), int(m.group(2)))
        return self.cached_dimensions

    @property
    def rotation(self):
        # for now we assume rotation never changes
        if self.cached_rotation:
            return self.cached_rotation

        rot_string = self.getInfo('rotation')['rotation'][0]
        m = re.match('ROTATION:([0-9]+)', rot_string)
        self.cached_rotation = int(m.group(1))
        return self.cached_rotation

    def updateApp(self, appBundlePath, processName=None, destPath=None, ipAddr=None, port=30000):
        '''Replacement for SUT version of updateApp which operates more like the ADB version'''
        '''(FIXME: TOTAL HACK ETC ETC)'''
        basename = os.path.basename(appBundlePath)
        pathOnDevice = os.path.join(self.getDeviceRoot(), basename)
        self.pushFile(appBundlePath, pathOnDevice)
        self.installApp(pathOnDevice)
        self.removeFile(pathOnDevice)

class EidetickerB2GMixin(EidetickerMixin):
    """B2G-specific extensions to the eideticker mixin"""

    def resetOrientation(self):
        self.setOrientation(self.deviceProperties['defaultOrientation'])

    def setOrientation(self, orientation):
        # set landscape or portrait mode
        print "Setting orientation: %s" % orientation
        self.marionette.execute_script("screen.mozLockOrientation('%s');" % orientation)

class B2GADB(EidetickerB2GMixin, mozb2g.DeviceADB):
    def __init__(self, **kwargs):
        mozb2g.DeviceADB.__init__(self, **kwargs)
        self._init() # custom eideticker init steps
        self.setupProfile()

    @property
    def type(self):
        return "b2g"

    @property
    def dimensions(self):
        return self.deviceProperties['dimensions']

    def rotation(self):
        return 90 # Assume portrait orientation for now

class B2GSUT(EidetickerB2GMixin, mozb2g.DeviceSUT):
    def __init__(self, **kwargs):
        mozb2g.DeviceSUT.__init__(self, **kwargs)
        self._init() # custom eideticker init steps
        self.setupProfile()

    @property
    def type(self):
        return "b2g"

def getDevicePrefs(options):
    '''Gets a dictionary of eideticker device parameters'''
    optionDict = {}
    optionDict['dmtype'] = options.dmtype
    optionDict['devicetype'] = options.devicetype

    host = options.host
    if not host and optionDict['dmtype'] == "sut":
        host = os.environ.get('TEST_DEVICE')

    optionDict['host'] = host
    optionDict['port'] = options.port

    return optionDict

def getDevice(dmtype="adb", devicetype="android", host=None, port=None):
    '''Gets an eideticker device according to parameters'''

    print "Using %s interface (type: %s, host: %s, port: %s)" % (dmtype,
                                                                 devicetype,
                                                                 host, port)
    if dmtype == "adb":
        if host and not port:
            port = 5555
        if devicetype=='b2g':
            # HACK: Assume adb-over-usb for now, with marionette forwarded
            # to localhost via "adb forward tcp:2828 tcp:2828"
            return B2GADB(marionetteHost="127.0.0.1")
            #return B2GADB(host=host, port=port)
        else:
            return DroidADB(packageName=None, host=host, port=port)
    elif dmtype == "sut":
        if not host:
            raise Exception("Must specify host with SUT!")
        if not port:
            port = 20701
        if devicetype=='b2g':
            return B2GSUT(host=host, port=port)
        else:
            return DroidSUT(host=host, port=port)
    else:
        raise Exception("Unknown device manager type: %s" % type)
