#!/usr/bin/env python

import eideticker
import sys

def main(args=sys.argv[1:]):
    usage = "usage: %prog"
    parser = eideticker.OptionParser(usage=usage)

    options, args = parser.parse_args()

    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)
    device.cleanup()

main()
