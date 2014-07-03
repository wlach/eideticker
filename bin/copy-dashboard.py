#!/usr/bin/env python

import concurrent.futures
import eideticker
import json
import optparse
import os
import requests
import sys

exit_status = 0
MAX_WORKERS = 8

def save_file(filename, content):
    open(filename, 'wo').write(content)

def create_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def validate_response(r):
    global exit_status

    if r.status_code != requests.codes.ok:
        print "WARNING: Problem downloading data at URL %s (HTTP " \
            "response code: %s)!" % (r.url, r.status_code)
        exit_status = 1
        return False

    return True

def validate_json_response(r):
    global exit_status

    if not validate_response(r):
        return False
    try:
        json.loads(r.text)
    except ValueError:
        exit_status = 1
        print "WARNING: Response from URL %s not valid json" % r.url
        return False

    return True

def download_file(url, filename):
    r = requests.get(url)
    if not validate_response(r):
        return
    open(filename, 'w').write(r.content)

def download_metadata(url, baseurl, filename, options, videodir, profiledir):
    r = requests.get(url)
    if not validate_json_response(r):
        return

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
    if not validate_json_response(r):
        return

    open(filename, 'w').write(r.content)
    with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        testdata = r.json()['testdata']
        for appname in testdata.keys():
            for date in testdata[appname].keys():
                for datapoint in testdata[appname][date]:
                    uuid = datapoint['uuid']
                    if options.download_metadata:
                        executor.submit(download_metadata,
                                        baseurl + 'metadata/%s.json' % uuid,
                                        baseurl,
                                        os.path.join(metadatadir,
                                                     '%s.json' % uuid),
                                        options, videodir,
                                        profiledir)

usage = "usage: %prog [options] <url> <output directory>"
parser = optparse.OptionParser(usage)
parser.add_option("--full-mirror", action="store_true",
                  default=False, dest="full_mirror",
                  help="Download videos, profiles to disk")
parser.add_option("--skip-metadata", action="store_false",
                  dest="download_metadata", default=True,
                  help="Skip downloading metadata JSON files")
parser.add_option("--device-id", action="store",
                  dest="device_id",
                  help="Only download information for device id")
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

r = requests.get(baseurl + 'devices.json')
if not validate_json_response(r):
    print "Can't download device list, exiting"
    sys.exit(1)

save_file(os.path.join(outputdir, 'devices.json'), r.content)

if options.device_id:
    if options.device_id in r.json()['devices'].keys():
        device_names = [ options.device_id ]
    else:
        print "WARNING: Device id '%s' specified but unavailable. Skipping." % \
            options.device_id
        device_names = []
else:
    device_names = r.json()['devices'].keys()

with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
    for device_name in device_names:
        r = requests.get(baseurl + '%s/tests.json' % device_name)
        if not validate_json_response(r):
            print "Skipping tests for %s" % device_name
            continue

        devicedir = os.path.join(outputdir, device_name)
        create_dir(devicedir)
        save_file(os.path.join(devicedir, 'tests.json'), r.content)
        testnames = r.json()['tests'].keys()
        for testname in testnames:
            executor.submit(download_testdata,
                            baseurl + '%s/%s.json' % (device_name, testname),
                            baseurl,
                            os.path.join(outputdir, device_name,
                                         '%s.json' % testname),
                            options,
                            metadatadir, videodir, profiledir)

sys.exit(exit_status)
