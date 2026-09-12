# Evidence guide

The project studies translation of typed commands into named-location plans. It does not measure general LLM intelligence or establish readiness for deployment.

## Original language experiment

| Evidence | Unit | Finding | Source |
|---|---|---|---|
| v2 L1, L2, L3 | 60 generated records per level | 58/60, 57/60, 57/60 strict automatic semantic passes | [v2 records](../../results/20260801_151047_openai_gpt-4o-mini_v2.jsonl) |
| L4 item summary | 20 command items | 11 pass, 6 partial, 3 fail; 55% strict, 70% at half-credit | [manual grades](../../results/l45_grades.json), v2 automatic outcomes |
| L5 item summary | 20 command items | 17 pass, 3 partial, 0 fail; 85% strict, 92.5% at half-credit | Same sources |
| v1 → v2 on L1–L3 | 180 generated records per version | 153/180 → 172/180 (85.0% → 95.6%) | [v1](../../results/20260801_145855_openai_gpt-4o-mini_v1.jsonl), v2 |
| v2 validity | 300 generated records | Parse 300/300; schema 295/300; map 295/295 among responses reaching that check | v2 records |
| v3 schema | 60 L4 generated records | 60/60, compared with v2 55/60 | [v3 records](../../results/20260807_154902_openai_gpt-4o-mini_v3.jsonl) |
| v3 selected branch diagnostic | 9 outputs across L4-12, L4-13, L4-17 | 7/9 encode the selected fallback check correctly; not complete semantic grading | [comparison code](../../src/compare_v3.py) |
| v2 latency | 300 generated records | Mean 2.2335 s; median 2.0845 s; exclusive-quantile p95 3.63105 s | v2 records |

The 27 manually graded outputs are not the entirety of L4/L5. There were 28 rubric-designated commands, with one schema-invalid response excluded from the manual sheet. The item summaries combine first-generation outcomes with manual judgements where required. Later trials do not provide three independently graded semantic judgements per L4/L5 command.

## Scientific limits to retain in a presentation

- L5 may pass through clarification; L4 conditional commands often need an executable branch. The categories do not offer equivalent success paths.
- The L4/L5 descriptive gap gives Fisher two-sided p=0.08236; it is not a statistically significant result at 0.05. Descriptive Wilson 95% intervals are approximately 34.2–74.2% and 64.0–94.8%.
- One model, one temperature, one authored map and dataset, and one human grader limit generalisation. The L1–L5 ordering is a design choice, not a validated universal complexity scale.
- Three worked prompt examples exactly match test commands (L1-01, L2-03, L4-09). Prompt v2 followed inspection of earlier failures.
- Blinding is unverified: the saved v2 grading interface displays the version and ordered IDs. Do not claim blinded grading without separate provenance.
- v3 changes both representation and prompt instructions. It is not a schema-only causal ablation, and full v3 semantic grading remains incomplete.
- Stable scoring outcomes on 99/100 and 97/100 commands do not mean identical plans. Full parsed JSON is stable on 43/100 and 50/100 respectively.
- Eight invalid contingency-field occurrences use three distinct values across five v2 responses; these are different denominators.

## Execution evidence by stage

| Stage | What happened | What it establishes |
|---|---|---|
| Original archived demo | A five-waypoint warehouse route is stored in the project | A selected end-to-end demonstration, not 100 robot trials |
| Three September replays | Direct 1/1, spatial 3/3, multi-step 5/5; odometry within 0.25 m | [Selected navigation integration checks](../validation/gazebo-20260911T213643Z/summary.json) using the pre-fix runtime |
| Runtime corrections | Shared gate, fallback handler and corrected exit status; 62 tests in Windows/WSL | [Controlled software checks](../validation/runtime-fixes-20260912/runtime-checks.json), not obstacle-triggered Gazebo fallback validation |
| Portfolio capture | Updated runtime reaches loading dock, 1/1 according to Nav2; 130 frames | [A genuine recorded simulation demonstration](media/navigation-log.txt), not a new odometry-cross-checked reliability study |

The initial failed simulation attempts are retained in [validation records](../validation/README.md). The report draft predates the last runtime corrections, so its implementation statements need updating before reuse.
