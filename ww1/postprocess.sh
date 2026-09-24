#!/usr/bin/env bash
# Turns a 4K master into: playable 4K parts under GitHub's 100 MB limit, a 1080p version,
# and a small 720p copy for phones.
# Usage: postprocess.sh <4k master.mp4> <output name prefix, e.g. WW1_Europe>
set -euo pipefail
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
SRC=$1
NAME=$2
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT4K="$ROOT/4K"
mkdir -p "$OUT4K"

# 4K parts: split at keyframes so every part plays on its own
size=$(stat -c %s "$SRC")
dur=$( ("$FF" -i "$SRC" 2>&1 || true) | sed -n 's/.*Duration: \([0-9:.]*\).*/\1/p' | awk -F: '{print $1*3600+$2*60+$3}')
parts=$(( (size + 89999999) / 90000000 ))
seg=$(awk -v d="$dur" -v n="$parts" 'BEGIN{printf "%.2f", d/n + 1}')
rm -f "$OUT4K/${NAME}_4K_part"*.mp4
"$FF" -loglevel error -y -i "$SRC" -c copy -map 0 -f segment -segment_time "$seg" -reset_timestamps 1 \
    "$OUT4K/${NAME}_4K_part%d.mp4"
for f in "$OUT4K/${NAME}_4K_part"*.mp4; do  # parts numbered from 1
    n=$(basename "$f" .mp4 | sed 's/.*part//'); mv "$f" "$OUT4K/${NAME}_4K_part$((n + 1))_tmp.mp4"; done
for f in "$OUT4K/${NAME}_4K_part"*_tmp.mp4; do mv "$f" "${f%_tmp.mp4}.mp4"; done

# 1080p from the 4K master (sharper than rendering at 1080p directly)
crf=21
while :; do
    "$FF" -loglevel error -y -i "$SRC" -vf scale=1920:1080:flags=lanczos -c:v libx264 -preset slow -crf $crf \
        -tune animation -c:a copy -movflags +faststart "$ROOT/${NAME}_1080p.mp4"
    [ "$(stat -c %s "$ROOT/${NAME}_1080p.mp4")" -lt 95000000 ] && break
    crf=$((crf + 2))
done

# small copy for sending to a phone (< 30 MB)
crf=28
while :; do
    "$FF" -loglevel error -y -i "$SRC" -vf scale=1280:720:flags=lanczos -c:v libx264 -preset slow -crf $crf \
        -tune animation -c:a aac -b:a 96k -movflags +faststart "$ROOT/ww1/${NAME}_720p_preview.mp4"
    [ "$(stat -c %s "$ROOT/ww1/${NAME}_720p_preview.mp4")" -lt 30000000 ] && break
    crf=$((crf + 2))
done
ls -la "$OUT4K" "$ROOT/${NAME}_1080p.mp4" "$ROOT/ww1/${NAME}_720p_preview.mp4"
