"""Record bounded runtime checks of saved plans; never regrade model outputs."""

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ros2_ws/src/nl_nav2_executor"))

from nl_nav2_executor.mock_navigator import MockNavigator
from nl_nav2_executor.plan_runner import run_plan
from nl_nav2_executor.plan_validation import PlanValidationError
from nl_nav2_executor.semantic_map import SemanticMap

EVIDENCE = ROOT / "docs/validation/execution-check-20260911T172852Z"
OUTPUT = ROOT / "docs/validation/runtime-fixes-20260912/runtime-checks.json"


class RecordingNavigator(MockNavigator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attempted = []

    def navigate_to(self, name, point):
        self.attempted.append(name)
        return super().navigate_to(name, point)


def main():
    smap = SemanticMap.from_file(ROOT / "map/warehouse_map.json")
    cases = [
        ("v2-L1-01-trial0", set(), None, 0),
        ("v2-L2-01-trial0", set(), None, 0),
        ("v2-L3-01-trial0", set(), None, 0),
        ("v3-L4-12-trial0", set(), ["storage_zone_a"], 0),
        ("v3-L4-12-trial0", {"storage_zone_a"}, ["storage_zone_a", "storage_zone_b"], 0),
        ("v3-L4-12-trial0", {"storage_zone_a", "storage_zone_b"}, ["storage_zone_a", "storage_zone_b"], 1),
        ("v2-L4-12-trial0", set(), ["storage_zone_a", "storage_zone_b"], 0),
    ]
    records = []
    for basename, blocked, expected_attempts, code in cases:
        path = EVIDENCE / f"{basename}.json"
        raw = path.read_bytes()
        plan = json.loads(raw)
        expected_attempts = expected_attempts or [s["target"] for s in plan["plan"] if s["action"] == "navigate"]
        nav = RecordingNavigator(blocked=blocked)
        result = run_plan(plan, smap, nav)
        assert result.exit_code == code and nav.attempted == expected_attempts
        records.append({
            "source": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "blocked_by_mock": sorted(blocked),
            "attempted": nav.attempted,
            "visited": nav.visited,
            "result": asdict(result),
            "exit_code": result.exit_code,
            "summary": result.summary(),
        })

    invalid = json.loads((EVIDENCE / "v3-L4-12-trial0.json").read_text(encoding="utf-8"))
    invalid["plan"][0]["fallback_target"] = "invented_location"
    nav = RecordingNavigator()
    try:
        run_plan(invalid, smap, nav)
    except PlanValidationError as exc:
        assert nav.attempted == []
        records.append({"synthetic_mutation": "unknown fallback target", "error": str(exc),
                        "attempted": nav.attempted, "rejected_before_motion": True})
    else:
        raise AssertionError("Unknown fallback was accepted")

    OUTPUT.write_text(json.dumps({
        "scope": "Controlled software checks, not Gazebo, model reliability estimates, or semantic grades.",
        "historical_limit": "The v2 L4-12 plan still visits B unconditionally. Runtime validation cannot repair a semantically wrong plan.",
        "cases": records,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(records)} controlled runtime cases: {OUTPUT}")


if __name__ == "__main__":
    main()
