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

WS_DEFAULT="/mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner/ros2_ws"
WS="${NL_NAV2_WS:-$WS_DEFAULT}"

source /opt/ros/humble/setup.bash

if [ -f "$WS/install/setup.bash" ]; then
    source "$WS/install/setup.bash"
else
    echo "WARN: $WS/install/setup.bash not found - workspace not built?" >&2
fi

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/william/.cyclonedds-wsl.xml
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID=30
export DISPLAY=:0

# A stale daemon started under a different RMW makes `ros2 topic list` come back
# empty while the sim is plainly running. Cheap to avoid.
ros2 daemon stop >/dev/null 2>&1 || true
