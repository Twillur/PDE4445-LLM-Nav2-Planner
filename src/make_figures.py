"""Generate the evaluation figures (SVG) from the raw result files.

Reads the v1/v2 eval JSONL runs plus the human L4/L5 rubric grades and writes
vector figures suitable for the report and the blog.

    python src/make_figures.py

Outputs into results/figures/. Colours come from a validated categorical pair
(blue/orange) and a lightness-monotone ordinal blue ramp, so the stacked figure
also survives greyscale printing.
"""

import json
import pathlib
import statistics
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "figures"

V1 = RESULTS / "20260801_145855_openai_gpt-4o-mini_v1.jsonl"
V2 = RESULTS / "20260801_151047_openai_gpt-4o-mini_v2.jsonl"
GRADES = RESULTS / "l45_grades.json"

LEVEL_NAMES = {1: "L1\nDirect", 2: "L2\nSpatial", 3: "L3\nMulti-step",
               4: "L4\nConditional", 5: "L5\nAmbiguous"}

# --- palette (validated with the dataviz validator, light surface #fcfcfb) ---
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
S1 = "#2a78d6"   # categorical slot 1 - blue
S2 = "#eb6834"   # categorical slot 2 - orange
ORD = ["#184f95", "#3987e5", "#86b6ef"]   # ordinal blue: pass / partial / fail
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"   # single quotes: nests inside XML attrs


def load(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def auto_stats(recs):
    """Per level: mean automatic passes across trials, and the manual item count."""
    out = {}
    for lvl in sorted({r["level"] for r in recs}):
        sub = [r for r in recs if r["level"] == lvl]
        trials = sorted({r["trial"] for r in sub})
        passes = [sum(1 for r in sub if r["trial"] == t and r["semantic"] == "pass") for t in trials]
        manual = len({r["id"] for r in sub if r["semantic"] == "manual"})
        n = len({r["id"] for r in sub})
        out[lvl] = {"auto_pass": statistics.mean(passes), "manual": manual, "n": n}
    return out


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_open(w, h, title):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">',
        f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>',
    ]


def text(x, y, s, size=12, fill=INK2, anchor="start", weight="400"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>')


def legend(x, y, entries):
    """entries: [(colour, label)] - swatch + label, identity never colour-alone."""
    out, cx = [], x
    for colour, label in entries:
        out.append(f'<rect x="{cx}" y="{y - 8}" width="10" height="10" rx="2" fill="{colour}"/>')
        out.append(text(cx + 16, y, label, size=12, fill=INK2))
        cx += 20 + len(label) * 6.6
    return out


# ---------------------------------------------------------------- figure 1
def fig_reliability_curve(levels, strict, lenient, path):
    W, H = 660, 400
    L, R, T, B = 66, 24, 56, 72
    pw, ph = W - L - R, H - T - B
    s = svg_open(W, H, "Reliability across command-complexity levels")
    s.append(text(L, 26, "Task success across command-complexity levels", 14, INK, weight="600"))
    s.append(text(L, 44, "prompt architecture v2, gpt-4o-mini, temperature 0", 12, MUTED))

    for v in range(0, 101, 20):                       # recessive gridlines
        y = T + ph - ph * v / 100
        s.append(f'<line x1="{L}" y1="{y}" x2="{L+pw}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
        s.append(text(L - 10, y + 4, f"{v}%", 11, MUTED, anchor="end"))
    s.append(f'<line x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}" stroke="{AXIS}" stroke-width="1"/>')

    n = len(levels)
    xs = [L + pw * (i + 0.5) / n for i in range(n)]

    def polyline(vals, colour):
        pts = " ".join(f"{x},{T + ph - ph * v / 100:.1f}" for x, v in zip(xs, vals))
        return (f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2" '
                f'stroke-linejoin="round" stroke-linecap="round"/>')

    s.append(polyline(lenient, S2))
    s.append(polyline(strict, S1))
    for x, v in zip(xs, lenient):                     # 2px surface ring on marks
        y = T + ph - ph * v / 100
        s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{S2}" stroke="{SURFACE}" stroke-width="2"/>')
    for x, v in zip(xs, strict):
        y = T + ph - ph * v / 100
        s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{S1}" stroke="{SURFACE}" stroke-width="2"/>')
        s.append(text(x, y + 22, f"{v:.0f}%", 12, INK, anchor="middle", weight="600"))

    for x, lvl in zip(xs, levels):
        for k, part in enumerate(LEVEL_NAMES[lvl].split("\n")):
            s.append(text(x, T + ph + 22 + k * 15, part, 12,
                          INK if k == 0 else MUTED, anchor="middle",
                          weight="600" if k == 0 else "400"))

    s += legend(L, H - 12, [(S1, "Pass only (strict)"), (S2, "With partial credit")])
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


# ---------------------------------------------------------------- figure 2
def fig_v1_v2(levels, v1v, v2v, path):
    W, H = 560, 380
    L, R, T, B = 60, 24, 56, 72
    pw, ph = W - L - R, H - T - B
    s = svg_open(W, H, "Prompt architecture v1 versus v2")
    s.append(text(L, 26, "Prompt architecture v1 vs v2", 14, INK, weight="600"))
    s.append(text(L, 44, "automatically scorable levels; mean of 3 trials", 12, MUTED))

    for v in range(0, 21, 5):
        y = T + ph - ph * v / 20
        s.append(f'<line x1="{L}" y1="{y}" x2="{L+pw}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
        s.append(text(L - 10, y + 4, str(v), 11, MUTED, anchor="end"))
    s.append(f'<line x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}" stroke="{AXIS}" stroke-width="1"/>')

    n = len(levels)
    gw = pw / n
    bw = (gw - 70) / 2                                  # 2px surface gap between bars
    for i, lvl in enumerate(levels):
        gx = L + gw * i + 17
        for j, (val, colour) in enumerate(((v1v[i], S2), (v2v[i], S1))):
            h = ph * val / 20
            x = gx + j * (bw + 2)
            y = T + ph - h
            s.append(f'<path d="M{x},{T+ph} L{x},{y+4} Q{x},{y} {x+4},{y} '
                     f'L{x+bw-4},{y} Q{x+bw},{y} {x+bw},{y+4} L{x+bw},{T+ph} Z" fill="{colour}"/>')
            s.append(text(x + bw / 2, y - 8, f"{val:.1f}", 12, INK, anchor="middle", weight="600"))
        for k, part in enumerate(LEVEL_NAMES[lvl].split("\n")):
            s.append(text(L + gw * i + gw / 2, T + ph + 22 + k * 15, part, 12,
                          INK if k == 0 else MUTED, anchor="middle",
                          weight="600" if k == 0 else "400"))

    s.append(text(L - 44, T + ph / 2, "commands solved (of 20)", 11, MUTED, anchor="middle")
             .replace("<text", f'<text transform="rotate(-90 {L-44} {T+ph/2})"', 1))
    s += legend(L, H - 12, [(S2, "v1 baseline"), (S1, "v2")])
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


# ---------------------------------------------------------------- figure 3
def fig_outcomes(rows, path):
    """rows: [(level, pass, partial, fail)] - stacked composition."""
    bh, gap = 48, 26
    W = 560
    L, R, T, B = 108, 40, 56, 56
    H = T + len(rows) * bh + (len(rows) - 1) * gap + B
    pw = W - L - R
    s = svg_open(W, H, "Outcome composition at levels 4 and 5")
    s.append(text(24, 26, "Where the judgement-dependent levels land", 14, INK, weight="600"))
    s.append(text(24, 44, "v2, human-graded against the dataset rubrics (n=20 per level)", 12, MUTED))

    for i, (lvl, p, pa, f) in enumerate(rows):
        y = T + i * (bh + gap)
        s.append(text(L - 14, y + bh / 2 + 4, LEVEL_NAMES[lvl].replace("\n", " "),
                      12, INK, anchor="end", weight="600"))
        x = L
        for val, colour, name in ((p, ORD[0], "pass"), (pa, ORD[1], "partial"), (f, ORD[2], "fail")):
            if val <= 0:
                continue
            w = pw * val / 20 - 2                      # 2px surface gap between segments
            s.append(f'<rect x="{x}" y="{y}" width="{max(w,1):.1f}" height="{bh}" rx="4" fill="{colour}"/>')
            if w > 22:                                 # direct labels: greyscale relief
                s.append(text(x + w / 2, y + bh / 2 + 5, str(int(val)), 13,
                              "#ffffff" if colour != ORD[2] else INK,
                              anchor="middle", weight="600"))
            x += w + 2
    s += legend(24, H - 12, [(ORD[0], "Pass"), (ORD[1], "Partial"), (ORD[2], "Fail")])
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v1, v2 = load(V1), load(V2)
    a1, a2 = auto_stats(v1), auto_stats(v2)

    grades = json.loads(GRADES.read_text(encoding="utf-8"))
    by_level = defaultdict(Counter)
    for g in grades:
        by_level[g["level"]][g["score"]] += 1

    levels = [1, 2, 3, 4, 5]
    strict, lenient, rows = [], [], []
    for lvl in levels:
        st = a2[lvl]
        c = by_level.get(lvl, Counter())
        p = st["auto_pass"] + c["pass"]
        pa = c["partial"]
        fail = st["n"] - p - pa
        strict.append(100 * p / st["n"])
        lenient.append(100 * (p + 0.5 * pa) / st["n"])
        if lvl in (4, 5):
            rows.append((lvl, p, pa, fail))

    fig_reliability_curve(levels, strict, lenient, OUT / "fig1_reliability_curve.svg")
    fig_v1_v2([1, 2, 3], [a1[l]["auto_pass"] for l in (1, 2, 3)],
              [a2[l]["auto_pass"] for l in (1, 2, 3)], OUT / "fig2_v1_vs_v2.svg")
    fig_outcomes(rows, OUT / "fig3_outcome_composition.svg")

    print(f"wrote 3 figures to {OUT}")
    for lvl, st, le in zip(levels, strict, lenient):
        print(f"  L{lvl}: strict {st:5.1f}%   with partial credit {le:5.1f}%")


if __name__ == "__main__":
    main()
