# Runtime corrections — 12 September 2026

These changes follow the three Gazebo replays recorded in `gazebo-20260911T213643Z`. They change execution code, not the August language experiments. The earlier 9/9 navigation result belongs to the executor **before these corrections**. This directory contains software-test evidence, not a new Gazebo run.

## Changes

- `goto_fallback` now tries the named alternative exactly once after the primary goal reports failure. It does not visit the alternative when the primary succeeds. The remaining plan then continues; if both destinations fail, the overall result remains incomplete. This follows the existing per-step continuation policy. Only `abort` stops subsequent steps.
- The typed-command bridge, dry-run, and executor share `plan_validation.py` and `execution_plan.schema.json`. The whole plan is checked before any navigation or waiting. Both primary and fallback names must exist in the map, including fallbacks that might never run.
- The runtime contract rejects unknown fields/actions, contradictory clarification responses, missing navigation targets, missing or invalid wait durations, non-finite numbers, and misplaced fallback fields. A fallback equal to the primary is rejected; same-target retry already has `wait_retry`. Perimeter rerouting requires usable perimeter points.
- `PlanResult.exit_code` distinguishes complete execution (0) from incomplete, aborted or deferred execution (1). Invalid input is rejected with code 2 at the CLI. Intentional skipping still continues, but it is not reported as all destinations reached. Reaching a fallback completes that step without being counted as reaching the failed primary.
- Clarification and invalid input return before ROS node creation. After an executed plan, the node releases its own client and leaves the shared Nav2 stack running. The previous `lifecycleShutdown()` stopped that stack after every plan.
- An explicitly requested zero-second retry delay is respected. An omitted or null retry duration still defaults to five seconds.

The runtime contract is intentionally separate from `schema/waypoint_plan*.schema.json` and `src/validate.py`. It supports the existing plan fields, including v3 fallback fields, but imposes extra execution checks. It must not be substituted into historical evaluation or described as the schema used for the August results.

## Verification

- 62 regression tests passed on Windows and WSL. These include whole-plan rejection before motion, the three fallback outcomes, continuation, failure exit status, clarification, CLI handling, and client cleanup with a mocked ROS transport.
- The package rebuilt with `colcon`; actual ROS imports and the installed runtime schema resource were verified. This checks packaging, not navigation.
- [Eight controlled checks](runtime-checks.json) use copied saved plans and deterministic navigation responses. One additional input is an explicitly labelled synthetic mutation with an invented fallback name. These are assertions about software behaviour, not semantic grades or independent samples of language reliability.
- The saved v3 L4-12 plan attempts only A when reachable, A then B when A fails, and returns failure when both fail. The saved v2 L4-12 plan still visits A and B unconditionally when both are reachable; structural validation cannot detect or repair that semantic error.

Reproduce from WSL:

```bash
bash setup/verify-runtime-fixes.sh
```

See [WSL test output](tests-wsl.txt), [installed-package check](installed-package.txt), and `build.log`. The script makes no model calls and launches no simulation.

## Provenance and remaining work

[before-hashes.json](before-hashes.json) and `before/` preserve the six runtime files before modification. The simulation run's original source hashes remain intact. The archived planner, evaluation code, dataset, prompts, schemas, grades and result files were not modified. The report's original source manifest now intentionally differs for `src/run_pipeline.py`; its original bytes are retained under `before/src/run_pipeline.py`.

The report PDF predates these runtime corrections. Its archived-results analysis remains applicable, but present-tense statements about a missing execution gate and fallback handler need an author update. Describe the fixes as a later engineering change and cite this test evidence; do not imply the August model experiment or the earlier Gazebo replays used them. Review locations: implementation pipeline and figure caption, implementation limitations, conclusion/future work, and the assistance declaration. Keep the historical evaluation map-check limitation: `src/validate.py` still does not inspect fallback names.

Outstanding evidence includes controlled Gazebo trials of the updated fallback path, v3 semantic grading, and independent grading. Navigation failure is the branch trigger; it does not uniquely establish a physical obstacle. Goal success and these validation checks do not establish collision safety, correct inspection behaviour, arbitrary conditional reasoning, or real-world deployment readiness.
