#!/bin/bash

if [ -z $DASHBOARD_SERVER ]; then
    if [ $# != 1 ]; then
        echo "Usage $0 <destination server>"
        exit 1
    else
        DASHBOARD_SERVER=$1
    fi
fi

if [ -z $DASHBOARD_SERVER_DIR ]; then
    DASHBOARD_SERVER_DIR="~/www/"
fi

EIDETICKER=$(dirname $0)/../

rsync -avz --copy-links -e ssh $EIDETICKER/src/dashboard/ eideticker@$DASHBOARD_SERVER:$DASHBOARD_SERVER_DIR

