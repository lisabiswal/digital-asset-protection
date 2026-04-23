#!/bin/bash

# Directory containing raw videos
RAW_DIR="backend/data/raw"
OUTPUT_DIR="backend/data/raw" # We'll put variants in the same dir for now as per task

mkdir -p "$OUTPUT_DIR"

for video in "$RAW_DIR"/*.mp4; do
    [ -e "$video" ] || continue
    filename=$(basename -- "$video")
    extension="${filename##*.}"
    filename="${filename%.*}"

    echo "Processing $video..."

    # 1. Trimmed (10s to 40s -> 30s duration)
    ffmpeg -y -i "$video" -ss 10 -t 30 -c copy "$OUTPUT_DIR/${filename}_trimmed.mp4"

    # 2. Speed-changed (0.75x speed -> faster)
    ffmpeg -y -i "$video" -filter:v "setpts=0.75*PTS" -an "$OUTPUT_DIR/${filename}_speed.mp4"

    # 3. Text overlay
    ffmpeg -y -i "$video" -vf "drawtext=text='COPYRIGHT TEST':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=(h-text_h)/2" -codec:a copy "$OUTPUT_DIR/${filename}_text.mp4"

    # 4. Cropped (Center crop 1/2 width and height)
    ffmpeg -y -i "$video" -vf "crop=iw/2:ih/2" -codec:a copy "$OUTPUT_DIR/${filename}_cropped.mp4"
done

echo "Variant generation complete."
