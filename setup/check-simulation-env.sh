#!/usr/bin/env bash
# Read-only preflight: no launches, daemon resets, builds, or process termination.
# --project-env additionally sources the normal environment (including its daemon stop).
set -e
NL_NAV2_CHECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf 'KERNEL\n'
uname -a
printf '\nROS2 HUMBLE\n'
if test -f /opt/ros/humble/setup.bash; then
    printf 'installed\n'
else
    printf 'MISSING /opt/ros/humble/setup.bash\n'
fi
printf '\nTOOLS\n'
command -v gzserver || true
command -v colcon || true
printf '\nCYCLONE CONFIG\n'
if test -f "$NL_NAV2_CHECK_DIR/cyclonedds-wsl.xml"; then
    printf 'present\n'
else
    printf 'MISSING setup/cyclonedds-wsl.xml\n'
fi
printf '\nBUILT WORKSPACE\n'
if test -f /mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner/ros2_ws/install/setup.bash; then
    printf 'present\n'
else
    printf 'MISSING ros2_ws/install/setup.bash\n'
fi
printf '\nEXISTING SIMULATION PROCESSES\n'
pgrep -a -f 'gzserver|nav2_container|component_container' || true
printf '\nREQUIRED ROS PACKAGES\n'
for package in nav2_bringup nav2_simple_commander turtlebot3_gazebo gazebo_ros rmw_cyclonedds_cpp; do
    if test -d "/opt/ros/humble/share/$package"; then
        printf '%s present\n' "$package"
    else
        printf '%s MISSING\n' "$package"
    fi
done
if [ "${1:-}" = '--project-env' ]; then
    source "$NL_NAV2_CHECK_DIR/sim-env.sh"
    test -f "${CYCLONEDDS_URI#file://}"
    test "$RMW_IMPLEMENTATION" = rmw_cyclonedds_cpp
    case ":$GAZEBO_MODEL_PATH:" in
        *:/usr/share/gazebo-11/models:*) ;;
        *) printf 'Missing standard Gazebo model path\n'; exit 1 ;;
    esac
    printf '\nPROJECT ENVIRONMENT VERIFIED\n'
    printf 'CYCLONEDDS_URI=%s\nGAZEBO_MODEL_PATH=%s\n' "$CYCLONEDDS_URI" "$GAZEBO_MODEL_PATH"
fi
printf '\nPYTHON IMPORTS\n'
source /opt/ros/humble/setup.bash
python3 -c 'import rclpy, nav2_simple_commander, gazebo_msgs; print("ROS Python imports OK")'
printf '\nGAZEBO STANDARD ASSETS\n'
for model_dir in /usr/share/gazebo-11/models /usr/share/gazebo-11 /opt/ros/humble/share/gazebo_ros /home/*/.gazebo/models; do
    if test -d "$model_dir"; then
        find "$model_dir" -maxdepth 3 -type f -name model.sdf
    fi
done
