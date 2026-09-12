"""Execute a validated waypoint plan against an abstract navigator.

This is the heart of the execution half and is deliberately ROS-free: it drives
any object implementing the `Navigator` protocol (see below), so the exact same
contingency logic is exercised by fast unit tests (MockNavigator) and by the
real Gazebo/Nav2 run (Nav2Navigator in executor_node.py).

A plan is the JSON object produced by the LLM planner. Before any movement,
the whole object is checked against the separate runtime execution contract.
Historical evaluation schemas and scores are not changed by this gate:

    { "understood": bool,
      "clarification_question": str | null,
      "plan": [ {"action": "navigate"|"wait", "target": str|null,
                 "duration_s": num|null, "on_blocked": str|null,
                 "reason": str|null}, ... ],
      "notes": str | null }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .plan_validation import validate_plan
from .semantic_map import Point, SemanticMap

WAIT_RETRY_SECONDS = 5.0  # default pause for on_blocked='wait_retry' when unspecified


class Navigator(Protocol):
    """What plan_runner needs from a navigator; Nav2 and the mock both satisfy it."""

    def navigate_to(self, name: str, point: Point) -> bool:
        """Drive to point (labelled `name`); True if reached, False if blocked."""
        ...

    def wait(self, seconds: float) -> None:
        ...

    def current_point(self) -> Point:
        ...

    def log(self, msg: str) -> None:
        ...


@dataclass
class StepResult:
    index: int
    action: str
    target: str | None
    outcome: str            # reached | waited | skipped | rerouted | fallback_reached | aborted | failed
    detail: str = ""
    fallback_target: str | None = None


@dataclass
class PlanResult:
    understood: bool
    clarification_question: str | None = None
    executed: bool = False
    aborted: bool = False
    steps: list[StepResult] = field(default_factory=list)

    @property
    def reached_count(self) -> int:
        return sum(s.outcome in ("reached", "rerouted") for s in self.steps)

    @property
    def fallback_count(self) -> int:
        return sum(s.outcome == "fallback_reached" for s in self.steps)

    @property
    def succeeded(self) -> bool:
        """Every executed step completed, directly or via its explicit fallback.

        A requested skip continues the plan but still leaves a destination
        unreached, so it does not count as full completion.
        """
        return (self.understood and self.executed and not self.aborted
                and bool(self.steps)
                and all(s.outcome in ("reached", "rerouted", "fallback_reached", "waited")
                        for s in self.steps))

    @property
    def exit_code(self) -> int:
        return 0 if self.succeeded else 1

    def summary(self) -> str:
        if not self.understood:
            return f"NOT EXECUTED — clarification needed: {self.clarification_question}"
        head = "ABORTED" if self.aborted else ("COMPLETED" if self.succeeded else "INCOMPLETE")
        navs = [s for s in self.steps if s.action == "navigate"]
        ok = sum(s.outcome in ("reached", "rerouted") for s in navs)
        summary = f"{head}: {ok}/{len(navs)} navigation goals reached"
        if self.fallback_count:
            summary += f"; {self.fallback_count} fallback destinations reached instead"
        return summary


def run_plan(plan: dict, smap: SemanticMap, nav: Navigator) -> PlanResult:
    """Validate, then execute `plan`, resolving names via `smap`.

    Invalid plans raise PlanValidationError before any step runs. A failed
    navigation goal triggers the explicit contingency; this does not establish
    that a physical obstacle was the cause of failure.
    """
    # Validate the whole plan before the first step, including unused fallbacks.
    validate_plan(plan, smap)
    result = PlanResult(
        understood=bool(plan.get("understood", False)),
        clarification_question=plan.get("clarification_question"),
    )

    if not result.understood:
        nav.log(f"Command not understood — asking: {result.clarification_question}")
        return result

    steps = plan.get("plan", [])
    result.executed = True

    for i, step in enumerate(steps):
        action = step.get("action")

        if action == "wait":
            secs = float(step.get("duration_s") or 0.0)
            nav.log(f"[{i}] wait {secs:.0f}s")
            nav.wait(secs)
            result.steps.append(StepResult(i, "wait", None, "waited", f"{secs:.0f}s"))
            continue

        target = step["target"]

        on_blocked = step.get("on_blocked")
        nav.log(f"[{i}] navigate -> {target}"
                + (f"  (on_blocked={on_blocked})" if on_blocked else ""))

        reached = nav.navigate_to(target, smap.point(target))
        if reached:
            result.steps.append(StepResult(i, "navigate", target, "reached"))
            continue

        # --- path was blocked: apply the step's contingency ------------------
        sr = _handle_blocked(i, target, on_blocked, step, smap, nav)
        result.steps.append(sr)
        if sr.outcome == "aborted":
            result.aborted = True
            nav.log(f"[{i}] on_blocked=abort -> stopping the remaining plan")
            break

    nav.log(result.summary())
    return result


def _handle_blocked(i, target, on_blocked, step, smap: SemanticMap, nav: Navigator) -> StepResult:
    if on_blocked == "abort":
        return StepResult(i, "navigate", target, "aborted", "path blocked, abort requested")

    if on_blocked == "skip":
        nav.log(f"[{i}] blocked -> skip, continuing")
        return StepResult(i, "navigate", target, "skipped", "path blocked")

    if on_blocked == "wait_retry":
        duration = step.get("duration_s")
        secs = WAIT_RETRY_SECONDS if duration is None else float(duration)
        nav.log(f"[{i}] blocked -> wait {secs:.0f}s and retry once")
        nav.wait(secs)
        if nav.navigate_to(target, smap.point(target)):
            return StepResult(i, "navigate", target, "reached", "reached on retry")
        return StepResult(i, "navigate", target, "failed", "still blocked after retry")

    if on_blocked == "goto_fallback":
        fallback = step["fallback_target"]
        nav.log(f"[{i}] blocked at {target} -> try fallback {fallback} once")
        if nav.navigate_to(fallback, smap.point(fallback)):
            return StepResult(i, "navigate", target, "fallback_reached",
                              f"primary blocked; reached fallback {fallback}", fallback)
        return StepResult(i, "navigate", target, "failed",
                          f"primary and fallback {fallback} both failed", fallback)

    if on_blocked == "reroute_perimeter":
        route = smap.perimeter_route(nav.current_point(), target)
        nav.log(f"[{i}] blocked -> reroute via perimeter: {route}")
        for name in route:
            if not nav.navigate_to(name, smap.point(name)):
                return StepResult(i, "navigate", target, "failed",
                                  f"perimeter reroute blocked at {name}")
        return StepResult(i, "navigate", target, "rerouted", f"via {route[:-1]}")

    # on_blocked is null: Nav2's own recovery already ran inside navigate_to.
    return StepResult(i, "navigate", target, "failed", "path blocked, no contingency")
