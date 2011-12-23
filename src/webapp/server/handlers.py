import templeton
import os
import json
import web
import videocapture

from zipfile import ZipFile
import Image
import tempfile

CAPTURE_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../captures"))

class CapturesHandler:

    @templeton.handlers.json_response
    def GET(self):
        captures = []
        for fname in os.listdir(CAPTURE_DIR):
            if fname == ".gitignore" or os.path.splitext(fname)[1] <> '.zip':
                continue

            capture = videocapture.Capture(os.path.join(CAPTURE_DIR, fname))
            if capture.num_frames > 0:
                captures.append(dict({ "id": fname,
                                       "length": capture.num_frames/60.0,
                                       "num_frames": capture.num_frames },
                                     **capture.metadata))

        return captures

class CaptureHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        try:
            capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))

            return dict({ "id": name, "length": capture.num_frames/60.0,
                          "num_frames": capture.num_frames },
                        **capture.metadata)
        except:
            raise web.notfound()

class CaptureImageHandler:

    @templeton.handlers.png_response
    def GET(self, name, num):
        params, body = templeton.handlers.get_request_parms()
        (width, height, cropped) = (params.get('width'), params.get('height'),
                                    bool(int(params.get('cropped', [ False ])[0])))
        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        im = capture.get_frame_image(num, cropped=cropped)
        if width and height:
            im.thumbnail((int(width[0]), int(height[0])), Image.ANTIALIAS)

        return im

class FrameDifferenceHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        return capture.get_framediff_sums()

class FrameDifferenceImageHandler:

    @templeton.handlers.png_response
    def GET(self, name, framenum1, framenum2):
        params, body = templeton.handlers.get_request_parms()
        (width, height) = (params.get('width'), params.get('height'))

        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        im = capture.get_framediff_image(framenum1, framenum2, cropped=True)
        if width and height:
            im.thumbnail((int(width[0]), int(height[0])), Image.ANTIALIAS)

        return im

class CheckerboardHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        return videocapture.get_checkerboarding_percents(capture)

class CheckerboardImageHandler:

    @templeton.handlers.png_response
    def GET(self, name, framenum):
        params, body = templeton.handlers.get_request_parms()
        (width, height) = (params.get('width'), params.get('height'))

        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        im = videocapture.get_checkerboard_image(capture, framenum)
        if width and height:
            im.thumbnail((int(width[0]), int(height[0])), Image.ANTIALIAS)

        return im


# URLs go here. "/api/" will be automatically prepended to each.
urls = (
    '/captures/?', "CapturesHandler",
    '/captures/([^/]+)/?', "CaptureHandler",
    '/captures/([^/]+)/images/([0-9]+)/?', "CaptureImageHandler",
    '/captures/([^/]+)/framediff/?', "FrameDifferenceHandler",
    '/captures/([^/]+)/framediff/images/([0-9]+)-([0-9]+)/?', "FrameDifferenceImageHandler",
    '/captures/([^/]+)/checkerboard/?', "CheckerboardHandler",
    '/captures/([^/]+)/checkerboard/images/([0-9]+)/?', "CheckerboardImageHandler"
)
