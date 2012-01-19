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

while 1:
    try:
        line = sys.stdin.readline()
    except KeyboardInterrupt:
        break

    if not line:
        break

    cmd = line.rstrip()

    if cmd == "quit":
        break
    elif cmd == "scroll_down":
        device.scroll_down()
    elif cmd == "sleep":
        time.sleep(1)
    else:
        raise Exception("Unknown command")
