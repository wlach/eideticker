#!/usr/bin/env python

import json
import optparse
import sys

def main(args=sys.argv[1:]):
    usage = "usage: %prog <data json file> [date1] ..."
    parser = optparse.OptionParser(usage)
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("incorrect number of arguments")

    filename = args[0]
    with open(filename) as f:
        data = json.loads(f.read())
    testdata = data['testdata']

    dates = args[1:]

    # If there are no dates, then just print all dates in the json
    if not dates:
        for (platform, platformdata) in testdata.iteritems():
            for date in platformdata:
                dates.append(date)
        for date in set(dates):
            print date
        return

    # keep a backup of the original data, just in case
    backupfilename = args[0] + ".bak"
    with open(backupfilename, 'w+') as f:
        f.write(json.dumps(data))

    data_to_remove = []
    for (platform, platformdata) in testdata.iteritems():
        for date in platformdata:
            if date in dates:
                data_to_remove.append((platform, date))

    for (platform, date) in data_to_remove:
        del testdata[platform][date]

    with open(filename, 'w+') as f:
        f.write(json.dumps(data))

main()
