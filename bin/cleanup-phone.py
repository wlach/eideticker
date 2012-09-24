#!/usr/bin/env python

import sys
from eideticker.products import default_products
import eideticker

def main(args=sys.argv[1:]):
    usage = "usage: %prog"
    parser = eideticker.OptionParser(usage=usage)

    options, args = parser.parse_args()

    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)

    for product in default_products:
        device.killProcess(product['appname'])

    # clean up any test stuff (profiles, etc.)
    device.removeDir(device.getDeviceRoot())

main()
