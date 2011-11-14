#!/usr/bin/env python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Eideticker.
#
# The Initial Developer of the Original Code is
# Mozilla foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   William Lachance <wlachance@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import atexit
import optparse
import os
import sys
import json
import signal
import subprocess

BINDIR = os.path.dirname(__file__)
TALOS_DIR = os.path.abspath(os.path.join(BINDIR, "../src/talos/talos"))
CAPTURE_DIR = os.path.abspath(os.path.join(BINDIR, "../captures"))
CONFIG_FILE = os.path.abspath(os.path.join(BINDIR, "../conf/talos.config"))
MANIFEST_FILES = {
    "tp4m": "page_load_test/tp4m.manifest",
    "tsvg": "page_load_test/svg/svg.manifest"
    }

class FatalError(Exception):
  def __init__(self, msg):
    self.msg = msg
  def __str__(self):
    return repr(self.msg)

class TalosRunner:

    def __init__(self, testname, manifest, pagename):
        try:
            self.config = json.loads(open(CONFIG_FILE).read())
        except:
            raise FatalError("Could not read configuration file %s" % CONFIG_FILE)

        self.testname = testname
        self.manifest = manifest
        self.pagename = pagename

    def _kill_bcontrollers(self):
        pids = subprocess.check_output("ps ax | grep bcontroller.py | grep -v grep | "
                                       " cut -d ' ' -f 1", shell=True).split()
        for pid in pids:
            os.kill(int(pid), 9)

    def _write_manifest_file(self):
        manifest_file = MANIFEST_FILES.get(self.manifest)
        if not manifest_file:
            raise FatalError("No file associated with manifest %s" % self.manifest)

        manifest_file = os.path.join(TALOS_DIR, manifest_file)
        page = None
        try:
            for line in open(manifest_file).readlines():
                if self.pagename in line:
                    page = line.rstrip()
                    break
        except:
            raise FatalError("Unable to read from manifest file %s" % manifest_file)

        if not page:
            raise FatalError("Page %s not found in manifest" % pagename)

        abridged_manifest_file = os.path.join(TALOS_DIR, "page_load_test/v.manifest")
        try:
            with open(abridged_manifest_file, "w") as f:
                f.write(page+"\n")
        except:
            raise FatalError("Can't write abridged manifest file %s" % abridged_manifest_file)

    def run(self):
        print "TESTNAME: %s" % self.testname
        if self.testname == "tpageload":
            print "WRITING manifest"
            self._write_manifest_file()

        try:
            os.chdir(TALOS_DIR)
            def check_shell_call(str):
                if subprocess.call(str, shell=True) != 0:
                    raise FatalError("Subprocess call '%s' failed" % str)

            check_shell_call("python remotePerfConfigurator.py -v -e %s "
                             "--activeTests %s --sampleConfig eideticker-base.config "
                             "--noChrome --videoCapture --captureDir %s --develop "
                             "--remoteDevice=%s "
                             "--output eideticker-%s.config" % (self.config['appname'],
                                                                self.testname,
                                                                CAPTURE_DIR,
                                                                self.config['device_ip'],
                                                                self.testname))
            check_shell_call("python run_tests.py -d -n eideticker-%s.config" % self.testname)
        except FatalError, err:
            self._kill_bcontrollers()
            os.killpg(0, signal.SIGKILL) # kill all processes in my group
            raise err # re-raise error
        except:
            self._kill_bcontrollers()
            os.killpg(0, signal.SIGKILL) # kill all processes in my group

def main(args=sys.argv[1:]):
    usage = "usage: %prog [options] <test name> [subtest]"
    parser = optparse.OptionParser(usage)

    options, args = parser.parse_args()
    if len(args) < 1 or len(args) > 2:
        parser.error("incorrect number of arguments")

    testnames = [ "tpageload", "tcolorcycle" ] # maybe eventually load this from a file
    (testname, manifest, pagename) = (args[0], None, None)
    if testname not in testnames:
        parser.error("test '%s' not valid. valid tests are: %s" % (
                testname, " ".join(testnames)))

    if testname == "tpageload":
        if len(args) < 2:
            parser.error("must specify a subtest with a manifest and page "
                         "name (e.g. tp5m:m.news.google.com) for tpageload")
        else:
            (manifest, pagename) = args[1].split(":")

    os.setpgrp() # create new process group, become its leader
    try:
        runner = TalosRunner(testname, manifest, pagename)
        runner.run()
    except FatalError, err:
        print >> sys.stderr, "ERROR: " + err.msg
        sys.exit(1)

main()
