import os
import shutil
import subprocess

DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "../../dashboard")

def copy_dashboard_files(outputdir, indexfile='index.html'):
    # nothing to do if output dir is actually dashboard dir (well, except
    # if indexfile=='metric.html', but in that case you probably shouldn't
    # be dumping results there...)
    if os.path.abspath(outputdir) == os.path.abspath(DASHBOARD_DIR):
        return

    dashboard_filenames = subprocess.check_output(
        ['git', 'ls-files', DASHBOARD_DIR]).splitlines()
    relative_dashboard_filenames = map(lambda f:
                                           os.path.relpath(f, DASHBOARD_DIR),
                                       dashboard_filenames)
    dirnames = [outputdir] + \
        sorted(set(map(lambda x: os.path.join(outputdir,
                                              os.path.dirname(x)),
                       relative_dashboard_filenames)))
    for dirname in dirnames:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    for filename in relative_dashboard_filenames:
        source = os.path.join(DASHBOARD_DIR, filename)
        outfilename = filename
        if indexfile is not 'index.html':
            if filename == indexfile:
                outfilename = 'index.html'
            elif filename == 'index.html':
                outfilename = None
        if outfilename:
            dest = os.path.join(outputdir, outfilename)

        if os.path.isfile(dest):
            # remove any existing files to ensure we use the latest
            os.remove(dest)
        shutil.copyfile(source, dest)
