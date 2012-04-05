#!/usr/bin/env python

import ConfigParser
import json
import mozdevice
import optparse
import os
import subprocess
import sys
import time
import urllib2
import videocapture
import zipfile

class NestedDict(dict):
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())

default_products = [
    {
        "name": "nightly",
        "url": "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/latest-mozilla-central-android/fennec-14.0a1.en-US.android-arm.apk",
        "appname": "org.mozilla.fennec"
    },
    {
        "name": "xul",
        "url": "http://ftp.mozilla.org/pub/mobile/releases/latest/android/en-US/fennec-10.0.3esr.en-US.android-arm.apk",
        "appname": "org.mozilla.firefox"
    },
    {
        "name": "stock",
        "url": None,
        "appname": "com.android.browser"
    }
]

default_tests = [
    {
        'name': 'clock',
        'path': 'src/tests/canvas/clock.html',
        'measure': 'fps'
    },
    {
        'name': 'taskjs',
        'path': 'src/tests/scrolling/taskjs.org/index.html',
        'measure': 'checkerboard'
    },
    {
        'name': 'nightly',
        'path': 'src/tests/zooming/nightly.mozilla.org/index.html',
        'measure': 'checkerboard'
    },
    {
        'name': 'nytimes-scroll',
        'path': 'src/tests/scrolling/nytimes/nytimes.com/nytimes-scroll.html',
        'measure': 'checkerboard'
    },
    {
        'name': 'nytimes-zoom',
        'path': 'src/tests/scrolling/nytimes/nytimes.com/nytimes-zoom.html',
        'measure': 'checkerboard'
    },
]

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

def get_appinfo(fname):
    archive = zipfile.ZipFile(fname, 'r')
    config = ConfigParser.ConfigParser()
    config.readfp(archive.open('application.ini'))
    buildid = config.get('App', 'BuildID')
    (year, month, day) = (buildid[0:4], buildid[4:6], buildid[6:8])
    return { 'date':  "%s-%s-%s" % (year, month, day) }

def kill_app(dm, appname):
    procs = dm.getProcessList()
    for (pid, name, user) in procs:
      if name == appname:
        dm.runCmd(["shell", "echo kill %s | su" % pid])

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <test> <output dir>"
    parser = optparse.OptionParser(usage)
    parser.add_option("--no-download",
                      action="store_true", dest = "no_download",
                      help = "Don't download new versions of the app")
    parser.add_option("--product", "-p",
                      action="store", dest="product",
                      help = "Restrict testing to product (options: %s)" %
                      ", ".join([product["name"] for product in default_products]))
    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    (testname, outputdir) = args

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

    for product in products:
        fname = os.path.join(DOWNLOAD_DIR, "%s.apk" % product['name'])

        if not options.no_download and product.get('url'):
            print "Downloading %s" % product['name']
            dl = urllib2.urlopen(product['url'])
            f = open(fname, 'w')
            f.write(dl.read())
            f.close()

        dm = mozdevice.DroidADB(packageName=product['appname'])

        if product.get('url'):
            dm.updateApp(fname)
            appinfo = get_appinfo(fname)
            capture_name = "%s %s" % (product['name'], appinfo['date'])
        else:
            appinfo = { }
            capture_name = "%s (taken on %s)" % (product['name'], current_date)

        # Kill any existing instances of the processes
        kill_app(dm, product['appname'])

        # Now run the test
        capture_file = os.path.join(CAPTURE_DIR,
                                    "%s-%s-%s-%s.zip" % (test['name'],
                                                         product['name'],
                                                         appinfo.get('date'),
                                                         int(time.time())))
        retval = subprocess.call(["runtest.py", "--name",
                         capture_name,
                         "--capture-file", capture_file,
                         product['appname'], test['path']])
        if retval != 0:
            raise Exception("Failed to run test %s for %s" % (test['name'], product['name']))

        # Kill app after test complete
        kill_app(dm, product['appname'])

        capture = videocapture.Capture(capture_file)

        # video file
        video_path = os.path.join('videos', 'video-%s.webm' % time.time())
        video_file = os.path.join(outputdir, video_path)
        open(video_file, 'w').write(capture.get_video().read())

        if test['measure'] == 'fps':
            framediff_sums = videocapture.get_framediff_sums(capture)
            num_different_frames = 1 + len([framediff for framediff in framediff_sums if framediff > 250])
            measure = num_different_frames / capture.length
        elif test['measure'] == 'checkerboard':
            measure = videocapture.get_checkerboarding_area_duration(capture)
        else:
            print "ERROR: Unknown measure '%s'" % test['measure']
            sys.exit(1)

        # need to initialize dict for product if not there already
        if not data[test['name']].get(product['name']):
            data[test['name']][product['name']] = {}

        if not data[test['name']][product['name']].get(current_date):
            data[test['name']][product['name']][current_date] = []
        data[test['name']][product['name']][current_date].append({ test['measure']: measure,
                                                               'video': video_path,
                                                               'appdate': appinfo.get('date') })

    # Write the data to disk
    open(datafile, 'w').write(json.dumps(data))

main()
