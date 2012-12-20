#!/usr/bin/env python

import eideticker
import json
import os
import subprocess
import sys
import time
import videocapture
import uuid
import manifestparser

class NestedDict(dict):
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

def kill_app(dm, appname):
    procs = dm.getProcessList()
    for (pid, name, user) in procs:
      if name == appname:
        dm.runCmd(["shell", "echo kill %s | su" % pid])

def runtest(dm, product, appname, appinfo, testinfo, capture_name,
            outputdir, datafile, data, enable_profiling=False,
            dmtype="adb", host=None, port=None, devicetype="android"):
    capture_file = os.path.join(CAPTURE_DIR,
                                "%s-%s-%s-%s.zip" % (testinfo['key'],
                                                     appname,
                                                     appinfo.get('date'),
                                                     int(time.time())))
    if enable_profiling:
        profile_path = os.path.join('profiles', 'sps-profile-%s.zip' % time.time())
        profile_file = os.path.join(outputdir, profile_path)

    test_completed = False
    for i in range(3):
        print "Running test (try %s of 3)" % (i+1)

        # Kill any existing instances of the processes before starting
        dm.killProcess(appname)

        args = [ "runtest.py", "--name", capture_name, "--capture-file",
                 capture_file ]
        if dmtype:
            args.extend(["-m", dmtype])
        if devicetype:
            args.extend(["-d", devicetype])
        if host:
            args.extend(["--host", host])
        if port:
            args.extend(["--port", port])
        if enable_profiling:
            args.extend(["--profile-file", profile_file])
        retval = subprocess.call(args + [ appname, testinfo['key'] ])
        if retval == 0:
            test_completed = True
            break
        else:
            print "Test failed, retrying..."

    if not test_completed:
        raise Exception("Failed to run test %s for %s (after 3 tries). "
                        "Aborting." % (testinfo['key'], product['name']))

    capture = videocapture.Capture(capture_file)

    # video file
    video_path = os.path.join('videos', 'video-%s.webm' % time.time())
    video_file = os.path.join(outputdir, video_path)
    open(video_file, 'w').write(capture.get_video().read())

    # need to initialize dict for product if not there already
    if not data['testdata'].get(product['name']):
        data['testdata'][product['name']] = {}

    # app date
    appdate = appinfo.get('date')

    if not data['testdata'][product['name']].get(appdate):
        data['testdata'][product['name']][appdate] = []

    datapoint = { 'uuid': uuid.uuid1().hex,
                  'video': video_path,
                  'appdate': appinfo.get('date'),
                  'buildid': appinfo.get('buildid'),
                  'revision': appinfo.get('revision') }

    if testinfo['type'] == 'startup':
        datapoint['timetostableframe'] = videocapture.get_stable_frame_time(capture)
    else:
        # standard test metrics
        datapoint['uniqueframes'] = videocapture.get_num_unique_frames(capture)
        datapoint['fps'] = videocapture.get_fps(capture)
        datapoint['checkerboard'] = videocapture.get_checkerboarding_area_duration(capture)

    if enable_profiling:
        datapoint['profile'] = profile_path

    data['testdata'][product['name']][appdate].append(datapoint)

    # Write the data to disk immediately (so we don't lose it if we fail later)
    datafile_dir = os.path.dirname(datafile)
    if not os.path.exists(datafile_dir):
        os.mkdir(datafile_dir)
    with open(datafile, 'w') as f:
        f.write(json.dumps(data))

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <product> <test> <output dir>"

    parser = eideticker.OptionParser(usage=usage)
    parser.add_option("--enable-profiling",
                      action="store_true", dest = "enable_profiling",
                      help = "Create SPS profile to go along with capture")
    parser.add_option("--device-id", action="store", dest="device_id",
                      help="id of device (used in output json)")
    parser.add_option("--apk", action="store", dest="apk",
                      help = "Product apk to get metadata from " \
                          "(Android-specific)")
    parser.add_option("--num-runs", action="store",
                      type = "int", dest = "num_runs",
                      help = "number of runs (default: 1)")

    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error("incorrect number of arguments")

    (productname, testkey, outputdir) = args
    num_runs = 1
    if options.num_runs:
        num_runs = options.num_runs

    manifest = manifestparser.TestManifest(manifests=[os.path.join(
                os.path.dirname(__file__), '../src/tests/manifest.ini')])

    # sanity check... does the test match a known test key?
    testkeys = [test["key"] for test in manifest.active_tests()]
    if testkey not in testkeys:
        print "ERROR: No tests matching '%s' (options: %s)" % (testkey, ", ".join(testkeys))
        sys.exit(1)

    testinfo = [test for test in manifest.active_tests() if test['key'] == testkey][0]

    device_id = options.device_id
    if not device_id:
        device_id = os.environ.get('DEVICE_ID')
    if not device_id:
        print "ERROR: Must specify device id (either with --device-id or with DEVICE_ID environment variable)"
        sys.exit(1)

    products = [product for product in eideticker.products if product['name'] == productname]
    if not products:
        print "ERROR: No products matching '%s'" % options.product
        sys.exit(1)
    product = products[0]

    current_date = time.strftime("%Y-%m-%d")
    datafile = os.path.join(outputdir, device_id, '%s.json' % testkey)

    data = NestedDict()
    if os.path.isfile(datafile):
        data.update(json.loads(open(datafile).read()))

    devicePrefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**devicePrefs)

    # update the device list for the dashboard
    devices = {}
    devicefile = os.path.join(outputdir, 'devices.json')
    if os.path.isfile(devicefile):
        devices = json.loads(open(devicefile).read())['devices']
    testfile = os.path.join(outputdir, '%s' % device_id, 'tests.json')
    if os.path.isfile(testfile):
        tests = json.loads(open(testfile).read())['tests']
    else:
        tests = {}
    tests[testkey] = { 'shortDesc': testinfo['shortDesc'],
                       'defaultMeasure': testinfo['defaultMeasure'] }
    devices[device_id] = { 'name': device.model,
                           'version': device.getprop('ro.build.version.release') }
    with open(devicefile, 'w') as f:
        f.write(json.dumps({ 'devices': devices }))
    testfiledir = os.path.dirname(testfile)
    if not os.path.exists(testfiledir):
        os.mkdir(testfiledir)
    with open(testfile, 'w') as f:
        f.write(json.dumps({ 'tests': tests }))

    if options.apk:
        appinfo = eideticker.get_fennec_appinfo(options.apk)
        appname = appinfo['appname']
        print "Using application name '%s' from apk '%s'" % (appname, options.apk)
        capture_name = "%s %s" % (product['name'], appinfo['date'])
    else:
        # no apk, assume it's something static on the device
        appinfo = { 'date': 'today' }
        appname = product['appname']
        capture_name = "%s (taken on %s)" % (product['name'], current_date)

    # Run the test the specified number of times
    for i in range(num_runs):
        # Now run the test
        runtest(device, product, appname, appinfo, testinfo,
                capture_name + " #%s" % i, outputdir, datafile, data,
                enable_profiling=options.enable_profiling, **devicePrefs)

        # Kill app after test complete
        device.killProcess(appname)

main()
