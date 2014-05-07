#!/bin/bash

INPUT_FILE=$1
OUTPUT_DIR=$2
HDMI_MODE=$3

if [ $HDMI_MODE == "1080p" ]; then
    AVCONV_MODE="hd1080"
else
    AVCONV_MODE="hd720"
fi

# Create archive
AVCONV="avconv -vcodec rawvideo -f rawvideo -pix_fmt uyvy422 -r 60 -s $AVCONV_MODE -i $INPUT_FILE --"
$AVCONV $OUTPUT_DIR/%d.png
