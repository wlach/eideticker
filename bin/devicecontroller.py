#!/usr/bin/env python

# This is meant to be launched by another process, which can then send
# various input events to an android phone via the monkeyrunner object
# It is meant to be invoked via the monkeyrunner executable, which is
# part of the tools provided with the Android SDK (see:
# http://developer.android.com/guide/developing/tools/monkeyrunner_concepts.html)

import sys
import time
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

class Device(object):

    def __init__(self):
        self.device = MonkeyRunner.waitForConnection()
        self.width = int(self.device.getProperty('display.width'))
        self.height = int(self.device.getProperty('display.height'))

    def scroll_down(self):
        x = int(self.width / 2)
        ybottom = self.height - 100
        ytop = 200
        self.device.drag((x,ybottom), (x, ytop), 0.1, 5)

device = Device()

print "READY"

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
        device.scroll_down()
    elif cmd == "sleep":
        sleeptime = 1
        if len(params) > 0:
            sleeptime = int(params[0])
        time.sleep(sleeptime)
    else:
        raise Exception("Unknown command")
