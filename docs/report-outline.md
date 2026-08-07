# PDE4445 Technical Report — structural outline

Working scaffold for the 40% technical article. **Structure and budgets only — all prose is William's.**
Delete this file before submission if you'd rather it not sit in the assessed repo.

---

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

## I. Introduction (700 w)

**Purpose:** problem, why it matters, what you built, what you found, contributions list.

Beats, in order:
1. Warehouse robots need non-expert operators; today's interface is waypoint GUIs or hard-coded routes.
2. LLMs can translate English → structure, so the bridge is plausible — but nobody has published reliability *numbers* for it into a production nav stack.
3. What this work is: a prompt architecture + JSON schema translating English into Nav2 waypoint plans, evaluated over 100 commands across 5 graded complexity levels in a Gazebo warehouse.
4. **Lead with the counter-intuitive result** — reliability is *non-monotonic*. Put "L5 85% vs L4 60%" in the introduction. It's your hook; don't make the marker wait until §V.
5. Scope exclusions, stated up front: navigation and observation only, no manipulation. Simulation-based (TRL 4–6, which the module expects).

**Contributions — state as an explicit numbered list.** Markers look for this:
> (i) a prompt architecture and named-location JSON schema that makes coordinate hallucination structurally impossible;
> (ii) a five-level command-complexity dataset (100 commands) and evaluation framework;
> (iii) evidence that reliability is bounded by **plan-schema expressiveness**, not linguistic complexity;
> (iv) a minimal schema extension (`fallback_target`) that tests (iii) directly, with its scope of effect measured.

---

## II. Literature Review (900 w)

**You already have this.** `_posts/2026-07-02-literature-review.md` is 687 words and correctly organised. Convert to IEEE numbered citations `[1]`–`[10]`, expand to ~900, keep the four-cluster structure:

| Cluster | Refs | The line you already have |
|---|---|---|
| A. LLMs as task planners | [1]–[4] | none quantify degradation as command complexity rises |
| B. Language + navigation | [5]–[7] | bespoke pipelines or VLN benchmarks, not a real ROS2 stack |
| C. Execution layer | [8], [9] | Nav2/SLAM Toolbox as the unmodified substrate |
| D. Prompting as method | [10] | basis for treating prompt architecture as an independent variable |

End with **Table I — the gap table**, lifted from the blog post. It's the strongest single object in your lit review; make it a numbered table, not prose.

**⚠️ You need ~6–10 more references.** 10 is thin for IEEE Transactions. Cheapest credible additions, all directly relevant:
- Structured/constrained LLM output and JSON-schema decoding (supports §III's schema contract)
- LLM hallucination + grounding (supports the named-locations-only design claim, which L5-18 validates)
- ReAct or Toolformer (reasoning/acting loops — contrast with your single-call design)
- A warehouse/logistics robotics deployment paper (motivates the application in §I)
- Rubric-based / human evaluation methodology (defends your Pass/Partial standard in §III-E — you currently have *no* citation for a hand-grading protocol, and that's the softest point in the methodology)
- Behaviour trees in Nav2 (Macenski has one) — connects your `on_blocked` vocabulary to established contingency representations, which strengthens §V-D considerably

---

## III. Methodology (1,300 w)

Lettered subsections, IEEE style.

**A. System architecture** — one call, no agent loop. English → LLM → validated JSON → executor → Nav2.
→ **Fig. 1**: block diagram. *Does not exist yet — you need to draw it.* Highest-value missing asset in the whole report.

**B. The plan schema as a contract** — `schema/waypoint_plan.schema.json`.
The key design claim: **the LLM names locations, never coordinates**, so coordinate hallucination is *structurally* impossible rather than merely unlikely. Every target is validated against the map before execution. State this as a design contribution — it's the cleanest one you have.
Cover: `understood` / `clarification_question` as the ambiguity escape hatch (this becomes load-bearing in §V), the `action` enum, and the `on_blocked` contingency vocabulary.

**C. Prompt architecture v1 → v2** — the independent variable. What changed and why. v2's additions include `wait_retry`, added specifically to express "wait a bit and try again."

**D. Dataset design** — 100 commands, 20 per level.
→ **Table II**: the five levels with an example command each.

| L | Name | Example |
|---|---|---|
| 1 | Direct | "Go to the loading dock" |
| 2 | Spatial | "Go to the north end of aisle 2" |
| 3 | Multi-step | "Patrol aisles 1 and 3, then return to base" |
| 4 | Conditional | "Inspect storage zone A; if it's unreachable, inspect zone B instead" |
| 5 | Ambiguous | "Go check that thing near the door" |

Justify the ordering as *designed* increasing linguistic difficulty — this matters, because §V shows success does **not** follow it. The ordering being defensible is what makes the non-monotonic result meaningful rather than an artefact.

**E. Metrics** → **Table III**. Four independent measures, and be explicit that they are independent:
1. parse validity · 2. **schema adherence** · 3. map validity · 4. semantic correctness

**State the decision that schema adherence and semantic accuracy are reported separately, not collapsed into one pass rate.** Justify it: a plan naming the right fallback destination in the wrong field is a different kind of wrong from a plan going to the wrong place. This decision is what makes §V-D legible.

**F. Grading protocol** — the soft spot; defend it properly.
- 27 items (10 L4, 17 L5) are rubric-type and need human judgement
- Blind grading: `results/grading_sheet.html`, prompt version **hidden**, shuffled with fixed seed 4445
- **The marking standard, stated verbatim:** Pass only if the rubric is satisfied **and** executed behaviour matches command intent. Rubric satisfied but behaviour deviates → **Partial**, limitation recorded. Deliberately strict, chosen to surface schema limitations as findings rather than hide them.
- **Declare the limitation honestly:** single grader, no second rater, no inter-rater reliability statistic. Say it; don't let the marker find it.

---

## IV. Implementation (700 w)

Compressible — trim here first.

- **A. Simulation environment.** ROS2 Humble, Gazebo Classic 11, TurtleBot3 Waffle, Nav2, SLAM Toolbox. Generated warehouse: 3 aisles at x = 6/9/12, occupancy map aligned to the world, all 20 named locations verified on free cells.
  → **Fig. 2**: Gazebo warehouse + the labelled occupancy map side by side. You have `assets/gazebo-turtlebot3-first-launch.png`; a labelled-map panel would be better.
- **B. Executor.** `nl_nav2_executor` ROS2 package: `plan_runner.py` (ROS-free execution logic, 7 unit tests green), `executor_node.py` wrapping `nav2_simple_commander`. **Mention the unit tests** — evidence of engineering rigour, cheap to state.
- **C. Engineering findings worth one paragraph** (shows depth, don't over-spend):
  - Fast DDS completes discovery but silently drops data under WSL2 mirrored networking → Cyclone DDS pinned to loopback
  - **The real one:** un-composed Nav2 caused `bt_navigator`↔`controller_server` action handshake timeouts → cascading recovery failure on long goals. Fixed by running the stack composed. Root-caused with evidence (open warehouse failed identically; odom traces showed smooth driving then mid-goal abort) — that *is* a methodology story, so tell it as one.
- **D. End-to-end validation.** "Patrol aisles 1 and 3, then return to base" → 5-waypoint plan → **4/4 goals reached** in the live sim.

---

## V. Experiments and Results (1,400 w) ← the centre of gravity

**A. Protocol.** gpt-4o-mini, temperature 0, 3 trials per command. Determinism check: v1 99/100 and v2 97/100 commands identical across all trials. **This matters — it establishes that failures are systematic and characterisable, not sampling noise.** Say so explicitly.

**B. Prompt architecture v1 vs v2** → **Fig. 3** (`fig2_v1_vs_v2.svg`) + **Table IV**

| Level | v1 | v2 |
|---|---|---|
| L1 | 18.0 / 20 | 19.3 / 20 |
| L2 | 16.0 / 20 | 19.0 / 20 |
| L3 | 17.0 / 20 | 19.0 / 20 |

Overall 62.0% → 69.3%. **8 commands improved, 0 regressed.** Note honestly that the earlier "v2 L1 = 20/20" was a lucky single trial; 19.3 is the honest three-trial figure. Volunteering that is a credibility gain, not a loss.
L4/L5 graded for v2 only — state the scope limit here so it can't read as an omission later.

**C. The reliability curve** → **Fig. 4** (`fig1_reliability_curve.svg`)

| Level | Strict | + partial credit |
|---|---|---|
| L1 Direct | 96.7% | 96.7% |
| L2 Spatial | 95.0% | 95.0% |
| L3 Multi-step | 95.0% | 95.0% |
| **L4 Conditional** | **60.0%** | 72.5% |
| **L5 Ambiguous** | **85.0%** | 92.5% |

→ **Fig. 5** (`fig3_outcome_composition.svg`): L4 = 12 pass / 5 partial / 3 fail; **L5 = 17 / 3 / 0 — zero outright failures at the level designed to be hardest.**

**D. Why the curve inverts** — the analytical core. Build it in this order:

1. **L5 has an escape hatch.** `understood: false` + a clarification question is always available and never wrong. **11 of 20 L5 commands use it.** Ambiguity has a representable response.
2. **L4 has none.** The command is unambiguous, so `understood: false` would be wrong — but every `on_blocked` option (`abort`, `skip`, `reroute_perimeter`, `wait_retry`) is **target-less**. "Go to B instead" is inexpressible.
3. **The worked example — L4-12.** Quote the raw output. The model writes `reason: "Inspect storage zone B if storage zone A is unreachable"` — perfect comprehension — then emits a plan visiting B *unconditionally*. **The conditional leaked into a free-text comment because nothing executable could hold it.** This single example carries the argument; give it the space.
4. **The taxonomy** → **Table V**, grades tracking schema rather than sentence:

| Conditional type | Items | Outcome |
|---|---|---|
| Retry same target | L4-09, L4-16 | pass |
| **Alternative destination** | L4-02, L4-10, L4-12, L4-13, L4-17 | **all partial** |
| Chained alternatives + abort | L4-19 | pass |
| Aggregate / counting | L4-15 | fail |
| Approach geometry | L4-20 | fail |

5. **The schema-violation evidence — your strongest single fact.** All three out-of-vocabulary `on_blocked` emissions in the entire v2 run are at L4; **zero** at L1/L2/L3/L5. `wait` ×6 (L4-08), `navigate` ×1 (L4-17), and **`try_aisle_1_north` ×1 (L4-19)** — a recovery *destination* where a recovery *behaviour* belongs. **The model synthesised the missing field.** Do not bury this.

**E. Testing the explanation — schema v3.** Turns the diagnosis into an experiment.
Method: v3 = v2 + exactly one change (`on_blocked: "goto_fallback"` + `fallback_target`), generated as a delta so it is the only variable. L4 re-run, 3 trials, same model and temperature.
- **Schema adherence 55/60 → 60/60.** Every out-of-vocabulary emission disappears, including `try_aisle_1_north`. **The model stops inventing the field once the field exists** — that is the causal confirmation.
- **Branch encoding 0/9 → 7/9 trials** on single-alternative-destination commands (v2 scores 0 *by construction*). L4-12 and L4-13 stable 3/3; L4-17 names the fallback every time but redundantly re-visits it on 2 of 3.
- **Residual failures fall exactly outside the fix's designed scope** — multi-waypoint alternatives (L4-02), aggregate conditions (L4-10, L4-15), approach geometry (L4-20). A fix that repaired everything would be suspicious; one with a measured boundary is a result.

🔴 **HARD LIMIT — do not overstate.** The v3 L4 rubric items are **ungraded** (33 of 60 records are `manual`). There is **no v3 semantic pass rate**. You may claim schema adherence and structural encoding. You may **not** write that v3 "fixes the 60%." Either grade those 33 records or scope the claim precisely.

**F. Threats to validity.** One honest paragraph — markers reward it:
one model, one temperature, one map, 20 items/level; single grader, no inter-rater statistic; simulation only, no hardware validation; v3 structurally but not semantically evaluated.

---

## VI. Conclusion and Future Work (480 w)

Restate the contributions against the evidence. The headline, in one sentence:

> Reliability is bounded by the expressiveness of the plan representation, not by the linguistic complexity of the command.

Why that matters: the two are routinely conflated, and the flat L1–L3 region plus the L4 dip separates them cleanly — designed linguistic difficulty rose monotonically and success did not.

**Future work, ordered by evidential support** (each already motivated by data, which is what makes this section strong rather than speculative):
1. Extend the schema for the three residual classes v3 does not cover — multi-waypoint fallbacks, aggregate conditions, alternative approach geometry
2. Grade v3 semantically to obtain the L4 pass rate
3. Cross-model comparison (the Anthropic provider path already exists in `planner.py` — zero code changes needed)
4. Replace the mock semantic map with a real SLAM Toolbox map, same location names
5. **Hardware deployment** — costed BOM, Jetson Nano + TurtleBot3-class platform, ~$430 custom / ~$900 kit. Declared out of scope from the outset (simulation-first was a design decision, not a fallback) but fully specified
6. Second grader + inter-rater reliability

---

## Assets: have vs. need

**Ready to drop in:**
- `results/figures/fig1_reliability_curve.svg` → Fig. 4
- `results/figures/fig2_v1_vs_v2.svg` → Fig. 3
- `results/figures/fig3_outcome_composition.svg` → Fig. 5
- `assets/gazebo-turtlebot3-first-launch.png` → Fig. 2 (partial)
- Tables I–V all populated above from real data

**Must create:**
- 🔴 **Fig. 1 — system architecture block diagram.** Doesn't exist. Highest-value gap; every report of this type has one and its absence is conspicuous.
- 🟡 Fig. 2 second panel — labelled occupancy map showing the 20 named locations
- 🟡 6–10 further references (see §II)
- 🟡 Abstract — write it **last**

---

## Writing order (not section order)

Draft in dependency order, not front to back. You have the most material for the middle, and the Introduction is far easier once the results section is fixed.

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
- 🟡 Tell Judhi about the late blog-link submission in your own words before he reads it cold.
