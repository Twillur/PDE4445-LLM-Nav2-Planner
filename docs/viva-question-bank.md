# Viva question bank — PDE4445, Wed 9 Sept 2026

Questions an examiner is realistically going to ask, built from *your* actual
results rather than generic viva advice. For each: what they're really testing,
where your evidence lives, and what a weak answer sounds like.

**No model answers here on purpose.** You have to say these out loud in a room
with no notes, so writing them for you would be worse than useless. Use this to
find the holes, then practise talking through them.

Pair with `results/justification_sheet.html` for the item-level grades.

---

## 1. The headline finding

**Q. Talk me through your main result.**
Testing whether you can state a finding crisply. Have one sentence ready — not
a tour of the project. Your material: reliability is bounded by what the plan
schema can express, not by how hard the English is.
⚠️ Weak answer: starting at "so first I set up ROS2…". They asked for the
finding, not the chronology.

**Q. Why is Level 5 easier than Level 4? That seems backwards.**
The central question of your whole project — expect it early.
Evidence: L5 85.0% vs L4 55.0%; L5 has zero outright failures (17/3/0); 11 of
20 L5 commands returned `understood: false` with a clarification question.

**Q. Isn't the L4 dip just an artefact of how you wrote the L4 commands?**
The sharpest attack available, and a fair one. If your L4 items happen to be
badly worded, the dip means nothing.
Evidence: the taxonomy. Grades track *conditional type*, not sentence
difficulty — retry-type passes, alternative-destination is 6/6 partial,
aggregate and geometry fail. That pattern is about structure, not phrasing.
⚠️ Don't get defensive. Concede the levels were designed by you, then point at
the taxonomy as the independent signal.

**Q. Could the dip be noise?**
Evidence: 3 trials at temperature 0; v1 gave identical output on 99/100
commands, v2 on 97/100. The failures are systematic and repeatable, not
sampling variance. A 40-point drop is also far outside any plausible noise band.

**Q. What's the single strongest piece of evidence you have?**
Have this ready — it's an invitation, not a trap. All three out-of-vocabulary
`on_blocked` emissions in the entire v2 run are at L4, none anywhere else, and
one of them is `try_aisle_1_north` — a destination where a behaviour belongs.

---

## 2. Methodology

**Q. Why three trials if temperature is 0?**
Testing whether you understand your own tooling. Temperature 0 is not a
determinism guarantee from the OpenAI API. You measured the residual rather
than assuming it away.

**Q. Why gpt-4o-mini and not GPT-4 or Claude?**
Cost, latency and reproducibility for a 300-call evaluation.
⚠️ The follow-up is "would a bigger model fix the L4 dip?" — think about this
now. Your finding says the bottleneck is representational, so a better model
should *not* fix it. That's a falsifiable prediction and saying so is a strength.
Your `planner.py` is already provider-agnostic, which is why it's future work.

**Q. Why five levels? Why twenty commands each?**
Testing whether the design was principled or arbitrary.

**Q. Did you actually execute all 100 commands on the robot?**
🔴 **The one most likely to catch you out. The answer is no.** You graded the
*plans*, and separately validated the pipeline end-to-end on representative
plans (4/4 goals reached in the live sim).
That's a normal, defensible scope decision — but you must volunteer it, not get
caught on it. Say it in your threats-to-validity slide before they ask.

---

## 3. Grading — your softest area

**Q. Who graded the 27 rubric items?**
🔴 You did. Alone. No second rater, no inter-rater reliability statistic.
Name it in the field's own vocabulary (see reference [14], Artstein & Poesio)
and propose the remedy. Owning it reads as awareness; being caught reads as an
oversight. Same fact, different mark.

**Q. You wrote the rubric and you graded against it. Isn't that circular?**
The strongest version of the above. Your mitigations: prompt version hidden
during grading, items shuffled with a fixed seed, criteria written before
results were seen.

**Q. Why is L4-12 partial and not fail?**
They will pick an item at random. This is exactly what
`results/justification_sheet.html` exists for — if it's still empty on 8 Sept,
you have a problem.

**Q. What's the difference between Pass and Partial?**
Your standard: Pass requires the rubric satisfied **and** executed behaviour
matching intent. Rubric satisfied but behaviour deviating → Partial, limitation
recorded. Deliberately strict, chosen so schema limitations surface as findings
instead of hiding inside pass rates.

---

## 4. Design decisions

**Q. Why named locations instead of coordinates?**
Makes coordinate hallucination *structurally impossible* rather than unlikely —
every target is validated against the map before execution.
Evidence: L5-18 refuses a non-existent "aisle 5" and enumerates the real aisles.

**Q. Where did the `on_blocked` vocabulary come from, and why those five?**
Honest answer available: `wait_retry` was added in v2 specifically because the
model needed it. That's the same lesson as v3, arriving earlier — you extended
the vocabulary and the matching commands started working.

**Q. Why one LLM call? Why not an agent loop that re-plans on failure?**
Reproducibility, latency, cost, and one variable to study. Reference [15]
(ReAct) is the alternative you rejected on purpose — say that you considered it.

**Q. Nav2's behaviour trees already express branching. Why didn't you use them?**
🔴 **The best question anyone could ask you**, and it's coming if the examiner
knows ROS. The expressiveness you needed existed one layer *below* your plan
format the whole time. Reference [16].
This isn't a gotcha to survive — it's the most interesting thing about your
result. Have a view on it.

---

## 5. The v3 experiment

**Q. What does v3 prove?**
Schema adherence 55/60 → 60/60; every out-of-vocabulary emission disappears,
including `try_aisle_1_north`. Branch encoding 0/9 → 7/9 trials on
single-alternative-destination commands.

**Q. So v3 fixes the 55%?**
🔴 **No, and do not say yes.** The v3 L4 rubric items are ungraded — 33 of 60
records are still `manual`. There is **no v3 semantic pass rate**. You can claim
schema adherence and structural encoding. Nothing more.
Getting this wrong is the difference between a rigorous result and an overclaim.

**Q. Why did L4-17 only work on one trial in three?**
Know your own weak spot before they find it. It names the fallback every time
but redundantly re-visits it on 2 of 3 trials.

**Q. What doesn't v3 fix?**
Strong answer available: multi-waypoint alternatives (L4-02), aggregate
conditions (L4-10, L4-15), approach geometry (L4-20) — exactly the classes it
was never designed to cover. A fix that repaired everything would be suspicious.

---

## 6. Positioning against the literature

**Q. Tam et al. already showed format restriction degrades LLM performance.
What's new here?**
🔴 **Reference [11], arXiv:2408.02442.** If your examiner has read it, this is
the hardest question in the room. Prepare it properly.
The distinction: they show degradation in the abstract on general benchmarks;
you show it bounding task success in an embodied setting, identify the specific
missing primitive, and demonstrate that restoring it recovers adherence.

**Q. How is this different from SayCan or ProgPrompt?**
Neither quantifies reliability against graded command complexity on a
production navigation stack using prompting alone.

**Q. Who would actually use this?**
Warehouse staff directing a robot in plain English without waypoint GUIs.
⚠️ Don't oversell. It's a simulation-validated proof of concept at TRL 4–6,
which is what the module asks for.

---

## 7. Scope and honesty

**Q. What are the limitations?**
Have five ready and say them without being asked: one model, one temperature,
one map, 20 items per level; single grader with no agreement statistic;
simulation only, no hardware; plans graded rather than all executed; v3
structurally but not semantically evaluated.
Volunteering limitations is one of the cheapest marks in a viva.

**Q. What would you do differently?**
⚠️ "Nothing" is the worst possible answer. Real candidates: put
`fallback_target` in from the start, recruit a second grader, execute a sample
of plans rather than reasoning about all of them.

**Q. Why no hardware?**
Declared a stretch goal from week one — simulation-first was a design decision,
not a fallback, and the module accepts simulation as lab testing. Costed BOM
exists (`docs/dissertation-hardware-build` notes: ~$430 custom / ~$900 kit).

---

## 8. Engineering depth

Asked to check the work is genuinely yours. Short, confident answers.

**Q. Biggest technical obstacle?**
The un-composed Nav2 stack causing `bt_navigator`↔`controller_server` action
handshake timeouts under loopback-pinned Cyclone DDS — long goals failed, short
hops succeeded. Root-caused by elimination (open warehouse failed identically;
odom traces showed smooth driving then a mid-goal abort), fixed by running the
nav stack composed.

**Q. Why Cyclone DDS and not the default?**
Fast DDS completes discovery but silently delivers no data under WSL2 mirrored
networking. Publisher fine, subscriber silent, no error anywhere.

**Q. How do you know your map and world are consistent?**
`gen_warehouse_assets.py` generates both from one definition; all 20 named
locations verified on free cells.

---

## The five to rehearse out loud

If you only prepare five, these:

1. **Why is L5 easier than L4?** — the whole project in 60 seconds
2. **Did you execute all 100 commands?** — the honesty trap
3. **Does v3 fix the 55%?** — the overclaim trap
4. **Nav2 behaviour trees already do branching. Why didn't you?** — the deep one
5. **How is this different from Tam et al.?** — the literature one

Say each one out loud, timed, to a wall. If it takes more than 90 seconds you
haven't found the core of it yet.

---

## Demo

The module asks you to *showcase*, so lead with something running, not slides.
Strongest option: **the same command through v2 and v3, side by side.**

```
PROMPT_VERSION=v2 python src/planner.py "Inspect storage zone A; if it's unreachable, inspect storage zone B instead"
PROMPT_VERSION=v3 SCHEMA_VERSION=v3 python src/planner.py "<same command>"
```

v2 returns two steps and visits zone B every time. v3 returns one step with
`goto_fallback`. Same model, same command, only the schema differs — your entire
finding in thirty seconds, live.

### Captured evidence — `assets/demo/`

Terminal captures of both runs, in case the live demo fails or there's no
network in the room. **Have these open in a tab as a fallback.**

Both captures show `$env:PROMPT_VERSION` being set in the same frame as the
output, so each image proves which prompt version produced it — worth insisting
on, because `planner.py` silently defaults to `v1` when that variable is unset.

| File | Shows |
|---|---|
| `v2-two-steps-always-goes-to-B.png` | `PROMPT_VERSION = "v2"`; **two** steps — `storage_zone_a` with `on_blocked: "reroute_perimeter"`, then `storage_zone_b` unconditionally, the conditional stranded in the `reason` string |
| `v3-one-step-fallback-only-if-A-fails.png` | `PROMPT_VERSION = "v3"`; **one** step — `on_blocked: "goto_fallback"`, `fallback_target: "storage_zone_b"` |

The v2 capture reproduces the recorded evaluation exactly: `reroute_perimeter`
plus the `reason` string *"Inspect storage zone B if storage zone A is
unreachable"*, matching all three trials in
`results/20260801_151047_openai_gpt-4o-mini_v2.jsonl`. If asked whether the demo
is cherry-picked, that's the answer — it's the same output the graded run
produced, not a lucky sample.

⚠️ **Check terminal captures for secrets before committing.** Both images show
the command that *reads* `OPENAI_API_KEY` from `.env`; the key value itself is
never printed, so these are safe. Confirm the same for any future capture —
`.env` is gitignored precisely to keep the key out of the repo.

Better still if you have an evening: run both plans in Gazebo with zone A
reachable. The v2 robot drives to A and then pointlessly continues to B. The v3
robot drives to A and stops. Showing the failure beats describing it.
