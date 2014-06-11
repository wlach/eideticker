#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

NEW_VERSION=$1

VERSION_FILE="src/eideticker/eideticker/gaia_compat_version.txt"
if [ -f $VERSION_FILE ]; then
  OLD_VERSION=$(head -n 1 $VERSION_FILE)
else
  OLD_VERSION=""
fi

if [ "$OLD_VERSION" == "$NEW_VERSION" ]; then
  echo "Target version is already installed. Nothing to do."
  exit
fi

PACKAGES="gaiatest b2gpopulate"

for NAME in $PACKAGES; do
  if [ "$OLD_VERSION" == "" ]; then
    OLD_PACKAGE=$NAME
  else
    OLD_PACKAGE="$NAME-v$OLD_VERSION"
  fi
  /usr/bin/yes | pip uninstall $OLD_PACKAGE

  if [ "$NEW_VERSION" == "" ]; then
    NEW_PACKAGE=$NAME
  else
    NEW_PACKAGE="$NAME-v$NEW_VERSION"
  fi
  pip install $NEW_PACKAGE
done

echo $1 > $VERSION_FILE
