#!/usr/bin/env python3
"""Generate the Nav2 occupancy map (PGM+YAML) and the matching Gazebo world.

Both are derived from one geometry description below, so the static map the
planner/Nav2 reason over and the physical world Gazebo simulates cannot drift
apart. Coordinates are in metres in the same frame as map/warehouse_map.json
(origin at the SW corner, +x east, +y north, 20 x 20 m floor).

    python3 gen_warehouse_assets.py         # writes ../maps and ../worlds

The shelves are four long north-south blocks; the gaps between them are the
three traversable aisles centred on x = 6, 9, 12 (matching the semantic map).
"""

import struct
from pathlib import Path

# --- world geometry (metres) --------------------------------------------------
W = H = 20.0                     # floor is 20 x 20 m
WALL_T = 0.20                    # wall / shelf half-drawn thickness in the grid
RES = 0.05                       # map resolution m/px  -> 400 x 400 px
import os as _os
_SHELVES_ENABLED = _os.environ.get("WAREHOUSE_SHELVES", "1") == "1"
SHELVES = [                      # (x_min, x_max, y_min, y_max)
    # Thin shelf rows centred between the aisles (x = 6, 9, 12), leaving ~2.5 m
    # traversable corridors so Nav2 threads them comfortably.
    (c - 0.25, c + 0.25, 4.0, 13.0) for c in (4.5, 7.5, 10.5, 13.5)
] if _SHELVES_ENABLED else []

HERE = Path(__file__).resolve().parent
MAPS = HERE.parent / "maps"
WORLDS = HERE.parent / "worlds"


# --- occupancy grid -----------------------------------------------------------
def build_grid():
    n = int(W / RES)                       # 400
    FREE, OCC = 254, 0
    grid = bytearray([FREE]) * (n * n)     # start all-free

    def px(x, y):
        # world (x,y) -> pixel col/row; image row 0 is top (max y)
        c = int(x / RES)
        r = int((H - y) / RES)
        return c, r

    def fill(x0, x1, y0, y1):
        c0, r1 = px(x0, y0)
        c1, r0 = px(x1, y1)
        for r in range(max(0, r0), min(n, r1 + 1)):
            for c in range(max(0, c0), min(n, c1 + 1)):
                grid[r * n + c] = OCC

    # perimeter walls
    fill(0, W, 0, WALL_T)
    fill(0, W, H - WALL_T, H)
    fill(0, WALL_T, 0, H)
    fill(W - WALL_T, W, 0, H)
    # shelves
    for (xa, xb, ya, yb) in SHELVES:
        fill(xa, xb, ya, yb)
    return grid, n


def write_pgm(path, grid, n):
    with open(path, "wb") as f:
        f.write(b"P5\n%d %d\n255\n" % (n, n))
        f.write(bytes(grid))


def write_map_yaml(path, pgm_name):
    path.write_text(
        f"image: {pgm_name}\n"
        f"resolution: {RES}\n"
        "origin: [0.0, 0.0, 0.0]\n"
        "negate: 0\n"
        "occupied_thresh: 0.65\n"
        "free_thresh: 0.25\n",
        encoding="utf-8",
    )


# --- Gazebo world -------------------------------------------------------------
def box(name, x, y, sx, sy, sz=1.0):
    return f"""
    <model name='{name}'>
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {sz/2:.3f} 0 0 0</pose>
      <link name='link'>
        <collision name='c'><geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry></collision>
        <visual name='v'><geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material><ambient>0.4 0.4 0.45 1</ambient><diffuse>0.5 0.5 0.55 1</diffuse></material>
        </visual>
      </link>
    </model>"""


def write_world(path):
    t = WALL_T
    parts = [
        box("wall_s", W / 2, t / 2, W, t),
        box("wall_n", W / 2, H - t / 2, W, t),
        box("wall_w", t / 2, H / 2, t, H),
        box("wall_e", W - t / 2, H / 2, t, H),
    ]
    for i, (xa, xb, ya, yb) in enumerate(SHELVES):
        parts.append(box(f"shelf_{i+1}", (xa + xb) / 2, (ya + yb) / 2,
                         xb - xa, yb - ya, sz=1.2))
    models = "".join(parts)
    path.write_text(f"""<?xml version='1.0'?>
<sdf version='1.6'>
  <world name='warehouse'>
    <include><uri>model://sun</uri></include>
    <include><uri>model://ground_plane</uri></include>
    <scene><ambient>0.5 0.5 0.5 1</ambient><background>0.7 0.7 0.7 1</background></scene>
    <!-- Lighter physics (4x fewer steps) so the sim keeps up with Nav2 on a
         CPU-capped host and the /clock advances smoothly. -->
    <physics type='ode'><real_time_update_rate>250</real_time_update_rate><max_step_size>0.004</max_step_size></physics>
{models}
  </world>
</sdf>
""", encoding="utf-8")


def main():
    MAPS.mkdir(exist_ok=True)
    WORLDS.mkdir(exist_ok=True)
    grid, n = build_grid()
    write_pgm(MAPS / "warehouse.pgm", grid, n)
    write_map_yaml(MAPS / "warehouse.yaml", "warehouse.pgm")
    write_world(WORLDS / "warehouse.world")
    occ = sum(1 for b in grid if b == 0)
    print(f"wrote maps/warehouse.pgm ({n}x{n}px, {occ} occupied cells)")
    print("wrote maps/warehouse.yaml")
    print("wrote worlds/warehouse.world")


if __name__ == "__main__":
    main()
