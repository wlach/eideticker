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
import optparse
import os
import signal
import subprocess
import sys
import time
import urllib
import urlparse
import videocapture
import StringIO

BINDIR = os.path.dirname(__file__)
CAPTURE_DIR = os.path.abspath(os.path.join(BINDIR, "../captures"))
TEST_DIR = os.path.abspath(os.path.join(BINDIR, "../src/tests"))

capture_controller = videocapture.CaptureController()

class CaptureServer(object):
    finished = False
    controller_finishing = False
    monkey_proc = None
    start_frame = None
    end_frame = None

    def __init__(self, capture_metadata, capture_file, controller):
        self.capture_metadata = capture_metadata
        self.capture_file = capture_file
        self.controller = controller

        # open up a monkeyrunner process on startup, wait for it to give a
        # line so we don't have to wait for it later
        args = ['python', os.path.join(BINDIR, 'devicecontroller.py')]
        self.monkey_proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        line = self.monkey_proc.stdout.readline()
        # Hack: this gets rid of the "finished charging" modal dialog that the
        # LG G2X sometimes brings up
        self.monkey_proc.stdin.write('tap 240 617\n')

    @mozhttpd.handlers.json_response
    def start_capture(self, request):
        self.controller.start_capture(self.capture_file, self.capture_metadata)

        return (200, {'capturing': True})

    @mozhttpd.handlers.json_response
    def end_capture(self, request):
        self.finished = True
        self.controller.terminate_capture()
        if self.monkey_proc and not self.monkey_proc.poll():
            self.monkey_proc.kill()
        return (200, {'capturing': False})

    @mozhttpd.handlers.json_response
    def input(self, request):
        commands = urlparse.parse_qs(request.body)['commands[]']
        print commands
        self.start_frame = self.controller.capture_framenum()
        #print "GOT COMMANDS. Framenum: %s" % self.start_frame
        print commands
        for command in commands:
            self.monkey_proc.stdin.write('%s\n' % command)
        self.monkey_proc.stdin.write('quit\n')
        self.monkey_proc.wait()
        self.end_frame = self.controller.capture_framenum()
        #print "DONE COMMANDS. Framenum: %s" % self.end_frame

        return (200, {})

class BrowserRunner(object):

    def __init__(self, dm, appname, url):
        self.dm = dm
        self.appname = appname
        self.url = url
        self.intent = "android.intent.action.VIEW"

        activity_mappings = {
            'com.android.browser': 'BrowserActivity'
            }

        # use activity mapping if not mozilla
        if self.appname.startswith('org.mozilla'):
            self.activity = 'App'
            self.intent = None
        else:
            self.activity = activity_mappings[self.appname]

    def start(self):
        # for fennec only, we create and use a profile
        args = []
        profile = None
        if self.appname.startswith('org.mozilla'):
            profile = mozprofile.Profile(preferences = { 'gfx.show_checkerboard_pattern': False })
            remote_profile_dir = "/".join([self.dm.getDeviceRoot(),
                                       os.path.basename(profile.profile)])
            if not self.dm.pushDir(profile.profile, remote_profile_dir):
                raise Exception("Failed to copy profile to device")

            args.extend(["-profile", remote_profile_dir])

        print "Starting %s... " % self.appname
        self.dm.launchApplication(self.appname, intent=self.intent,
                                  activity=self.activity,
                                  url=self.url, extra_args=args)

    def stop(self):
        self.dm.killProcess(self.appname)

# FIXME: make this part of devicemanager
def _shell_check_output(dm, args):
    buf = StringIO.StringIO()
    dm.shell(args, buf)
    return buf.getvalue()


def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <appname> <test path>"
    parser = optparse.OptionParser(usage)
    parser.add_option("--name", action="store",
                      type = "string", dest = "capture_name",
                      help = "name to give capture")
    parser.add_option("--capture-file", action="store",
                      type = "string", dest = "capture_file",
                      help = "name to give to capture file")

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
    capture_file = options.capture_file
    if not capture_file:
        capture_file = os.path.join(CAPTURE_DIR, "capture-%s.zip" %
                                         datetime.datetime.now().isoformat())

    dm = mozdevice.DroidADB(packageName=appname)

    if dm.processExist(appname):
        print "An instance of %s is running. Please stop it before running Eideticker." % appname
        sys.exit(1)

    print "Creating webserver..."
    capture_metadata = {
        'name': capture_name,
        'testpath': testpath,
        'app': appname,
        'device': _shell_check_output(dm, ["getprop", "ro.product.model"]).strip()
        }
    capture_server = CaptureServer(capture_metadata, capture_file,
                                   capture_controller)
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
        except Exception, e:
            print "Can't connect to %s:%s, retrying..." % (host, http.httpd.server_port)

    if not connected:
        print "Could not open webserver. Error!"
        sys.exit(1)

    url = "http://%s:%s/start.html?testpath=%s" % (host,
                                                   http.httpd.server_port,
                                                   testpath)
    print "Test URL is: %s" % url
    runner = BrowserRunner(dm, appname, url)
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
        sys.exit(1)

    print "Converting capture..."
    capture_controller.convert_capture(capture_server.start_frame, capture_server.end_frame)

main()
