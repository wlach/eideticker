#!/usr/bin/env python

import datetime
import glob
import os
import re
import time

now = int(time.time())

expire_before = now - 7*24*60*60

print 'expiring files before %s' % datetime.datetime.fromtimestamp(expire_before)

files = glob.glob('src/dashboard/videos/*.webm')
files.extend(glob.glob('captures/*.zip'))
files.extend(glob.glob('captures/*.cache'))

stamped_file_re = re.compile('-(\d{10})(\.?)(\d+)?.[^\.]+$')

to_expire = []

for f in files:
    m = re.search(stamped_file_re, f)
    if not m:
        continue
    timestamp = int(m.group(1))
    if timestamp < expire_before:
        to_expire.append(f)

print 'expiring %d files' % len(to_expire)
for f in to_expire:
    os.unlink(f)

