#!/bin/sh

set -e

EIDETICKER=$(dirname $0)/../
TESTS="clock taskjs nightly cnn nytimes-scroll nytimes-zoom"

if [ $# -gt 0 ]; then
    TESTS=$@
fi

export PATH=$PATH:$HOME/tools/android-sdk-linux/tools:$HOME/tools/android-sdk-linux/platform-tools:$HOME/bin:$HOME/.local/bin

cd $EIDETICKER
. bin/activate

# Reboot phone and wait for watcher to come up (this ensures phone is in a good
# state)
# FIXME: temporarily disabled because we're using adb-over-tcp now and
# I don't know how to make things come back with that enabled by default
#./bin/reboot-device.py

for TEST in $TESTS; do
  echo "Running $TEST"
  ./bin/update-dashboard.py -p xul $TEST src/dashboard
  ./bin/update-dashboard.py -p stock $TEST src/dashboard
  ./bin/update-dashboard.py -p nightly --num-runs 5 $TEST src/dashboard
done
