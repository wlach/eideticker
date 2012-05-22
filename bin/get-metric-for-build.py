#!/usr/bin/env python

import datetime
import json
import mozdevice
from mozregression.runnightly import FennecNightly
from mozregression.utils import get_date
import optparse
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib2
import videocapture
import zipfile

CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
CHECKERBOARD_REGEX = re.compile('.*GeckoLayerRendererProf.*1000ms:.*\ '
                                '([0-9]+\.[0-9]+)\/([0-9]+).*')

# FIXME: copypasted from update-dashboard
def kill_app(dm, appname):
    procs = dm.getProcessList()
    for (pid, name, user) in procs:
      if name == appname:
        dm.runCmd(["shell", "echo kill %s | su" % pid])

def parse_checkerboard_log(fname):
    checkerboarding_percent_totals = 0.0
    with open(fname) as f:
        for line in f.readlines():
            match = CHECKERBOARD_REGEX.search(line.rstrip())
            if match:
                (amount, total) = (float(match.group(1)), float(match.group(2)))
                checkerboarding_percent_totals += (total - amount)

    return checkerboarding_percent_totals

def get_build_for_date(date):
    fname = os.path.join(DOWNLOAD_DIR,
                         "nightly-%s-%s-%s.apk" % (date.year,
                                                   date.month,
                                                   date.day))
    if os.path.exists(fname):
        print "Build already exists for %s. Skipping download." % date
        return fname

    fennec = FennecNightly()
    build_url = fennec.getBuildUrl(date)
    if not build_url:
        print "ERROR: Couldn't get build url for date %s" % date
        return None

    print "Downloading %s" % build_url
    dl = urllib2.urlopen(build_url)
    with open(fname, 'w') as f:
        f.write(dl.read())

    return fname

def run_test(device, apk, outputfile, test, url_params, num_runs, no_capture,
             get_internal_checkerboard_stats):
    with zipfile.ZipFile(apk) as zip:
        try:
            appname = zip.read('package-name.txt').rstrip()
        except KeyError:
            print "No file named 'package-name.txt' in archive. Are you sure "
            "this is a fennec apk?"
            sys.exit(1)
        print "appname is '%s'" % appname


    device.updateApp(apk)

    captures = []

    for i in range(num_runs):
        # Kill any existing instances of the processes
        kill_app(device, appname)

        # Now run the test
        capture_file = os.path.join(CAPTURE_DIR,
                                    "metric-test-%s-%s.zip" % (appname,
                                                               int(time.time())))
        args = ["runtest.py", "--url-params", url_params, appname, test]
        if get_internal_checkerboard_stats:
            checkerboard_logfile = tempfile.NamedTemporaryFile()
            args.extend(["--checkerboard-log-file", checkerboard_logfile.name])
        if no_capture:
            args.extend(["--no-capture"])
        else:
            args.extend(["--capture-file", capture_file])
        print args
        retval = subprocess.call(args)
        if retval != 0:
            raise Exception("Failed to run test %s for %s" % (test, appname))

        capture_result = {}
        if not no_capture:
            capture_result['file'] = capture_file

            capture = videocapture.Capture(capture_file)

            framediff_sums = videocapture.get_framediff_sums(capture)
            capture_result['uniqueframes'] = 1 + len([framediff for framediff in framediff_sums if framediff > 0])

            capture_result['checkerboard'] = videocapture.get_checkerboarding_area_duration(capture)

        if get_internal_checkerboard_stats:
            internal_checkerboard_totals = parse_checkerboard_log(checkerboard_logfile.name)
            capture_result['internalcheckerboard'] = internal_checkerboard_totals

        captures.append(capture_result)

    apkname = os.path.basename(apk)
    print "=== Results for %s ===" % apkname

    if not no_capture:
        print "  Number of unique frames:"
        print "  %s" % map(lambda c: c['uniqueframes'], captures)
        print

        print "  Checkerboard area/duration (sum of percents NOT percentage):"
        print "  %s" % map(lambda c: c['checkerboard'], captures)
        print

        print "  Capture files (for further reference):"
        print "  Capture files: %s" % map(lambda c: c['file'], captures)
        print

    if get_internal_checkerboard_stats:
        print "  Internal Checkerboard Stats (sum of percents, not percentage):"
        print "  %s" % map(lambda c: c['internalcheckerboard'], captures)
        print

    if outputfile:
        data = {}
        if os.path.isfile(outputfile):
            data.update(json.loads(open(outputfile).read()))

        if not data.get(apkname):
            data[apkname] = []
        data[apkname].extend(captures)

        with open(outputfile, 'w') as f:
            f.write(json.dumps(data))

def main(args=sys.argv[1:]):
    usage = "usage: %prog <test> [apk of build]"
    parser = optparse.OptionParser(usage)
    parser.add_option("--num-runs", action="store",
                      type = "int", dest = "num_runs",
                      default=1,
                      help = "number of runs (default: 1)")
    parser.add_option("--output-file", action="store",
                      type="string", dest="output_file",
                      help="output results to json file")
    parser.add_option("--no-capture", action="store_true",
                      dest = "no_capture",
                      help = "run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--get-internal-checkerboard-stats",
                      action="store_true",
                      dest="get_internal_checkerboard_stats",
                      help="get and calculate internal checkerboard stats")
    parser.add_option("--url-params", action="store",
                      dest="url_params", default="",
                      help="additional url parameters for test")
    parser.add_option("--date", action="store", dest="date",
                      metavar="YYYY-MM-DD",
                      help="get and test nightly build for date")
    parser.add_option("--start-date", action="store", dest="start_date",
                      metavar="YYYY-MM-DD",
                      help="start date for range of nightlies to test")
    parser.add_option("--end-date", action="store", dest="end_date",
                      metavar="YYYY-MM-DD",
                      help="end date for range of nightlies to test")

    options, args = parser.parse_args()

    dates = []
    apk = None
    if options.start_date and options.end_date and len(args) == 1:
        test = args[0]
        start_date = get_date(options.start_date)
        end_date = get_date(options.end_date)
        days=(end_date-start_date).days
        for numdays in range(days+1):
            dates.append(start_date+datetime.timedelta(days=numdays))
    elif options.date and len(args) == 1:
        test = args[0]
        dates = [get_date(options.date)]
    elif not options.date and len(args) == 2:
        (apk, test) = args
    elif not options.date or (not options.start_date and not options.end_date):
        parser.error("Must specify date, date range, or a (single) apk file")

    device = mozdevice.DroidADB(packageName=None)
    if apk:
        run_test(device, apk, options.output_file, test, options.url_params,
                 options.num_runs, options.no_capture,
                 options.get_internal_checkerboard_stats)
    else:
        for date in dates:
            apk = get_build_for_date(date)
            run_test(device, apk, options.output_file, test,
                     options.url_params, options.num_runs,
                     options.no_capture,
                     options.get_internal_checkerboard_stats)


main()
