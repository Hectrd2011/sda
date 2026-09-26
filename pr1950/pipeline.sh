#!/usr/bin/env bash
# renders the 1950 Nationalist uprisings video in 4K and makes the 4K parts, 1080p and phone copies
cd "$(dirname "$0")"
python3 render_pr.py video --w 3840 --h 2160 --jobs 4 --out build/pr1950_4k.mp4 > build/render.log 2>&1
grep -q "wrote" build/render.log || { echo "RENDER FAILED"; tail -5 build/render.log; exit 1; }
echo "render done $(date)"
../ww1/postprocess.sh build/pr1950_4k.mp4 PR_Nationalist_Uprisings_1950 > build/post.log 2>&1 && echo "postprocess done" \
    || { echo "POSTPROCESS FAILED"; tail -5 build/post.log; }
