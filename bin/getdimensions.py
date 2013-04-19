#!/usr/bin/env python

import eideticker
import mozhttpd
import moznetwork
import sys
import time
import videocapture
import os
import videocapture.square as square

class CaptureServer(object):

    finished = False
    start_frame = None
    end_frame = None
    capture_controller = None
    capture_file = None

    def __init__(self, capture_file, capture_device, mode, no_capture=False):
        if not no_capture:
            self.capture_controller = videocapture.CaptureController(capture_device)
            self.mode = mode
            self.capture_file = capture_file

    def start_capture(self, req):
        if self.capture_controller:
            self.capture_controller.start_capture(self.capture_file, self.mode)
            while self.capture_controller.capture_framenum() < 1:
                time.sleep(0.1)
            self.start_frame = self.capture_controller.capture_framenum()
        print "Start capture. Frame: %s. Time: %s" % (self.start_frame, time.time())
        return (200, {}, '')

    def end_capture(self, req):
        if self.capture_controller:
            self.end_frame = self.capture_controller.capture_framenum()
            print "End capture. Frame: %s. Time: %s" % (self.end_frame, time.time())
            self.capture_controller.terminate_capture()

        self.finished = True
        return (200, {}, '')

    def convert_capture(self):
        if self.capture_controller:
            self.capture_controller.convert_capture(self.start_frame,
                                                    self.end_frame)

CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")

def run_capture(options, capture_file):
    device_prefs = eideticker.getDevicePrefs(options)

    capture_server = CaptureServer(capture_file, options.capture_device,
                                   options.mode,
                                   no_capture=options.no_capture)
    host = moznetwork.get_ip()
    docroot = eideticker.runtest.TEST_DIR
    httpd = mozhttpd.MozHttpd(port=0, host=host, docroot=docroot,
                              urlhandlers = [ { 'method': 'GET',
                                                'path': '/api/captures/start/?',
                                                'function': capture_server.start_capture },
                                              { 'method': 'GET',
                                                'path': '/api/captures/end/?',
                                                'function': capture_server.end_capture }
                                              ])
    httpd.start(block=False)
    print "Serving '%s' at %s:%s" % (httpd.docroot, httpd.host, httpd.httpd.server_port)

    device = eideticker.getDevice(**device_prefs)
    mode = options.mode
    if not mode:
        mode = device.hdmiResolution

    url = "http://%s:%s/getdimensions.html" % (host, httpd.httpd.server_port)

    device.executeCommand("tap", [100, 100])
    if device_prefs['devicetype'] == 'android':
        device.launchFennec(options.appname, url=url)
    else:
        device.setupDHCP()
        device.setupMarionette()
        session = device.marionette.session
        if 'b2g' not in session:
            raise Exception("bad session value %s returned by start_session" % session)

        device.unlock()
        # wait for device to become ready (yes, this is terrible, can we
        # detect this condition in marionette somehow?)
        time.sleep(5)
        device.marionette.execute_script("window.location.href='%s';" % url)

    while not capture_server.finished:
        time.sleep(0.25)

    capture_server.convert_capture()

    device.killProcess(options.appname)
    httpd.stop()

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <app name>"
    parser = eideticker.CaptureOptionParser(usage=usage)
    parser.add_option("--no-capture", action="store_true",
                      dest = "no_capture",
                      help = "run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--capture-file", action="store",
                      type="string", dest="capture_file",
                      help="Existing capture to analyze instead of running test")
    parser.add_option("--app-name", action="store",
                      type="string", dest="appname",
                      default="org.mozilla.fennec",
                      help="Specify an application name (android only)")

    options, args = parser.parse_args()
    parser.validate_options(options)

    capture_file = options.capture_file
    if not capture_file:
        capture_file = os.path.join(CAPTURE_DIR, "capture-test-%s.zip" % time.time())
        print "Capturing to file %s" % capture_file
        run_capture(options, capture_file)

    if options.no_capture:
        # we were just doing a test run through the steps here, we're done
        return

    print "Processing capture..."
    capture = videocapture.Capture(capture_file)
    squares = []
    largest_square = None
    largest_square_area = None
    for (i, framenum) in enumerate(range(1, capture.num_frames)):
        imgarray = videocapture.get_framediff_imgarray(capture, framenum-1, framenum,
                                                       threshold=8.0)
        squares.append(square.get_biggest_square([255,0,0],
                                                 imgarray,
                                                 x_tolerance_min=100,
                                                 x_tolerance_max=100,
                                                 handle_multiple_scanlines=True))
        if squares[i]:
            square_area = square.get_area(squares[i])
        else:
            square_area = 0
        if largest_square is None or largest_square_area < square_area:
            largest_square = i
            largest_square_area = square_area
        print (i, largest_square)
    if largest_square is not None:
        print "Capture area: %s (frame: %s)" % (squares[largest_square], largest_square)
    else:
        print "Couldn't find capture area"

main()
