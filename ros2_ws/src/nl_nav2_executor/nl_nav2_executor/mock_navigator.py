"""In-memory navigator for testing plan_runner without ROS or Gazebo.

Teleports instantly to each goal and reports success, except for locations
named in `blocked`, which report a blocked path (as Nav2 would when it exhausts
its recovery behaviours). This lets the contingency logic be exercised
deterministically and fast.
"""

from __future__ import annotations

from .semantic_map import Point


class MockNavigator:
    def __init__(self, start: Point = Point(1.0, 1.0), blocked: set[str] | None = None):
        self._pos = start
        self.blocked = blocked or set()
        self.visited: list[str] = []
        self.waits: list[float] = []
        self.logs: list[str] = []

    def navigate_to(self, name: str, point: Point) -> bool:
        if name in self.blocked:
            self.logs.append(f"  (blocked) could not reach {name}")
            return False
        self._pos = point
        self.visited.append(name)
        return True

    def wait(self, seconds: float) -> None:
        self.waits.append(seconds)

    def current_point(self) -> Point:
        return self._pos

    def log(self, msg: str) -> None:
        self.logs.append(msg)
