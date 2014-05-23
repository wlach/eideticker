#!/usr/bin/env python

import eideticker
import optparse
import sys

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options]"

    parser = optparse.OptionParser(usage=usage)
    eideticker.add_dashboard_options(parser)

    options, args = parser.parse_args()

    if args: # should not be specifying any arguments
        parser.print_usage()
        sys.exit(1)

    if not options.dashboard_server:
        parser.error("ERROR: Need to specify dashboard server (via the "
                     "--dashboard-server option)")

    eideticker.upload_dashboard(options)

main()
