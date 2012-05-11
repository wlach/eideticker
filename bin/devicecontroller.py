#!/usr/bin/env python

import StringIO
import optparse
import os
import select
import socket
import subprocess
import sys
import tempfile
import time

import mozdevice

class DeviceController(object):

    def __init__(self, droid, device_width, device_height):
        self._droid = droid
        self.dimensions  = (device_width, device_height)

    def _execute_script(self, script):
        '''Executes a set of monkey commands on the device'''
        f = tempfile.NamedTemporaryFile()
        f.write("type= raw events\ncount= %s\nspeed= 0.0\nstart data >>\n" % len(script.split('\n')))
        f.write(script)
        f.flush()
        remotefilename = os.path.join(self._droid.getDeviceRoot(),
                                      os.path.basename(f.name))
        self._droid.pushFile(f.name, remotefilename)
        buf = StringIO.StringIO()
        self._droid.shell(["su", "-c", "LD_LIBRARY_PATH=/vendor/lib:/system/lib monkey -f %s 1" % remotefilename], buf)

    def drag(self, touch_start, touch_end, duration=1.0, num_steps=5):
        script = ""
        script += ("createDispatchPointer(0,-1,0,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                   "0)\n" % touch_start)
        delta = ((touch_end[0] - touch_start[0]) / num_steps,
                 (touch_end[1] - touch_start[1]) / num_steps)
        for i in range(num_steps):
            current = (touch_start[0] + delta[0]*i,
                       touch_start[1] + delta[1]*i)
            script += ("createDispatchPointer(0,-1,2,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                       "0)\n" % current)
            script += ("UserWait(%s)\n" % int((duration / num_steps) * 1000.0))
        script += ("createDispatchPointer(0,-1,1,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                   "0)\n" % touch_end)
        print script
        self._execute_script(script)

    def tap(self, x, y, times=1):
        script = ""
        for i in range(0, times):
            script += ("createDispatchPointer(0,-1,0,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                          "0)\n" % (x,y))
            script += ("createDispatchPointer(0,-1,1,%s,%s,1.0,1.0,0,0.0,0.0,-1,"
                       "0)\n" % (x,y))
        self._execute_script(script)

    def scroll_down(self):
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - 100
        ytop = 200
        self.drag((x,ybottom), (x,ytop), 0.1, 10)

    def scroll_up(self):
        x = int(self.dimensions[0] / 2)
        ybottom = self.dimensions[1] - 100
        ytop = 200
        self.drag((x,ytop), (x,ybottom), 0.1, 10)

    def execute_command(self, cmd, args):
        if cmd == "quit":
            pass # for backwards compatibility only
        elif cmd == "scroll_down":
            self.scroll_down()
        elif cmd == "scroll_up":
            self.scroll_up()
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

    def execute_commands(self, cmds):
        for cmd in cmds:
            (cmd, args) = (cmd[0], cmd[1:])
            self.execute_command(cmd, args)

def get_droid(type, host, port):
    if type == "adb":
        if host and not port:
            port = 5555
        return mozdevice.DroidADB(host=host, port=port)
    elif type == "sut":
        if not host:
            raise Exception("Must specify host with SUT!")
        if not port:
            port = 20701
        return mozdevice.DroidSUT(host=host, port=port)
    else:
        raise Exception("Unknown device manager type: %s" % type)

def main(args=sys.argv[1:]):

    usage = "usage: %prog <device width> <device height>"
    parser = optparse.OptionParser(usage)
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

    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    # Create a droid object to interface with the phone
    if not options.dmtype:
        options.dmtype = os.environ.get('DM_TRANS', 'adb')
    if not options.host and options.dmtype == "sut":
        options.host = os.environ.get('TEST_DEVICE')
    print "Using %s interface (host: %s, port: %s)" % (options.dmtype,
                                                       options.host,
                                                       options.port)
    droid = get_droid(options.dmtype, options.host, options.port)

    device = DeviceController(droid, int(args[0]), int(args[1]))

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

        (cmd, args) = (tokens[0], tokens[1:])
        device.execute_command(cmd, args)

if __name__ == '__main__':
    main()
