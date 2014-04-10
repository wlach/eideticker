#!/bin/bash

if [ -z $DASHBOARD_USERNAME ]; then
    DASHBOARD_USERNAME="eideticker"
fi

if [ -z $DASHBOARD_SERVER ]; then
    if [ $# != 1 ]; then
        echo "Usage $0 <destination server>"
        exit 1
    else
        DASHBOARD_SERVER=$1
    fi
fi

if [ -z $DASHBOARD_REMOTE_PATH ]; then
    DASHBOARD_REMOTE_PATH="~/www/"
fi

if [ -z $DASHBOARD_LOCAL_PATH ]; then
    DASHBOARD_LOCAL_PATH=$(dirname $0)/../src/dashboard/
fi

rsync -avz --copy-links -e ssh $DASHBOARD_LOCAL_PATH $DASHBOARD_USERNAME@$DASHBOARD_SERVER:$DASHBOARD_REMOTE_PATH
