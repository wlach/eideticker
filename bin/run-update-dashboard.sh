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

# Update timeout is per sequence of test runs. Default is 10 minutes per test
if [ -z $UPDATE_TIMEOUT ]; then
    UPDATE_TIMEOUT=$((600*NUM_RUNS))
fi

if [ -z $EXPIRY_THRESHOLD ]; then
    EXPIRY_THRESHOLD=3
fi

if [ $# -gt 0 ]; then
    TESTS=$@
else
    if [ -z $TESTS ]; then
        # Default set of tests
        TESTS="clock taskjs nightly cnn nytimes-scroll nytimes-zoom reddit wikipedia imgur"
    fi
fi

export PATH=$PATH:$HOME/tools/android-sdk-linux/tools:$HOME/tools/android-sdk-linux/platform-tools:$HOME/bin:$HOME/.local/bin

cd $EIDETICKER
. bin/activate

# Expire old captures/videos
./bin/expire.py --max-age $EXPIRY_THRESHOLD

# Update apps on the phone to the latest
./bin/update-phone.py

# We want to allow failures when updating the dashboard, so we can be more
# verbose about errors before exiting
set +e

FAILURES=0
for TEST in $TESTS; do
  # Clean out /tmp/eideticker directory (in case there are any artifacts
  # from unsuccessful runs kicking around)
  rm -rf /tmp/eideticker/*
  echo "Running $TEST"
  timeout $UPDATE_TIMEOUT ./bin/update-dashboard.py --product nightly --num-runs $NUM_RUNS $EXTRA_UPDATE_DASHBOARD_ARGS $TEST src/dashboard
  RET=$?
  if [ $RET == 124 ]; then
      echo "ERROR: Timed out when updating dashboard (TEST: $TEST)"
      cleanup
      exit 1
  elif [ ! $RET == 0 ]; then
      echo "ERROR: Failure updating dashboard (TEST: $TEST)"
      cleanup
      exit 1
  fi
done

cleanup
exit 0
