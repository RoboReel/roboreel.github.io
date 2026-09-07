#!/usr/bin/env bash
# Rebuild the hero mosaic video from the clips in assets/mosaic_src/.
#
#   tools/build_mosaic.sh                 # 12x7 grid, 10s loop
#   tools/build_mosaic.sh --cols 14 --rows 8
#   tools/build_mosaic.sh --duration 14 --crf 28
#
# Clips whose filename contains "_sim_" get a centre zoom, because the ManiSkill
# renders have a black void above the horizon that otherwise shows as a band.
set -euo pipefail

COLS=12
ROWS=7
TILE_W=160
TILE_H=154
DURATION=10
FPS=24
CRF=30
JOBS=8
SRC_DIR="assets/mosaic_src"
OUT="assets/video/hero-mosaic.mp4"
POSTER="assets/img/hero-mosaic-poster.jpg"
OUT_SET=0
POSTER_SET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cols) COLS="$2"; shift 2 ;;
    --rows) ROWS="$2"; shift 2 ;;
    --tile-w) TILE_W="$2"; shift 2 ;;
    --tile-h) TILE_H="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --fps) FPS="$2"; shift 2 ;;
    --crf) CRF="$2"; shift 2 ;;
    --jobs) JOBS="$2"; shift 2 ;;
    --src) SRC_DIR="$2"; shift 2 ;;
    --out) OUT="$2"; OUT_SET=1; shift 2 ;;
    --poster) POSTER="$2"; POSTER_SET=1; shift 2 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

# A custom --out must not clobber the site's poster; derive one alongside it.
if (( OUT_SET && ! POSTER_SET )); then
  POSTER="${OUT%.*}-poster.jpg"
fi

cd "$(dirname "$0")/.."          # repo root

command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }
[[ -d "$SRC_DIR" ]] || { echo "no source dir: $SRC_DIR" >&2; exit 1; }

# H.264 needs even dimensions.
(( TILE_W % 2 == 0 && TILE_H % 2 == 0 )) || { echo "tile dims must be even" >&2; exit 1; }

mapfile -t CLIPS < <(find "$SRC_DIR" -maxdepth 1 -name '*.mp4' | sort)
(( ${#CLIPS[@]} > 0 )) || { echo "no .mp4 files in $SRC_DIR" >&2; exit 1; }

NEED=$(( COLS * ROWS ))
echo "grid ${COLS}x${ROWS} = ${NEED} tiles of ${TILE_W}x${TILE_H} -> $(( COLS*TILE_W ))x$(( ROWS*TILE_H ))"
echo "source clips: ${#CLIPS[@]}"
if (( ${#CLIPS[@]} < NEED )); then
  echo "  fewer clips than tiles - cycling with varied time offsets"
elif (( ${#CLIPS[@]} > NEED )); then
  echo "  more clips than tiles - using the first ${NEED}"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ---- stage 1: normalise every tile (parallel) ----
: > "$TMP/cmds"
for (( i=0; i<NEED; i++ )); do
  src="${CLIPS[$(( i % ${#CLIPS[@]} ))]}"
  # spread the loop phase so neighbouring tiles are not in lockstep
  off=$(awk -v i="$i" 'BEGIN{ printf "%.2f", (i*0.37) % 3.5 }')
  pre=""
  [[ "$(basename "$src")" == *_sim_* ]] && pre="crop=iw:ih*0.72:0:ih*0.17,"
  printf 'ffmpeg -y -loglevel error -stream_loop -1 -i %q -ss %s -t %s -an -vf %q -c:v libx264 -crf 20 -preset veryfast %q\n' \
    "$src" "$off" "$DURATION" \
    "${pre}scale=${TILE_W}:${TILE_H}:force_original_aspect_ratio=increase,crop=${TILE_W}:${TILE_H},fps=${FPS},setsar=1" \
    "$TMP/t$(printf '%03d' "$i").mp4" >> "$TMP/cmds"
done
echo "building ${NEED} tiles..."
xargs -P "$JOBS" -I{} bash -c "{}" < "$TMP/cmds"

# ---- stage 2: rows ----
echo "stacking ${ROWS} rows..."
for (( r=0; r<ROWS; r++ )); do
  args=()
  for (( c=0; c<COLS; c++ )); do
    args+=( -i "$TMP/t$(printf '%03d' $(( r*COLS + c ))).mp4" )
  done
  ffmpeg -y -loglevel error "${args[@]}" -filter_complex "hstack=inputs=${COLS}" \
    -c:v libx264 -crf 20 -preset veryfast "$TMP/row$r.mp4"
done

# ---- stage 3: final grid ----
echo "encoding final mosaic..."
args=()
for (( r=0; r<ROWS; r++ )); do args+=( -i "$TMP/row$r.mp4" ); done
mkdir -p "$(dirname "$OUT")" "$(dirname "$POSTER")"
ffmpeg -y -loglevel error "${args[@]}" -filter_complex "vstack=inputs=${ROWS}" \
  -c:v libx264 -crf "$CRF" -preset slow -pix_fmt yuv420p -movflags +faststart -an "$OUT"

# poster still, used for prefers-reduced-motion and as the <video> poster
ffmpeg -y -loglevel error -ss $(( DURATION / 2 )) -i "$OUT" -frames:v 1 -q:v 6 "$POSTER"

echo
echo "done:"
ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0 "$OUT" | sed 's/^/  /'
ls -lh "$OUT" "$POSTER" | awk '{print "  "$9"  "$5}'
