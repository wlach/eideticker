import templeton
import os
import json
import web

from zipfile import ZipFile
import Image
import tempfile
import StringIO

CAPTURE_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../captures"))

class CapturesHandler:

    @templeton.handlers.json_response
    def GET(self):
        captures = []
        for fname in os.listdir(CAPTURE_DIR):
            if fname == ".gitignore":
                continue

            fullpath = os.path.join(CAPTURE_DIR, fname)
            with ZipFile(fullpath, 'r') as archive:
                metadata = json.loads(archive.open('metadata.json').read())
                num_frames = len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                                        archive.namelist()))
                captures.append(dict({ "id": fname, "length": num_frames/60.0,
                                       "num_frames": num_frames }, **metadata))

        return captures

class CaptureHandler:

    @templeton.handlers.json_response
    def GET(self, name):
        path = os.path.join(CAPTURE_DIR, name)
        # FIXME: generalize this duplicated code in capture.py
        with ZipFile(path, 'r') as archive:
            metadata = json.loads(archive.open('metadata.json').read())
            num_frames = len(filter(lambda s: s[0:7] == "images/" and len(s) > 8,
                                    archive.namelist()))
            (width, height) = (0,0)
            if num_frames > 0:
                f = tempfile.TemporaryFile(suffix=".png")
                f.write(archive.read('images/1.png'))
                f.seek(0)
                im = Image.open(f)
                (width, height) = im.size

            return dict({ "id": name, "length": num_frames/60.0,
                          "num_frames": num_frames,
                          "width": width, "height": height },
                        **metadata)
        raise web.notfound()


class CaptureImageHandler:

    def GET(self, name, num):
        params, body = templeton.handlers.get_request_parms()
        (width, height) = (params.get('width'), params.get('height'))

        path = os.path.join(CAPTURE_DIR, name)
        with ZipFile(path, 'r') as archive:
            imagepath = "images/%s.png" % num
            f = tempfile.TemporaryFile(suffix=".png")
            f.write(archive.open(imagepath).read())
            f.seek(0)
            im = Image.open(f)
            print (width, height)
            if width and height:
                im.thumbnail((int(width[0]), int(height[0])), Image.ANTIALIAS)
            output = StringIO.StringIO()
            im.save(output, format="PNG")
            data = output.getvalue()
            print "Gotcha!"
            web.header('Content-Length', len(data))
            web.header('Content-Type', 'image/png')
            return data

        #raise web.notfound()

# URLs go here. "/api/" will be automatically prepended to each.
urls = (
    '/captures/?', "CapturesHandler",
    '/captures/([^/]+)/?', "CaptureHandler",
    '/captures/([^/]+)/images/([0-9]+)/?', "CaptureImageHandler",
)

# Handler classes go here
