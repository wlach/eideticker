#!/bin/bash

INPUT_FILE=$1
OUTPUT_DIR=$2
HDMI_MODE=$3

if [ $HDMI_MODE == "1080p" ]; then
    FFMPEG_MODE="hd1080"
else
    FFMPEG_MODE="hd720"
fi

# Create archive
FFMPEG="ffmpeg -vcodec rawvideo -f rawvideo -pix_fmt uyvy422 -r 60 -s $FFMPEG_MODE -i $INPUT_FILE --"
$FFMPEG $OUTPUT_DIR/%d.png

