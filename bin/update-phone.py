#!/usr/bin/env python

import optparse
import os
import sys
import urllib2
from eideticker.products import default_products
import eideticker

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")

def main(args=sys.argv[1:]):
    usage = "usage: %prog [product1] [product2]"
    parser = eideticker.OptionParser(usage=usage)

    options, args = parser.parse_args()
    if len(args):
        products = [product for product in default_products if product['name'] in args]
    else:
        products = default_products

    if not products:
        print "No products matching arguments!"
        sys.exit(1)

    print products

    device = eideticker.getDevice(options)

    for product in products:
        if not product.get('url'):
            print "No download / installation needed for %s" % product['name']
        else:
            print "Downloading %s" % product['name']
            product_fname = os.path.join(DOWNLOAD_DIR, "%s.apk" % product['name'])

            dl = urllib2.urlopen(product['url'])
            with open(product_fname, 'w') as f:
                f.write(dl.read())
            device.updateApp(product_fname)

main()
