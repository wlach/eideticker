#!/usr/bin/env python

import datetime
import glob
import os
import re
import time

now = int(time.time())

expire_before = now - 7*24*60*60

print 'expiring captures before %s' % datetime.datetime.fromtimestamp(expire_before)

captures = glob.glob('captures/*.zip')
captures.extend(glob.glob('captures/*.cache'))

capture_re = re.compile('-(\d{10}).[^\.]+$')

to_expire = []

for f in captures:
    m = re.search(capture_re, f)
    if not m:
        continue
    timestamp = int(m.group(1))
    if timestamp < expire_before:
        to_expire.append(f)

print 'expiring %d files' % len(to_expire)

for f in to_expire:
    os.unlink(f)

