"""Validation and scoring for LLM waypoint plans.

Three independent checks, mirroring the dissertation's metrics:
  1. schema_valid  - output conforms to the WaypointPlan JSON schema
  2. map_valid     - every navigate target is a real named location
  3. semantic      - the plan matches the dataset's expected answer (auto for
                     'sequences'/'must_visit', deferred to manual for 'rubric')
"""

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "waypoint_plan.schema.json").read_text(encoding="utf-8"))
MAP = json.loads((ROOT / "map" / "warehouse_map.json").read_text(encoding="utf-8"))
KNOWN_LOCATIONS = set(MAP["locations"].keys())


def check_schema(plan: dict) -> str | None:
    try:
        jsonschema.validate(plan, SCHEMA)
        return None
    except jsonschema.ValidationError as e:
        return e.message


def check_map(plan: dict) -> str | None:
    for i, step in enumerate(plan.get("plan", [])):
        if step.get("action") == "navigate":
            t = step.get("target")
            if t not in KNOWN_LOCATIONS:
                return f"step {i}: unknown location '{t}'"
        if step.get("action") == "navigate" and step.get("target") is None:
            return f"step {i}: navigate without target"
    return None


def nav_targets(plan: dict) -> list[str]:
    return [s["target"] for s in plan.get("plan", []) if s.get("action") == "navigate"]


def _is_ordered_subsequence(needles: list[str], haystack: list[str]) -> bool:
    it = iter(haystack)
    return all(n in it for n in needles)


def score_semantic(plan: dict, expected: dict) -> tuple[str, str]:
    """Returns (verdict, detail). Verdict: pass | fail | manual."""
    etype = expected.get("type")
    targets = nav_targets(plan)

    if etype == "rubric":
        # Clarification counts as an answer for rubric items; auto-fail only hallucinated locations (map_valid catches those).
        return "manual", "rubric-scored"

    if not plan.get("understood", False):
        ok = expected.get("clarification_ok", False)
        return ("pass" if ok else "fail"), "asked for clarification"

    if etype == "sequences":
        if targets in [list(s) for s in expected["sequences"]]:
            return "pass", f"matched {targets}"
        return "fail", f"got {targets}, wanted one of {expected['sequences']}"

    if etype == "must_visit":
        missing = [l for l in expected["locations"] if l not in targets]
        if missing:
            return "fail", f"missing {missing} (got {targets})"
        if expected.get("ordered") and not _is_ordered_subsequence(expected["locations"], targets):
            return "fail", f"order wrong: wanted {expected['locations']} within {targets}"
        avoided = expected.get("must_avoid", [])
        hit = [l for l in avoided if l in targets]
        if hit:
            return "fail", f"visited forbidden {hit}"
        if expected.get("wait_expected") and not any(s.get("action") == "wait" for s in plan.get("plan", [])):
            return "fail", "no wait step"
        return "pass", f"visited all of {expected['locations']}"

    return "manual", f"unknown expected type {etype}"


def check_on_blocked(plan: dict, expected: dict) -> tuple[str, str]:
    """Level-4 contingency check. Returns (verdict, detail); 'n/a' when nothing expected."""
    steps = plan.get("plan", [])
    if "on_blocked_all" in expected:
        want = expected["on_blocked_all"]
        navs = [s for s in steps if s.get("action") == "navigate"]
        ok = navs and all(s.get("on_blocked") == want for s in navs)
        return ("pass" if ok else "fail"), f"all steps should have on_blocked={want}"
    if "on_blocked_expect" in expected:
        for target, want in expected["on_blocked_expect"].items():
            if any(s.get("target") == target and s.get("on_blocked") == want for s in steps):
                return "pass", f"{target} has on_blocked={want}"
        return "fail", f"expected {expected['on_blocked_expect']}"
    return "n/a", ""
