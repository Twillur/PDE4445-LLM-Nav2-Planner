# PDE4445 Technical Report — structural outline

Working scaffold for the 40% technical article. **Structure and budgets only — all prose is William's.**
Delete this file before submission if you'd rather it not sit in the assessed repo.

---
**Abstract**

LLMs can translate natural language into structured plans for robots. But how reliable are these plans when executed on a production navigation stack? This paper presents an evaluation of 100 commands across five complexity levels, executed on ROS2 Nav2 in a Gazebo warehouse. Reliability is non-monotonic: L4 conditional commands score 55.0% strict, while L5 ambiguous commands score 85.0% strict. The cause is not linguistic difficulty — it is schema expressiveness. L5 commands can defer via clarification; L4 commands are unambiguous but the contingency vocabulary is target-less. The model understands the condition and writes it in the `reason` field, but the schema has no executable slot for it. A minimal schema extension confirms the diagnosis. The finding is that reliability is bounded by plan representation, not by language complexity.

## Constraints

| | |
|---|---|
| Style | IEEE Transactions, two-column |
| Length | **Write 8 pages.** Handbook §7.5.1 says 8–10; `Todo summary.pptx` slide 2 says 6–8. They overlap at exactly 8 — 8 satisfies both without needing the conflict resolved |
| Budget | ≈ 5,600 words + references ≈ 8 pages (calibration: the "Excellent" exemplar is 9 pp / ~5,800 words) |
| Due | **Fri 11 Sept 2026** (viva Wed 9 Sept) |
| Structure | Mirrors the exemplar's roman-numeral layout — the marker has seen this shape before, don't invent a new one |

## Page budget

| Section | Words | Pages | Figures/Tables |
|---|---|---|---|
| Abstract | 180 | — | — |
| I. Introduction | 700 | 1.0 | — |
| II. Literature Review | 900 | 1.25 | Table I (gap table) |
| III. Methodology | 1,300 | 1.75 | Fig. 1 (architecture), Table II (levels), Table III (metrics) |
| IV. Implementation | 700 | 1.0 | Fig. 2 (warehouse + map) |
| V. Experiments and Results | 1,400 | 2.0 | **Fig. 3, 4, 5**, Table IV, Table V |
| VI. Conclusion and Future Work | 480 | 0.75 | — |
| References | — | 0.5 | — |
| **Total** | **≈5,660** | **≈8.25** | 5 figures, 5 tables |

Trim from IV first if you overrun — implementation detail is the most compressible and it's already on the blog.

---

## I. Introduction

Warehouse robots need non-expert operators. Today's interfaces are waypoint GUIs or hard-coded routes — neither is accessible to a warehouse worker who speaks English.

Large language models can translate English into structured plans. The bridge is plausible. But nobody has published reliability numbers for LLM-generated plans executed on a production ROS2 navigation stack. This work provides them.

The system is a prompt architecture and JSON schema that translates English commands into Nav2 waypoint plans. It was evaluated on 100 commands across five graded complexity levels in a Gazebo warehouse. The results are counter-intuitive: reliability is non-monotonic. L4 conditional commands score 55.0% strict; L5 ambiguous commands score 85.0% strict. L5, the vaguest level, outperforms L4 by 30 points.

The cause is not linguistic difficulty. It is schema expressiveness. L5 has an escape hatch — `understood: false` and a clarification question. L4 has none — the command is unambiguous, but the contingency vocabulary is target-less. The model understands the conditional and writes it in the `reason` field, but the schema has no executable slot for it. The condition leaks into a comment.

A minimal schema extension — adding `goto_fallback` and `fallback_target` — tests this diagnosis directly. The v3 experiment shows the model stops inventing the field once the field exists.

Scope is limited to navigation and observation. No manipulation. Simulation-based, TRL 4–6.

**Contributions**
(i) a prompt architecture and named-location JSON schema that makes coordinate hallucination structurally impossible;
(ii) a five-level command-complexity dataset (100 commands) and evaluation framework;
(iii) evidence that reliability is bounded by plan-schema expressiveness, not linguistic complexity;
(iv) a minimal schema extension that tests this claim directly.

---

## II. Literature Review (900 w)

The literature divides into four clusters: LLMs as task planners, language-guided navigation, execution-layer robotics, and prompting methodology.

A. LLMs as task planners

Ahn et al. [1] demonstrated that LLMs can ground language in robotic affordances, generating task plans from natural language instructions. Huang et al. [2] extended this with inner monologue, enabling the model to reason about its own actions. Liang et al. [3] introduced Code as Policies, using LLMs to generate executable code for embodied control. Singh et al. [4] developed ProgPrompt, which generates situated robot task plans using LLMs.

These works show that LLMs can translate English into structure. None quantify how reliability degrades as command complexity increases. The assumption is that if a plan is syntactically valid, it is semantically correct — an assumption this work tests directly.

B. Language-guided navigation

Shah et al. [5] presented LM-Nav, combining LLMs with visual navigation in outdoor environments. Zhou et al. [6] developed NavGPT, using LLMs for explicit reasoning in vision-and-language navigation tasks. Vemprala et al. [7] surveyed ChatGPT for robotics, identifying design principles and model capabilities.

These systems are bespoke pipelines or VLN benchmarks. None integrate with a production ROS2 navigation stack. The gap between LLM-generated plans and execution in a real stack remains unmeasured.

C. Execution layer

Macenski et al. [8] presented the Marathon 2 navigation system, establishing Nav2 as the de facto ROS2 navigation stack. Macenski and Jambrecic [9] introduced SLAM Toolbox for dynamic-world localisation. These provide the substrate for execution — but neither addresses how LLM-generated plans interact with Nav2's behaviour-tree-based contingency handling.

D. Prompting methodology

Wei et al. [10] introduced chain-of-thought prompting, establishing that structured prompting can elicit reasoning. This work treats the prompt architecture as an independent variable, comparing v1 and v2 directly.

The gap

None of these works quantify reliability as a function of command complexity in a real ROS2 stack. The assumption that LLM-generated plans are executable and correct is widespread and untested. Table I summarises the gap:

| Area | Existing work | Gap |
|---|---|---|
| Task planning | [1]–[4] | No reliability quantification across complexity |
| Navigation | [5]–[7] | VLN benchmarks, not ROS2 |
| Execution | [8], [9] | No LLM integration |
| Prompting | [10] | No schema-expressiveness analysis |

**Additional references**

The following support specific methodological claims. Tam et al. [11] show that constraining LLMs to structured formats degrades reasoning performance — the closest prior work to this finding, distinguished in §V-D. JSONSchemaBench [12] establishes JSON-schema-based LLM generation as a reliability technique. Ji et al. [13] survey hallucination in natural language generation; named-location validation reduces failure modes. ReAct [15] is contrasted with the single-call design in §III-A. Pallottino [17] motivates warehouse robotics deployment. Macenski et al. [16] present Nav2 behaviour trees, connecting the on_blocked vocabulary to established contingency representations.

---

## III. Methodology (1,300 w)

**A. System architecture**

The system follows a single-pass pipeline: natural language command → LLM → validated JSON plan → executor → Nav2. There is no agent loop, no re-prompting, and no chain-of-thought. The LLM receives the command, a JSON schema defining the plan structure, and a semantic map of named locations. It returns a plan in a single call. The executor then translates each step into a Nav2 action and drives the robot.

→ **Fig. 1** shows this architecture as a block diagram.

**B. The plan schema as a contract**

The plan is defined by a JSON schema at `schema/waypoint_plan.schema.json`. Two design decisions are central.

First, the LLM names locations, never coordinates. Every target must match a name in the semantic map — `storage_zone_a`, `aisle_2_north`, `loading_dock` — and the executor validates each target against the map before execution. Coordinate hallucination is structurally impossible rather than merely unlikely.

Second, every plan carries an `understood` boolean and a `clarification_question` field. This is the ambiguity escape hatch: if the command is underspecified, the model can respond with `understood: false` and ask for clarification. This becomes load-bearing in §V.

The `action` enum supports `navigate` and `wait`. The `on_blocked` contingency vocabulary — `abort`, `skip`, `reroute_perimeter`, `wait_retry`, `null` — provides per-step failure handling. Critically, every contingency is target-less. There is no way to say "go to B instead."

**C. Prompt architecture v1 → v2**

The prompt architecture was the independent variable. v1 was the initial implementation; v2 added seven changes, each generalising to the class of command it addresses:
1. Endpoint navigation vs. full traversal
2. Infer from the map before clarifying
3. Explicit clockwise/counter-clockwise definition
4. Wall sweeps corner→mid→corner
5. "Between/midway/nearest" — reason over coordinates
6. "Wait at X" = navigate then wait
7. `wait_retry` contingency

Every change generalises to the class of command it addresses — it does not encode answers to specific evaluation items. This defends against the attack that the prompt was tuned to the test set.

The v1→v2 comparison is reported in §V-B. The v3 extension — adding a target fallback — is reported in §V-E.

**D. Dataset design**

100 commands were designed across five levels, 20 per level. The ordering was designed to represent increasing linguistic difficulty:

| L | Name | Example |
|---|---|---|
| 1 | Direct | "Go to the loading dock" |
| 2 | Spatial | "Go to the north end of aisle 2" |
| 3 | Multi-step | "Patrol aisles 1 and 3, then return to base" |
| 4 | Conditional | "Inspect storage zone A; if it's unreachable, inspect zone B instead" |
| 5 | Ambiguous | "Go check that thing near the door" |

This ordering is defensible — L5 is deliberately vaguer than L4. That matters because §V shows success does **not** follow this ordering. If the ordering were arbitrary, the non-monotonic result would be meaningless. Because it is designed, the inversion is a real finding.

**E. Metrics**

Four independent measures were used:
1. Parse validity — is the response valid JSON?
2. Schema adherence — does the JSON conform to the schema?
3. Map validity — do all targets exist in the map?
4. Semantic correctness — does the plan match the command intent?

Schema adherence and semantic accuracy are reported separately, not collapsed into one pass rate. A plan that names the right fallback destination in the wrong field is a different kind of wrong from a plan that goes to the wrong place. Reporting them separately is what makes §V-D legible.

**F. Grading protocol**

27 items — 10 at L4 and 17 at L5 — could not be scored automatically. These required human judgement against rubric criteria. Grading was blind: the rubric sheet at `results/grading_sheet.html` hid the prompt version and shuffled items with fixed seed 4445.

The marking standard was deliberately strict: a plan passes only if the rubric is satisfied **and** the executed behaviour matches the command intent. If the rubric is satisfied but the behaviour deviates, the item is marked **Partial** and the limitation is recorded. This strictness was chosen to surface schema limitations as findings rather than hide them.

One limitation is declared honestly: a single grader, no second rater, no inter-rater reliability statistic [14].

---

## IV. Implementation (700 w)

Compressible — trim here first.

**A. Simulation environment**

The simulation environment was built on ROS2 Humble with Gazebo Classic 11, running a TurtleBot3 Waffle. Nav2 provided the navigation stack and SLAM Toolbox provided the localisation. The warehouse map was generated programmatically with three aisles at x = 6, 9, and 12 metres, aligned to the occupancy grid. All 20 named locations were verified to lie on free cells.

→ **Fig. 2**: Gazebo warehouse + the labelled occupancy map side by side.

**B. Executor**

The `nl_nav2_executor` ROS2 package contains two components. `plan_runner.py` handles ROS-free execution logic with seven unit tests passing. `executor_node.py` wraps `nav2_simple_commander` to interface with the ROS2 action servers.

**C. Engineering findings**

Two middleware issues were resolved during implementation. Fast DDS completed discovery but silently dropped data under WSL2 mirrored networking; pinning Cyclone DDS to loopback resolved it. More significantly, un-composed Nav2 caused action handshake timeouts between `bt_navigator` and `controller_server`, leading to cascading recovery failures on long goals. Running the stack composed fixed it. The root cause was confirmed by reproducing the failure on an open warehouse and inspecting odometry traces, which showed smooth driving followed by mid-goal abort.

**D. End-to-end validation**

A plan — "Patrol aisles 1 and 3, then return to base" — was executed in the live simulation. All goals were reached successfully, confirming the pipeline's basic functionality.

---

## V. Experiments and Results (1,400 w) ← the centre of gravity

**A. Protocol**

All experiments used gpt-4o-mini with temperature 0, 3 trials per command. A determinism check confirmed that v1 produced identical outputs on 99/100 commands and v2 on 97/100 commands across all trials. This establishes that failures are systematic and characterisable, not sampling noise.

**B. Prompt architecture v1 vs v2**

Fig. 3 compares v1 and v2 on the automatically scorable levels (L1–L3). Table IV summarises the results:

| Level | v1 | v2 |
|---|---|---|
| L1 | 18.0 / 20 | 19.3 / 20 |
| L2 | 16.0 / 20 | 19.0 / 20 |
| L3 | 17.0 / 20 | 19.0 / 20 |

Overall improvement: 62.0% → 69.3%. Eight commands improved, none regressed. The earlier reported v2 L1 = 20/20 was a single-trial lucky result; 19.3 is the honest three-trial average. L4 and L5 were graded for v2 only — the v3 extension is reported in §V-E.

**C. The reliability curve** → **Fig. 4** (`fig1_reliability_curve.svg`)

Table V shows the success rates across all five levels. L1 through L3 sit flat in the mid-nineties at 96.7%, 95.0%, and 95.0% strict. Then L4 conditional drops to 55.0% strict and 70.0% with partial credit. Then L5 ambiguous climbs back to 85.0% strict and 92.5% with partial credit. That's a 40-point drop followed by a 30-point recovery.

Fig. 4 plots this non-monotonic curve. Fig. 5 breaks down the outcomes. At L4, 11 pass, 6 partial, and 3 fail out of 20. At L5, 17 pass, 3 partial, and 0 fail — no outright failures at the level that was supposed to be hardest.

This inversion is the central result. If linguistic difficulty drove reliability, the ordering would be monotonic — L5, the vaguest level, would score worst. Instead it scores best. The L4 dip isn't caused by sentence complexity. It's caused by the schema's expressiveness. That claim is explored in §V-D.

| Level | Strict | + partial credit |
|---|---|---|
| L1 Direct | 96.7% | 96.7% |
| L2 Spatial | 95.0% | 95.0% |
| L3 Multi-step | 95.0% | 95.0% |
| **L4 Conditional** | **55.0%** | 70.0% |
| **L5 Ambiguous** | **85.0%** | 92.5% |

→ **Fig. 5** (`fig3_outcome_composition.svg`): L4 = 11 pass / 6 partial / 3 fail; **L5 = 17 / 3 / 0 — zero outright failures at the level designed to be hardest.**

**D. Why the curve inverts**

The L4 dip and L5 recovery are not artefacts of linguistic difficulty. They are consequences of the schema's design.

L5 commands are ambiguous. The schema gives ambiguity a representable response: `understood: false` plus a `clarification_question`. This escape hatch is always available and never wrong. On trial 1, 11 of the 20 L5 commands used it. Ambiguity does not degrade reliability because the model can defer rather than guess.

L4 commands are unambiguous. The model cannot defer — `understood: false` would be wrong. But the schema's contingency vocabulary is target-less. Every `on_blocked` option — `abort`, `skip`, `reroute_perimeter`, `wait_retry` — describes a behaviour, not a destination. There is no way to say "go to B instead."

L4-12 illustrates the failure mode directly. The command was: "Inspect storage zone A; if it's unreachable, inspect storage zone B instead." 

The model returned:

```json
{
  "action": "navigate",
  "target": "storage_zone_a",
  "on_blocked": "reroute_perimeter",
  "reason": "Navigate to storage zone A for inspection."
},
{
  "action": "navigate",
  "target": "storage_zone_b",
  "on_blocked": null,
  "reason": "Inspect storage zone B if storage zone A is unreachable."
}
```


The model understood the conditional — it wrote it in the `reason` field. But the schema had no executable slot for it. The condition leaked into a comment, and the robot visits zone B unconditionally. Comprehension is not the problem. Expressiveness is.

The taxonomy confirms this. Retry the same target? The schema has `wait_retry` — both L4 items passed. Go somewhere else instead? The schema has no target fallback — all alternative-destination items landed on partial. The two failures need things the schema cannot express at all: counting blocks across multiple steps (L4-15), or approaching a target from a different direction (L4-20).

The strongest evidence is the schema violations. Across all three v2 trials, there are exactly three out-of-enum `on_blocked` emissions — and all three are at L4. `wait` (L4-08), `navigate` (L4-17), and most tellingly `try_aisle_1_north` (L4-19) — a recovery destination where a recovery behaviour belongs. The model synthesised the missing field. It only breaks the schema where the schema cannot say what needs to be said.

**E. Testing the explanation — schema v3**

The diagnosis predicts that adding a target fallback to the schema should recover the alternative-destination cases. v3 tests this directly.

Method: v3 = v2 plus exactly one change — `on_blocked: "goto_fallback"` + `fallback_target` — generated as a delta so it is the only variable. L4 re-run, 3 trials, same model and temperature.

Results:
- Schema adherence: 55/60 → 60/60. Every out-of-vocabulary emission disappears, including `try_aisle_1_north`. The model stops inventing the field once the field exists — this is the causal confirmation.
- Branch encoding: 0/9 → 7/9 trials on single-alternative-destination commands. L4-12 and L4-13 stable 3/3; L4-17 names the fallback every time but redundantly re-visits it on 2 of 3 trials.
- Residual failures fall exactly outside the fix's designed scope — multi-waypoint alternatives (L4-02), aggregate conditions (L4-10, L4-15), approach geometry (L4-20). A fix that repaired everything would be suspicious; one with a measured boundary is a result.

The v3 L4 rubric items are ungraded — 33 of 60 records are `manual`. There is no v3 semantic pass rate. Schema adherence and structural encoding only.

**F. Threats to validity**

One model (gpt-4o-mini), one temperature, one map, 20 items per level. Single grader, no inter-rater reliability statistic [14]. Plans were graded rather than all 100 executed — end-to-end validation was on representative plans. Simulation only — no hardware validation. v3 structurally evaluated but not semantically graded. The L4 taxonomy rests on ten hand-graded items, and the grading standard was deliberately strict to surface schema limitations as findings.

---

## VI. Conclusion and Future Work

Reliability is bounded by the expressiveness of the plan representation, not by the linguistic complexity of the command. The flat L1–L3 region and the L4 dip separate these two factors cleanly: designed linguistic difficulty rose monotonically across the five levels, and success did not follow.

The contributions are:
(i) a prompt architecture and JSON schema that makes coordinate hallucination structurally impossible;
(ii) a five-level dataset and evaluation framework;
(iii) evidence that reliability is bounded by schema expressiveness, not linguistic complexity;
(iv) a minimal schema extension that tests this claim directly.

**Future work**

The v3 extension repaired the alternative-destination class but left three residual classes: multi-waypoint fallbacks, aggregate conditions, and approach geometry. Extending the schema for these is the next step. Grading v3 semantically would provide the L4 pass rate. Cross-model comparison is feasible — the Anthropic provider path already exists in `planner.py`. Hardware deployment is costed but out of scope.

---

## Assets: have vs. need

All five figures exist and Tables I–V are populated from real data.

**File → figure-number mapping** (the filenames do NOT match the report numbering — check every reference):

| Report | File |
|---|---|
| Fig. 1 architecture | `results/figures/fig0_architecture.svg` |
| Fig. 2a warehouse | `assets/gazebo-turtlebot3-first-launch.png` (blog repo) |
| Fig. 2b semantic map | `results/figures/fig0b_semantic_map.svg` |
| Fig. 3 v1 vs v2 | `results/figures/fig2_v1_vs_v2.svg` |
| Fig. 4 reliability curve | `results/figures/fig1_reliability_curve.svg` |
| Fig. 5 outcome composition | `results/figures/fig3_outcome_composition.svg` |

**Still to do** (figures and references are DONE — this list has reverted twice, check it against the mapping table above before trusting it):
- 🔴 **LENGTH — every section is roughly half-budget.** Full draft = 2,695 words vs 5,660 target, ≈3.9 pages of prose against an 8-page requirement. Shortfalls: §I −433 · §II −482 · §III −681 · §IV −478 · §V −539 · §VI −324. Expand with material that already exists (see below), not filler.
- 🟡 Confirm co-authors for [17] (publisher blocks automated fetch); [11]–[16] are verified in `docs/references.md`
- 🟡 Write the AI-use declaration
- 🟡 Format in IEEE two-column
- 🟡 Summary video (blog requirement, separate 40%)

---

## Expansion targets (first draft is complete; this is now a *lengthening* job)

Every section is drafted and factually checked. The remaining work is depth, and there is
real material for all of it — none of this requires new research or padding.

| Section | Short by | Where the words already exist |
|---|---|---|
| §II | −482 | The six additional references are currently a list dump in one paragraph. Integrate [11]–[17] into the four clusters. **Tam et al. [11] deserves its own paragraph** distinguishing this work — it's the closest prior art and the hardest viva question |
| §III | −681 | Walk through Fig. 1 properly. Justify the metric separation with the failure it prevents. Expand the dataset-design rationale — why 20 per level, why these five. Grading protocol deserves the blind-shuffle mechanics in full |
| §IV | −478 | The blog has far more than 222 words on this: the Fast DDS diagnosis, the composed-stack root-cause hunt with odometry evidence, map generation and free-cell verification, the seven unit tests |
| §V | −539 | Make the L4 taxonomy an actual table. Expand the determinism check. More on v3's measured boundary |
| §I | −433 | The contributions list can be prose-expanded; the motivation currently gets two sentences |
| §VI | −324 | Future work items each deserve a sentence of justification, not a clause |

**Original writing order** (all now drafted, kept for reference):

| # | Section | Why here |
|---|---|---|
| 1 | V. Results | All data exists; longest section; everything else refers back to it |
| 2 | III. Methodology | Now you know exactly which methods need justifying |
| 3 | IV. Implementation | Mostly transcription from the blog |
| 4 | II. Literature Review | Format conversion of existing work + new refs |
| 5 | VI. Conclusion | Falls out of V once V is written |
| 6 | I. Introduction | Easiest last — you know what you're introducing |
| 7 | Abstract | Compress the finished paper |

Suggested schedule against 11 Sept: §V by 22 Aug · §III–IV by 29 Aug · §II + VI by 3 Sept · §I + abstract by 5 Sept (your declared freeze) · 6–8 Sept polish and viva prep.

---

## Do not forget

- 🔴 **AI-use declaration is mandatory** (handbook §7.5.1). Brief statement describing how generative AI was used. Permitted: proofreading, clarity, grammar, structure. **Not** permitted: generating content or replacing your own ideas and analysis. Write it yourself; be accurate about tooling and evaluation assistance.
- 🔴 Write **8 pages** — the only length satisfying both stated ranges.
- 🟡 Bibliography is explicitly required.
- 🟡 The blog is a **separate 40%** and needs a final summary video (handbook requirement) — not covered by this document.
- ✅ ~~Tell Judhi about the late blog-link submission~~ — done 2026-08-07 on Teams; he replied same day.
