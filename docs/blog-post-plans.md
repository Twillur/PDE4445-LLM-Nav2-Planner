# Four remaining blog posts — structure

The blog is **40%**, the same as the report, and it currently has five posts.
These four are the gap. **Every one draws on work already finished and graded —
none needs new research.**

**Structure and data mapping only; the prose is William's.**

House style, from the existing posts:

```
---
layout: post
title: "Something: a colon and a claim"
week: "Week N · Topic"
---
```

Existing weeks: 1 kickoff/planning · 2 background/setup · 7 evaluation.
These four sit at **Week 8**. Target **650–900 words** each — matching the
July posts, not the 1,600-word results post.

The method that worked on the results post: read the source, **close it**, say it
out loud, type what came out of your mouth.

---

## Post A — How the evaluation was designed

**Title angle:** the design decisions, not the results. The results post already
covers what happened; this covers why it was set up to be answerable.

**Suggested sections**
1. Five levels, twenty commands each — what each level adds (L1 direct, L2 spatial,
   L3 sequencing, L4 conditionals, L5 ambiguity)
2. Why 20 and not 50 — hand-grading the ambiguous levels has to stay feasible
3. Why three trials at temperature 0 — temperature 0 is not a determinism
   guarantee from the API, so you measured the residual instead of assuming it
4. The four metrics, and why schema adherence is reported separately from
   semantic correctness
5. The bit that matters: the level ordering had to be **defensible in advance**,
   because §V shows success does not follow it. An arbitrary ordering would have
   made the non-monotonic result meaningless

**Numbers available**
- v1 identical scores on 99/100 commands, v2 on 97/100
- The three v2 variations: L1-18, L4-17, L4-19 — two at L4, and both of those
  varied because the schema broke on one trial in three

**Assets:** `results/figures/fig2_v1_vs_v2.svg`

⚠️ Say "identical **scores**", not "identical outputs" — raw text matches on only
35/100. Same trap the report had.

---

## Post B — Grading 27 items by hand

**The most interesting of the four**, because it is about judgement rather than
code, and it contains the regrade story.

**Suggested sections**
1. Why 27 items could not be scored automatically — a machine can tell you a plan
   is *valid*, not that it is *reasonable*
2. The blind setup: prompt version hidden, items shuffled with seed 4445
3. The marking standard, stated plainly: Pass only if the rubric is satisfied
   **and** the executed behaviour matches intent; rubric satisfied but behaviour
   deviating → Partial. Deliberately strict, so schema limits surface as findings
4. **The L4-19 regrade** — you passed it, traced what `skip` actually does in
   `plan_runner.py`, found the robot makes an unrequested trip on the success
   path, and regraded it. Cost five points off the headline number
5. The limitation you cannot design away: one grader, no second rater, no
   inter-rater agreement statistic (reference [14], Artstein & Poesio)

**Why this post is worth writing:** most students describe what they found. A post
saying *here is where I got it wrong, here is the trace that showed me, here is
what it cost* reads as research rather than reporting. It is also the single best
preparation for the grading questions in `docs/viva-question-bank.md`.

**Assets:** screenshots of `results/grading_sheet.html` and
`results/justification_sheet.html`

---

## Post C — The robot actually drives

**Suggested sections**
1. English in, five waypoints out, robot drives the patrol —
   `aisle_1_south → aisle_1_north → aisle_3_south → aisle_3_north → charging_dock`
2. **5/5 goals reached**, exit 0 (run of 2026-08-07)
3. The two middleware findings, told as diagnosis rather than trivia:
   - Fast DDS completes discovery under WSL2 mirrored networking and then
     silently delivers nothing → Cyclone DDS pinned to loopback
   - Un-composed Nav2 timed out the `bt_navigator`↔`controller_server` action
     handshake → cascading recovery failure on long goals. Root-caused by
     elimination: an obstacle-free warehouse failed identically, and odometry
     traces showed smooth driving then a mid-goal abort
4. Optional and genuinely good: the five traps in building a repeatable demo
   harness — `execute_plan` tears Nav2 down on exit so it is single-use per
   launch; `pkill -f` matches its own parent shell; `set -u` aborts ROS2 sourcing
   silently; desktop capture films the desktop; Nav2 reports active before
   the Gazebo window exists. All in `setup/DEMO-RECORDING.md`

**Assets:** `docs/warehouse-run.html` (animates 402 real trajectory points),
`results/demo-footage/gazebo_check.png`

**Point to land:** without the middleware fixes, intermittent transport failures
would have been indistinguishable from LLM errors. The engineering is not a
detour — it is what made the evaluation trustworthy.

---

## Post D — The schema is the contract

**Sections**
1. Named locations, never coordinates — every target validated against the map
   before execution, so coordinate hallucination is structurally impossible
   rather than unlikely
2. **L5-18 as the proof**: "Go to aisle 5" returns `understood: false` with
   *"This warehouse only has aisles 1, 2 and 3 — which aisle should I go to?"*,
   byte-identical across all three trials
3. `understood` / `clarification_question` as the ambiguity escape hatch — and
   the point that this is what makes L5 survivable
4. The `on_blocked` vocabulary and why every option is target-less
5. v3: one field added, and the model stops inventing it. Schema adherence
   55/60 → 60/60

**Assets:** `results/figures/fig0_architecture.svg`,
`results/figures/fig0b_semantic_map.svg`, both captures in `assets/demo/`

⚠️ Do not claim v3 fixes the L4 score unless
`results/v3_grading_sheet.html` has been completed. Schema adherence and
structural encoding only until then.

---

## Order to write them

| # | Post | Why here |
|---|---|---|
| 1 | **C — robot drives** | Most concrete, freshest, and you have a live 5/5 result |
| 2 | **D — schema** | Reuses the v2/v3 material you can already explain cold |
| 3 | **B — grading** | Needs the most careful writing; do it with a clear head |
| 4 | **A — eval design** | Driest, and the material is stable — safe to leave last |

Then the summary video (`docs/summary-video-plan.md`), which reuses the same
assets a third time.

---

## Do not forget

- `git pull` before editing, `git diff --stat` after — a paste from a stale copy
  destroyed content six times in one session.
- Code fences vanish when pasting between editors. Check them.
- The blog is assessed work: no AI attribution in commits, and the AI-use
  declaration covers the blog as well as the report.
