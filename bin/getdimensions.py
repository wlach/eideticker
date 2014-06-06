#!/usr/bin/env python

from PIL import ImageDraw
import eideticker
import json
import mozhttpd
import moznetwork
import os
import sys
import time
import videocapture
import videocapture.square as square


class CaptureServer(object):

    finished = False
    start_frame = None
    end_frame = None
    capture_controller = None

    def __init__(self, capture_filename, options):
        if options.capture:
            self.capture_controller = videocapture.CaptureController(
                capture_filename, options)

    @mozhttpd.handlers.json_response
    def start_capture(self, req):
        if self.capture_controller:
            self.capture_controller.start_capture()
            self.start_frame = self.capture_controller.capture_framenum()
        print "Start capture. Frame: %s. Time: %s" % (
            self.start_frame, time.time())
        return (200, {})

    @mozhttpd.handlers.json_response
    def end_capture(self, req):
        if self.capture_controller:
            self.end_frame = self.capture_controller.capture_framenum()
            print "End capture. Frame: %s. Time: %s" % (
                self.end_frame, time.time())
            self.capture_controller.terminate_capture()

        self.finished = True
        return (200, {})

    def convert_capture(self):
        if self.capture_controller:
            self.capture_controller.convert_capture(
                self.start_frame, self.end_frame, create_webm=False)

CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "../captures")


def run_capture(options, capture_filename):
    device_prefs = eideticker.getDevicePrefs(options)

    capture_server = CaptureServer(capture_filename, options)
    host = moznetwork.get_ip()
    docroot = eideticker.test.TEST_DIR
    httpd = mozhttpd.MozHttpd(port=0, host=host, docroot=docroot, urlhandlers=[
        {'method': 'GET',
         'path': '/api/captures/start/?',
         'function': capture_server.start_capture},
        {'method': 'GET',
         'path': '/api/captures/end/?',
         'function': capture_server.end_capture}])
    httpd.start(block=False)
    print "Serving '%s' at %s:%s" % (
        httpd.docroot, httpd.host, httpd.httpd.server_port)

    device = eideticker.getDevice(**device_prefs)

    url = "http://%s:%s/getdimensions.html" % (host, httpd.httpd.server_port)

    device.executeCommand("tap", [100, 100])
    if device_prefs['devicetype'] == 'android':
        device.launchFennec(options.appname, url=url)
    else:
        if not options.wifi_settings_file:
            print "WIFI settings file (see --help) required for B2G!"
            sys.exit(1)
        device.restartB2G()
        device.connectWIFI(json.loads(open(options.wifi_settings_file).read()))

        device.marionette.execute_script("window.location.href='%s';" % url)

    while not capture_server.finished:
        time.sleep(0.25)

    capture_server.convert_capture()

    httpd.stop()

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <app name>"
    parser = eideticker.CaptureOptionParser(
        usage=usage, capture_area_option=False)
    parser.add_option("--no-capture", action="store_false",
                      dest="capture", default=True,
                      help="run through the test, but don't actually "
                      "capture anything")
    parser.add_option("--capture-file", action="store",
                      type="string", dest="capture_filename",
                      help="Existing capture to analyze instead of running "
                      "test")
    parser.add_option("--app-name", action="store",
                      type="string", dest="appname",
                      default="org.mozilla.fennec",
                      help="Specify an application name (android only)")
    parser.add_option("--output-file", action="store",
                      type="string", dest="output_file",
                      help="Output the results to file")
    parser.add_option("--output-screenshot", action="store",
                      type="string", dest="output_screenshot",
                      help="Output screenshot of a capture frame with capture "
                      "area overlayed")

    options, args = parser.parse_args()

    capture_filename = options.capture_filename
    if not capture_filename:
        if options.capture:
            capture_filename = os.path.join(CAPTURE_DIR, "capture-test-%s.zip" %
                                        time.time())
            print "Capturing to file %s" % capture_filename
        run_capture(options, capture_filename)

    if not options.capture:
        # we were just doing a test run through the steps here, we're done
        return

    print "Processing capture..."
    capture = videocapture.Capture(capture_filename)

    # create a difference. threshold differences above 32 to 255, then
    # run our existing algorithm on it
    framediff = capture.get_frame(0) - capture.get_frame(capture.num_frames-1)
    for y,row in enumerate(framediff):
        for x,px in enumerate(row):
            if px[0] > 32 or px[1] > 32 or px[2] > 32:
                framediff[y][x] = [255.0,255.0,255.0]

    largest_square = square.get_biggest_square([255,255,255], framediff,
                                               x_tolerance_min=100,
                                               x_tolerance_max=100,
                                               handle_multiple_scanlines=True)

    if largest_square is not None:
        print "Capture area: %s" % largest_square
        if options.output_file:
            with open(options.output_file, 'w+') as f:
                f.write('CAPTURE_AREA=%s\n' % largest_square)
        if options.output_screenshot:
            im = capture.get_frame_image(int(capture.length / 2))
            draw = ImageDraw.Draw(im)
            draw.rectangle(largest_square, outline=(255, 0, 0))
            im.save(options.output_screenshot)
    else:
        print "Couldn't find capture area"
        sys.exit(1)

main()
