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

products = [
    { "name": "aurora",
      "url": "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/latest-mozilla-aurora-android/fennec-12.0a2.en-US.android-arm.apk" },
    { "name": "nightly",
      "url": "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/latest-mozilla-central-android/fennec-13.0a1.en-US.android-arm.apk" }
]

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

def get_appinfo(fname):
    archive = zipfile.ZipFile(fname, 'r')
    config = ConfigParser.ConfigParser()
    config.readfp(archive.open('application.ini'))
    buildid = config.get('App', 'BuildID')
    (year, month, day) = (buildid[0:4], buildid[4:6], buildid[6:8])
    name = archive.open('package-name.txt').read().rstrip()
    return { 'date':  "%s-%s-%s" % (year, month, day),
             'name': name }

def kill_app(dm, appname):
    procs = dm.getProcessList()
    for (pid, name, user) in procs:
      if name == appname:
        dm.runCmd(["shell", "su" "-c" "'kill %s'" % pid])

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <test name> <output json file>"
    parser = optparse.OptionParser(usage)
    parser.add_option("-d", "--download",
                      action="store_true", dest = "download",
                      help = "Download new versions of the app")
    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    (testname, datafile) = (args[0], args[1])

    data = NestedDict()
    if os.path.isfile(datafile):
        data.update(json.loads(open(datafile).read()))

    for product in products:
        fname = os.path.join(DOWNLOAD_DIR, "fennec-%s.apk" % product['name'])

        if options.download:
            print "Downloading %s" % product['name']
            dl = urllib2.urlopen(product['url'])
            f = open(fname, 'w')
            f.write(dl.read())
            f.close()

        appinfo = get_appinfo(fname)
        dm = mozdevice.DeviceManagerADB(packageName=appinfo['name'])
        dm.updateApp(fname)

        # Kill any existing instances of the processes
        kill_app(dm, appinfo['name'])

        # Now run the test
        capture_file = os.path.join(CAPTURE_DIR,
                                    "%s-%s-%s.zip" % (product['name'], appinfo['date'], int(time.time())))
        retval = subprocess.call(["runtest.py", "--name",
                         "%s %s" % (product['name'], appinfo['date']),
                         "--capture-file", capture_file,
                         appinfo['name'], testname])
        if retval != 0:
            raise Exception("Failed to run test %s for %s" % (testname, product['name']))

        # Kill app after test complete
        kill_app(dm, appinfo['name'])

        capture = videocapture.Capture(capture_file)

        # fps calculation
        framediff_sums = videocapture.get_framediff_sums(capture)
        num_different_frames = 1 + len([framediff for framediff in framediff_sums if framediff > 1000])
        fps = num_different_frames / capture.length

        if not data[testname][product['name']].get(appinfo['date']):
            data[testname][product['name']][appinfo['date']] = []
        data[testname][product['name']][appinfo['date']].append({ 'fps': fps })

    # Write the data to disk
    open(datafile, 'w').write(json.dumps(data))

main()
