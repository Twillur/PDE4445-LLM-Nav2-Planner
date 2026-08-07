"""Compare prompt/schema v2 against v3 on Level 4 (conditional commands).

v3 adds exactly one thing to v2: on_blocked="goto_fallback" plus a
fallback_target field, so "if A is unreachable, go to B instead" becomes
representable rather than being flattened into an unconditional sequence.
This script quantifies what that single change bought.

    python src/compare_v3.py

Two metrics, deliberately kept separate (a plan naming the right fallback in
the wrong field is not the same kind of wrong as a plan going to the wrong
place):

  1. schema adherence  - how many records validate, and which out-of-vocabulary
                         on_blocked values the model reached for
  2. branch encoding   - on single-alternative-destination commands, is the
                         conditional a real branch, or is the fallback also
                         emitted as an unconditional step (i.e. visited every
                         time, not only when the first target is blocked)?
"""

import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
V2 = RESULTS / "20260801_151047_openai_gpt-4o-mini_v2.jsonl"

V2_VOCAB = {"abort", "skip", "reroute_perimeter", "wait_retry", None}
V3_VOCAB = V2_VOCAB | {"goto_fallback"}

# Commands whose contingency is a single alternative *destination* - the only
# class goto_fallback is designed to cover. The others at L4 need things it
# deliberately does not provide: a multi-waypoint alternative (L4-02), an
# aggregate/counting condition (L4-10, L4-15), or a different approach
# direction to the same target (L4-20).
SINGLE_ALT = {"L4-12": "storage_zone_b", "L4-13": "aisle_2_south", "L4-17": "north_wall_mid"}


def load(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def latest_v3():
    runs = sorted(RESULTS.glob("*_v3.jsonl"))
    if not runs:
        raise SystemExit("no v3 run found - generate one with:\n"
                         "  PROMPT_VERSION=v3 SCHEMA_VERSION=v3 python src/run_eval.py --levels 4 --trials 3")
    return runs[-1]


def out_of_vocab(recs, vocab):
    bad = collections.Counter()
    for r in recs:
        for m in re.finditer(r'"on_blocked":\s*("[^"]*"|null)', r["raw"] or ""):
            v = json.loads(m.group(1))
            if v not in vocab:
                bad[(r["id"], v)] += 1
    return bad


def plan_steps(rec):
    try:
        return json.loads(rec["raw"])["plan"]
    except Exception:
        return []


def encodes_branch(rec, expected_fallback=None):
    """True when the fallback is a real branch: named in fallback_target and NOT
    also re-emitted as a later unconditional navigate step."""
    steps = plan_steps(rec)
    navs = [s.get("target") for s in steps if s.get("action") == "navigate"]
    gf = [s for s in steps
          if s.get("on_blocked") == "goto_fallback" and s.get("fallback_target")]
    if not gf:
        return False, None
    fb = gf[0]["fallback_target"]
    if expected_fallback and fb != expected_fallback:
        return False, fb
    return fb not in navs[1:], fb


def main():
    v3_path = latest_v3()
    v2 = [r for r in load(V2) if r["level"] == 4]
    v3 = [r for r in load(v3_path) if r["level"] == 4]

    print(f"v2: {V2.name}\nv3: {v3_path.name}\n")
    print("=" * 62)
    print("1. SCHEMA ADHERENCE, level 4")
    print("=" * 62)
    for tag, recs, vocab in (("v2", v2, V2_VOCAB), ("v3", v3, V3_VOCAB)):
        valid = sum(1 for r in recs if r["schema_error"] is None)
        bad = out_of_vocab(recs, vocab)
        print(f"  {tag}: {valid}/{len(recs)} records valid, "
              f"{sum(bad.values())} out-of-vocabulary on_blocked emissions")
        for (item, val), n in bad.most_common():
            print(f"        {item}: {val!r} x{n}")

    print()
    print("=" * 62)
    print("2. BRANCH ENCODING, single-alternative-destination commands")
    print("=" * 62)
    print("  v2 scores 0 by construction: the field does not exist in that contract.\n")
    ok = total = 0
    for item, want in SINGLE_ALT.items():
        for rec in sorted((r for r in v3 if r["id"] == item), key=lambda r: r["trial"]):
            good, fb = encodes_branch(rec, want)
            ok += good
            total += 1
            print(f"  {item} t{rec['trial']}: fallback_target={fb!r:<20} "
                  f"{'branch' if good else 'flattened - fallback also visited unconditionally'}")
    print(f"\n  encoded as a real branch: v3 {ok}/{total} trials, v2 0/{total}")


if __name__ == "__main__":
    main()
