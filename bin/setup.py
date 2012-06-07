#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import optparse
import os
import sys
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../conf/talos.config")

usage = "usage: %prog [options] <device ip> <fennec appname>"
parser = optparse.OptionParser(usage)

options, args = parser.parse_args()
if len(args) != 2:
    parser.error("incorrect number of arguments")

try:
    open(CONFIG_FILE, "w").write(json.dumps({"device_ip": args[0],
                                             "appname": args[1]}))
except:
    fatal_error("Could not write configuration file %s" % CONFIG_FILE)
