#!/usr/bin/env python

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
    usage = "usage: %prog <apk of build> <test> <metric>"
    parser = optparse.OptionParser(usage)

    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error("incorrect number of arguments")

    (apk, test, metric) = args

    valid_metrics = ['fps', 'checkerboard']
    if metric not in valid_metrics:
        parser.error("bad metric '%s' (valid metrics: %s)" % (metric, ",".join(valid_metrics)))

    # first get the appname from the apk
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

    if metric == 'fps':
        framediff_sums = videocapture.get_framediff_sums(capture)
        num_different_frames = 1 + len([framediff for framediff in framediff_sums if framediff > 250])
        print "Estimated FPS: %s" % (num_different_frames / capture.length)
    elif metric == 'checkerboard':
        print "Checkerboard area/duration (sum of percents NOT percentage): %s" % videocapture.get_checkerboarding_area_duration(capture)

    print "Capture file is '%s'" % capture_file

main()
