"""ROS2 node: execute an LLM waypoint plan on Nav2 in the Gazebo warehouse.

Wraps nav2_simple_commander's BasicNavigator in the Navigator protocol that
plan_runner expects, so the identical contingency logic that the unit tests
exercise now drives a real TurtleBot3.

Usage (inside a sourced ROS2 + running Nav2 stack):
    ros2 run nl_nav2_executor execute_plan --plan /path/to/plan.json \
        --map /path/to/warehouse_map.json
Or pipe a plan on stdin:
    cat plan.json | ros2 run nl_nav2_executor execute_plan --map .../warehouse_map.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.parameter import Parameter

from .plan_runner import run_plan
from .semantic_map import Point, SemanticMap

DEFAULT_MAP = "/mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner/map/warehouse_map.json"


def _yaw_to_quat(yaw: float):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


class Nav2Navigator:
    """Adapts BasicNavigator to the plan_runner.Navigator protocol."""

    def __init__(self, navigator: BasicNavigator, start: Point):
        self.nav = navigator
        self._pos = start

    def navigate_to(self, name: str, point: Point) -> bool:
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.nav.get_clock().now().to_msg()
        goal.pose.position.x = point.x
        goal.pose.position.y = point.y
        yaw = math.atan2(point.y - self._pos.y, point.x - self._pos.x)
        qx, qy, qz, qw = _yaw_to_quat(yaw)
        goal.pose.orientation.z = qz
        goal.pose.orientation.w = qw

        self.nav.goToPose(goal)
        while not self.nav.isTaskComplete():
            # Feedback loop; a stuck robot is handled by Nav2 recovery + goal timeout.
            time.sleep(0.2)

        if self.nav.getResult() == TaskResult.SUCCEEDED:
            self._pos = point
            return True
        return False

    def wait(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def current_point(self) -> Point:
        return self._pos

    def log(self, msg: str) -> None:
        self.nav.get_logger().info(msg)


def _load_plan(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", help="Path to a plan JSON file (else read stdin).")
    parser.add_argument("--map", default=DEFAULT_MAP, help="Path to warehouse_map.json.")
    parser.add_argument("--start", default="charging_dock",
                        help="Named location the robot starts at (sets initial pose).")
    parser.add_argument("--localization", default="ground_truth",
                        choices=["ground_truth", "amcl"],
                        help="Match the sim's localization mode; controls the Nav2 readiness wait.")
    args, ros_args = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    rclpy.init(args=ros_args)
    smap = SemanticMap.from_file(args.map)
    plan = _load_plan(args.plan)
    start = smap.point(args.start) if smap.has(args.start) else Point(0.0, 0.0)

    navigator = BasicNavigator()
    # The whole sim runs on /clock; the navigator node must too, or stamps mismatch.
    navigator.set_parameters([Parameter("use_sim_time", Parameter.Type.BOOL, True)])

    if args.localization == "amcl":
        # Tell AMCL where we are, then wait for it to localise.
        init = PoseStamped()
        init.header.frame_id = "map"
        init.header.stamp = navigator.get_clock().now().to_msg()
        init.pose.position.x = start.x
        init.pose.position.y = start.y
        init.pose.orientation.w = 1.0
        navigator.setInitialPose(init)
        navigator.get_logger().info("Waiting for Nav2 (amcl) to become active...")
        navigator.waitUntilNav2Active()
    else:
        # ground_truth: map->odom is a static identity tf; there is no amcl to
        # wait on, so key readiness off map_server instead of /amcl_pose.
        navigator.get_logger().info("Waiting for Nav2 (ground_truth) to become active...")
        navigator.waitUntilNav2Active(localizer="map_server")

    result = run_plan(plan, smap, Nav2Navigator(navigator, start))

    navigator.get_logger().info("=" * 60)
    navigator.get_logger().info(result.summary())
    for s in result.steps:
        navigator.get_logger().info(
            f"  step {s.index}: {s.action} {s.target or ''} -> {s.outcome} {s.detail}")
    navigator.get_logger().info("=" * 60)

    navigator.lifecycleShutdown()
    rclpy.shutdown()
    # Non-zero exit if the plan was executed but a goal was ultimately not reached.
    return 0 if (result.understood and not result.aborted) else 1


if __name__ == "__main__":
    sys.exit(main())
