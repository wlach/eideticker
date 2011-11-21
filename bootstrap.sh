#!/bin/sh

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
# The Original Code is the Mozilla GoFaster Dashboard.
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

PYPI_DEPS=" \
pyyaml \
"

BASEDIR=$PWD
TALOS_DIR=src/talos/talos
TALOS_EXTENSION_DIR=$TALOS_DIR/mobile_profile/extensions

# Check out git submodules
git submodule init
git submodule update

# Create virtualenv
virtualenv .
./bin/easy_install $PYPI_DEPS

# Build up videocapture utility (FIXME: should be part of the egg building process)
make -C src/videocapture/videocapture/decklink

# Install videocapture and jsbridge python eggs (and their deps)
./bin/pip install -e src/videocapture
./bin/pip install -e src/mozmill/mozrunner
./bin/pip install -e src/mozmill/jsbridge
./bin/pip install -e src/templeton

# Install fennecmark extension required by mobile talos
if [ ! -e $TALOS_EXTENSION_DIR/bench@taras.glek ]; then
    hg clone http://hg.mozilla.org/users/tglek_mozilla.com/fennecmark \
        $TALOS_EXTENSION_DIR/bench@taras.glek
fi

# Link to local extensions required by talos videocapture
for I in eideticker@mozilla.com jsbridge@mozilla.com pageloader@mozilla.org; do
    rm -f $TALOS_EXTENSION_DIR/$I
done
ln -sf $BASEDIR/src/ffx-extension $TALOS_EXTENSION_DIR/eideticker@mozilla.com
ln -sf $BASEDIR/src/mozmill/jsbridge/jsbridge/extension $TALOS_EXTENSION_DIR/jsbridge@mozilla.com
ln -sf $BASEDIR/src/pageloader $TALOS_EXTENSION_DIR/pageloader@mozilla.org

# Install mobile tp4 pageset
if [ ! -e $TALOS_DIR/page_load_test/mobile_tp4 ]; then
    wget http://people.mozilla.org/~jmaher/mobile_tp4.zip -O downloads/mobile_tp4.zip
    unzip -o downloads/mobile_tp4.zip -d $TALOS_DIR/page_load_test
fi
