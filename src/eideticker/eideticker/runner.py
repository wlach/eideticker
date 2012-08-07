# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import mozprofile
import os
import time

from marionette import Marionette

class B2GRunner(object):
    remote_profile_dir = None

    def __init__(self, dm, url, marionette_host='localhost', marionette_port=2828):
        self.dm = dm
        self.url = url
        self.marionette = Marionette(marionette_host, marionette_port)

    def start(self):
	"""
        #restart b2g so we start with a clean slate
        self.dm.checkCmd(['shell', 'stop', 'b2g'])
        # Wait for a bit to make sure B2G has completely shut down.
        time.sleep(10)
        self.dm.checkCmd(['shell', 'start', 'b2g'])
	"""
        #TODO: how to check for when b2g is up? procs?

        #forward the marionette port
        self.dm.checkCmd(['forward',
                          'tcp:%s' % self.marionette.port,
                          'tcp:%s' % self.marionette.port])

	#enable ethernet connection
        #ethFile = open("ethFile", "rw")
        #self.dm.shell("netcfg eth0 dhcp", ethFile)
        print "running netcfg, it may take some time"
	t = time.time()
        self.dm.checkCmd(['shell', 'netcfg', 'eth0', 'dhcp'])
	print time.time() - t
        print "sleeping"
        #time.sleep(4)
        print "launching"
        #launch app
        session = self.marionette.start_session()
	print "got session"
        if 'b2g' not in session:
            raise Exception("bad session value %s returned by start_session" % session)

        # start the tests by navigating to the mochitest url
	print "loading test"
        self.marionette.execute_script("window.location.href='%s';" % self.url)
	print "loaded"

    def stop(self):
        self.marionette.delete_session()

class BrowserRunner(object):

    remote_profile_dir = None
    intent = "android.intent.action.VIEW"

    def __init__(self, dm, appname, url):
        self.dm = dm
        self.appname = appname
        self.url = url

        activity_mappings = {
            'com.android.browser': '.BrowserActivity',
            'com.google.android.browser': 'com.android.browser.BrowserActivity',
            'com.android.chrome': '.Main',
            'com.opera.browser': 'com.opera.Opera',
            'mobi.mgeek.TunnyBrowser': '.BrowserActivity' # Dolphin
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
            profile = mozprofile.Profile(preferences = { 'gfx.show_checkerboard_pattern': False,
                                                         'browser.firstrun.show.uidiscovery': False,
                                                         'toolkit.telemetry.prompted': 2 })
            self.remote_profile_dir = "/".join([self.dm.getDeviceRoot(),
                                                os.path.basename(profile.profile)])
            if not self.dm.pushDir(profile.profile, self.remote_profile_dir):
                raise Exception("Failed to copy profile to device")

            args.extend(["-profile", self.remote_profile_dir])

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
        if not self.dm.removeDir(self.remote_profile_dir):
            raise Exception("Failed to remove profile from device")
