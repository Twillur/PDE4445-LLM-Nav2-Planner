"""Batch evaluation runner.

Usage:
    python src/run_eval.py                 # full dataset, 1 trial each
    python src/run_eval.py --levels 1 2    # only levels 1 and 2
    python src/run_eval.py --ids L1-01 L5-18
    python src/run_eval.py --trials 3      # repeat each command (LLM non-determinism)

Writes results/<timestamp>_<provider>_<model>.jsonl (one record per trial) and
prints a per-level summary table. Rubric items are marked 'manual' for scoring
in the results file afterwards.
"""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from planner import MODEL, PROVIDER, build_system_prompt, plan_command
from validate import check_map, check_on_blocked, check_schema, score_semantic

ROOT = Path(__file__).resolve().parent.parent
DATASET = json.loads((ROOT / "dataset" / "commands.json").read_text(encoding="utf-8"))["commands"]


def run(args):
    items = [c for c in DATASET
             if (not args.levels or c["level"] in args.levels)
             and (not args.ids or c["id"] in args.ids)]
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{stamp}_{PROVIDER}_{MODEL.replace('/', '-')}.jsonl"

    system_prompt = build_system_prompt()
    tally = defaultdict(lambda: defaultdict(int))

    with out_path.open("w", encoding="utf-8") as f:
        for item in items:
            for trial in range(args.trials):
                r = plan_command(item["command"], system_prompt)
                rec = {
                    "id": item["id"], "level": item["level"], "trial": trial,
                    "command": item["command"], "provider": PROVIDER, "model": MODEL,
                    "latency_s": r["latency_s"], "raw": r["raw"],
                    "parse_ok": r["plan"] is not None, "parse_error": r["parse_error"],
                    "schema_error": None, "map_error": None,
                    "semantic": None, "semantic_detail": None,
                    "on_blocked": None, "manual_score": None,
                }
                lvl = tally[item["level"]]
                lvl["n"] += 1
                if r["plan"] is not None:
                    lvl["parse"] += 1
                    rec["schema_error"] = check_schema(r["plan"])
                    if rec["schema_error"] is None:
                        lvl["schema"] += 1
                        rec["map_error"] = check_map(r["plan"])
                        if rec["map_error"] is None:
                            lvl["map"] += 1
                        verdict, detail = score_semantic(r["plan"], item["expected"])
                        rec["semantic"], rec["semantic_detail"] = verdict, detail
                        lvl[f"sem_{verdict}"] += 1
                        ob_verdict, ob_detail = check_on_blocked(r["plan"], item["expected"])
                        if ob_verdict != "n/a":
                            rec["on_blocked"] = f"{ob_verdict}: {ob_detail}"
                            lvl[f"ob_{ob_verdict}"] += 1
                lvl["latency"] += r["latency_s"]
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                flag = "OK " if rec["semantic"] == "pass" else ("?? " if rec["semantic"] in (None, "manual") else "FAIL")
                print(f"  {flag} {item['id']} t{trial} [{r['latency_s']:.2f}s] {rec['semantic_detail'] or rec['parse_error'] or rec['schema_error'] or ''}")

    print(f"\n=== {PROVIDER}/{MODEL} — {out_path.name} ===")
    print(f"{'Lvl':<4}{'N':<5}{'Parse':<8}{'Schema':<8}{'Map':<8}{'SemPass':<9}{'SemFail':<9}{'Manual':<8}{'AvgLat':<7}")
    for level in sorted(tally):
        t = tally[level]
        print(f"{level:<4}{t['n']:<5}{t['parse']:<8}{t['schema']:<8}{t['map']:<8}"
              f"{t['sem_pass']:<9}{t['sem_fail']:<9}{t['sem_manual']:<8}{t['latency']/max(t['n'],1):<7.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", type=int, nargs="*", default=None)
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--trials", type=int, default=1)
    run(ap.parse_args())
