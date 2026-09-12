#!/usr/bin/env python3
"""Execute a plan JSON against the real semantic map WITHOUT ROS/Gazebo.

Runs the exact same plan_runner logic the robot uses, but on the MockNavigator,
so you can check what a plan *would* do (waypoint order, contingency handling,
clarifications) instantly. Pass locations to pretend are blocked to exercise the
on_blocked branches.

    python3 dry_run.py --plan plan.json
    python3 dry_run.py --plan plan.json --blocked aisle_2_south,aisle_2_north
    echo '<plan json>' | python3 dry_run.py
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nl_nav2_executor.mock_navigator import MockNavigator     # noqa: E402
from nl_nav2_executor.plan_runner import run_plan             # noqa: E402
from nl_nav2_executor.semantic_map import SemanticMap         # noqa: E402

DEFAULT_MAP = Path(__file__).resolve().parents[4] / "map" / "warehouse_map.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", help="plan JSON file (else stdin)")
    ap.add_argument("--map", default=str(DEFAULT_MAP))
    ap.add_argument("--blocked", default="", help="comma-separated locations to block")
    args = ap.parse_args()

    smap = SemanticMap.from_file(args.map)
    plan = json.loads(Path(args.plan).read_text()) if args.plan else json.loads(sys.stdin.read())
    blocked = {b for b in args.blocked.split(",") if b}

    nav = MockNavigator(start=smap.point("charging_dock"), blocked=blocked)
    result = run_plan(plan, smap, nav)

    print("\n".join(nav.logs))
    print("-" * 60)
    print(result.summary())
    print(f"visited: {nav.visited}")
    return 0 if (result.understood and not result.aborted) else 1


if __name__ == "__main__":
    sys.exit(main())
