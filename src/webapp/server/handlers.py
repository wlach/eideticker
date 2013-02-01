import templeton
import os
import web
import videocapture

from PIL import Image

CAPTURE_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../captures"))

class CapturesHandler:

    @templeton.handlers.json_response
    def GET(self):
        captures = []
        for fname in os.listdir(CAPTURE_DIR):
            if fname == ".gitignore" or os.path.splitext(fname)[1] <> '.zip':
                continue

            try:
                capture = videocapture.Capture(os.path.join(CAPTURE_DIR, fname))
                if capture.num_frames > 0:
                    print "filename: %s" % fname
                    captures.append(dict({ "id": fname,
                                           "length": capture.num_frames/60.0,
                                           "numFrames": capture.num_frames,
                                           "filename": fname },
                                         **capture.metadata))
            except videocapture.BadCapture, error:
                print "File %s unreadable: %s" % (fname, str(error))
                # just ignore files that aren't readable as captures
                pass

        return sorted(captures, key=lambda c: c['date'])

class CaptureHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        try:
            fname = os.path.join(CAPTURE_DIR, name)
            capture = videocapture.Capture(fname)

            return dict({ "id": name, "length": capture.num_frames/60.0,
                          "numFrames": capture.num_frames, "filename": fname },
                        **capture.metadata)
        except:
            raise web.notfound()

class CaptureVideoHandler:

    def GET(self, name):
        try:
            capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
            videofile = capture.get_video()
            data = videofile.getvalue()
            web.header('Content-Type', 'video/webm')

            # Using idea from here:
            # http://vanderwijk.info/2010/9/17/implementing-http-206-partial-content-support-for-web-py
            range = web.ctx.env.get('HTTP_RANGE')
            if range is None:
                web.header('Content-Length', len(data))
                return data

            total = len(data)
            _, r = range.split("=")
            partial_start, partial_end = r.split("-")

            start = int(partial_start)

            if not partial_end:
                end = total-1
            else:
                end = int(partial_end)

            chunksize = (end-start)+1

            web.ctx.status = "206 Partial Content"
            web.header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
            web.header("Accept-Ranges", "bytes")
            web.header("Content-Length", chunksize)

            return data[start:end+1]
        except:
            raise web.notfound()

class CaptureImageHandler:

    @templeton.handlers.png_response
    def GET(self, name, num):
        params, body = templeton.handlers.get_request_parms()
        (width, height) = (params.get('width'), params.get('height'))
        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        im = capture.get_frame_image(int(num))
        if width and height:
            im.thumbnail((int(width[0]), int(height[0])), Image.ANTIALIAS)

        return im

class FrameDifferenceHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        return videocapture.get_framediff_sums(capture)

class FrameDifferenceImageHandler:

    @templeton.handlers.png_response
    def GET(self, name, framenum1, framenum2):
        params, body = templeton.handlers.get_request_parms()
        (width, height) = (params.get('width'), params.get('height'))

        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        im = videocapture.get_framediff_image(capture, framenum1, framenum2)
        if width and height:
            im.thumbnail((int(width[0]), int(height[0])), Image.ANTIALIAS)

        return im

class CheckerboardHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        capture = videocapture.Capture(os.path.join(CAPTURE_DIR, name))
        percents = videocapture.get_checkerboarding_percents(capture)
        area_duration = videocapture.get_checkerboarding_area_duration(capture)
        return { "areaDuration": area_duration,
                 "numCheckerboards": len(filter(lambda f: f > 0.0, percents)),
                 "numFrames": capture.num_frames }

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
    '/captures/([^/]+)/video/?', "CaptureVideoHandler",
    '/captures/([^/]+)/images/([0-9]+)/?', "CaptureImageHandler",
    '/captures/([^/]+)/framediff/?', "FrameDifferenceHandler",
    '/captures/([^/]+)/framediff/images/([0-9]+)-([0-9]+)/?', "FrameDifferenceImageHandler",
    '/captures/([^/]+)/checkerboard/?', "CheckerboardHandler",
    '/captures/([^/]+)/checkerboard/images/([0-9]+)/?', "CheckerboardImageHandler"
)
