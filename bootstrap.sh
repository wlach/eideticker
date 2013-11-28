#!/bin/sh

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

BASEDIR=$PWD

for PROG in virtualenv g++ ffmpeg; do
    which $PROG > /dev/null
    if [ $? != 0 ]; then
        echo "Required dep $PROG not found. Please install ('sudo apt-get install -y python-virtualenv g++ ffmpeg' on Ubuntu gets them all)"
        exit 1
    fi
done

if [ ! -e /usr/include/python2.7/Python.h ]; then
    echo "Please install Python 2.7 development files ('sudo apt-get install -y python2.7-dev' on Ubuntu)"
    exit 1
fi

set -e

# Check out git submodules
git submodule init
git submodule update

# Create virtualenv
virtualenv .

# Build up videocapture utility (FIXME: should be part of the egg building process)
make -C src/videocapture/videocapture/decklink

# Install local deps
./bin/python src/mozbase/setup_development.py
./bin/pip install -e src/templeton
./bin/pip install -e src/eideticker
./bin/pip install -e src/videocapture
