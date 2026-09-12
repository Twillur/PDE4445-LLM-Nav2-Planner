# Report revision — 11 September 2026

Read [main.pdf](main.pdf). Edit [main.tex](main.tex). Rebuild with `./build.ps1` from PowerShell. The PDF uses the standard IEEEtran journal layout and is eight pages including references and the AI-use statement. The build uses pdflatex and BibTeX directly because the installed latexmk cannot find Perl.

This is a full rewritten draft based on the existing report, code, saved outputs, and grades, updated with simulation checks on 12 September. The original report and outline were preserved. No evaluation code, dataset, schemas, grades, or archived result files were changed; no new API experiments, hardware runs, commits, pushes, or publications were performed.

## Simulation follow-up — 12 September 2026

Three archived v2 plans were replayed in fresh Gazebo warehouses: L1-01 reached 1/1 goals, L2-01 reached 3/3, and L3-01 reached 5/5. Recorded odometry corroborated all nine destinations within 0.25 m. These are selected execution checks, not new language samples or conditional-fallback validation. Initial failures caused by missing model resolution and startup timeout are retained alongside the successful runs.

The environment setup now resolves the repository's Cyclone DDS configuration and installed Gazebo models. Shell files use LF line endings. Core executor, map, schema and evaluation sources remain unchanged. Seven existing executor tests passed under WSL Python. See [validation notes](../../docs/validation/README.md), [run summary](../../docs/validation/gazebo-20260911T213643Z/summary.json), and [trajectory plot](../../docs/validation/trajectories.pdf).

The updated report remains eight pages. All pages and the separate trajectory plot were visually inspected. v3 semantic grading, its missing executor fallback handler, and the missing shared validation gate remain unresolved.

## Later code changes: author update needed

After the PDF was built, the execution gate, fallback handler and failure exit status were corrected and tested. See [runtime correction notes](../../docs/validation/runtime-fixes-20260912/README.md). The PDF still describes the code before those changes. Update its present-tense implementation statements before submission; retain the historical evaluation limitations and distinguish software tests from the earlier Gazebo evidence. The table below records findings from the original audit, not the corrected runtime's current behaviour.

## Corrections that affect your defence

| Earlier claim | What the checked evidence supports | Where to check |
|---|---|---|
| Localisation uses SLAM Toolbox | Ground-truth odometry, map server, and static map-to-odom transform in the demonstrated launch configuration | `ros2_ws/src/nl_nav2_executor/launch/warehouse_sim.launch.py` |
| Executor subscribes to plans and publishes status | Reads JSON from a file or stdin; logs outcomes through BasicNavigator | `ros2_ws/src/nl_nav2_executor/nl_nav2_executor/executor_node.py` |
| Every demo plan is fully validated before execution | Batch evaluation calls schema/map validators. The demo bridge does not call them, and the executor is not a full schema gate | `src/run_pipeline.py`, `src/run_eval.py`, executor files |
| JSON output is constrained by the full schema during generation | JSON-object mode; schema checking happens after generation | `src/planner.py` |
| Three invalid contingency emissions | Three distinct values, in five responses, with eight field occurrences: `wait` six times, `navigate` once, `try_aisle_1_north` once | August v2 JSONL; read-only `src/compare_v3.py` |
| 99/100 and 97/100 identical plans | Identical recorded scoring outcomes. Full parsed JSON, including explanations, is identical on 43/100 v1 commands and 50/100 v2 commands | August v1/v2 JSONL |
| Eight commands improved on L1–L3 | Seven on L1–L3; the eighth is L5-13. None regress on the recorded automatic pass count | August v1/v2 JSONL |
| Overall 62.0% → 69.3% indicates L1–L3 success | L1–L3: 153/180 → 172/180, or 85.0% → 95.6%. The other percentages mix automatically passed records with ungraded rubric records | August v1/v2 JSONL |
| No exact test-item exposure in the prompt | Three worked examples exactly match L1-01, L2-03, and L4-09. v2 was developed after inspecting failures | `prompts/system_prompt_v2.md`, `dataset/commands.json` |
| Blind grading, shuffled with seed 4445 | Notes describe this, but the saved v2 interface labels v2 and lists IDs in order. Blinding is unverified; the report says so | `results/grading_sheet.html`; compare `src/make_v3_grading_sheet.py` |
| There are 27 rubric-designated commands | There are 28: 11 L4 + 17 L5. L4-08 fails schema checking, leaving 27 items in the manual sheet | Dataset, grades, v2 JSONL |
| All L4/L5 outcomes use three graded trials | Rubric outputs were graded once, using the first generation. Later schema failures on L4-17/L4-19 are not reflected in the once-graded 20-item summary | Grading sheet and v2 JSONL |
| v3 changes only the schema | One conceptual fallback feature changes both the schema and prompt policy. It is not a schema-only ablation | v2/v3 prompt and schema files |
| v3 proves semantic or robot success | 60/60 schema validity and 7/9 on a selected structural check; 33/60 records remain manual. The executor has no fallback handler; map checking does not inspect fallback targets | `src/compare_v3.py`, `src/validate.py`, `plan_runner.py` |
| All remaining v3 failures are outside the fix's scope | L4-17 still flattens its branch in two trials; L4-19 repeats the fallback in all three, and is excluded from the 7/9 subset | v3 JSONL |
| The saved demo patrols aisles 1 and 3 | Saved replay and trajectory instead show aisle 1, packing station, loading dock, and return to charging dock | `docs/warehouse-run.html`, `docs/warehouse-run-trajectory.json` |
| Existing screenshot depicts the warehouse | It depicts the default TurtleBot3 world. The revised report uses the stored warehouse trajectory instead | Original `report/figures/gazebo-turtlebot3-first-launch.png` |

## Verified numbers and their meaning

- v2 parse validity: 300/300; schema adherence: 295/300. All 295 responses reaching ordinary-target map checking pass it; five did not reach that check.
- L1–L3: 58/60, 57/60, 57/60 automatic semantic passes for v2.
- L4: 11 pass, six partial, three fail in the item summary. L5: 17 pass, three partial, zero fail. Partial credit means a weight of **0.5**, not a completed task.
- L4 strict 55.0%, weighted 70.0%; L5 strict 85.0%, weighted 92.5%.
- L4 vs L5 two-sided Fisher exact p = 0.0823587770. Descriptive Wilson 95% intervals: 34.2085–74.1802% and 63.9581–94.7631%. These calculations do not repair the scoring confound or make authored items a random population sample.
- v3 selected branch check: L4-12 3/3, L4-13 3/3, L4-17 1/3. This does not check all conditional semantics or every fallback command.
- v2 latency mean 2.233503 s; median 2.084500 s. p95 = 3.631050 s using `statistics.quantiles(..., n=100, method='exclusive')`. Inclusive interpolation gives 3.559950 s; nearest rank gives 3.556 s. The report retains 3.63 s and states the convention.
- The stored trajectory contains 402 coordinate samples. These are not 402 independent trials. All 20 named locations occupy free cells in the stored PGM; this is not a clearance or reachability proof.
- Seven existing ROS-free executor tests passed in the initial audit and again under WSL during the simulation follow-up. The three additional Gazebo checks are documented above.

## Items requiring your review

1. **Grading provenance:** identify any different original grading sheet if you actually used a blinded, shuffled interface. The current report follows the archived artifact rather than repeating the unsupported claim. A punctuation encoding difference in the archived L5-18 display does not change its refusal/clarification meaning.
2. **AI declaration:** the report accurately discloses substantive drafting and analysis assistance in this revision. Review it for completeness against your earlier tool use. Your existing outline attributes restrictions on generated content to handbook §7.5.1; authorship permission here does not establish compliance with module assessment rules. The handbook itself was not available for independent verification in this session.
3. **Remaining evidence:** v3 semantic grading and controlled fallback execution are still outstanding. The report describes these as future work; it does not supply grades or imply the experiments already happened.
4. **Presentation consistency:** replace the old “three emissions,” “identical plans,” “eight L1–L3 improvements,” blind-grading assertion, and two-aisle demo story in your own preparation notes. This task did not modify those notes or the public blog.

The Claude artifact and public journal did not load through the available web tool. The report was based on local project evidence. Seventeen bibliography entries were checked against primary paper/publisher records, and their source links are in [references.bib](references.bib). This is verification of the cited material, not an exhaustive survey through September 2026.

## Files and verification

- [main.pdf](main.pdf): eight-page report.
- [main.tex](main.tex): editable manuscript.
- [references.bib](references.bib): bibliography with primary-source links.
- [trajectory.tex](trajectory.tex), [trajectory.dat](trajectory.dat), [reliability.tex](reliability.tex): report figures; no results figures were overwritten.
- [build.ps1](build.ps1): reproducible build without Perl.
- [verification.txt](verification.txt): final numerical and preservation checks.
- [source-hashes.json](source-hashes.json): hashes recorded before manuscript changes, used to check original evidence preservation.

All eight PDF pages were rendered and visually inspected. The final LaTeX build resolves all references/citations and reports no overflowing text. MiKTeX printed nonfatal warnings about its separate user-profile log directory; PDF and bibliography generation succeeded.
