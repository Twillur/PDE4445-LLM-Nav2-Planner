#!/usr/bin/env bash
# Build the executor, run regression tests, and check installed runtime resources.
# No simulation launches, model calls, historical regrading, or ROS node startup.
set -euo pipefail
NL_NAV2_VERIFY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NL_NAV2_VERIFY_OUTPUT="$NL_NAV2_VERIFY_ROOT/docs/validation/runtime-fixes-20260912"
mkdir -p "$NL_NAV2_VERIFY_OUTPUT"
set +u
source /opt/ros/humble/setup.bash
set -u
(
    cd "$NL_NAV2_VERIFY_ROOT/ros2_ws"
    colcon build --packages-select nl_nav2_executor --symlink-install --event-handlers console_direct+
) > "$NL_NAV2_VERIFY_OUTPUT/build.log" 2>&1
set +u
source "$NL_NAV2_VERIFY_ROOT/ros2_ws/install/local_setup.bash"
set -u
python3 -m pytest "$NL_NAV2_VERIFY_ROOT/ros2_ws/src/nl_nav2_executor/test" -q -p no:cacheprovider \
    | tee "$NL_NAV2_VERIFY_OUTPUT/tests-wsl.txt"
python3 -c 'from importlib.resources import files; from nl_nav2_executor.executor_node import main; from nl_nav2_executor.plan_validation import validate_plan; assert files("nl_nav2_executor").joinpath("execution_plan.schema.json").is_file(); print("Installed executor, ROS imports and runtime schema resource OK")' \
    | tee "$NL_NAV2_VERIFY_OUTPUT/installed-package.txt"
python3 "$NL_NAV2_VERIFY_ROOT/setup/check-runtime-fixes.py"
