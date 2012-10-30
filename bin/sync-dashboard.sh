#!/bin/bash

if [ -z $DASHBOARD_SERVER ]; then
    if [ $# != 1 ]; then
        echo "Usage $0 <destination server>"
        exit 1
    else
        $DASHBOARD_SERVER=$1
    fi
fi

EIDETICKER=$(dirname $0)/../

rsync -avz -e ssh $EIDETICKER/src/dashboard/ eideticker@$DASHBOARD_SERVER:~/www/

