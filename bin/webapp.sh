#!/bin/sh

set -e

PYTHON=$PWD/$(dirname $0)/python
SERVER_DIR=$(dirname $0)/../src/eideticker/eideticker/webapp/server/
cd $SERVER_DIR && $PYTHON server.py $1 &
PID=$!
echo "Server running with PID $PID"

trap "echo 'Killing server...'; kill -9 $PID" INT TERM EXIT
while true; do
    sleep 60
done
