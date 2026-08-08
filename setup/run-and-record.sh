#!/usr/bin/env bash
# End-to-end demo: launch the sim, wait for Nav2, capture the Gazebo window
# while the robot drives a plan, then tear everything down.
#
#   bash setup/run-and-record.sh [PLAN_JSON]
#
# Runs entirely inside WSL so nothing depends on cross-shell quoting, and the
# capture grabs the Gazebo X window by id rather than the Windows desktop.
#
# Why a fresh launch every time: execute_plan calls lifecycleShutdown() when it
# finishes, which deactivates Nav2. A second run against the same sim hangs
# forever at "Waiting for Nav2 to become active". One sim launch per run.

# NO `set -u` here: /opt/ros/humble/setup.bash line 8 references
# AMENT_TRACE_SETUP_FILES unguarded, so `set -u` aborts the script during
# sourcing - before any output - which looks like a silent crash.
ROOT=/mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner
PLAN="${1:-$ROOT/results/last_plan.json}"
FRAMES="$ROOT/results/demo-footage/frames"
LAUNCH_LOG=/tmp/sim_launch.log

cd "$ROOT" || exit 1
source setup/sim-env.sh >/dev/null 2>&1
echo "RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}"


# Kill sim processes by PID. `pkill -f <pattern>` is unsafe here: this script's
# own command line can contain the pattern, so pkill kills its own shell
# (exit 15) and leaves the simulation running.
kill_sim() {
    local sig="${1:--TERM}" pat pid
    for pat in execute_plan warehouse_sim component_container_isolated; do
        for pid in $(pgrep -f "$pat" 2>/dev/null); do
            [ "$pid" = "$$" ] && continue
            kill "$sig" "$pid" 2>/dev/null
        done
    done
    pkill "$sig" -x gzclient 2>/dev/null
    pkill "$sig" -x gzserver 2>/dev/null
    return 0
}

cleanup() {
    echo; echo "=== tearing down ==="
    [ -n "${CAP_PID:-}" ] && kill "$CAP_PID" 2>/dev/null
    kill_sim -TERM; sleep 3; kill_sim -KILL; sleep 1
    echo "gzserver left: $(pgrep -c -x gzserver 2>/dev/null || echo 0)"
}
trap cleanup EXIT

echo "=== killing any previous sim ==="
kill_sim -TERM; sleep 3; kill_sim -KILL; sleep 2

echo "=== launching sim ==="
nohup ros2 launch nl_nav2_executor warehouse_sim.launch.py > "$LAUNCH_LOG" 2>&1 &
for i in $(seq 1 120); do
    grep -q "Managed nodes are active" "$LAUNCH_LOG" 2>/dev/null && { echo "Nav2 active after ~$((i*3))s"; break; }
    grep -qiE "traceback|process has died" "$LAUNCH_LOG" 2>/dev/null && { echo "LAUNCH FAILED"; tail -15 "$LAUNCH_LOG"; exit 1; }
    sleep 3
done
grep -q "Managed nodes are active" "$LAUNCH_LOG" || { echo "TIMEOUT waiting for Nav2"; tail -15 "$LAUNCH_LOG"; exit 1; }

# Nav2 reports "Managed nodes are active" before gzclient has mapped its X
# window, so poll rather than checking once.
WIN=""
for i in $(seq 1 60); do
    WIN=$(DISPLAY=:0 xwininfo -root -tree 2>/dev/null | grep -iE '"Gazebo": \("gazebo"' | head -1 | awk '{print $1}')
    [ -n "$WIN" ] && { echo "Gazebo window $WIN found after ~$((i*3))s"; break; }
    sleep 3
done
[ -z "$WIN" ] && { echo "no Gazebo window after 180s"; exit 1; }

echo "=== starting capture (2 fps) ==="
rm -rf "$FRAMES"; mkdir -p "$FRAMES"
(
    i=0
    while :; do
        printf -v N "%05d" "$i"
        DISPLAY=:0 import -window "$WIN" "$FRAMES/f_$N.png" 2>/dev/null || break
        i=$((i+1)); sleep 0.5
    done
) & CAP_PID=$!

echo "=== executing plan ==="
ros2 run nl_nav2_executor execute_plan --plan "$PLAN" --localization ground_truth 2>&1 | tail -20
RC=$?

sleep 2
kill "$CAP_PID" 2>/dev/null; CAP_PID=""
echo "frames captured: $(ls "$FRAMES" 2>/dev/null | wc -l)"
exit $RC
