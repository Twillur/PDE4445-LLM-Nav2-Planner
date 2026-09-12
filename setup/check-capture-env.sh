#!/usr/bin/env bash
set -e
printf 'Capture tools\n'
for tool in gzclient gzserver xwininfo import xdotool Xvfb ffmpeg; do
    command -v "$tool" || true
done
printf '\nDisplay\n'
printf 'DISPLAY=%s\n' "${DISPLAY:-unset}"
DISPLAY=:0 xwininfo -root 2>/dev/null | head -15 || true
printf '\nExisting simulation processes\n'
pgrep -a -f 'gzserver|gzclient|nav2_container|component_container' || true
printf '\nGazebo camera command\n'
gz camera --help 2>&1 | head -45 || true
