# NL → Nav2 Waypoint Planner

Core pipeline for my MSc Robotics dissertation (PDE4445, Middlesex University Dubai):
**Natural Language Task Planning for Autonomous Robot Navigation via Large Language Models**.

Project blog: https://twillur.github.io/PDE4445-Robotics-Dissertation/

An operator types a plain-English command ("patrol aisles 1 and 3, then come home").
A prompt-engineered LLM — no fine-tuning — translates it into a structured JSON waypoint
plan validated against a semantic map, which ROS2 Nav2 then executes. Reliability is
evaluated across five command-complexity levels.

## Layout

| Path | What |
|---|---|
| `prompts/system_prompt_v1.md` | The prompt architecture (the research contribution) |
| `schema/waypoint_plan.schema.json` | LLM ↔ executor contract; named locations only, so coordinate hallucination is structurally impossible |
| `map/warehouse_map.json` | Semantic warehouse map (v0 mock; regenerated from SLAM Toolbox later with the same names) |
| `dataset/commands.json` | 100 evaluation commands, 20 per complexity level, with expected answers |
| `src/planner.py` | One command → one LLM call → parsed plan + latency |
| `src/validate.py` | Schema / map / semantic scoring |
| `src/run_eval.py` | Batch runner → `results/*.jsonl` + per-level summary |
| `src/run_pipeline.py` | End-to-end bridge: English → LLM plan JSON → ready for Nav2 |
| `ros2_ws/` | Nav2 executor node + Gazebo warehouse world ([details](ros2_ws/README.md)) |

## Run

```bash
pip install -r requirements.txt
cp .env.example .env   # add your API key

# planning only
python src/planner.py "Sweep aisle 2 then go charge"
python src/run_eval.py --levels 1 --trials 1

# English command straight to an executable plan
python src/run_pipeline.py "Patrol aisles 1 and 3, then return to base"
```

`LLM_PROVIDER` = `openai` (default, gpt-4o-mini) or `anthropic`.

For the execution half — building the workspace, launching the Gazebo warehouse,
and driving the robot through a plan — see [`ros2_ws/README.md`](ros2_ws/README.md).

## The five complexity levels

1. Direct — "Go to the loading dock"
2. Spatial — "Move along the east wall"
3. Multi-step — "Patrol aisles 1 and 3, then return"
4. Conditional — "Check aisle 2; if blocked, take the perimeter"
5. Ambiguous — "Have a look around the storage area"

Level 5 includes hallucination traps ("go to aisle 5" — there is no aisle 5) and
capability traps ("clean up aisle 2" — the robot has no arm).

## Results

100 commands × 3 trials, `gpt-4o-mini` at temperature 0, prompt architecture v2.
Schema and map validation are automatic; semantics were graded by hand where
automation cannot judge.

| Level | Strict | With partial credit |
|---|---|---|
| L1 Direct | 96.7% | 96.7% |
| L2 Spatial | 95.0% | 95.0% |
| L3 Multi-step | 95.0% | 95.0% |
| **L4 Conditional** | **55.0%** | 70.0% |
| **L5 Ambiguous** | **85.0%** | 92.5% |

**Reliability is non-monotonic.** L5 — the vaguest level — beats L4 by 30 points.

The cause is not linguistic difficulty, it is schema expressiveness. L5 has an
escape hatch: the plan can return `understood: false` with a clarification
question. L4 has none. The command is unambiguous, but the contingency
vocabulary is target-less, so the model understands the condition, writes it
into the `reason` field, and the condition leaks into a comment instead of
becoming executable.

A minimal schema extension — adding `goto_fallback` and `fallback_target` —
tests that diagnosis directly: once the field exists, the model stops inventing
it. The finding is that **reliability is bounded by plan representation, not by
language complexity.**

Write-up: [The Dip at Level 4](https://twillur.github.io/PDE4445-Robotics-Dissertation/2026/08/07/the-dip-at-level-4/)

Scope is navigation and observation only — no manipulation. Simulation-based, TRL 4–6.
