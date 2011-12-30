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
import mozdevice
import mozhttpd
import mozprofile
import mozrunner
import optparse
import os
import signal
import subprocess
import sys
import time
import urllib
import videocapture

BINDIR = os.path.dirname(__file__)
CAPTURE_DIR = os.path.abspath(os.path.join(BINDIR, "../captures"))
TEST_DIR = os.path.abspath(os.path.join(BINDIR, "../src/tests"))

captureController = videocapture.CaptureController("LG-P999")
captureControllerFinishing = False
finished = False
capture_name = None

class EidetickerHandler(mozhttpd.MozRequestHandler):
    def do_GET(self):
        def json_response_ok(responsedict):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            json_data = json.dumps(responsedict)
            self.send_header('Content-Length', len(json_data))
            self.end_headers()
            self.wfile.write(json_data)

        # this is a bit of a ridiculous hack, but it seems to work ok
        if self.path == '/api/captures/start':
            global capture_name
            capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                        datetime.datetime.now().isoformat())
            captureController.launch(capture_name, capture_file)
            json_response_ok({'capturing': True})

        elif self.path == '/api/captures/end':
            global finished
            global captureControllerFinishing
            captureControllerFinishing = True
            captureController.terminate()
            json_response_ok({'capturing': False})
            finished = True

        else:
            mozhttpd.MozRequestHandler.do_GET(self)

def main(args=sys.argv[1:]):
    global capture_name

    usage = "usage: %prog [options] <fennec appname> <test path>"
    parser = optparse.OptionParser(usage)
    parser.add_option("--name", action="store",
                      type = "string", dest = "capture_name",
                      help = "name to give capture")

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")
    appname = args[0]
    try:
        testpath = os.path.abspath(args[1]).split(TEST_DIR)[1][1:]
    except:
        print "Test must be relative to %s" % TEST_DIR
        sys.exit(1)

    capture_name = options.capture_name
    if not capture_name:
        capture_name = testpath

    host = mozhttpd.iface.get_lan_ip()
    http = mozhttpd.MozHttpd(handler_class=EidetickerHandler, docroot=TEST_DIR,
                             host=host, port=0)
    http.start(block=False)
    import socket
    s = socket.socket()
    s.connect

    dm = mozdevice.DeviceManagerADB(packageName=appname)
    profile = mozprofile.Profile()

    baseurl = "http://%s:%s" % (host, http.httpd.server_port)
    args = ['%s/start.html?testpath=%s' % (baseurl, testpath)]

    print "ARGS: " + str(args)
    runner = mozrunner.RemoteFennecRunner(dm, profile, args, appname=appname)
    runner.start_instance()

    timeout = 100
    timer = 0
    interval = 0.1
    while not finished and timer < timeout:
        time.sleep(interval)
        timer += interval

    print "Waiting for capture controller to finish..."
    while captureControllerFinishing and not finished:
        time.sleep(interval)

    if not finished:
        print "Did not finish test! Error!"
        sys.exit(1)

    runner.kill_all_instances()

main()
