#!/usr/bin/env python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Eideticker.
#
# The Initial Developer of the Original Code is
# Mozilla foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   William Lachance <wlachance@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import datetime
import json
import mozhttpd
import mozprofile
import optparse
import os
import subprocess
import sys
import time
import urllib
import urlparse
import videocapture
import StringIO
import eideticker.device

BINDIR = os.path.dirname(__file__)
CAPTURE_DIR = os.path.abspath(os.path.join(BINDIR, "../captures"))
TEST_DIR = os.path.abspath(os.path.join(BINDIR, "../src/tests"))
EIDETICKER_TEMP_DIR = "/tmp/eideticker"

capture_controller = videocapture.CaptureController(custom_tempdir=EIDETICKER_TEMP_DIR)

class CaptureServer(object):
    finished = False
    controller_finishing = False
    start_frame = None
    end_frame = None

    def __init__(self, capture_metadata, capture_file,
                 checkerboard_log_file, capture_controller, device, actions):
        self.capture_metadata = capture_metadata
        self.capture_file = capture_file
        self.checkerboard_log_file = checkerboard_log_file
        self.capture_controller = capture_controller
        self.device = device
        self.actions = actions

    def terminate_capture(self):
        if self.capture_file:
            self.capture_controller.terminate_capture()

    @mozhttpd.handlers.json_response
    def start_capture(self, request):
        if self.capture_file:
            print "Starting capture on device '%s' with mode: '%s'" % (self.capture_metadata['device'],
                                                                       self.device.hdmiResolution)
            self.capture_controller.start_capture(self.capture_file,
                                                  self.device.hdmiResolution,
                                                  self.capture_metadata)

        return (200, {'capturing': True})

    @mozhttpd.handlers.json_response
    def end_capture(self, request):
        self.finished = True
        self.terminate_capture()
        return (200, {'capturing': False})

    @mozhttpd.handlers.json_response
    def input(self, request):
        commandset = urlparse.parse_qs(request.body)['commands'][0]
        if self.capture_file:
            self.start_frame = self.capture_controller.capture_framenum()

        if self.checkerboard_log_file:
            self.device.clear_logcat()

        if not self.actions.get(commandset) or not \
                self.actions[commandset].get(self.device.model):
            print "Could not get actions for commandset '%s', model " \
                "'%s'" % (commandset, self.device.model)
            sys.exit(1)

        print "Executing commands '%s' for device '%s' (time: %s, framenum: %s)" % (
            commandset, self.device.model, time.time(), self.start_frame)

        self.device.executeCommands(self.actions[commandset][self.device.model])

        if self.capture_file:
            self.end_frame = self.capture_controller.capture_framenum()
        print "Finished commands (time: %s, framenum: %s)" % (time.time(),
                                                              self.end_frame)

        if self.checkerboard_log_file:
            # sleep a bit to make sure we get all the checkerboard stats from
            # test
            time.sleep(1)
            with open(self.checkerboard_log_file, 'w') as f:
                output = self.device.get_logcat(["GeckoLayerRendererProf:D",
                                                 "*:S"])
                f.write(output)

        return (200, {})


class BrowserRunner(object):

    def __init__(self, dm, appname, url):
        self.dm = dm
        self.appname = appname
        self.url = url
        self.intent = "android.intent.action.VIEW"

        activity_mappings = {
            'com.android.browser': '.BrowserActivity',
            'com.google.android.browser': 'com.android.browser.BrowserActivity',
            'com.android.chrome': '.Main'
            }

        # use activity mapping if not mozilla
        if self.appname.startswith('org.mozilla'):
            self.activity = '.App'
            self.intent = None
        else:
            self.activity = activity_mappings[self.appname]

    def start(self):
        print "Starting %s... " % self.appname

        # for fennec only, we create and use a profile
        if self.appname.startswith('org.mozilla'):
            args = []
            profile = None
            profile = mozprofile.Profile(preferences = { 'gfx.show_checkerboard_pattern': False })
            remote_profile_dir = "/".join([self.dm.getDeviceRoot(),
                                       os.path.basename(profile.profile)])
            if not self.dm.pushDir(profile.profile, remote_profile_dir):
                raise Exception("Failed to copy profile to device")

            args.extend(["-profile", remote_profile_dir])

            # sometimes fennec fails to start, so we'll try three times...
            for i in range(3):
                print "Launching fennec (try %s of 3)" % (i+1)
                if self.dm.launchFennec(self.appname, url=self.url, extraArgs=args):
                    return
            raise Exception("Failed to start Fennec after three tries")
        else:
            self.dm.launchApplication(self.appname, self.activity, self.intent,
                                      url=self.url)

    def stop(self):
        self.dm.killProcess(self.appname)

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <appname> <test path>"
    parser = optparse.OptionParser(usage)
    parser.add_option("--url-params", action="store",
                      dest="url_params",
                      help="additional url parameters for test")
    parser.add_option("--name", action="store",
                      type = "string", dest = "capture_name",
                      help = "name to give capture")
    parser.add_option("--capture-file", action="store",
                      type = "string", dest = "capture_file",
                      help = "name to give to capture file")
    parser.add_option("--no-capture", action="store_true",
                      dest = "no_capture",
                      help = "run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--checkerboard-log-file", action="store",
                      type = "string", dest = "checkerboard_log_file",
                      help = "name to give checkerboarding stats file")
    eideticker.device.addDeviceOptionsToParser(parser)

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")
    (appname, testpath) = args
    try:
        testpath_rel = os.path.abspath(testpath).split(TEST_DIR)[1][1:]
    except:
        print "Test must be relative to %s" % TEST_DIR
        sys.exit(1)

    actions_path = os.path.join(os.path.dirname(testpath), "actions.json")
    try:
        with open(actions_path) as f:
            actions = json.loads(f.read())
    except EnvironmentError:
        print "Couldn't open actions file '%s'" % actions_path
        sys.exit(1)

    if not os.path.exists(EIDETICKER_TEMP_DIR):
        os.mkdir(EIDETICKER_TEMP_DIR)
    if not os.path.isdir(EIDETICKER_TEMP_DIR):
        print "Could not open eideticker temporary directory"
        sys.exit(1)

    capture_name = options.capture_name
    if not capture_name:
        capture_name = testpath_rel
    capture_file = options.capture_file
    if not capture_file and not options.no_capture:
        capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                         datetime.datetime.now().isoformat())

    # Create a droid object to interface with the phone
    deviceParams = eideticker.device.getDeviceParams(options)
    device = eideticker.device.getDevice(**deviceParams)

    if device.processExist(appname):
        print "An instance of %s is running. Please stop it before running Eideticker." % appname
        sys.exit(1)

    # If we're logging checkerboard stats, set that up here (seems like it
    # takes a second or so to accept the new setting, so let's do that here --
    # ideally we would detect when that's working, but I'm not sure how to do
    # so trivially)
    if options.checkerboard_log_file:
        old_log_val = device.getprop("log.tag.GeckoLayerRendererProf")
        device.setprop("log.tag.GeckoLayerRendererProf", "DEBUG")

    print "Creating webserver..."
    capture_metadata = {
        'name': capture_name,
        'testpath': testpath_rel,
        'app': appname,
        'device': device.model
        }
    capture_server = CaptureServer(capture_metadata,
                                   capture_file,
                                   options.checkerboard_log_file,
                                   capture_controller, device, actions)
    host = mozhttpd.iface.get_lan_ip()
    http = mozhttpd.MozHttpd(docroot=TEST_DIR,
                             host=host, port=0,
                             urlhandlers = [ { 'method': 'GET',
                                               'path': '/api/captures/start/?',
                                               'function': capture_server.start_capture },
                                             { 'method': 'GET',
                                               'path': '/api/captures/end/?',
                                               'function': capture_server.end_capture },
                                             { 'method': 'POST',
                                               'path': '/api/captures/input/?',
                                               'function': capture_server.input } ])
    http.start(block=False)

    connected = False
    tries = 0
    while not connected and tries < 20:
        tries+=1
        import socket
        s = socket.socket()
        try:
            s.connect((host, http.httpd.server_port))
            connected = True
        except Exception:
            print "Can't connect to %s:%s, retrying..." % (host, http.httpd.server_port)

    if not connected:
        print "Could not open webserver. Error!"
        sys.exit(1)

    if options.url_params:
        testpath_rel += "?%s" % urllib.quote_plus(options.url_params)

    url = "http://%s:%s/start.html?testpath=%s" % (host,
                                                   http.httpd.server_port,
                                                   testpath_rel)
    print "Test URL is: %s" % url
    runner = BrowserRunner(device, appname, url)
    runner.start()

    timeout = 100
    timer = 0
    interval = 0.1
    while not capture_server.finished and timer < timeout:
        time.sleep(interval)
        timer += interval

    runner.stop()

    if not capture_server.finished:
        print "Did not finish test! Error!"
        capture_server.terminate_capture()
        sys.exit(1)

    if capture_file:
        print "Converting capture..."
        capture_controller.convert_capture(capture_server.start_frame, capture_server.end_frame)

    # Clean up checkerboard logging preferences
    if options.checkerboard_log_file:
        device.setprop("log.tag.GeckoLayerRendererProf", old_log_val)


main()
