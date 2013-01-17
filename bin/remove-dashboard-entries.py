#!/usr/bin/env python

import json
import optparse
import sys
import eideticker
import datetime

def main(args=sys.argv[1:]):
    usage = "usage: %prog <data json file> [date1] ..."
    parser = optparse.OptionParser(usage)
    parser.add_option("--start-date", action="store", dest="start_date",
                      metavar="YYYY-MM-DD",
                      help="start date for range of entries to remove")
    parser.add_option("--end-date", action="store", dest="end_date",
                      metavar="YYYY-MM-DD",
                      help="end date for range of entries to remove")
    parser.add_option('--dry-run', dest='dry_run',
                      action='store_true', default=False,
                      help="don't make changes, just display what would be removed")
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("incorrect number of arguments")
    elif (options.start_date and not options.end_date) or \
            (not options.start_date and options.end_date):
        parser.error("If start date is specified, so must end date and "
                     "vice versa")

    filename = args[0]
    with open(filename) as f:
        data = json.loads(f.read())
    testdata = data['testdata']

    if options.start_date and options.end_date:
        start_date = eideticker.BuildRetriever.get_date(options.start_date)
        end_date = eideticker.BuildRetriever.get_date(options.end_date)
        days=(end_date-start_date).days
        dates = []
        for numdays in range(days+1):
            dates.append(str(start_date+datetime.timedelta(days=numdays)))
    else:
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
    if not options.dry_run:
        backupfilename = args[0] + ".bak"
        with open(backupfilename, 'w+') as f:
            f.write(json.dumps(data))

    data_to_remove = []
    for (platform, platformdata) in testdata.iteritems():
        for date in platformdata:
            if date in dates:
                data_to_remove.append((platform, date))

    for (platform, date) in data_to_remove:
        if not options.dry_run:
            del testdata[platform][date]
        else:
            print "%s %s" % (platform, date)

    if not options.dry_run:
        with open(filename, 'w+') as f:
            f.write(json.dumps(data))

main()
