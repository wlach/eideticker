#!/usr/bin/env python

import ConfigParser
import eideticker.device
import json
import mozdevice
import optparse
import os
import subprocess
import sys
import time
import videocapture
import zipfile
from eideticker.products import default_products

class NestedDict(dict):
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())

default_tests = [
    {
        'name': 'clock',
        'path': 'src/tests/ep1/clock/index.html'
    },
    {
        'name': 'taskjs',
        'path': 'src/tests/ep1/taskjs.org/index.html'
    },
    {
        'name': 'nightly',
        'path': 'src/tests/ep1/nightly.mozilla.org/index.html'
    },
    {
        'name': 'nytimes-scroll',
        'path': 'src/tests/ep1/nytimes/nytimes.com/index.html',
        'urlparams': 'testtype=scroll'
    },
    {
        'name': 'nytimes-zoom',
        'path': 'src/tests/ep1/nytimes/nytimes.com/index.html',
        'urlparams': 'testtype=zoom'
    },
    {
        'name': 'cnn',
        'path': 'src/tests/ep1/cnn/cnn.com/index.html'
    },
    {
        'name': 'reddit',
        'path': 'src/tests/ep1/reddit.com/www.reddit.com/index.html'
    },
    {
        'name': 'imgur',
        'path': 'src/tests/ep1/imgur.com/imgur.com/gallery/index.html'
    },
    {
        'name': 'wikipedia',
        'path': 'src/tests/ep1/en.wikipedia.org/en.wikipedia.org/wiki/Rorschach_test.html'
    }
]

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

def get_appinfo(fname):
    archive = zipfile.ZipFile(fname, 'r')
    config = ConfigParser.ConfigParser()
    config.readfp(archive.open('application.ini'))
    buildid = config.get('App', 'BuildID')
    revision = config.get('App', 'SourceStamp')
    (year, month, day) = (buildid[0:4], buildid[4:6], buildid[6:8])
    if 'package-name.txt' in archive.namelist():
        appname = archive.open('package-name.txt').read().rstrip()
    else:
        appname = None
    return { 'date':  "%s-%s-%s" % (year, month, day),
             'buildid': buildid,
             'revision': revision,
             'appname': appname }

def kill_app(dm, appname):
    procs = dm.getProcessList()
    for (pid, name, user) in procs:
      if name == appname:
        dm.runCmd(["shell", "echo kill %s | su" % pid])

def runtest(dm, product, current_date, appname, appinfo, test, capture_name,
            outputdir, datafile, data):
    capture_file = os.path.join(CAPTURE_DIR,
                                "%s-%s-%s-%s.zip" % (test['name'],
                                                     appname,
                                                     appinfo.get('date'),
                                                     int(time.time())))
    urlparams = test.get('urlparams', '')
    retval = subprocess.call(["runtest.py", "--url-params", urlparams,
                              "--name", capture_name,
                              "--capture-file", capture_file,
                              appname, test['path']])
    if retval != 0:
        raise Exception("Failed to run test %s for %s" % (test['name'], product['name']))


    capture = videocapture.Capture(capture_file)

    # video file
    video_path = os.path.join('videos', 'video-%s.webm' % time.time())
    video_file = os.path.join(outputdir, video_path)
    open(video_file, 'w').write(capture.get_video().read())

    # frames-per-second / num unique frames
    framediff_sums = videocapture.get_framediff_sums(capture)
    num_unique_frames = 1 + len([framediff for framediff in framediff_sums if framediff > 0])
    fps = num_unique_frames / capture.length

    # checkerboarding
    checkerboard = videocapture.get_checkerboarding_area_duration(capture)

    # need to initialize dict for product if not there already
    if not data[test['name']].get(product['name']):
        data[test['name']][product['name']] = {}

    if not data[test['name']][product['name']].get(current_date):
        data[test['name']][product['name']][current_date] = []
    datapoint = { 'fps': fps,
                  'checkerboard': checkerboard,
                  'uniqueframes': num_unique_frames,
                  'video': video_path,
                  'appdate': appinfo.get('date'),
                  'buildid': appinfo.get('buildid'),
                  'revision': appinfo.get('revision') }
    data[test['name']][product['name']][current_date].append(datapoint)

    # Write the data to disk immediately (so we don't lose it if we fail later)
    with open(datafile, 'w') as f:
        f.write(json.dumps(data))

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <test> <output dir>"
    parser = optparse.OptionParser(usage)
    parser.add_option("--product",
                      action="store", dest="product",
                      help = "Restrict testing to product (options: %s)" %
                      ", ".join([product["name"] for product in default_products]))
    parser.add_option("--num-runs", action="store",
                      type = "int", dest = "num_runs",
                      help = "number of runs (default: 1)")
    eideticker.device.addDeviceOptionsToParser(parser)

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")

    (testname, outputdir) = args
    num_runs = 1
    if options.num_runs:
        num_runs = options.num_runs

    testnames = [test["name"] for test in default_tests]
    if testname not in testnames:
        print "ERROR: No tests matching '%s' (options: %s)" % (testname, ", ".join(testnames))
        sys.exit(1)
    else:
        test = [test for test in default_tests if test['name'] == testname][0]

    products = default_products
    if options.product:
        products = [product for product in default_products if product['name'] == options.product]
        if not products:
            print "ERROR: No products matching '%s'" % options.product
            sys.exit(1)

    current_date = time.strftime("%Y-%m-%d")
    datafile = os.path.join(outputdir, 'data.json')

    data = NestedDict()
    if os.path.isfile(datafile):
        data.update(json.loads(open(datafile).read()))

    deviceParams = eideticker.device.getDeviceParams(options)
    device = eideticker.device.getDevice(**deviceParams)

    for product in products:
        if product.get('url'):
            product_fname = os.path.join(DOWNLOAD_DIR, "%s.apk" % product['name'])
            appinfo = get_appinfo(product_fname)
            appname = appinfo['appname']
            capture_name = "%s %s" % (product['name'], appinfo['date'])
        else:
            appinfo = { }
            appname = product['appname']
            capture_name = "%s (taken on %s)" % (product['name'], current_date)

        if appinfo.get('appname'):
            appname = appinfo['appname']
        else:
            appname = product['appname']

        # Run the test the specified number of times
        for i in range(num_runs):
            # Kill any existing instances of the processes
            device.killProcess(appname)

            # Now run the test
            runtest(device, product, current_date, appname, appinfo, test,
                    capture_name + " #%s" % i, outputdir, datafile, data)

            # Kill app after test complete
            device.killProcess(appname)

main()
