#!/usr/bin/env python

# This is meant to be launched by another process, which can then send
# various input events to an android phone via the monkeyrunner object
# It is meant to be invoked via the monkeyrunner executable, which is
# part of the tools provided with the Android SDK (see:
# http://developer.android.com/guide/developing/tools/monkeyrunner_concepts.html)

import StringIO
import os
import select
import socket
import subprocess
import sys
import tempfile
import time

import mozdevice

class MonkeyConnection(object):

    def __init__(self, port=9999):
        # kill any existing instances of the monkey process
        self._droid = mozdevice.DroidADB()
        self._droid.killProcess('app_process')

        subprocess.check_call(["adb", "forward", "tcp:%s" % port, "tcp:%s" % port])
        p = subprocess.Popen(["adb", "shell", "monkey", "--port", str(port)])

        connected = False
        tries = 0
        while not connected and tries < 20:
            time.sleep(0.5)
            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.connect(('localhost', port))
                self.dimensions = self._get_display_dimensions()
                connected = True
            except Exception, e:
                print "Can't connect to localhost:%s, retrying..." % port
            tries+=1

        if not connected:
            raise Exception("Could not open monkey connection!")
        print "Connected!"
        time.sleep(1)

    def _send_cmd(self, cmd):
        select.select([], [self._sock], [])
        sent = self._sock.send("%s\r\n" % cmd)
        ret = None
        while not ret:
            select.select([self._sock], [], [])
            ret = self._sock.recv(1024)
        if not ret.startswith("OK"):
            raise Exception("Exception running command '%s'. Got: %s" % (cmd, ret))
        if len(ret) > 3:
            return ret[3:]
        return ""

    def _get_display_dimensions(self):
        width = int(self._send_cmd("getvar display.width"))
        height = int(self._send_cmd("getvar display.height"))
        return [width, height]

    def tap(self, x, y):
        self._send_cmd("touch down %s %s" % (x, y))
        self._send_cmd("touch up %s %s" % (x, y))

    def _execute_script(self, script):
        '''Executes a set of monkey commands on the device'''

        f = tempfile.NamedTemporaryFile()
        f.write("type= raw events\ncount= %s\nspeed= 0.0\nstart data >>\n" % len(script.split('\n')))
        f.write(script)
        f.flush()
        print "FLUSHED: %s" % time.time()
        remotefilename = '%s/%s' % ('/mnt/sdcard/tests',
                                    os.path.basename(f.name))
        print time.time()
        self._droid.pushFile(f.name, remotefilename)
        print "PUSHED: %s" % time.time()
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
        print time.time()
        self._execute_script(script)
        print time.time()

    def double_tap(self, x, y):
        # HACK: monkeyrunner doesn't set downTime correctly when in network
        # mode, which Android's gesture recognizer needs to detect a double
        # tap properly. as a workaround, use monkey's script functionality
        script = ""
        for i in range(0,2):
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

connection = MonkeyConnection()

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
        print "QUIT: %s" % time.time()
        break
    elif cmd == "scroll_down":
        connection.scroll_down()
    elif cmd == "scroll_up":
        connection.scroll_up()
    elif cmd == "tap":
        connection.tap(*params)
    elif cmd == "double_tap":
        connection.double_tap(*params)
    elif cmd == "sleep":
        sleeptime = 1
        if len(params) > 0:
            sleeptime = int(params[0])
        time.sleep(sleeptime)
    else:
        raise Exception("Unknown command")
