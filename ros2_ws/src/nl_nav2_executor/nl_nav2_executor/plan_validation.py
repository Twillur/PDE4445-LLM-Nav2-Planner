"""Shared execution gate, deliberately separate from archived evaluation scoring."""

from __future__ import annotations

import json
import math
from importlib.resources import files

from jsonschema import Draft7Validator

from .semantic_map import PERIMETER_RING, SemanticMap

_SCHEMA = json.loads(
    files("nl_nav2_executor").joinpath("execution_plan.schema.json").read_text(encoding="utf-8")
)
_VALIDATOR = Draft7Validator(_SCHEMA)


class PlanValidationError(ValueError):
    """The entire plan must be rejected before any navigation or waiting."""


def validate_plan(plan: object, smap: SemanticMap) -> None:
    """Check structure, cross-field rules and every possible destination.

    This gate does not decide whether a plan correctly answers the English
    command. In particular, it cannot diagnose an unconditional alternative
    described as conditional only in a comment.
    """
    error = next(_VALIDATOR.iter_errors(plan), None)
    if error is not None:
        path = ".".join(str(part) for part in error.absolute_path) or "plan"
        raise PlanValidationError(f"{path}: {error.message}")

    if not plan["understood"]:
        if not plan["clarification_question"].strip():
            raise PlanValidationError("clarification_question must contain a question")
        return

    for i, step in enumerate(plan["plan"]):
        duration = step.get("duration_s")
        if isinstance(duration, float) and not math.isfinite(duration):
            raise PlanValidationError(f"step {i}: duration_s must be finite")
        if duration is not None:
            try:
                float(duration)
            except OverflowError as exc:
                raise PlanValidationError(f"step {i}: duration_s is too large") from exc

        if step["action"] != "navigate":
            continue
        for field in ("target", "fallback_target"):
            name = step.get(field)
            if name is None:
                continue
            if not smap.has(name):
                raise PlanValidationError(f"step {i}: unknown {field} '{name}'")
            if not all(math.isfinite(v) for v in smap.point(name)):
                raise PlanValidationError(f"step {i}: non-finite map coordinates for '{name}'")

        if step.get("on_blocked") == "goto_fallback" and step["fallback_target"] == step["target"]:
            raise PlanValidationError(f"step {i}: fallback_target must differ from target; use wait_retry for a retry")
        if step.get("on_blocked") == "reroute_perimeter":
            ring = [name for name in PERIMETER_RING if smap.has(name)]
            if not ring or any(not all(math.isfinite(v) for v in smap.point(name)) for name in ring):
                raise PlanValidationError(f"step {i}: perimeter rerouting requires finite perimeter waypoints")
