"""End-to-end bridge: English command -> LLM plan -> ready for Nav2 execution.

Ties the two halves of the dissertation pipeline together. Runs the planner on a
natural-language command, writes the validated plan to JSON, prints a readable
trace, and shows the exact command to execute it on the robot in the Gazebo
warehouse (ros2_ws/src/nl_nav2_executor).

    # load the OpenAI key first (planner.py does not read .env itself)
    python src/run_pipeline.py "Patrol aisles 1 and 3, then go charge"

The plan is written to results/last_plan.json by default (--out to change).
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path=ROOT / ".env"):
    """Minimal .env loader so OPENAI_API_KEY is available without extra deps."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", help="Natural-language navigation command")
    ap.add_argument("--out", default=str(ROOT / "results" / "last_plan.json"))
    args = ap.parse_args()

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY") and os.environ.get("LLM_PROVIDER", "openai") == "openai":
        sys.exit("OPENAI_API_KEY not set (put it in .env or the environment).")

    sys.path.insert(0, str(ROOT / "src"))
    from planner import MODEL, PROVIDER, plan_command  # noqa: E402

    print(f"provider={PROVIDER} model={MODEL}")
    print(f"command: {args.command}\n")

    r = plan_command(args.command)
    plan = r["plan"]
    if plan is None:
        sys.exit(f"planner returned unparseable output:\n{r['raw']}")

    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    if not plan.get("understood", False):
        print(f"NOT UNDERSTOOD -> asks: {plan.get('clarification_question')}")
    else:
        for i, step in enumerate(plan.get("plan", [])):
            if step["action"] == "navigate":
                extra = f"  on_blocked={step['on_blocked']}" if step.get("on_blocked") else ""
                print(f"  [{i}] navigate -> {step['target']}{extra}")
            else:
                print(f"  [{i}] wait {step.get('duration_s')}s")
        if plan.get("notes"):
            print(f"  notes: {plan['notes']}")

    print(f"\nplan written to {out}")
    print("\nExecute it on the robot (with the sim running):")
    print(f"  ros2 run nl_nav2_executor execute_plan --plan {out}")
    print("Or dry-run the logic without Gazebo:")
    print(f"  python3 ros2_ws/src/nl_nav2_executor/scripts/dry_run.py --plan {out}")


if __name__ == "__main__":
    main()
