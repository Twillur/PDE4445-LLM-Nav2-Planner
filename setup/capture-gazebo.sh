#!/usr/bin/env bash
# Capture the Gazebo window as a frame sequence, from inside WSL.
#
#   bash setup/capture-gazebo.sh [SECONDS] [FPS]
#
# Why not ffmpeg/gdigrab on the Windows side: that captures the Windows desktop,
# so it records whatever happens to be on screen rather than the simulation.
# This grabs the X window by id, so it captures Gazebo and nothing else no
# matter what is in front of it.
#
# Frames land in results/demo-footage/frames/ and are stitched by
# setup/frames-to-video.ps1. Capturing at 2 fps and playing back at 15 gives a
# ~7x timelapse, which suits a 3-minute summary video better than real time -
# the five-waypoint patrol takes over four minutes to drive.

set -u
SECS="${1:-120}"
FPS="${2:-2}"
ROOT=/mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner
OUT="$ROOT/results/demo-footage/frames"

WIN=$(DISPLAY=:0 xwininfo -root -tree 2>/dev/null \
      | grep -iE '"Gazebo": \("gazebo"' | head -1 | awk '{print $1}')

if [ -z "$WIN" ]; then
    echo "ERROR: no Gazebo window found on DISPLAY=:0. Is the sim running?" >&2
    exit 1
fi
echo "capturing window $WIN for ${SECS}s at ${FPS}fps"

rm -rf "$OUT"; mkdir -p "$OUT"
INTERVAL=$(awk "BEGIN{print 1/$FPS}")
TOTAL=$(awk "BEGIN{print int($SECS*$FPS)}")

i=0
while [ "$i" -lt "$TOTAL" ]; do
    printf -v NAME "%05d" "$i"
    DISPLAY=:0 import -window "$WIN" "$OUT/f_$NAME.png" 2>/dev/null || {
        echo "capture failed at frame $i (window closed?)" >&2; break; }
    i=$((i+1))
    [ $((i % 20)) -eq 0 ] && echo "  $i/$TOTAL frames"
    sleep "$INTERVAL"
done

echo "wrote $i frames to $OUT"
