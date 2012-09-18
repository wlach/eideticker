#!/bin/bash

if [ $# != 1 ]; then
    echo "Usage $0 <destination server>"
    exit 1
fi

EIDETICKER=$(dirname $0)/../

rsync -avz -e ssh $EIDETICKER/src/dashboard/ eideticker@$1:~/www/
