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
        "url": "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/latest-mozilla-central-android/fennec-13.0a1.en-US.android-arm.apk",
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
    usage = "usage: %prog [options] <test name> <output dir> [product name]"
    parser = optparse.OptionParser(usage)
    parser.add_option("--no-download",
                      action="store_true", dest = "no_download",
                      help = "Don't download new versions of the app")
    options, args = parser.parse_args()

    if len(args) < 2 or len(args) > 3:
        parser.error("incorrect number of arguments")

    (testname, outputdir) = (args[0], args[1])
    products = default_products
    if len(args) > 2:
        products = [product for product in default_products if product['name'] == args[2]]
        if not products:
            print "ERROR: No products matching '%s'" % product['name']
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

        if product.get('url'):
            appinfo = get_appinfo(fname)
            capture_name = "%s %s" % (product['name'], appinfo['date'])
        else:
            appinfo = { }
            capture_name = "%s (taken on %s)" % (product['name'], current_date)

        dm = mozdevice.DroidADB(packageName=product['appname'])
        dm.updateApp(fname)

        # Kill any existing instances of the processes
        kill_app(dm, product['appname'])

        # Now run the test
        capture_file = os.path.join(CAPTURE_DIR,
                                    "%s-%s-%s.zip" % (product['name'],
                                                      appinfo.get('date'),
                                                      int(time.time())))
        retval = subprocess.call(["runtest.py", "--name",
                         capture_name,
                         "--capture-file", capture_file,
                         product['appname'], testname])
        if retval != 0:
            raise Exception("Failed to run test %s for %s" % (testname, product['name']))

        # Kill app after test complete
        kill_app(dm, product['appname'])

        capture = videocapture.Capture(capture_file)

        # video file
        video_path = os.path.join('videos', 'video-%s.webm' % time.time())
        video_file = os.path.join(outputdir, video_path)
        open(video_file, 'w').write(capture.get_video().read())

        # fps calculation
        framediff_sums = videocapture.get_framediff_sums(capture)
        num_different_frames = 1 + len([framediff for framediff in framediff_sums if framediff > 250])
        fps = num_different_frames / capture.length

        # need to initialize dict for product if not there already
        if not data[testname].get(product['name']):
            data[testname][product['name']] = {}

        if not data[testname][product['name']].get(current_date):
            data[testname][product['name']][current_date] = []
        data[testname][product['name']][current_date].append({ 'fps': fps,
                                                               'video': video_path,
                                                               'appdate': appinfo.get('date') })

    # Write the data to disk
    open(datafile, 'w').write(json.dumps(data))

main()
