#!/usr/bin/env python

import eideticker
import re
import sys

def main(args=sys.argv[1:]):
    usage = "usage: %prog"
    parser = eideticker.OptionParser(usage=usage)

    options, args = parser.parse_args()

    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)

    if device.type == 'b2g':
        print "No cleanup presently required on b2g"
        return

    for product in eideticker.products:
        if product['platform'] == device.type:
            device.killProcess(product['appname'])

    # clean up any test stuff (profiles, etc.)
    device.removeDir(device.getDeviceRoot())

    # profile files are dumped directly to the sdcard,
    # not the testroot so we need to clean them up
    # seperately
    files = device.listFiles('/mnt/sdcard/')
    for file in files:
        if re.match('profile_.*txt', file):
            device.removeFile('/mnt/sdcard/%s' % file)

main()
