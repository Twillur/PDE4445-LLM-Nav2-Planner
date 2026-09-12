# Execution validation — 11–12 September 2026

This folder records additional checks requested after the report rewrite. It does not replace or alter the August language-evaluation results.

**Later runtime corrections:** [12 September runtime checks](runtime-fixes-20260912/README.md) add conditional fallback handling, a common execution gate, and corrected failure status. The Gazebo results below predate those code changes. Their logs and source hashes are preserved; the later software tests are separate evidence.

## Verified outcome

All three corrected-environment runs completed: **1/1 + 3/3 + 5/5 = 9/9 requested navigation goals**. The stored odometry corroborates all destinations within the configured 0.25 m tolerance. Recorded height remains approximately 0.009 m in every run. The existing seven executor tests also passed under WSL Python (7 passed in 0.41 s).

See the [derived run summary](gazebo-20260911T213643Z/summary.json) and [trajectory comparison](trajectories.pdf). The [report PDF](../../report/revised/main.pdf) includes these follow-up checks and retains their limitations.

## What was checked

Three archived v2 plans (trial 0) are replayed through the unchanged executor in a fresh headless Gazebo warehouse for each plan:

| Case | Request | Navigation goals |
|---|---|---|
| L1-01 | Go to the loading dock | 1 |
| L2-01 | Move along the east wall from south to north | 3 |
| L3-01 | Patrol aisles 1 and 3, then return to the charging dock | 5 |

These are selected integration checks, one run per case after restoring the environment. They are not a new language benchmark, a repeated-trial reliability estimate, or an evaluation of conditional fallbacks.

## Evidence locations

- [Mock executor checks](execution-check-20260911T172852Z/mock-checks.json): the existing ROS-free executor with controlled navigation outcomes; **not Gazebo**. The `exact_successful_visit_list_match` field compares lists only and is not a semantic grade. In particular, extra perimeter waypoints need interpretation rather than automatically constituting a task failure.
- [Initial Gazebo attempt](gazebo-20260911T173623Z/summary.json): the direct goal failed because Gazebo did not resolve its ground-plane model; recorded Z decreases continuously. The next case timed out during startup and did not execute. These attempts are retained as environment failures.
- [Corrected-environment run](gazebo-20260911T213643Z/summary.json): individual executor logs, derived trajectories, and raw odometry bags are retained. The summary cross-checks goal results and physical positions.

## Environment fixes

The host already had ROS2 Humble, Gazebo Classic and Nav2. Cyclone DDS was missing and was installed in WSL after refreshing a stale apt index. The existing executor package was built without changing its source.

The validation launcher uses the repository's loopback Cyclone DDS configuration directly, ROS domain 44, and Gazebo master port 11365. It adds `/usr/share/gazebo-11/models` to the model search path so the already-installed floor and sun assets resolve. No warehouse geometry, navigation parameters, map coordinates, prompts, or saved plans were changed.

The normal `setup/sim-env.sh` now resolves its workspace and Cyclone configuration relative to the repository, and includes the installed standard Gazebo model directory. It retains its normal ROS domain 30; the validation runner uses domain 44 separately.

The initial runner left one Nav2 component behind during shutdown; the process group was identified from the run and stopped. Cleanup now checks the entire process group it created, including children surviving their launcher. It does not use global name-based process killing.

Both map-server and navigation lifecycle managers must report active before a plan starts. Missing Gazebo assets stop the run. The runner also checks the achieved-goal summary because the unchanged executor can return exit code zero after a failed goal. Raw logs preserve that defect rather than hiding it.

## What remains unresolved

The original mock checks reproduce two different failures for L4-12. With v2 and an available primary destination, the robot visits both A and B unconditionally. With v3 and a blocked primary destination, the pre-fix executor does not attempt B because it has no `goto_fallback` handler. The later runtime corrections fix the missing handler and verify it in software tests; the v2 semantic error remains.

The shared runtime gate and fallback software tests are now implemented in the later correction stage. Complete v3 semantic grading, controlled Gazebo fallback trials and independent grading remain outstanding. These integration runs cannot resolve prompt/test overlap, the mixed semantic denominators, or uncertain grading blinding.

## Reproduction

From WSL, use `setup/check-simulation-env.sh` for a read-only preflight. Then run:

```bash
bash setup/validate-simulation.sh \
  /mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner/docs/validation/execution-check-20260911T172852Z
bash setup/summarize-validation.sh
```

Each invocation creates a fresh timestamped directory. The runner uses saved plans and makes no model calls. The summary reads raw bags without modifying them, verifies reported goal order, checks that recorded height remains physically plausible, and saves a sampled trajectory. Physical plausibility and goal success do not amount to collision certification or a complete task-semantic evaluation.
