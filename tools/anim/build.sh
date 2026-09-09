#!/usr/bin/env bash
# Render the Manim overview animation and install it as the site's pipeline video.
#
#   tools/anim/build.sh              # full 1080p30 render + web encode + poster
#   tools/anim/build.sh --preview    # fast 720p pass, leaves the site untouched
#
# First run only:
#   python3 -m venv tools/anim/.venv && tools/anim/.venv/bin/pip install manim
# (the fonts in tools/anim/fonts/ and the stills in tools/anim/frames/ are
#  committed, so nothing else needs fetching)
set -euo pipefail

PREVIEW=0
[[ "${1:-}" == "--preview" ]] && PREVIEW=1

cd "$(dirname "$0")/../.."          # repo root
VENV="tools/anim/.venv"
OUT="assets/video/pipeline.mp4"
POSTER="assets/img/pipeline-poster.jpg"
WORK="tools/anim/.render"

[[ -x "$VENV/bin/manim" ]] || { echo "manim venv missing - see header" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }

if (( PREVIEW )); then
  "$VENV/bin/manim" -qm tools/anim/overview.py Overview --media_dir "$WORK"
  echo "preview at $WORK/videos/overview/720p30/Overview.mp4"
  exit 0
fi

"$VENV/bin/manim" --resolution 1920,1080 --fps 30 \
  tools/anim/overview.py Overview --media_dir "$WORK"

SRC="$WORK/videos/overview/1080p30/Overview.mp4"
[[ -f "$SRC" ]] || { echo "render missing: $SRC" >&2; exit 1; }

# Re-encode for the web. Manim's own output is already h264 but not tuned for
# streaming; crf 26 keeps the flat vector art clean at a fraction of the size.
mkdir -p "$(dirname "$OUT")" "$(dirname "$POSTER")"
ffmpeg -y -loglevel error -i "$SRC" -an \
  -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT"

# Poster: the end of act 1, once all four pipeline stages are on screen.
ffmpeg -y -loglevel error -ss 6 -i "$OUT" -frames:v 1 -q:v 4 "$POSTER"

echo
echo "done:"
ls -lh "$OUT" "$POSTER" | awk '{print "  "$9"  "$5}'
ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration -of csv=p=0 "$OUT" | sed 's/^/  /'
