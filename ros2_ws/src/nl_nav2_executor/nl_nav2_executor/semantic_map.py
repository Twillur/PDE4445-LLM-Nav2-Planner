"""Pure-Python view of the semantic warehouse map.

No ROS imports: the same map that the LLM planner validates against is loaded
here so the executor resolves named locations to metric poses. Keeping this
ROS-free means the resolution and perimeter-routing logic is unit-testable
without a running simulation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import NamedTuple


class Point(NamedTuple):
    x: float
    y: float


# Perimeter waypoints, in clockwise order, used to route around a blocked aisle.
PERIMETER_RING = [
    "corner_sw", "west_wall_mid", "corner_nw", "north_wall_mid",
    "corner_ne", "east_wall_mid", "corner_se", "south_wall_mid",
]


class SemanticMap:
    def __init__(self, locations: dict[str, Point], meta: dict | None = None):
        self.locations = locations
        self.meta = meta or {}

    @classmethod
    def from_file(cls, path: str | Path) -> "SemanticMap":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        locs = {
            name: Point(float(v["x"]), float(v["y"]))
            for name, v in data["locations"].items()
        }
        meta = {k: v for k, v in data.items() if k != "locations"}
        return cls(locs, meta)

    def has(self, name: str) -> bool:
        return name in self.locations

    def point(self, name: str) -> Point:
        if name not in self.locations:
            raise KeyError(f"unknown location '{name}'")
        return self.locations[name]

    def nearest_perimeter(self, p: Point) -> str:
        """Name of the perimeter waypoint closest to point p."""
        return min(
            (n for n in PERIMETER_RING if n in self.locations),
            key=lambda n: _dist(self.point(n), p),
        )

    def perimeter_route(self, start: Point, target: str) -> list[str]:
        """Waypoint names to reach `target` via the perimeter ring.

        Enter the ring at the waypoint nearest the start, walk the ring the
        short way round to the waypoint nearest the target, then cut in to the
        target itself. Used for the on_blocked='reroute_perimeter' contingency.
        """
        ring = [n for n in PERIMETER_RING if n in self.locations]
        enter = self.nearest_perimeter(start)
        exit_ = self.nearest_perimeter(self.point(target))
        i, j = ring.index(enter), ring.index(exit_)
        cw = _ring_slice(ring, i, j, step=1)
        ccw = _ring_slice(ring, i, j, step=-1)
        path = cw if len(cw) <= len(ccw) else ccw
        return path + [target]


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _ring_slice(ring: list[str], i: int, j: int, step: int) -> list[str]:
    """Names from index i to j inclusive, walking the cyclic ring by `step`."""
    out = [ring[i]]
    k = i
    while k != j:
        k = (k + step) % len(ring)
        out.append(ring[k])
    return out
