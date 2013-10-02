#!/bin/sh

set -e

SERVER_DIR=$(dirname $0)/../src/webapp/server/
cd $SERVER_DIR && ../../../bin/python server.py $1 &
PID=$!
echo "Server running with PID $PID"

trap "echo 'Killing server...'; kill -9 $PID" INT TERM EXIT
while true; do
    sleep 60
done
