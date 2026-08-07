"""Generate the labelled semantic map figure (Fig. 2b of the report).

    python src/make_map_figure.py

Writes results/figures/fig0b_semantic_map.svg — the 20 named locations that
constitute the planner's entire spatial vocabulary, over the real warehouse
geometry.

Geometry is read from map/warehouse_map.json and mirrors the shelf definition
in ros2_ws/src/nl_nav2_executor/scripts/gen_warehouse_assets.py, so the figure
cannot drift from the world the robot actually drives in. Palette and
typography match make_figures.py.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"
MAP = json.loads((ROOT / "map" / "warehouse_map.json").read_text(encoding="utf-8"))

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
S1 = "#2a78d6"
S2 = "#eb6834"
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

# Mirrors SHELVES in gen_warehouse_assets.py: thin rows centred between the
# aisles at x = 6/9/12, stopping at y=13 so the aisles reconnect to the north.
SHELVES = [(c - 0.25, c + 0.25, 4.0, 13.0) for c in (4.5, 7.5, 10.5, 13.5)]

# Category drives colour; label offsets are hand-placed to avoid collisions.
# (category, dx, dy, anchor) in map metres.
PLACEMENT = {
    "charging_dock":   ("task", 0.5, 1.0, "start"),
    "loading_dock":    ("task", -0.5, 0.0, "end"),
    # below its marker, so it clears east_wall_mid's label on the same y
    "packing_station": ("task", 0.0, -0.9, "middle"),
    "storage_zone_a":  ("task", 0.0, 0.9, "middle"),
    "storage_zone_b":  ("task", 0.0, 0.9, "middle"),
    "office_door":     ("task", 0.5, 0.0, "start"),
    "aisle_1_south":   ("aisle", 0.0, -1.1, "middle"),
    "aisle_2_south":   ("aisle", 0.0, -1.1, "middle"),
    "aisle_3_south":   ("aisle", 0.0, -1.1, "middle"),
    "aisle_1_north":   ("aisle", 0.0, 0.9, "middle"),
    "aisle_2_north":   ("aisle", 0.0, 0.9, "middle"),
    "aisle_3_north":   ("aisle", 0.0, 0.9, "middle"),
    # shares (1,1) with charging_dock; sits level with the marker while the
    # dock's label goes above, and stays clear of the bottom wall
    "corner_sw":       ("perim", 0.6, 0.0, "start"),
    "corner_nw":       ("perim", 0.5, 0.0, "start"),
    "corner_ne":       ("perim", -0.5, 0.0, "end"),
    "corner_se":       ("perim", -0.5, 0.0, "end"),
    "west_wall_mid":   ("perim", 0.5, 0.0, "start"),
    "east_wall_mid":   ("perim", -0.5, 0.0, "end"),
    "north_wall_mid":  ("perim", 0.0, -1.1, "middle"),
    "south_wall_mid":  ("perim", 0.0, 0.9, "middle"),
}
COLOUR = {"task": S1, "aisle": S2, "perim": MUTED}
LEGEND = [("task", "task locations"), ("aisle", "aisle endpoints"), ("perim", "perimeter waypoints")]

W, H = 620, 690
PAD_L, PAD_T, PLOT = 46, 74, 528


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=12, fill=INK2, anchor="start", weight="400", style=""):
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{st}>{esc(s)}</text>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    b = MAP["bounds"]
    span = b["x_max"] - b["x_min"]
    sc = PLOT / span

    def px(mx):
        return PAD_L + (mx - b["x_min"]) * sc

    def py(my):                      # north is +y in the map, but SVG y grows down
        return PAD_T + (b["y_max"] - my) * sc

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="Labelled semantic map of the 20x20 metre warehouse showing the '
        f'twenty named locations available to the planner">',
        f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
        text(PAD_L, 30, "Semantic map: the planner's entire spatial vocabulary", 14, INK, weight="600"),
        text(PAD_L, 48, "20 m x 20 m warehouse, 20 named locations. The LLM may reference these "
                        "names and nothing else —", 12, MUTED),
        text(PAD_L, 63, "it never emits coordinates, so a hallucinated location fails map "
                        "validation rather than driving the robot.", 12, MUTED),
    ]

    # 1 m grid, recessive
    for i in range(int(span) + 1):
        s.append(f'<line x1="{px(i)}" y1="{py(b["y_min"])}" x2="{px(i)}" y2="{py(b["y_max"])}" '
                 f'stroke="{GRID}" stroke-width="0.5"/>')
        s.append(f'<line x1="{px(b["x_min"])}" y1="{py(i)}" x2="{px(b["x_max"])}" y2="{py(i)}" '
                 f'stroke="{GRID}" stroke-width="0.5"/>')

    # shelving
    for xa, xb, ya, yb in SHELVES:
        s.append(f'<rect x="{px(xa):.1f}" y="{py(yb):.1f}" width="{(xb - xa) * sc:.1f}" '
                 f'height="{(yb - ya) * sc:.1f}" fill="{AXIS}" rx="1"/>')

    # walls
    s.append(f'<rect x="{px(b["x_min"])}" y="{py(b["y_max"])}" width="{span * sc}" '
             f'height="{span * sc}" fill="none" stroke="{INK2}" stroke-width="2"/>')

    # markers, then labels, so no label is overdrawn by a later marker
    locs = MAP["locations"]
    for name, loc in locs.items():
        cat = PLACEMENT.get(name, ("perim", 0.5, 0.0, "start"))[0]
        s.append(f'<circle cx="{px(loc["x"]):.1f}" cy="{py(loc["y"]):.1f}" r="4" '
                 f'fill="{COLOUR[cat]}" stroke="{SURFACE}" stroke-width="1.5"/>')
    for name, loc in locs.items():
        cat, dx, dy, anchor = PLACEMENT.get(name, ("perim", 0.5, 0.0, "start"))
        s.append(text(px(loc["x"] + dx), py(loc["y"] + dy) + 4, name, 10.5,
                      COLOUR[cat] if cat != "perim" else INK2, anchor=anchor,
                      weight="600" if cat == "task" else "400"))

    # axes
    s.append(text(PAD_L - 10, py(b["y_max"]) + 4, "20", 10, MUTED, anchor="end"))
    s.append(text(PAD_L - 10, py(b["y_min"]) + 4, "0", 10, MUTED, anchor="end"))
    s.append(text(PAD_L - 26, (py(0) + py(20)) / 2, "y (m), north +", 10, MUTED, anchor="middle")
             .replace("<text", f'<text transform="rotate(-90 {PAD_L - 26} {(py(0) + py(20)) / 2})"', 1))
    s.append(text(px(b["x_max"]), py(b["y_min"]) + 20, "20", 10, MUTED, anchor="middle"))
    s.append(text(px(b["x_min"]), py(b["y_min"]) + 20, "0", 10, MUTED, anchor="middle"))
    s.append(text((px(0) + px(20)) / 2, py(b["y_min"]) + 34, "x (m), east +", 10, MUTED, anchor="middle"))

    # legend + geometry note
    ly = H - 34
    cx = PAD_L
    for cat, label in LEGEND:
        s.append(f'<circle cx="{cx + 5}" cy="{ly - 4}" r="4" fill="{COLOUR[cat]}"/>')
        s.append(text(cx + 16, ly, label, 11, INK2))
        cx += 26 + len(label) * 6.2
    s.append(text(PAD_L, H - 12, "Shelving (grey) blocks east–west movement between aisles below "
                                 "y = 13 m; the perimeter route is always available.",
                  10.5, MUTED, style="italic"))

    s.append("</svg>")
    path = OUT / "fig0b_semantic_map.svg"
    path.write_text("\n".join(s), encoding="utf-8")
    print(f"wrote {path}  ({len(locs)} locations)")


if __name__ == "__main__":
    main()
