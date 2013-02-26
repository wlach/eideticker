#!/usr/bin/env python

import os
import sys
import eideticker

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")

def main(args=sys.argv[1:]):
    usage = "usage: %prog <product> <date>"
    parser = eideticker.OptionParser(usage=usage)

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")

    (productname, datestr) = args

    product = eideticker.get_product(productname)

    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)

    if device.type != 'android':
        print "Device type '%s' does not currently support updates" % device.type
        sys.exit(0)

    if not product.get('reponame'):
        print "No download / installation needed for %s" % product['name']
    else:
        print "Downloading %s (date: %s)" % (product['name'], datestr)
        br = eideticker.BuildRetriever()
        if datestr == 'latest':
            date = None
        else:
            date = eideticker.BuildRetriever.get_date(datestr)
        filename = br.get_build(product, date)

        print "Installing %s (%s)" % (product['name'], filename)
        device.updateApp(filename)

main()
