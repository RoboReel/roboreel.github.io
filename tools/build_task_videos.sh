#!/usr/bin/env bash
# Transcode the per-task human/robot clips into the web-sized mp4s that the
# Tasks section plays.
#
#   in:   assets/task_src/<slug>-human.mp4   (full-size originals, git-ignored)
#         assets/task_src/<slug>-robot.mp4
#   out:  assets/video/tasks/<slug>-human.mp4  (small, committed, what ships)
#         assets/video/tasks/<slug>-robot.mp4
#
#   tools/build_task_videos.sh                     # rebuild all ten tasks
#   tools/build_task_videos.sh push_cube open_lid  # rebuild just these
#   tools/build_task_videos.sh --list              # slugs + which sources exist
#
# TO REPLACE A ROBOT VIDEO:
#   tools/build_task_videos.sh --robot push_cube ~/new_push_cube.mp4
# which copies it over assets/task_src/push_cube-robot.mp4 and rebuilds that
# task. Or drop the files in yourself, named <slug>-robot.mp4, and just run
# tools/build_task_videos.sh with no arguments.
#
# index.html never changes: the page derives both filenames from the slug on
# the .task-card. Slugs are listed in SLUGS below.
#
# The originals were copied from the LfO benchmark SSD ("X10 Pro") on
# 2026-09-08, demo 0000 of each task:
#   human  raw_demonstration_videos/pose_defined/<task>/0000/front.mp4
#   robot  raw_training_trajectories/without_distraction/<task>/0000/base_camera.mp4
# where <task> is the slug, except toy_drawer_close, whose robot clip comes
# from the differently-named toys_in_drawer/.
set -euo pipefail

SLUGS=(push_cube close_drawer empty_basket press_toaster open_lid
       pick_cube bowl_in_plate toys_in_basket toy_drawer_close stack_cups)

SRC_DIR="assets/task_src"
OUT_DIR="assets/video/tasks"
WIDTH=640          # long edge of the encoded clip; the page never shows it larger
FPS=24
CRF=30
JOBS=4
LIST_ONLY=0

cd "$(dirname "$0")/.."          # repo root

is_slug() {
  local s
  for s in "${SLUGS[@]}"; do [[ "$s" == "$1" ]] && return 0; done
  return 1
}

# --robot/--human are handled first: they stage a new source file, then fall
# through to a normal rebuild of that one task.
REPLACED=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --robot|--human)
      kind="${1#--}"
      [[ $# -ge 3 ]] || { echo "usage: $1 <slug> <file>" >&2; exit 2; }
      slug="$2"; file="$3"
      is_slug "$slug" || { echo "unknown task slug: $slug" >&2; exit 2; }
      [[ -f "$file" ]] || { echo "no such file: $file" >&2; exit 2; }
      mkdir -p "$SRC_DIR"
      cp -- "$file" "$SRC_DIR/$slug-$kind.mp4"
      echo "staged $SRC_DIR/$slug-$kind.mp4  <- $file"
      REPLACED+=( "$slug" )
      shift 3 ;;
    --src-dir) SRC_DIR="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --width)   WIDTH="$2"; shift 2 ;;
    --fps)     FPS="$2"; shift 2 ;;
    --crf)     CRF="$2"; shift 2 ;;
    --jobs)    JOBS="$2"; shift 2 ;;
    --list)    LIST_ONLY=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) break ;;
  esac
done

command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }

# Explicit slugs win; otherwise rebuild whatever --robot/--human staged;
# otherwise everything.
TARGETS=("$@")
if (( ${#TARGETS[@]} == 0 )) && (( ${#REPLACED[@]} > 0 )); then
  TARGETS=("${REPLACED[@]}")
fi
if (( ${#TARGETS[@]} == 0 )); then
  TARGETS=("${SLUGS[@]}")
else
  for t in "${TARGETS[@]}"; do
    is_slug "$t" || { echo "unknown task slug: $t" >&2; exit 2; }
  done
fi

if (( LIST_ONLY )); then
  printf '%-18s %-8s %-8s\n' slug human robot
  for slug in "${SLUGS[@]}"; do
    h=missing; r=missing
    [[ -f "$SRC_DIR/$slug-human.mp4" ]] && h=ok
    [[ -f "$SRC_DIR/$slug-robot.mp4" ]] && r=ok
    printf '%-18s %-8s %-8s\n' "$slug" "$h" "$r"
  done
  exit 0
fi

# H.264 needs even dimensions, hence the -2 on the scale filter's free axis.
# Clips keep their native aspect ratio; the page crops them to 16:9 in CSS, so
# a square sim render and a 16:9 human video can sit side by side.
VF="scale='min(${WIDTH},iw)':-2,fps=${FPS},setsar=1"

mkdir -p "$OUT_DIR"

# Parallel arrays rather than a command file piped through xargs, so paths with
# spaces survive.
SRCS=() OUTS=()
missing=0
for slug in "${TARGETS[@]}"; do
  for kind in human robot; do
    src="$SRC_DIR/$slug-$kind.mp4"
    if [[ ! -f "$src" ]]; then
      echo "  MISSING  $src" >&2
      missing=$(( missing + 1 ))
      continue
    fi
    SRCS+=( "$src" )
    OUTS+=( "$OUT_DIR/$slug-$kind.mp4" )
  done
done

(( ${#SRCS[@]} > 0 )) || { echo "nothing to encode" >&2; exit 1; }

echo "encoding ${#SRCS[@]} clips from ${#TARGETS[@]} task(s)..."
for (( i=0; i<${#SRCS[@]}; i++ )); do
  while (( $(jobs -rp | wc -l) >= JOBS )); do wait -n || true; done
  ffmpeg -y -loglevel error -i "${SRCS[$i]}" -an -vf "$VF" \
    -c:v libx264 -crf "$CRF" -preset slow -pix_fmt yuv420p -movflags +faststart \
    "${OUTS[$i]}" &
done
wait

echo
echo "done:"
for out in "${OUTS[@]}"; do
  if [[ -s "$out" ]]; then
    printf '  %-38s %6s  %s\n' "$out" \
      "$(du -h "$out" | cut -f1)" \
      "$(ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0 "$out")"
  else
    echo "  FAILED  $out" >&2
    missing=$(( missing + 1 ))
  fi
done

(( missing == 0 )) || { echo; echo "${missing} clip(s) missing or failed - see above" >&2; exit 1; }
