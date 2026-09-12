#!/usr/bin/env bash
# Run archived v2 plans in fresh headless simulations. No model calls or regrading.
# Usage: bash setup/validate-simulation.sh ABSOLUTE_PLAN_DIRECTORY [PLAN_BASENAME ...]
# Cleanup targets only process groups created by this script.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLAN_DIR="${1:?Supply the directory of copied archived plan JSON files}"
shift
if [ "$#" -eq 0 ]; then
    set -- v2-L1-01-trial0 v2-L2-01-trial0 v2-L3-01-trial0
fi
RUN="$ROOT/docs/validation/gazebo-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$RUN"
printf 'ARTIFACT_DIRECTORY %s\n' "$RUN"
export ROS_LOG_DIR="$RUN/ros-logs"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://$ROOT/setup/cyclonedds-wsl.xml"
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID=44
export GAZEBO_MASTER_URI=http://127.0.0.1:11365
export GAZEBO_MODEL_DATABASE_URI=''
source /opt/ros/humble/setup.bash
if ! test -d /opt/ros/humble/share/rmw_cyclonedds_cpp; then
    printf 'Missing Cyclone DDS; no simulation started.\n'
    exit 2
fi
printf 'Building existing executor package...\n'
(
    cd "$ROOT/ros2_ws"
    colcon build --packages-select nl_nav2_executor --symlink-install --event-handlers console_direct+
) > "$RUN/build.log" 2>&1 || { tail -40 "$RUN/build.log"; exit 2; }
source "$ROOT/ros2_ws/install/local_setup.bash"
export GAZEBO_MODEL_PATH="/usr/share/gazebo-11/models${GAZEBO_MODEL_PATH:+:$GAZEBO_MODEL_PATH}"
printf 'Build complete.\n'
sha256sum "$ROOT/ros2_ws/src/nl_nav2_executor/nl_nav2_executor/plan_runner.py" \
    "$ROOT/ros2_ws/src/nl_nav2_executor/nl_nav2_executor/executor_node.py" \
    "$ROOT/ros2_ws/src/nl_nav2_executor/maps/warehouse.pgm" \
    "$ROOT/ros2_ws/src/nl_nav2_executor/worlds/warehouse.world" \
    "$ROOT/ros2_ws/src/nl_nav2_executor/params/nav2_params.yaml" > "$RUN/source-hashes.txt"
printf 'ROS_DOMAIN_ID=%s\nRMW=%s\nGAZEBO_MASTER_URI=%s\n' \
    "$ROS_DOMAIN_ID" "$RMW_IMPLEMENTATION" "$GAZEBO_MASTER_URI" > "$RUN/environment.txt"
LAUNCH_PID=''
BAG_PID=''
cleanup() {
    local pid
    for pid in "$BAG_PID" "$LAUNCH_PID"; do
        if [ -n "$pid" ] && kill -0 -- "-$pid" 2>/dev/null; then
            kill -INT -- "-$pid" 2>/dev/null || true
        fi
    done
    sleep 5
    for pid in "$BAG_PID" "$LAUNCH_PID"; do
        if [ -n "$pid" ] && kill -0 -- "-$pid" 2>/dev/null; then
            kill -TERM -- "-$pid" 2>/dev/null || true
        fi
    done
    sleep 3
    for pid in "$BAG_PID" "$LAUNCH_PID"; do
        if [ -n "$pid" ] && kill -0 -- "-$pid" 2>/dev/null; then
            kill -KILL -- "-$pid" 2>/dev/null || true
        fi
        if [ -n "$pid" ]; then wait "$pid" 2>/dev/null || true; fi
    done
    BAG_PID=''
    LAUNCH_PID=''
}
trap cleanup EXIT
for case_name in "$@"; do
    PLAN="$PLAN_DIR/$case_name.json"
    test -f "$PLAN" || { printf 'Missing plan: %s\n' "$PLAN"; exit 2; }
    CASE_DIR="$RUN/$case_name"
    mkdir "$CASE_DIR"
    cp "$PLAN" "$CASE_DIR/plan.json"
    sha256sum "$PLAN" > "$CASE_DIR/plan-hash.txt"
    printf '\nStarting %s with a fresh Gazebo world...\n' "$case_name"
    date -u +%FT%TZ > "$CASE_DIR/start-utc.txt"
    setsid timeout --signal=INT --kill-after=20s 1500s \
        ros2 launch nl_nav2_executor warehouse_sim.launch.py gui:=false \
        > "$CASE_DIR/launch.log" 2>&1 &
    LAUNCH_PID=$!
    printf '%s\n' "$LAUNCH_PID" > "$CASE_DIR/launch-process-group.txt"
    ready=false
    for attempt in $(seq 1 120); do
        if grep -qE 'process has died|Segmentation fault|core dumped|Traceback|Unable to find uri' "$CASE_DIR/launch.log"; then
            printf 'Launch failed; stopping this validation session.\n'
            tail -35 "$CASE_DIR/launch.log"
            printf 'launch_failed\n' > "$CASE_DIR/status.txt"
            exit 2
        fi
        if grep -qE 'lifecycle_manager_localization.*Managed nodes are active' "$CASE_DIR/launch.log" && \
           grep -qE 'lifecycle_manager_navigation.*Managed nodes are active' "$CASE_DIR/launch.log"; then
            ready=true
            break
        fi
        if [ $((attempt % 15)) -eq 0 ]; then
            printf 'Waiting for map server and Nav2 (%ss)...\n' "$((attempt * 2))"
        fi
        sleep 2
    done
    if [ "$ready" != true ]; then
        printf 'Readiness timeout; no plan was executed.\n'
        tail -35 "$CASE_DIR/launch.log"
        printf 'readiness_timeout\n' > "$CASE_DIR/status.txt"
        exit 2
    fi
    printf 'Map server and navigation active. Recording odometry.\n'
    setsid ros2 bag record /odom -o "$CASE_DIR/odometry" > "$CASE_DIR/record.log" 2>&1 &
    BAG_PID=$!
    printf '%s\n' "$BAG_PID" > "$CASE_DIR/record-process-group.txt"
    sleep 2
    printf 'Executing archived plan, with a 900-second limit...\n'
    set +e
    timeout --signal=INT --kill-after=15s 900s ros2 run nl_nav2_executor execute_plan \
        --plan "$CASE_DIR/plan.json" --map "$ROOT/map/warehouse_map.json" \
        --localization ground_truth > "$CASE_DIR/executor.log" 2>&1
    executor_rc=$?
    set -e
    printf '%s\n' "$executor_rc" > "$CASE_DIR/executor-exit-code.txt"
    date -u +%FT%TZ > "$CASE_DIR/end-utc.txt"
    tail -16 "$CASE_DIR/executor.log"
    # Exit zero alone is not sufficient: the existing executor can return zero
    # after an unreached goal. Preserve its complete log for goal-level checking.
    printf 'execution_finished_exit_%s\n' "$executor_rc" > "$CASE_DIR/status.txt"
    cleanup
    if grep -qE 'Segmentation fault|core dumped' "$CASE_DIR/launch.log" "$CASE_DIR/executor.log"; then
        printf 'Crash detected; no further simulations will be launched.\n'
        exit 2
    fi
    if [ "$executor_rc" -ne 0 ]; then
        printf 'Nonzero execution result; stopping for diagnosis.\n'
        exit "$executor_rc"
    fi
    expected_goals=$(python3 -c 'import json,sys; print(sum(s["action"] == "navigate" for s in json.load(open(sys.argv[1]))["plan"]))' "$PLAN")
    if ! grep -q "COMPLETED: $expected_goals/$expected_goals navigation goals reached" "$CASE_DIR/executor.log"; then
        printf 'goal_failure_despite_exit_zero\n' > "$CASE_DIR/status.txt"
        printf 'A navigation goal failed despite exit zero; stopping for diagnosis.\n'
        exit 2
    fi
    printf 'all_goals_reached\n' > "$CASE_DIR/status.txt"
done
printf '\nFinished. Review goal outcomes and odometry in %s\n' "$RUN"
