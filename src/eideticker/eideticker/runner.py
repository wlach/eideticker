# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import mozprofile
import os

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
