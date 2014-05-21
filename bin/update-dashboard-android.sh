#!/bin/bash

set -e

# function borrowed from:
# http://stas-blogspot.blogspot.ca/2010/02/kill-all-child-processes-from-shell.html
kill_child_processes() {
    isTopmost=$1
    curPid=$2
    childPids=`ps -o pid --no-headers --ppid ${curPid}`
    for childPid in $childPids
    do
        kill_child_processes 0 $childPid
    done
    if [ $isTopmost -eq 0 ]; then
        kill -9 $curPid 2> /dev/null
    fi
}

cleanup() {
    kill_child_processes 1 $$
    rm -rf /tmp/eideticker/*
}

# Ctrl-C trap. Catches INT signal
trap "cleanup; exit 0" INT

EIDETICKER=$(dirname $0)/../

if [ -z $NUM_RUNS ]; then
    NUM_RUNS=5
fi

if [ -z $EXPIRY_THRESHOLD ]; then
    EXPIRY_THRESHOLD=3
fi

if [ -z $PRODUCT ]; then
    PRODUCT=nightly
fi

if [ -z $DATE ]; then
    DATE="latest"
fi

if [ $# -gt 0 ]; then
    TESTS=$@
elif [ -z "$TESTS" ]; then
    # Default set of tests
    TESTS="taskjs cnn startup-abouthome-fresh startup-abouthome-dirty nytimes-load nytimes-load-poststartup nightly nytimes-scroll nytimes-zoom reddit wikipedia imgur timecube canvas-box"
fi

export PATH=$PATH:$HOME/tools/android-sdk-linux/tools:$HOME/tools/android-sdk-linux/platform-tools:$HOME/bin:$HOME/.local/bin

cd $EIDETICKER
. bin/activate

# Expire old captures/videos
./bin/expire.py --max-age $EXPIRY_THRESHOLD

# Update app on the phone to the latest
./bin/update-phone.py $PRODUCT $DATE

# We want to allow failures when updating the dashboard, so we can be more
# verbose about errors before exiting
set +e

# Clean out /tmp/eideticker directory (in case there are any artifacts
# from unsuccessful runs kicking around)
rm -rf /tmp/eideticker/*

if [ $PRODUCT = nightly -o $PRODUCT = nightly-armv6 ]; then
   APK="downloads/$PRODUCT-$DATE.apk"
   ./bin/update-dashboard.py --apk $APK --num-runs $NUM_RUNS --product $PRODUCT $EXTRA_UPDATE_DASHBOARD_ARGS $TESTS
else
   ./bin/update-dashboard.py --baseline --app-version $VERSION --num-runs $NUM_RUNS --product $PRODUCT $EXTRA_UPDATE_DASHBOARD_ARGS $TESTS
fi

cleanup
exit 0
