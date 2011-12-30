#!/bin/bash

INPUT_FILE=$1
OUTPUT_DIR=$2

# Create archive
FFMPEG="ffmpeg -vcodec rawvideo -f rawvideo -pix_fmt uyvy422 -r 60 -s hd1080 -i $INPUT_FILE --"
$FFMPEG $OUTPUT_DIR/%d.png

