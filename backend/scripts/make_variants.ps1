# PowerShell version of make_variants.sh

$RAW_DIR = "backend/data/raw"
$OUTPUT_DIR = "backend/data/raw"

if (!(Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR
}

$videos = Get-ChildItem -Path $RAW_DIR -Filter *.mp4

$ffmpeg = "ffmpeg"
if (!(Get-Command $ffmpeg -ErrorAction SilentlyContinue)) {
    $ffmpeg = "C:\Users\light\miniconda3\envs\digital\Library\bin\ffmpeg.exe"
}

foreach ($video in $videos) {
    $videoPath = $video.FullName
    $filename = $video.BaseName
    
    Write-Host "Processing $videoPath..."

    # 1. Trimmed
    & $ffmpeg -y -i "$videoPath" -ss 10 -t 30 -c copy "$OUTPUT_DIR/${filename}_trimmed.mp4"

    # 2. Speed-changed
    & $ffmpeg -y -i "$videoPath" -filter:v "setpts=0.75*PTS" -an "$OUTPUT_DIR/${filename}_speed.mp4"

    # 3. Text overlay
    & $ffmpeg -y -i "$videoPath" -vf "drawtext=text='COPYRIGHT TEST':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=(h-text_h)/2" -codec:a copy "$OUTPUT_DIR/${filename}_text.mp4"

    # 4. Cropped
    & $ffmpeg -y -i "$videoPath" -vf "crop=iw/2:ih/2" -codec:a copy "$OUTPUT_DIR/${filename}_cropped.mp4"
}

Write-Host "Variant generation complete."
