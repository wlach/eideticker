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

import eideticker.device


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

    # Create a droid object to interface with the phone
    if not options.dmtype:
        options.dmtype = os.environ.get('DM_TRANS', 'adb')
    if not options.host and options.dmtype == "sut":
        options.host = os.environ.get('TEST_DEVICE')
    print "Using %s interface (host: %s, port: %s)" % (options.dmtype,
                                                       options.host,
                                                       options.port)
    device = eideticker.device.getDevice(options.dmtype, options.host, options.port)

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
        device.executeCommand(cmd, args)

if __name__ == '__main__':
    main()
