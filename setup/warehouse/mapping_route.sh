#!/bin/bash
# Autonomous SLAM mapping route for the PDE4445 warehouse.
# Sends NavigateToPose goals covering the perimeter and all three aisles.
# Nav2 handles obstacle avoidance; slam_toolbox builds the map as it drives.
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle ROS_DOMAIN_ID=30
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/william/.cyclonedds-wsl.xml

# x y label
ROUTE=(
  "1.0 10.0  west_wall_mid"
  "1.5 18.5  corner_nw"
  "10.0 18.5 north_wall_mid"
  "18.5 18.5 corner_ne"
  "18.5 10.0 east_wall_mid"
  "18.0 2.0  loading_dock"
  "10.0 1.5  south_wall_mid"
  "6.0 4.0   aisle_1_south"
  "6.0 16.0  aisle_1_north"
  "9.0 16.0  aisle_2_north"
  "9.0 4.0   aisle_2_south"
  "12.0 4.0  aisle_3_south"
  "12.0 16.0 aisle_3_north"
  "15.0 10.0 packing_station"
  "16.0 14.0 storage_zone_b"
  "4.0 14.0  storage_zone_a"
  "1.0 1.0   charging_dock"
)

ok=0; fail=0
for wp in "${ROUTE[@]}"; do
  read -r X Y LABEL <<< "$wp"
  echo "GOAL -> $LABEL ($X, $Y)"
  if timeout 180 ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
      "{pose: {header: {frame_id: map}, pose: {position: {x: $X, y: $Y, z: 0.0}, orientation: {w: 1.0}}}}" \
      2>&1 | grep -q "SUCCEEDED"; then
    echo "  OK  $LABEL"; ok=$((ok+1))
  else
    echo "  FAIL $LABEL"; fail=$((fail+1))
  fi
done
echo "ROUTE COMPLETE: $ok succeeded, $fail failed"
