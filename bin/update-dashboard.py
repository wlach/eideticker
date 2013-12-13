#!/usr/bin/env python

import eideticker
import json
import os
import sys
import time
import videocapture
import uuid
import xml
import StringIO


class NestedDict(dict):
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

def get_revision_data(sources_xml):
    revision_data = {}
    sources = xml.dom.minidom.parseString(open(sources_xml).read())
    for element in sources.getElementsByTagName('project'):
        path = element.getAttribute('path')
        revision = element.getAttribute('revision')
        print path
        if path in ['gaia', 'build']:
            revision_data[path + 'Revision'] = revision
    return revision_data


def runtest(dm, device_prefs, capture_device, capture_area, product, appname,
            appinfo, testinfo, capture_name, outputdir, datafile, data,
            enable_profiling=False, log_http_requests=False, log_actions=False,
            baseline=False, wifi_settings_file=None, sync_time=True):
    capture_file = os.path.join(CAPTURE_DIR,
                                "%s-%s-%s-%s.zip" % (testinfo['key'],
                                                     appname,
                                                     appinfo.get('appdate'),
                                                     int(time.time())))
    productname = product['name']

    profile_file = None
    if enable_profiling:
        productname += "-profiling"
        profile_path = os.path.join('profiles', 'sps-profile-%s.zip' % time.time())
        profile_file = os.path.join(outputdir, profile_path)

    test_completed = False
    for i in range(3):
        print "Running test (try %s of 3)" % (i+1)

        # Kill any existing instances of the processes before starting
        dm.killProcess(appname)

        try:
            testlog = eideticker.run_test(testinfo['key'], capture_device,
                                          appname, capture_name, device_prefs,
                                          profile_file=profile_file,
                                          capture_area=capture_area,
                                          capture_file=capture_file,
                                          wifi_settings_file=wifi_settings_file,
                                          sync_time=sync_time)
            test_completed = True
            break
        except eideticker.TestException, e:
            if e.can_retry:
                print "Test failed, but not fatally. Retrying..."
            else:
                raise

    if not test_completed:
        raise Exception("Failed to run test %s for %s (after 3 tries). "
                        "Aborting." % (testinfo['key'], productname))

    capture = videocapture.Capture(capture_file)

    # video file
    video_relpath = os.path.join('videos', 'video-%s.webm' % time.time())
    video_path = os.path.join(outputdir, video_relpath)
    open(video_path, 'w').write(capture.get_video().read())

    # need to initialize dict for product if not there already
    if not data['testdata'].get(productname):
        data['testdata'][productname] = {}

    # app date
    appdate = appinfo['appdate']

    if not data['testdata'][productname].get(appdate):
        data['testdata'][productname][appdate] = []

    datapoint = { 'uuid': uuid.uuid1().hex,
                  'video': video_relpath }
    for key in ['appdate', 'buildid', 'revision', 'geckoRevision',
                'gaiaRevision', 'buildRevision', 'sourceRepo']:
        if appinfo.get(key):
            datapoint.update({key: appinfo[key]})

    # only interested in version if we don't have revision
    if not appinfo.get('revision') and appinfo.get('version'):
        datapoint.update({ 'version': appinfo['version'] })

    if baseline:
        datapoint.update({ 'baseline': True })

    if testinfo['type'] == 'startup' or testinfo['type'] == 'webstartup' or \
            testinfo['defaultMeasure'] == 'timetostableframe':
        datapoint['timetostableframe'] = eideticker.get_stable_frame_time(capture)
    else:
        # standard test metrics
        datapoint.update(eideticker.get_standard_metrics(capture,
                                                         testlog.actions))

    framediff_relpath = os.path.join('framediffs', 'framediff-%s.json' % time.time())
    framediff_path = os.path.join(outputdir, framediff_relpath)
    with open(framediff_path, 'w') as f:
        framediff = videocapture.get_framediff_sums(capture)
        f.write(json.dumps({ 'diffsums': framediff }))
    datapoint['frameDiff'] = framediff_relpath

    if enable_profiling:
        datapoint['profile'] = profile_path

    if log_http_requests:
        request_log_relpath = os.path.join('httplogs',
                                        'http-log-%s.json' % time.time())
        testlog.save_logs(http_request_log_path=
                          os.path.join(outputdir, request_log_relpath))
        datapoint['httpLog'] = request_log_relpath

    if log_actions:
        actions_log_relpath = os.path.join('actionlogs',
                                           'action-log-%s.json' % time.time())
        testlog.save_logs(actions_log_path=os.path.join(outputdir,
                                                        actions_log_relpath))
        datapoint['actionLog'] = actions_log_relpath

    # Add datapoint
    data['testdata'][productname][appdate].append(datapoint)

    # Write the data to disk immediately (so we don't lose it if we fail later)
    datafile_dir = os.path.dirname(datafile)
    if not os.path.exists(datafile_dir):
        os.mkdir(datafile_dir)
    with open(datafile, 'w') as f:
        f.write(json.dumps(data))

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <product> <test> <output dir>"

    parser = eideticker.TestOptionParser(usage=usage)
    parser.add_option("--enable-profiling",
                      action="store_true", dest = "enable_profiling",
                      help = "Create SPS profile to go along with capture")
    parser.add_option("--device-id", action="store", dest="device_id",
                      help="id of device (used in output json)",
                      default=os.environ.get('DEVICE_ID'))
    parser.add_option("--device-name", action="store", dest="device_name",
                      help="name of device to display in dashboard (if not "
                      "specified, display model name)",
                      default=os.environ.get('DEVICE_NAME'))
    parser.add_option("--apk", action="store", dest="apk",
                      help = "Product apk to get metadata from " \
                          "(Android-specific)")
    parser.add_option("--baseline", action="store_true", dest="baseline",
                      help = "Create baseline results for dashboard")
    parser.add_option("--num-runs", action="store",
                      type = "int", dest = "num_runs",
                      help = "number of runs (default: 1)")
    parser.add_option("--app-version", action="store", dest="app_version",
                      help="Specify app version (if not automatically " \
                          "available; Android-specific)")
    parser.add_option("--sources-xml", action="store", dest="sources_xml",
                      help="Path to sources XML file for getting revision " \
                          "information (B2G-specific)")

    options, args = parser.parse_args()

    if len(args) != 3:
        parser.print_usage()
        sys.exit(1)

    (productname, testkey, outputdir) = args
    num_runs = 1
    if options.num_runs:
        num_runs = options.num_runs

    testinfo = eideticker.get_testinfo(testkey)

    device_id = options.device_id
    if not device_id:
        print "ERROR: Must specify device id (either with --device-id or with DEVICE_ID environment variable)"
        sys.exit(1)

    # we'll log http requests for webstartup tests only
    log_http_requests = False
    if testinfo['type'] == 'webstartup':
        log_http_requests = True

    # likewise, log actions only for web tests and b2g tests
    log_actions = False
    if testinfo['type'] == 'web' or testinfo['type'] == 'b2g':
        log_actions = True

    product = eideticker.get_product(productname)
    current_date = time.strftime("%Y-%m-%d")
    capture_name = "%s (taken on %s)" % (product['name'], current_date)
    datafile = os.path.join(outputdir, device_id, '%s.json' % testkey)

    data = NestedDict()
    if os.path.isfile(datafile):
        data.update(json.loads(open(datafile).read()))

    device_prefs = eideticker.getDevicePrefs(options)
    device = eideticker.getDevice(**device_prefs)

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

    device_name = options.device_name
    if not device_name:
        device_name = device.model

    if options.devicetype == "android":
        devices[device_id] = { 'name': device_name,
                               'version': device.getprop('ro.build.version.release') }
        if options.apk:
            if options.app_version:
                raise Exception("Should specify either --app-version or --apk, not both!")
            appinfo = eideticker.get_fennec_appinfo(options.apk)
            appname = appinfo['appname']
            print "Using application name '%s' from apk '%s'" % (appname, options.apk)
            capture_name = "%s %s" % (product['name'], appinfo['appdate'])
        else:
            if not options.app_version:
                raise Exception("Should specify --app-version if not --apk!")

            # no apk, assume it's something static on the device
            appinfo = { 'appdate': time.strftime("%Y-%m-%d"), 'version': options.app_version }
            appname = product['appname']

    elif options.devicetype == "b2g":
        if not options.sources_xml:
            raise Exception("Must specify --sources-xml on b2g!")

        devices[device_id] = { 'name': device_name }
        appinicontents = device.pullFile('/system/b2g/application.ini')
        sfh = StringIO.StringIO(appinicontents)
        appinfo = eideticker.get_appinfo(sfh)
        appinfo.update(get_revision_data(options.sources_xml))
        appname = None
    else:
        print "Unknown device type '%s'!" % options.devicetype

    # update the device / test list for the dashboard
    with open(devicefile, 'w') as f:
        f.write(json.dumps({ 'devices': devices }))
    testfiledir = os.path.dirname(testfile)
    if not os.path.exists(testfiledir):
        os.mkdir(testfiledir)
    with open(testfile, 'w') as f:
        f.write(json.dumps({ 'tests': tests }))

    if options.prepare_test:
        eideticker.prepare_test(testkey, device_prefs)

    # Run the test the specified number of times
    for i in range(num_runs):
        runtest(device, device_prefs, options.capture_device, options.capture_area,
                product, appname, appinfo, testinfo,
                capture_name + " #%s" % i, outputdir, datafile, data,
                enable_profiling=options.enable_profiling,
                log_http_requests=log_http_requests,
                log_actions=log_actions,
                baseline=options.baseline,
                wifi_settings_file=options.wifi_settings_file,
                sync_time=options.sync_time)
        if options.devicetype == "android":
            # Kill app after test complete
            device.killProcess(appname)

main()
