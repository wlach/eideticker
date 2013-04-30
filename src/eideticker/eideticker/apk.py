# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import zipfile

def get_fennec_appinfo(fname):
    archive = zipfile.ZipFile(fname, 'r')
    config = ConfigParser.ConfigParser()
    config.readfp(archive.open('application.ini'))
    buildid = config.get('App', 'BuildID')
    try:
        revision = config.get('App', 'SourceStamp')
    except ConfigParser.NoOptionError:
        # happens if we're not using mercurial to build fennec
        revision = None
    version = config.get('App', 'Version')
    (year, month, day) = (buildid[0:4], buildid[4:6], buildid[6:8])
    if 'package-name.txt' in archive.namelist():
        appname = archive.open('package-name.txt').read().rstrip()
    else:
        appname = None
    return { 'appdate':  "%s-%s-%s" % (year, month, day),
             'buildid': buildid,
             'revision': revision,
             'appname': appname,
             'version': version }
