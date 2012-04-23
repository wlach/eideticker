#!/usr/bin/env python

import json
import mozdevice
import optparse
import os
import subprocess
import sys
import time
import videocapture
import zipfile

CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

# FIXME: copypasted from update-dashboard
def kill_app(dm, appname):
    procs = dm.getProcessList()
    for (pid, name, user) in procs:
      if name == appname:
        dm.runCmd(["shell", "echo kill %s | su" % pid])

def main(args=sys.argv[1:]):
    usage = "usage: %prog <apk of build> <test>"
    parser = optparse.OptionParser(usage)
    parser.add_option("--num-runs", action="store",
                      type = "int", dest = "num_runs",
                      help = "number of runs (default: 1)")
    parser.add_option("--output-file", action="store",
                      type="string", dest="output_file",
                      help="output results to json file")

    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    (apk, test) = args

    num_runs = 1
    if options.num_runs:
        num_runs = options.num_runs

    with zipfile.ZipFile(apk) as zip:
        try:
            appname = zip.read('package-name.txt').rstrip()
        except KeyError:
            print "No file named 'package-name.txt' in archive. Are you sure "
            "this is a fennec apk?"
            sys.exit(1)
        print "appname is '%s'" % appname

    droid = mozdevice.DroidADB(packageName=appname)
    droid.updateApp(apk)

    captures = []

    for i in range(num_runs):
        # Kill any existing instances of the processes
        kill_app(droid, appname)

        # Now run the test
        capture_file = os.path.join(CAPTURE_DIR,
                                    "metric-test-%s-%s.zip" % (appname,
                                                               int(time.time())))

        retval = subprocess.call(["runtest.py", "--capture-file", capture_file,
                                  appname, test])
        if retval != 0:
            raise Exception("Failed to run test %s for %s" % (test, appname))

        capture = videocapture.Capture(capture_file)

        framediff_sums = videocapture.get_framediff_sums(capture)
        num_unique_frames = 1 + len([framediff for framediff in framediff_sums if framediff > 0])

        checkerboard = videocapture.get_checkerboarding_area_duration(capture)

        captures.append({'capture_file': capture_file, 'checkerboard': checkerboard,
                         'uniqueframes': num_unique_frames})

    print "=== Number of unique frames ==="
    print "%s" % map(lambda c: c['uniqueframes'], captures)
    print

    print "=== Checkerboard area/duration (sum of percents NOT percentage) ==="
    print "%s" % map(lambda c: c['checkerboard'], captures)
    print

    print "Capture files: %s" % map(lambda c: c['capture_file'], captures)

    if options.output_file:
        with open(options.output_file, 'w') as f:
            f.write(json.dumps(captures))

main()
