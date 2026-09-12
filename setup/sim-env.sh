#!/usr/bin/env bash
# Source this inside WSL to get a working ROS2 + Nav2 + Gazebo environment for
# this project. Non-interactive shells launched via wsl.exe do NOT read
# ~/.bashrc, so every variable the stack needs is set explicitly here.
#
#   source setup/sim-env.sh
#
# Fast DDS completes discovery under WSL2 mirrored networking and then silently
# delivers nothing, so Cyclone DDS pinned to loopback is mandatory, not a
# preference.

# Do NOT run `set -u` in a script that sources this: ROS2's setup.bash
# references AMENT_TRACE_SETUP_FILES unguarded and the shell dies silently.
NL_NAV2_SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DEFAULT="$(cd "$NL_NAV2_SETUP_DIR/.." && pwd)/ros2_ws"
WS="${NL_NAV2_WS:-$WS_DEFAULT}"

source /opt/ros/humble/setup.bash

if [ -f "$WS/install/setup.bash" ]; then
    source "$WS/install/setup.bash"
else
    echo "WARN: $WS/install/setup.bash not found - workspace not built?" >&2
fi

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://$NL_NAV2_SETUP_DIR/cyclonedds-wsl.xml"
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID=30
export DISPLAY=:0
# An existing model path can hide Gazebo's installed floor and sun assets.
# Missing ground_plane leaves the robot falling while Nav2 still starts.
export GAZEBO_MODEL_PATH="/usr/share/gazebo-11/models${GAZEBO_MODEL_PATH:+:$GAZEBO_MODEL_PATH}"

# A stale daemon started under a different RMW makes `ros2 topic list` come back
# empty while the sim is plainly running. Cheap to avoid.
ros2 daemon stop >/dev/null 2>&1 || true
