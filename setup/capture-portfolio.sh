#!/usr/bin/env bash
# Genuine Gazebo window capture on an isolated virtual display. No desktop capture.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export NL_NAV2_CAPTURE_MODE="${1:-overview}"
RUN="$ROOT/docs/validation/portfolio-capture-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN/frames"
printf 'CAPTURE_DIRECTORY %s\n' "$RUN"
export DISPLAY=:91
export ROS_DOMAIN_ID=45
export GAZEBO_MASTER_URI=http://127.0.0.1:11366
export GAZEBO_MODEL_DATABASE_URI=''
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://$ROOT/setup/cyclonedds-wsl.xml"
export TURTLEBOT3_MODEL=waffle
export LIBGL_ALWAYS_SOFTWARE=1
export ROS_LOG_DIR="$RUN/ros-logs"
source /opt/ros/humble/setup.bash
source "$ROOT/ros2_ws/install/local_setup.bash"
export GAZEBO_MODEL_PATH="/usr/share/gazebo-11/models${GAZEBO_MODEL_PATH:+:$GAZEBO_MODEL_PATH}"
PIDS=()
cleanup() {
    for pid in "${PIDS[@]}"; do kill -INT -- "-$pid" 2>/dev/null || true; done
    sleep 3
    for pid in "${PIDS[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
    sleep 2
    for pid in "${PIDS[@]}"; do
        kill -KILL -- "-$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT
test ! -S /tmp/.X11-unix/X91 || { printf 'Display 91 already in use; stopping.\n'; exit 2; }
setsid Xvfb :91 -screen 0 1440x960x24 -nolisten tcp > "$RUN/display.log" 2>&1 &
PIDS+=("$!")
export NL_NAV2_CAPTURE_RUN="$RUN" NL_NAV2_CAPTURE_ROOT="$ROOT"
python3 - <<'PY'
import hashlib, json, os
from pathlib import Path
root, run = Path(os.environ['NL_NAV2_CAPTURE_ROOT']), Path(os.environ['NL_NAV2_CAPTURE_RUN'])
pkg = root / 'ros2_ws/src/nl_nav2_executor'
world = (pkg / 'worlds/warehouse.world').read_text()
pose = '3 3 2 0 0.65 -2.356' if os.environ['NL_NAV2_CAPTURE_MODE'] == 'detail' else '26 -15 28 0 0.755 2.14'
world = world.replace('</world>', f"<gui><camera name='user_camera'><pose>{pose}</pose><view_controller>orbit</view_controller></camera></gui></world>")
(run / 'capture.world').write_text(world)
launch = (pkg / 'launch/warehouse_sim.launch.py').read_text()
needle = 'world = os.path.join(pkg, "worlds", "warehouse.world")'
assert needle in launch
launch = launch.replace(needle, 'world = ' + repr(str(run / 'capture.world')))
(run / 'capture.launch.py').write_text(launch)
sources = list((pkg / 'nl_nav2_executor').glob('*.py')) + [pkg / 'nl_nav2_executor/execution_plan.schema.json', pkg / 'worlds/warehouse.world']
(run / 'source-hashes.json').write_text(json.dumps({str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, indent=2))
PY
setsid timeout --signal=INT --kill-after=15s 900s ros2 launch "$RUN/capture.launch.py" gui:=true \
    > "$RUN/launch.log" 2>&1 &
PIDS+=("$!")
WIN=''
for attempt in $(seq 1 100); do
    if grep -qE 'process has died|Traceback|Unable to find uri' "$RUN/launch.log"; then
        tail -35 "$RUN/launch.log"; exit 2
    fi
    WIN=$(xdotool search --onlyvisible --name '^Gazebo$' 2>/dev/null | head -1 || true)
    if [ -n "$WIN" ] && grep -qE 'lifecycle_manager_navigation.*Managed nodes are active' "$RUN/launch.log" && \
        grep -qE 'lifecycle_manager_localization.*Managed nodes are active' "$RUN/launch.log"; then break; fi
    if [ $((attempt % 15)) -eq 0 ]; then printf 'Waiting for rendered warehouse (%ss)...\n' "$((attempt * 2))"; fi
    sleep 2
done
test -n "$WIN" || { printf 'No Gazebo window.\n'; exit 2; }
grep -qE 'lifecycle_manager_navigation.*Managed nodes are active' "$RUN/launch.log" || exit 2
xdotool windowsize "$WIN" 1440 960
sleep 3
import -window "$WIN" "$RUN/warehouse-start.png"
printf 'Captured warehouse overview.\n'
if [ "$NL_NAV2_CAPTURE_MODE" = detail ]; then
    date -u +%FT%TZ > "$RUN/captured-utc.txt"
    printf 'Static robot detail capture; no navigation executed.\n' > "$RUN/capture-scope.txt"
    exit 0
fi
PLAN="$ROOT/docs/validation/execution-check-20260911T172852Z/v2-L1-01-trial0.json"
cp "$PLAN" "$RUN/plan.json"
setsid timeout --signal=INT --kill-after=10s 600s ros2 run nl_nav2_executor execute_plan --plan "$PLAN" \
    --map "$ROOT/map/warehouse_map.json" > "$RUN/executor.log" 2>&1 &
EXEC_PID=$!
PIDS+=("$EXEC_PID")
i=0
while kill -0 "$EXEC_PID" 2>/dev/null; do
    printf -v FRAME '%05d' "$i"
    import -window "$WIN" -quality 85 "$RUN/frames/frame-$FRAME.jpg"
    i=$((i+1))
    if [ $((i % 40)) -eq 0 ]; then printf 'Captured %s frames; navigation running...\n' "$i"; fi
    sleep 0.5
done
set +e
wait "$EXEC_PID"
RC=$?
set -e
printf '%s\n' "$RC" > "$RUN/executor-exit-code.txt"
import -window "$WIN" "$RUN/warehouse-end.png"
printf '%s\n' "$i" > "$RUN/frame-count.txt"
date -u +%FT%TZ > "$RUN/captured-utc.txt"
tail -12 "$RUN/executor.log"
printf 'CAPTURE_COMPLETE %s frames; exit %s\n' "$i" "$RC"
exit "$RC"
