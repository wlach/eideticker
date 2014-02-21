#!/bin/sh

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

BASEDIR=$PWD

if [ ! $VENV ]; then
    VENV="."
    virtualenv $VENV
fi

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

# Build up videocapture utility (FIXME: should be part of the egg building process)
make -C src/videocapture/videocapture/decklink

# Set a long timeout for pip, especially for travis testing
export PIP_DEFAULT_TIMEOUT=120

# Upgrade pip to latest (so we can use --allow-external on all platforms)
$VENV/bin/pip install --upgrade pip

# Install local deps
$VENV/bin/pip install --allow-external which --allow-unverified which -e src/eideticker
$VENV/bin/pip install -e src/videocapture
