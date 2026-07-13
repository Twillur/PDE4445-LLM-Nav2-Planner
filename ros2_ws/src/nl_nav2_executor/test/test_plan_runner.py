"""Unit tests for the plan-execution logic (no ROS / no Gazebo required).

Run with:  python -m pytest ros2_ws/src/nl_nav2_executor/test -q
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nl_nav2_executor.mock_navigator import MockNavigator          # noqa: E402
from nl_nav2_executor.plan_runner import run_plan                  # noqa: E402
from nl_nav2_executor.semantic_map import Point, SemanticMap       # noqa: E402

# Minimal map with the perimeter ring + a couple of aisle/target points.
MAP = SemanticMap({
    "charging_dock": Point(1, 1),
    "loading_dock": Point(18, 2),
    "aisle_2_south": Point(9, 4),
    "aisle_2_north": Point(9, 16),
    "corner_sw": Point(1, 1), "west_wall_mid": Point(1, 10),
    "corner_nw": Point(1, 19), "north_wall_mid": Point(10, 19),
    "corner_ne": Point(19, 19), "east_wall_mid": Point(19, 10),
    "corner_se": Point(19, 1), "south_wall_mid": Point(10, 1),
})


def nav_plan(*targets, **kw):
    return {"understood": True, "clarification_question": None,
            "plan": [{"action": "navigate", "target": t, **kw} for t in targets],
            "notes": None}


def test_simple_navigation_reaches_all():
    r = run_plan(nav_plan("aisle_2_south", "aisle_2_north"), MAP, MockNavigator())
    assert r.executed and not r.aborted
    assert r.reached_count == 2


def test_not_understood_does_not_execute():
    plan = {"understood": False, "clarification_question": "Which aisle?",
            "plan": [], "notes": None}
    r = run_plan(plan, MAP, MockNavigator())
    assert not r.executed
    assert "Which aisle?" in r.summary()


def test_abort_stops_remaining_steps():
    nav = MockNavigator(blocked={"aisle_2_south"})
    plan = nav_plan("aisle_2_south", "loading_dock")
    plan["plan"][0]["on_blocked"] = "abort"
    r = run_plan(plan, MAP, nav)
    assert r.aborted
    assert "loading_dock" not in nav.visited        # never attempted after abort


def test_skip_continues_to_next_step():
    nav = MockNavigator(blocked={"aisle_2_south"})
    plan = nav_plan("aisle_2_south", "loading_dock")
    plan["plan"][0]["on_blocked"] = "skip"
    r = run_plan(plan, MAP, nav)
    assert not r.aborted
    assert "loading_dock" in nav.visited


def test_wait_retry_succeeds_on_second_attempt():
    class FlakyNav(MockNavigator):
        def navigate_to(self, name, point):
            if name == "loading_dock" and name not in self.visited and not self.waits:
                return False            # blocked until we have waited once
            return super().navigate_to(name, point)

    nav = FlakyNav()
    plan = nav_plan("loading_dock")
    plan["plan"][0]["on_blocked"] = "wait_retry"
    plan["plan"][0]["duration_s"] = 3
    r = run_plan(plan, MAP, nav)
    assert nav.waits == [3]
    assert "loading_dock" in nav.visited


def test_reroute_perimeter_visits_ring_then_target():
    class RerouteNav(MockNavigator):
        """Direct approach to the aisle is blocked; once we've detoured onto the
        perimeter ring, the same target becomes reachable from the other side."""

        def navigate_to(self, name, point):
            detoured = any(v.startswith("corner_") or v.endswith("_mid")
                           for v in self.visited)
            if name == "aisle_2_north" and not detoured:
                self.logs.append("  (blocked) direct approach to aisle_2_north")
                return False
            return super().navigate_to(name, point)

    nav = RerouteNav(start=Point(9, 4))
    plan = nav_plan("aisle_2_north")
    plan["plan"][0]["on_blocked"] = "reroute_perimeter"
    r = run_plan(plan, MAP, nav)
    assert r.steps[0].outcome == "rerouted"
    assert any(n.startswith("corner_") or n.endswith("_mid") for n in nav.visited)
    assert "aisle_2_north" in nav.visited


def test_wait_action():
    plan = {"understood": True, "clarification_question": None,
            "plan": [{"action": "wait", "duration_s": 10}], "notes": None}
    nav = MockNavigator()
    run_plan(plan, MAP, nav)
    assert nav.waits == [10]
