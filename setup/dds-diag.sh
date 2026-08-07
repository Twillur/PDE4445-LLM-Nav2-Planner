#!/bin/bash
# DDS discovery diagnostic for WSL2 mirrored networking
source /opt/ros/humble/setup.bash
ros2 daemon stop >/dev/null 2>&1

echo "=== multicast test (default ifaces) ==="
(timeout 8 ros2 multicast receive 2>&1 | head -2 &)
sleep 2
timeout 5 ros2 multicast send >/dev/null 2>&1
sleep 7

echo "=== talker/listener, default ==="
(timeout 18 ros2 run demo_nodes_cpp talker >/dev/null 2>&1 &)
sleep 4
timeout 10 ros2 run demo_nodes_cpp listener 2>&1 | head -2
pkill -f demo_nodes_cpp 2>/dev/null

echo "=== talker/listener, ROS_LOCALHOST_ONLY=1 ==="
export ROS_LOCALHOST_ONLY=1
(timeout 18 ros2 run demo_nodes_cpp talker >/dev/null 2>&1 &)
sleep 4
timeout 10 ros2 run demo_nodes_cpp listener 2>&1 | head -2
pkill -f demo_nodes_cpp 2>/dev/null

echo "=== ifaces ==="
ip -brief addr
echo "=== done ==="
