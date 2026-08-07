"""Generate the system architecture figure (Fig. 1 of the report).

    python src/make_architecture_figure.py

Writes results/figures/fig0_architecture.svg. Palette and typography match
make_figures.py so all four report figures read as one set, and the ordinal
blue ramp keeps the validation gates legible in greyscale print.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
S1 = "#2a78d6"
S2 = "#eb6834"
ORD = ["#184f95", "#3987e5", "#86b6ef"]
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

W, H = 940, 400
BOX_W, BOX_H, GAP = 124, 84, 30
LEFT, TOP = 23, 96

STAGES = [
    ("Operator", ["natural-language", "command"], INK2),
    ("System prompt", ["schema +", "20 named locations"], INK2),
    ("LLM", ["one call", "gpt-4o-mini, T=0"], S1),
    ("Validation", ["three gates", "(below)"], S1),
    ("Executor", ["plan_runner", "+ on_blocked"], INK2),
    ("Nav2 + Gazebo", ["TurtleBot3", "Waffle"], INK2),
]

GATES = [
    ("1. parse", "valid JSON returned", ORD[0]),
    ("2. schema", "conforms to WaypointPlan", ORD[1]),
    ("3. map", "every target is a real location", ORD[2]),
]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=12, fill=INK2, anchor="start", weight="400", style=""):
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{st}>{esc(s)}</text>')


def box(x, y, w, h, stroke, fill=SURFACE, width=1.5, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"{d}/>')


def arrow(x1, y1, x2, y2, colour=AXIS, dash="", width=1.5):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" marker-end="url(#head)"{d}/>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="System architecture: natural language command through prompt '
        f'assembly, a single LLM call, three validation gates and the executor into Nav2">',
        f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
        f'<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{AXIS}"/></marker></defs>',
        text(LEFT, 34, "System architecture", 14, INK, weight="600"),
        text(LEFT, 52, "one LLM call per command; no agent loop, no re-prompting except a single "
                       "bounded retry on invalid JSON", 12, MUTED),
    ]

    # --- pipeline stages -------------------------------------------------
    xs = []
    for i, (title, sub, colour) in enumerate(STAGES):
        x = LEFT + i * (BOX_W + GAP)
        xs.append(x)
        s.append(box(x, TOP, BOX_W, BOX_H, colour, width=1.8 if colour == S1 else 1.2))
        cx = x + BOX_W / 2
        s.append(text(cx, TOP + 26, title, 12.5, INK, anchor="middle", weight="600"))
        for k, line in enumerate(sub):
            s.append(text(cx, TOP + 46 + k * 15, line, 11, MUTED, anchor="middle"))
        if i:
            s.append(arrow(xs[i - 1] + BOX_W + 4, TOP + BOX_H / 2, x - 6, TOP + BOX_H / 2))

    # --- the design claim, annotated above the prompt box ----------------
    # Sits at TOP-10; the subtitle baseline is at 52, so there is ~24px clearance.
    s.append(text(xs[1] + BOX_W / 2, TOP - 10, "named locations only — coordinates never generated",
                  11, S2, anchor="middle", weight="600"))

    # --- validation gates ------------------------------------------------
    gy = TOP + BOX_H + 58
    s.append(f'<line x1="{xs[3] + BOX_W / 2}" y1="{TOP + BOX_H + 4}" x2="{xs[3] + BOX_W / 2}" '
             f'y2="{gy - 8}" stroke="{AXIS}" stroke-width="1.5" marker-end="url(#head)"/>')
    for i, (name, desc, colour) in enumerate(GATES):
        y = gy + i * 40
        # width 280 from xs[2] leaves a 22px gutter before the contingency box at xs[4]-6
        s.append(box(xs[2], y, 280, 30, colour, width=1.2))
        s.append(f'<rect x="{xs[2]}" y="{y}" width="5" height="30" rx="2" fill="{colour}"/>')
        s.append(text(xs[2] + 16, y + 19, name, 11.5, INK, weight="600"))
        s.append(text(xs[2] + 86, y + 19, desc, 11, MUTED))

    s.append(text(xs[2], gy + 3 * 40 + 16,
                  "any gate failing is recorded as a typed failure, not silently retried",
                  11, MUTED, style="italic"))

    # --- clarification feedback path -------------------------------------
    fy = TOP + BOX_H + 26
    s.append(f'<path d="M{xs[3] + 20},{TOP + BOX_H + 4} L{xs[3] + 20},{fy} '
             f'L{xs[0] + BOX_W / 2},{fy} L{xs[0] + BOX_W / 2},{TOP + BOX_H + 8}" '
             f'fill="none" stroke="{S2}" stroke-width="1.5" stroke-dasharray="4 3" '
             f'marker-end="url(#head)"/>')
    s.append(text(xs[0] + BOX_W / 2 + 10, fy - 7,
                  'understood: false  →  clarification_question returned to the operator',
                  11, S2, weight="600"))

    # --- contingency note on the executor --------------------------------
    ey = gy + 12
    s.append(box(xs[4] - 6, ey, BOX_W + 36, 74, GRID, width=1.2, dash="4 3"))
    s.append(text(xs[4] + 6, ey + 20, "on_blocked", 11.5, INK, weight="600"))
    for k, line in enumerate(["abort · skip", "reroute_perimeter", "wait_retry", "goto_fallback (v3)"]):
        s.append(text(xs[4] + 6, ey + 36 + k * 13, line, 10.5,
                      S1 if "v3" in line else MUTED))
    s.append(f'<line x1="{xs[4] + BOX_W / 2}" y1="{TOP + BOX_H + 4}" x2="{xs[4] + BOX_W / 2}" '
             f'y2="{ey - 6}" stroke="{GRID}" stroke-width="1"/>')

    s.append("</svg>")
    path = OUT / "fig0_architecture.svg"
    path.write_text("\n".join(s), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
