#!/usr/bin/env python

from multiprocessing.pool import ThreadPool
import eideticker
import json
import optparse
import os
import requests
import sys

def save_file(filename, content):
    open(filename, 'wo').write(content)

def create_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def download_file(url, filename):
    print (url, filename)
    r = requests.get(url)
    open(filename, 'w').write(r.content)

def download_metadata(url, baseurl, filename, options, videodir, profiledir):
    r = requests.get(url)
    metadata = r.json()
    videourl = baseurl + metadata['video']
    profileurl = None
    if metadata.get('profile'):
        profileurl = baseurl + metadata['profile']
    if options.full_mirror:
        download_file(videourl,
                      os.path.join(videodir, os.path.basename(metadata['video'])))
        if profileurl:
            download_file(profileurl,
                          os.path.join(profiledir,
                                       os.path.basename(metadata['profile'])))
    else:
        # make it relative
        metadata['video'] = videourl
        if profileurl:
            metadata['profile'] = profileurl
    save_file(filename, json.dumps(metadata))

def download_testdata(url, baseurl, filename, options, metadatadir,
                      videodir, profiledir):
    r = requests.get(url)
    open(filename, 'w').write(r.content)
    pool = ThreadPool()
    testdata = r.json()['testdata']
    for appname in testdata.keys():
        for date in testdata[appname].keys():
            for datapoint in testdata[appname][date]:
                uuid = datapoint['uuid']
                if options.download_metadata:
                    pool.apply_async(download_metadata,
                                     [baseurl + 'metadata/%s.json' % uuid,
                                      baseurl,
                                      os.path.join(metadatadir,
                                                   '%s.json' % uuid),
                                      options, videodir,
                                      profiledir])
    pool.close()
    pool.join()

usage = "usage: %prog [options] <url> <output directory>"
parser = optparse.OptionParser(usage)
parser.add_option("--full-mirror", action="store_true",
                  default=False, dest="full_mirror",
                  help="Download videos, profiles to disk")
parser.add_option("--skip-metadata", action="store_false",
                  dest="download_metadata", default=True,
                  help="Skip downloading metadata JSON files")
options, args = parser.parse_args()

if len(args) != 2:
    parser.print_usage()
    sys.exit(1)

if options.full_mirror and not options.download_metadata:
    parser.error("ERROR: Need to download metadata for full mirror")
    sys.exit(1)

(baseurl, outputdir) = args
if baseurl[-1] != '/':
    baseurl += '/'

eideticker.copy_dashboard_files(outputdir)

metadatadir = os.path.join(outputdir, 'metadata')
videodir = os.path.join(outputdir, 'videos')
profiledir = os.path.join(outputdir, 'profiles')

devices = requests.get(baseurl + 'devices.json')
save_file(os.path.join(outputdir, 'devices.json'), devices.content)

device_names = devices.json()['devices'].keys()

pool = ThreadPool()
for device_name in device_names:
    tests = requests.get(baseurl + '%s/tests.json' % device_name)
    devicedir = os.path.join(outputdir, device_name)
    create_dir(devicedir)
    save_file(os.path.join(devicedir, 'tests.json'), tests.content)
    testnames = tests.json()['tests'].keys()
    for testname in testnames:
        pool.apply_async(download_testdata,
                         [baseurl + '%s/%s.json' % (device_name, testname),
                          baseurl,
                          os.path.join(outputdir, device_name,
                                       '%s.json' % testname),
                          options,
                          metadatadir, videodir, profiledir])

pool.close()
pool.join()
