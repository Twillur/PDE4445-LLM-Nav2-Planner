"""Summarise saved validation logs and odometry; never edit source recordings.

Run with the ROS2 Python environment sourced:
    python3 setup/summarize-simulation.py docs/validation/gazebo-TIMESTAMP
"""

import argparse
import json
import math
import re
import sqlite3
from pathlib import Path

from nav_msgs.msg import Odometry
from rclpy.serialization import deserialize_message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run = args.run.resolve()
    if not run.is_relative_to(root / "docs" / "validation"):
        parser.error("Only this project's docs/validation runs may be summarised.")
    locations = json.loads((root / "map/warehouse_map.json").read_text())["locations"]
    summaries = []
    for case in sorted(run.iterdir()):
        if not case.is_dir() or not (case / "plan.json").exists():
            continue
        plan = json.loads((case / "plan.json").read_text())
        targets = [s["target"] for s in plan["plan"] if s["action"] == "navigate"]
        log_path = case / "executor.log"
        log = log_path.read_text() if log_path.exists() else ""
        result_lines = re.findall(r"step (\d+): navigate (\S+) -> (\w+) ([^\n]*)", log)
        reached = [target for _, target, outcome, _ in result_lines if outcome in ("reached", "rerouted")]
        poses = []
        for db_path in sorted((case / "odometry").glob("*.db3")):
            with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as db:
                for (data,) in db.execute(
                    "SELECT messages.data FROM messages JOIN topics ON topics.id = messages.topic_id "
                    "WHERE topics.name = '/odom' ORDER BY messages.timestamp"
                ):
                    message = deserialize_message(data, Odometry)
                    p = message.pose.pose.position
                    t = message.header.stamp.sec + message.header.stamp.nanosec / 1e9
                    poses.append({"sim_time_s": t, "x": p.x, "y": p.y, "z": p.z})
        summary = {
            "case": case.name,
            "expected_navigation_targets": targets,
            "reported_reached_targets": reached,
            "all_goals_reported_reached": reached == targets,
            "goal_result_lines": result_lines,
            "odometry_samples": len(poses),
            "executor_started": log_path.exists(),
        }
        if poses:
            summary.update({
                "first_pose": poses[0],
                "last_pose": poses[-1],
                "z_range_m": [min(p["z"] for p in poses), max(p["z"] for p in poses)],
                "recorded_sim_duration_s": poses[-1]["sim_time_s"] - poses[0]["sim_time_s"],
                "raw_xy_path_length_m": sum(math.hypot(b["x"]-a["x"], b["y"]-a["y"]) for a, b in zip(poses, poses[1:])),
                "nearest_recorded_distance_to_each_target_m": {
                    target: min(math.hypot(p["x"]-locations[target]["x"], p["y"]-locations[target]["y"]) for p in poses)
                    for target in targets
                },
                "odometry_physically_plausible": all(
                    all(math.isfinite(p[k]) for k in ("x", "y", "z")) and abs(p["z"]) < 0.5
                    for p in poses
                ),
            })
            sampled = []
            for pose in poses:
                if not sampled or pose["sim_time_s"] - sampled[-1]["sim_time_s"] >= 0.5:
                    sampled.append(pose)
            if sampled[-1] != poses[-1]:
                sampled.append(poses[-1])
            (case / "trajectory-sampled.json").write_text(json.dumps(sampled, indent=2) + "\n")
        summary["verified_navigation_success"] = (
            summary["all_goals_reported_reached"] and summary.get("odometry_physically_plausible", False)
            and all(distance <= 0.25 for distance in summary.get("nearest_recorded_distance_to_each_target_m", {}).values())
        )
        summary["position_cross_check_tolerance_m"] = 0.25
        summaries.append(summary)
        print(case.name, "goals", f"{len(reached)}/{len(targets)}", "odometry", len(poses),
              "verified_success", summary["verified_navigation_success"])
    (run / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")


if __name__ == "__main__":
    main()
