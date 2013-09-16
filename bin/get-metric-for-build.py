#!/usr/bin/env python

import datetime
import eideticker
import json
import os
import sys
import time
import videocapture

CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")
PROFILE_DIR = os.path.join(os.path.dirname(__file__), "../profiles")

def runtest(device_prefs, testname, options, apk=None, appname = None,
            appdate = None):
    device = None
    if apk:
        appinfo = eideticker.get_fennec_appinfo(apk)
        appname = appinfo['appname']
        print "Installing %s (version: %s, revision %s)" % (appinfo['appname'],
                                                            appinfo['version'],
                                                            appinfo['revision'])
        device = eideticker.getDevice(**device_prefs)
        device.updateApp(apk)
    else:
        appinfo = None

    capture_results = []

    for i in range(options.num_runs):
        # Kill any existing instances of the processes (for Android)
        if device:
            device.killProcess(appname)

        # Now run the test
        curtime = int(time.time())
        capture_file = os.path.join(CAPTURE_DIR,
                                    "metric-test-%s-%s.zip" % (appname,
                                                               curtime))
        if options.enable_profiling:
            profile_file = os.path.join(PROFILE_DIR,
                                        "profile-%s-%s.zip" % (appname, curtime))
        else:
            profile_file = None

        current_date = time.strftime("%Y-%m-%d")
        capture_name = "%s - %s (taken on %s)" % (testname, appname, current_date)

        testlog = eideticker.run_test(testname, options.capture_device,
                                      appname, capture_name, device_prefs,
                                      extra_prefs=options.extra_prefs,
                                      extra_env_vars=options.extra_env_vars,
                                      log_checkerboard_stats=options.get_internal_checkerboard_stats,
                                      profile_file=profile_file,
                                      capture_area=options.capture_area,
                                      no_capture=options.no_capture,
                                      capture_file=capture_file,
                                      sync_time=options.sync_time)

        capture_result = {}
        if not options.no_capture:
            capture_result['file'] = capture_file

            capture = videocapture.Capture(capture_file)

            difference_threshold = 2048
            if options.capture_device == "pointgrey":
                # even with median filtering, pointgrey captures tend to have a
                # bunch of visual noise -- try to compensate for this by setting
                # a higher threshold for frames to be considered different
                difference_threshold = 4096


            if options.startup_test:
                capture_result['stableframe'] = videocapture.get_stable_frame(capture,
                                                                              threshold=difference_threshold)
            else:
                capture_result.update(
                    eideticker.get_standard_metrics(capture, testlog.actions,
                                                    difference_threshold=difference_threshold))
            if options.outputdir:
                video_path = os.path.join('videos', 'video-%s.webm' % time.time())
                video_file = os.path.join(options.outputdir, video_path)
                open(video_file, 'w').write(capture.get_video().read())
                capture_result['video'] = video_path

        if options.enable_profiling:
            capture_result['profile'] = profile_file

        if options.get_internal_checkerboard_stats:
            capture_result['internalcheckerboard'] = testlog.checkerboard_percent_totals

        capture_results.append(capture_result)

    if options.devicetype == "b2g":
        # FIXME: get information from sources.xml and application.ini on
        # device, as we do in update-dashboard.py
        display_key = "FirefoxOS"
    else:
        appkey = appname
        if appdate:
            appkey = appdate.isoformat()
        else:
            appkey = appname

        if appinfo and appinfo.get('revision'):
            display_key = "%s (%s)" % (appkey, appinfo['revision'])
        else:
            display_key = appkey

    print "=== Results on %s for %s ===" % (testname, display_key)

    if not options.no_capture:
        if options.startup_test:
            print "  First stable frames:"
            print "  %s" % map(lambda c: c['stableframe'], capture_results)
            print
        else:
            print "  Number of unique frames:"
            print "  %s" % map(lambda c: c['uniqueframes'], capture_results)
            print

            print "  Average number of unique frames per second:"
            print "  %s" % map(lambda c: c['fps'], capture_results)
            print

            print "  Checkerboard area/duration (sum of percents NOT percentage):"
            print "  %s" % map(lambda c: c['checkerboard'], capture_results)
            print

            print "  Time to first input response: "
            print "  %s" % map(lambda c: c['timetoresponse'], capture_results)
            print

        print "  Capture files:"
        print "  Capture files: %s" % map(lambda c: c['file'], capture_results)
        print

    if options.enable_profiling:
        print "  Profile files:"
        print "  Profile files: %s" % map(lambda c: c['profile'], capture_results)
        print

    if options.get_internal_checkerboard_stats:
        print "  Internal Checkerboard Stats (sum of percents, not percentage):"
        print "  %s" % map(lambda c: c['internalcheckerboard'], capture_results)
        print

    if options.outputdir:
        outputfile = os.path.join(options.outputdir, "metric-test-%s.json" % time.time())
        resultdict = { 'title': testname, 'data': {} }
        if os.path.isfile(outputfile):
            resultdict.update(json.loads(open(outputfile).read()))

        if not resultdict['data'].get(appkey):
            resultdict['data'][appkey] = []
        resultdict['data'][appkey].extend(capture_results)

        with open(outputfile, 'w') as f:
            f.write(json.dumps(resultdict))

def main(args=sys.argv[1:]):
    usage = "usage: %prog <test> [appname1] [appname2] ..."
    parser = eideticker.TestOptionParser(usage=usage)
    parser.add_option("--num-runs", action="store",
                      type = "int", dest = "num_runs",
                      default=1,
                      help = "number of runs (default: 1)")
    parser.add_option("--output-dir", action="store",
                      type="string", dest="outputdir",
                      help="output results to json file")
    parser.add_option("--no-capture", action="store_true",
                      dest = "no_capture",
                      help = "run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--enable-profiling", action="store_true",
                      dest = "enable_profiling",
                      help="Collect performance profiles using the built in profiler.")
    parser.add_option("--get-internal-checkerboard-stats",
                      action="store_true",
                      dest="get_internal_checkerboard_stats",
                      help="get and calculate internal checkerboard stats")
    parser.add_option("--startup-test",
                      action="store_true",
                      dest="startup_test",
                      help="measure startup times instead of normal metrics")
    parser.add_option("--url-params", action="store",
                      dest="url_params", default="",
                      help="additional url parameters for test")
    parser.add_option("--use-apks", action="store_true", dest="use_apks",
                      help="use and install android APKs as part of test (instead of specifying appnames)")
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

    if len(args) == 0:
        parser.error("Must specify at least one argument: the test")

    dates = []
    appnames = []
    apks = []
    if options.start_date and options.end_date and len(args) == 1:
        testname = args[0]
        start_date = eideticker.BuildRetriever.get_date(options.start_date)
        end_date = eideticker.BuildRetriever.get_date(options.end_date)
        days=(end_date-start_date).days
        for numdays in range(days+1):
            dates.append(start_date+datetime.timedelta(days=numdays))
    elif options.date and len(args) == 1:
        testname = args[0]
        dates = [eideticker.BuildRetriever.get_date(options.date)]
    elif not options.date and len(args) >= 2:
        testname = args[0]
        if options.use_apks:
            apks = args[1:]
        else:
            appnames = args[1:]
    elif options.devicetype == "b2g":
        testname = args[0]
    elif not options.date or (not options.start_date and not options.end_date):
        parser.error("On Android, must specify date, date range, a set of appnames (e.g. org.mozilla.fennec) or a set of apks (if --use-apks is specified)")

    device_prefs = eideticker.getDevicePrefs(options)

    if options.devicetype == "b2g":
        runtest(device_prefs, testname, options)
    elif appnames:
        for appname in appnames:
            runtest(device_prefs, testname, options, appname=appname)
    elif apks:
        for apk in apks:
            runtest(device_prefs, testname, options, apk=apk)
    else:
        br = eideticker.BuildRetriever()
        productname = "nightly"
        product = eideticker.get_product(productname)
        for date in dates:
            apk = br.get_build(product, date)
            runtest(device_prefs, testname, options, apk=apk, appdate=date)

main()
