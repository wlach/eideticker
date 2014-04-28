# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import zipfile
import datetime
import time

def get_appinfo(fh):
    config = ConfigParser.ConfigParser()
    config.readfp(fh)
    buildid = config.get('App', 'BuildID')
    try:
        revision = config.get('App', 'SourceStamp')
    except ConfigParser.NoOptionError:
        # happens if we're not using mercurial to build fennec
        revision = None
    version = config.get('App', 'Version')
    tm = time.strptime(buildid, '%Y%m%d%H%M%S')
    date = datetime.datetime(*tm[:6])
    try:
        sourcerepo = config.get('App', 'SourceRepository')
    except ConfigParser.NoOptionError:
        sourcerepo = None
    return {'appdate': "%s" % int(time.mktime(date.timetuple())),
            'buildid': buildid,
            'revision': revision,
            'sourceRepo': sourcerepo,
            'version': version}


def get_fennec_appinfo(fname):
    archive = zipfile.ZipFile(fname, 'r')
    appinfo = {}
    if 'package-name.txt' in archive.namelist():
        appinfo['appname'] = archive.open('package-name.txt').read().rstrip()

    appinfo.update(get_appinfo(archive.open('application.ini')))

    return appinfo
