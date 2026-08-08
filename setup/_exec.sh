#!/usr/bin/env bash
cd /mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner || exit 1
source setup/sim-env.sh >/dev/null 2>&1
echo "RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}"
echo "plan:"
cat results/last_plan.json
echo
echo "=== executing ==="
ros2 run nl_nav2_executor execute_plan \
    --plan results/last_plan.json \
    --localization ground_truth 2>&1
echo "=== exit code: $? ==="
