# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import eideticker
import mozhttpd
import urlparse
import time
import imp
import os
from gaiatest.gaia_test import LockScreen

class CaptureServer(object):

    start_capture_called = False
    end_capture_called = False
    input_called = False

    def __init__(self, test):
        self.test = test

    @mozhttpd.handlers.json_response
    def start_capture(self, request):
        print "Received start capture callback from test"
        assert not self.start_capture_called
        self.start_capture_called = True
        self.test.start_capture()

        return (200, {'capturing': True})

    @mozhttpd.handlers.json_response
    def end_capture(self, request):
        print "Received end capture callback from test"
        assert not self.end_capture_called
        self.end_capture_called = True
        self.test.end_capture()

        return (200, {'capturing': False})

    @mozhttpd.handlers.json_response
    def input(self, request):
        commandset = urlparse.parse_qs(request.body)['commands'][0]
        print "Received input callback from test"
        assert not self.input_called
        self.input_called = True
        self.test.execute_actions(commandset)

        return (200, {})

def get_test(devicetype="android", testtype="web", testpath=None, **kwargs):
    if devicetype == 'b2g':
        if testtype == 'web':
            return B2GWebTest(**kwargs)
        else:
            (basepath, testfile) = os.path.split(testpath)
            (file, pathname, description) = imp.find_module(testfile[0:-3],
                                                            [basepath])
            module = imp.load_module('test', file, pathname, description)
            test = module.Test(**kwargs)
            return test
    else:
        if testtype == 'webstartup':
            return AndroidWebStartupTest(**kwargs)
        elif testtype == 'appstartup':
            return AndroidAppStartupTest(**kwargs)
        elif testtype == "web":
            return AndroidWebTest(**kwargs)

class Test(object):

    finished_capture = False
    start_frame = None
    end_frame = None
    track_start_end_frames = False

    def __init__(self, testpath=None, testpath_rel=None, device=None, capture_file = None,
                 capture_controller=None,
                 capture_metadata={}, capture_timeout=None, tempdir=None,
                 no_capture=False, track_start_end_frames=False, **kwargs):
        self.testpath = testpath
        self.testpath_rel = testpath_rel
        self.device = device
        self.capture_file = capture_file
        self.capture_controller = capture_controller
        self.capture_metadata = capture_metadata
        self.capture_timeout = capture_timeout
        self.tempdir = tempdir
        self.no_capture = no_capture
        self.track_start_end_frames = track_start_end_frames

    def cleanup(self):
        pass

    def wait(self):
        # Keep on capturing until we finish or timeout
        if self.capture_timeout:
            timeout = int(self.capture_timeout)
        else:
            timeout = 100
        timer = 0
        interval = 0.1

        try:
            while not self.finished_capture and timer < timeout:
                time.sleep(interval)
                timer += interval
        except KeyboardInterrupt:
            self.end_capture()
            raise Exception("Aborted test")

        if self.capture_timeout and not self.finished_capture:
            # this test was meant to time out, ok
            self.test_finished()
            self.end_capture()
        elif not self.finished_capture:
            raise Exception("Did not finish test / capture! Error!")

    def start_capture(self):
        # callback indicating we should start capturing (if we're not doing so already)
        if self.capture_file and not self.capture_controller.capturing:
            print "Starting capture on device '%s' with mode: '%s'" % (self.capture_metadata['device'],
                                                                       self.device.hdmiResolution)
            self.capture_controller.start_capture(self.capture_file,
                                                  self.device.hdmiResolution,
                                                  self.capture_metadata)

    def end_capture(self):
        # callback indicating we should terminate the capture
        print "Ending capture"
        self.finished_capture = True
        if self.capture_file:
            self.capture_controller.terminate_capture()

    def test_started(self):
        # callback indicating test has started
        if self.capture_file and self.track_start_end_frames:
            self.start_frame = self.capture_controller.capture_framenum()

        print "Test started callback (time: %s, framenum: %s)" % (time.time(), self.start_frame)

    def test_finished(self):
        # callback indicating test has finished
        if self.capture_file and self.track_start_end_frames:
            self.end_frame = self.capture_controller.capture_framenum()

        print "Test finished callback (time: %s, framenum: %s)" % (time.time(), self.end_frame)

class WebTest(Test):

    def __init__(self, actions={}, docroot=None, **kwargs):
        super(WebTest, self).__init__(track_start_end_frames = True, **kwargs)

        self.actions = actions

        self.capture_server = CaptureServer(self)
        self.host = mozhttpd.iface.get_lan_ip()
        self.http = mozhttpd.MozHttpd(docroot=docroot,
                                      host=self.host, port=0,
                                      urlhandlers = [
                { 'method': 'GET',
                  'path': '/api/captures/start/?',
                  'function': self.capture_server.start_capture },
                { 'method': 'GET',
                  'path': '/api/captures/end/?',
                  'function': self.capture_server.end_capture },
                { 'method': 'POST',
                  'path': '/api/captures/input/?',
                  'function': self.capture_server.input } ])
        self.http.start(block=False)

        connected = False
        tries = 0
        while not connected and tries < 20:
            tries+=1
            import socket
            s = socket.socket()
            try:
                s.connect((self.host, self.http.httpd.server_port))
                connected = True
            except Exception:
                print "Can't connect to %s:%s, retrying..." % (self.host, self.http.httpd.server_port)

        print "Test URL is: %s" % self.url

        if not connected:
            raise "Could not open webserver. Error!"


    @property
    def url(self):
        return "http://%s:%s/start.html?testpath=%s" % (self.host,
                                                        self.http.httpd.server_port,
                                                        self.testpath_rel)
    def execute_actions(self, commandset):
        if self.actions: # startup test indicated by no actions
            print "Executing commands '%s' for device '%s' (time: %s, framenum: %s)" % (
                commandset, self.device.model, time.time(), self.start_frame)
            if not self.actions.get(commandset) or not \
                        self.actions[commandset].get(self.device.model):
                    raise Exception("Could not get actions for commandset "
                                    "'%s', model '%s'" % (commandset,
                                                          self.device.model))
            device_actions = self.actions[commandset][self.device.model]

            def executeCallback():
                self.test_started()
            self.device.executeCommands(device_actions,
                                        executeCallback=executeCallback)
            self.test_finished()
        else:
            # startup test: we start and finish, all at once
            self.test_started()
            self.test_finished()

class AndroidWebTest(WebTest):

    def __init__(self, appname = None, extra_prefs = {}, profile_file = None,
                 preinitialize_user_profile = False,
                 gecko_profiler_addon_dir = None, checkerboard_log_file = None,
                 **kwargs):
        super(AndroidWebTest, self).__init__(**kwargs)

        self.appname = appname
        self.extra_prefs = extra_prefs
        self.checkerboard_log_file = checkerboard_log_file
        self.profile_file = profile_file
        self.gecko_profiler_addon_dir = gecko_profiler_addon_dir
        self.preinitialize_user_profile = preinitialize_user_profile

        # If we're logging checkerboard stats, set that up here (seems like it
        # takes a second or so to accept the new setting, so let's do that here --
        # ideally we would detect when that's working, but I'm not sure how to do
        # so trivially)
        if self.checkerboard_log_file:
            self.old_log_val = self.device.getprop("log.tag.GeckoLayerRendererProf")
            self.device.setprop("log.tag.GeckoLayerRendererProf", "DEBUG")

        # something of a hack. if profiling is enabled, carve off an area to
        # ignore in the capture
        if self.profile_file:
            self.capture_metadata['ignoreAreas'] = [ [ 0, 0, 3*64, 3 ] ]

        # precondition: app should not be running. abort if it is
        if self.device.processExist(self.appname):
            raise Exception("An instance of %s is running. Please stop it "
                            "before running Eideticker." % self.appname)

        self.runner = eideticker.AndroidBrowserRunner(self.device, self.appname,
                                                      self.url, self.tempdir,
                                                      preinitialize_user_profile=self.preinitialize_user_profile,
                                                      enable_profiling=bool(self.profile_file),
                                                      gecko_profiler_addon_dir=gecko_profiler_addon_dir,
                                                      extra_prefs=self.extra_prefs)

    def cleanup(self):
        # Clean up checkerboard logging preferences
        if self.checkerboard_log_file:
            self.device.setprop("log.tag.GeckoLayerRendererProf", self.old_log_val)

        # kill fennec, clean up temporary user profile
        self.runner.cleanup()

    def test_started(self):
        super(AndroidWebTest, self).test_started()

        if self.checkerboard_log_file:
            self.device.recordLogcat()

    def test_finished(self):
        super(AndroidWebTest, self).test_finished()

        if self.checkerboard_log_file:
            # sleep a bit to make sure we get all the checkerboard stats from
            # test
            time.sleep(1)
            with open(self.checkerboard_log_file, 'w') as f:
                output = "\n".join(self.device.getLogcat(
                        filterSpecs=["GeckoLayerRendererProf:D", "*:S"],
                        format="brief"))
                f.write(output)

        if self.profile_file:
            self.runner.save_profile()

    def run(self):
        self.runner.start()

        self.wait()

        if self.profile_file:
            self.runner.process_profile(self.profile_file)

        self.runner.cleanup()

class AndroidWebStartupTest(AndroidWebTest):

    def __init__(self, **kwargs):
        super(AndroidWebStartupTest, self).__init__(**kwargs)

    def run(self):
        # FIXME: currently start capture before launching app because we wait until app is
        # launched -- would be better to make waiting optional and then start capture
        # after triggering app launch to reduce latency?
        self.runner.initialize_user_profile()
        if not self.no_capture:
            self.start_capture()

        super(AndroidWebStartupTest, self).run()

    @property
    def url(self):
        if self.testpath_rel == "about:home":
            return self.testpath_rel
        else:
            return "http://%s:%s/%s?startup_test=1" % (self.host,
                                                       self.http.httpd.server_port,
                                                       self.testpath_rel)

class AndroidAppStartupTest(Test):

    def __init__(self, appname=None, activity=None, intent=None, **kwargs):
        super(AndroidAppStartupTest, self).__init__(**kwargs)
        self.appname = appname
        self.activity = activity
        self.intent = intent

        # precondition: app should not be running. abort if it is
        if self.device.processExist(self.appname):
            raise Exception("An instance of %s is running. Please stop it "
                            "before running Eideticker." % self.appname)

    def run(self):
        # FIXME: currently start capture before launching app because we wait until app is
        # launched -- would be better to make waiting optional and then start capture
        # after triggering app launch to reduce latency?
        if not self.no_capture:
            self.start_capture()
        self.device.launchApplication(self.appname, self.activity, self.intent)
        self.wait()

class B2GTest(Test):

    def __init__(self, **kwargs):
        super(B2GTest, self).__init__(**kwargs)
        print "Setting up device"
        self.device.setupDHCP()

        self.device.setupMarionette()
        session = self.device.marionette.session
        if 'b2g' not in session:
            raise Exception("bad session value %s returned by start_session" % session)

        # unlock device, so it doesn't go to sleep
        ls = LockScreen(self.device.marionette)
        ls.unlock()

        # Wait for device to properly recognize network
        # (FIXME: this timeout is terrible, can we do check for network
        # connectivity with marionette somehow?)
        time.sleep(5)

        # reset orientation to default for this type of device
        self.device.resetOrientation()

    def cleanup(self):
        self.device.marionette.delete_session()
        self.device.cleanup()
        self.device.restartB2G()

class B2GWebTest(B2GTest, WebTest):

    def __init__(self, **kwargs):
        super(B2GWebTest, self).__init__(**kwargs)

    def run(self):
        # start the tests by navigating to the url
        print "Navigating to %s" % self.url
        self.device.marionette.execute_script("window.location.href='%s';" % self.url)
        self.wait()
