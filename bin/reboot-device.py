#!/usr/bin/env python

# Reboots device and waits for it to come back with the watcher started

import mozdevice
import sys
import time

WATCHER_TIMEOUT=120

dm = mozdevice.DroidADB()
dm.reboot(wait=True)

wait_start = time.time()
elapsed = 0
while elapsed < WATCHER_TIMEOUT:
    if dm.processExist('com.mozilla.watcher'):
        print "Watcher running! We are good"
        sys.exit(0)

    remaining = (WATCHER_TIMEOUT - elapsed)
    print "Waiting for watcher... (%s seconds remaining)" % remaining
    time.sleep(5)
    elapsed = time.time() - wait_start

print "ERROR: Timed out waiting for watcher"
sys.exit(1)
