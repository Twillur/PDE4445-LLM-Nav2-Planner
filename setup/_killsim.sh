#!/usr/bin/env bash
# Kill sim processes by PID. Using `pkill -f <pattern>` here is unsafe: the
# calling shell's own command line can contain the pattern, so pkill kills its
# own parent (exit 15) and leaves the simulation running.
SELF=$$
for pat in execute_plan warehouse_sim component_container_isolated; do
    for pid in $(pgrep -f "$pat" 2>/dev/null); do
        [ "$pid" = "$SELF" ] && continue
        kill -TERM "$pid" 2>/dev/null
    done
done
pkill -x gzclient 2>/dev/null
pkill -x gzserver 2>/dev/null
sleep 3
for pat in execute_plan warehouse_sim component_container_isolated; do
    for pid in $(pgrep -f "$pat" 2>/dev/null); do
        [ "$pid" = "$SELF" ] && continue
        kill -KILL "$pid" 2>/dev/null
    done
done
pkill -9 -x gzclient 2>/dev/null; pkill -9 -x gzserver 2>/dev/null
sleep 2
echo "remaining: gzserver=$(pgrep -c -x gzserver || echo 0) gzclient=$(pgrep -c -x gzclient || echo 0) container=$(pgrep -fc component_container_isolated || echo 0)"
exit 0
