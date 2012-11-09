# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import mozdevice
import mozprofile
import os
import shutil
import subprocess
import tempfile
import time
import zipfile

class AndroidBrowserRunner(object):

    remote_profile_dir = None
    intent = "android.intent.action.VIEW"

    def __init__(self, dm, appname, url, tmpdir, gecko_profiler_addon_dir=None,
                 extra_prefs={}):
        self.dm = dm
        self.appname = appname
        self.url = url
        self.tmpdir = tmpdir
        self.gecko_profiler_addon_dir = gecko_profiler_addon_dir
        self.extra_prefs = extra_prefs

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

    def get_profile_and_symbols(self, remote_sps_profile_location, target_zip):
        if not self.is_profiling:
           raise Exception("Can't get profile if it isn't started with the profiling option")

        files_to_package = []

        # create a temporary directory to place the profile and shared libraries
        profiledir = tempfile.mkdtemp(dir=self.tmpdir)

        # remove previous profiles if there is one
        sps_profile_path = os.path.join(profiledir, "fennec_profile.txt")
        if os.path.exists(sps_profile_path):
            os.remove(sps_profile_path)

        print "Fetching fennec_profile.txt"
        self.dm.getFile(remote_sps_profile_location, sps_profile_path)
        files_to_package.append(sps_profile_path)

        # FIXME: We still get a useful profile without the symbols from the apk
        # make doing this optional so we don't require a rooted device
        print "Fetching app symbols"
        local_apk_path = os.path.join(profiledir, "symbol.apk")
        self.dm.getAPK(self.appname, local_apk_path)
        files_to_package.append(local_apk_path)

        # get all the symbols library for symbolication
        print "Fetching system libraries"
        libpaths = [ "/system/lib",
                     "/system/lib/egl",
                     "/system/lib/hw",
                     "/system/vendor/lib",
                     "/system/vendor/lib/egl",
                     "/system/vendor/lib/hw",
                     "/system/b2g" ]

        for libpath in libpaths:
             print "Fetching from: " + libpath
             dirlist = self.dm.listFiles(libpath)
             for filename in dirlist:
                 filename = filename.strip()
                 if filename.endswith(".so"):
                     lib_path = os.path.join(profiledir, filename)
                     remotefilename = libpath + '/' + filename
                     self.dm.getFile(remotefilename, lib_path)
                     files_to_package.append(lib_path);

        with zipfile.ZipFile(target_zip, "w") as zip_file:
            for file_to_package in files_to_package:
                zip_file.write(file_to_package, os.path.basename(file_to_package))

        shutil.rmtree(profiledir)

    def start(self, enable_profiling=False):
        print "Starting %s... " % self.appname

        # for fennec only, we create and use a profile
        if self.appname.startswith('org.mozilla'):
            args = []
            self.is_profiling = enable_profiling
            preferences = { 'gfx.show_checkerboard_pattern': False,
                            'browser.firstrun.show.uidiscovery': False,
                            'toolkit.telemetry.prompted': 2 }
            preferences.update(self.extra_prefs)

            # Add frame counter to correlate video capture with profile
            if self.is_profiling:
                preferences['layers.acceleration.frame-counter'] = True

            profile = mozprofile.Profile(preferences = preferences)
            self.remote_profile_dir = "/".join([self.dm.getDeviceRoot(),
                                                os.path.basename(profile.profile)])
            self.dm.pushDir(profile.profile, self.remote_profile_dir)

            if self.is_profiling:
                mozEnv = { "MOZ_PROFILER_STARTUP": "true" }
            else:
                mozEnv = None

            args.extend(["-profile", self.remote_profile_dir])

            # sometimes fennec fails to start, so we'll try three times...
            for i in range(3):
                print "Launching %s (try %s of 3)" % (self.appname, i+1)
                try:
                    self.dm.launchFennec(self.appname, url=self.url, mozEnv=mozEnv, extraArgs=args)
                except mozdevice.DMError:
                    continue
                return # Ok!
            raise Exception("Failed to start Fennec after three tries")
        else:
            self.is_profiling = False # never profiling with non-fennec browsers
            self.dm.launchApplication(self.appname, self.activity, self.intent,
                                      url=self.url)

    def save_profile(self):
        # Dump the profile (don't process it yet because we need to cleanup
        # the capture first)
        print "Saving sps performance profile"
        appPID = self.dm.getPIDs(self.appname)[0]
        self.dm.sendSaveProfileSignal(self.appname)
        self.remote_sps_profile_location = "/mnt/sdcard/profile_0_%s.txt" % appPID
        # Saving goes through the main event loop so give it time to flush
        time.sleep(10)

    def process_profile(self, profile_file):
        with tempfile.NamedTemporaryFile() as temp_profile_file:
            self.get_profile_and_symbols(self.remote_sps_profile_location,
                                         temp_profile_file.name)
            self.dm.removeFile(self.remote_sps_profile_location)
            subprocess.check_call(["./symbolicate.sh",
                                   os.path.abspath(temp_profile_file.name),
                                   os.path.abspath(profile_file)],
                                  cwd=self.gecko_profiler_addon_dir)



    def cleanup(self):
        # stops the process and cleans up after a run
        self.dm.killProcess(self.appname)

        # Remove the Mozilla profile from the sdcard (not to be confused with
        # the sampling profile)
        if self.remote_profile_dir:
            self.dm.removeDir(self.remote_profile_dir)
            print "WARNING: Failed to remove profile (%s) from device" % self.remote_profile_dir
