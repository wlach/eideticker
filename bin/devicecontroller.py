#!/usr/bin/env python

# This is meant to be launched by another process, though you can also
# call it by hand if you know the device resolution

import StringIO
import os
import select
import socket
import subprocess
import sys
import tempfile
import time

import mozdevice

class Device(object):

    def __init__(self, device_width, device_height):
        self.dimensions  = (device_width, device_height)
        self._droid = mozdevice.DroidADB()

    def _execute_script(self, script):
        '''Executes a set of monkey commands on the device'''
        f = tempfile.NamedTemporaryFile()
        f.write("type= raw events\ncount= %s\nspeed= 0.0\nstart data >>\n" % len(script.split('\n')))
        f.write(script)
        f.flush()
        remotefilename = '%s/%s' % ('/mnt/sdcard/tests',
                                    os.path.basename(f.name))
        self._droid.pushFile(f.name, remotefilename)
        buf = StringIO.StringIO()
        self._droid.shell(["monkey", "-f", remotefilename, "1"], buf)

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
        self._execute_script(script)

    def tap(self, x, y, times=1):
        script = ""
        for i in range(0, times):
            script += ("createDispatchPointer(0,0,0,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                          "0)\n" % (x,y))
            script += ("createDispatchPointer(0,0,1,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                       "0)\n" % (x,y))
        self._execute_script(script)

    def scroll_down(self):
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - 100
        ytop = 120
        self.drag((x,ybottom), (x,ytop), 0.1, 5)

    def scroll_up(self):
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - 100
        ytop = 120
        self.drag((x,ytop), (x,ybottom), 0.1, 5)


if len(sys.argv) != 3:
    print "Usage: %prog <device width> <device height>"
    sys.exit(1)

device = Device(int(sys.argv[1]), int(sys.argv[2]))

print "READY"
sys.stdout.flush()

while 1:
    try:
        line = sys.stdin.readline()
    except KeyboardInterrupt:
        break

    if not line:
        break

    tokens = line.rstrip().split()
    if len(tokens) < 1:
        raise Exception("No command")

    (cmd, params) = (tokens[0], tokens[1:])

    if cmd == "quit":
        break
    elif cmd == "scroll_down":
        device.scroll_down()
    elif cmd == "scroll_up":
        device.scroll_up()
    elif cmd == "tap":
        device.tap(*params)
    elif cmd == "double_tap":
        device.tap(*params, times=2)
    elif cmd == "sleep":
        sleeptime = 1
        if len(params) > 0:
            sleeptime = int(params[0])
        time.sleep(sleeptime)
    else:
        raise Exception("Unknown command")
