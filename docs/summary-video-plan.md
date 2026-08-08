# Summary video — shot plan

Handbook requirement on the blog (40%). Currently zero footage exists.

**Structure and assets only — the narration is William's.** Beats below say what
is on screen and what point it has to land; the words are yours.

**Every shot works without Gazebo.** The sim stack does not travel to the laptop,
so nothing here depends on it. If you do get Gazebo recording later, it slots
into beat 3 as an upgrade, not a dependency.

Target: **3 minutes**. Assessors watch a lot of these; a tight three beats a
rambling six.

---

## Assets — all of these already exist

| Asset | Path | Used in |
|---|---|---|
| Architecture diagram | `results/figures/fig0_architecture.svg` | beat 2 |
| Semantic map, 20 locations | `results/figures/fig0b_semantic_map.svg` | beat 2 |
| **Animated trajectory replay** | `docs/warehouse-run.html` | **beat 3** |
| Warehouse render (still) | `results/demo-footage/gazebo_check.png` | beat 3 |
| Reliability curve | `results/figures/fig1_reliability_curve.svg` | beat 4 |
| Outcome composition | `results/figures/fig3_outcome_composition.svg` | beat 4 |
| v2 terminal output | `assets/demo/v2-two-steps-always-goes-to-B.png` | beat 5 |
| v3 terminal output | `assets/demo/v3-one-step-fallback-only-if-A-fails.png` | beat 5 |
| Prompt v1 vs v2 | `results/figures/fig2_v1_vs_v2.svg` | optional |

`docs/warehouse-run.html` animates **402 recorded trajectory points** from the
real run — the robot's actual path, not a mock-up. Serve it over localhost and
screen-record the playback. That is your "robot moves" shot.

---

## The six beats

### 1 — The problem · ~25s
**On screen:** a warehouse worker's plain-English sentence, then a waypoint GUI
or a coordinate list as the alternative.
**Point:** the interface is the barrier, not the robot. Someone who can say
"go to the loading dock" should not have to learn coordinates.

### 2 — What was built · ~30s
**On screen:** `fig0_architecture.svg`, then `fig0b_semantic_map.svg`.
**Point:** one LLM call, no agent loop. The model names locations from a fixed
vocabulary of 20 and never emits coordinates, so a hallucinated location fails
validation instead of driving the robot.
⚠️ Do not narrate the whole pipeline box by box. Two sentences.

### 3 — It works · ~30s
**On screen:** `warehouse-run.html` playing the recorded trajectory. Cut in
`gazebo_check.png` for one beat to establish it is a real simulation.
**Point:** English in, five waypoints out, robot drives the patrol.
Say the number: **5/5 goals reached**.

### 4 — The finding · ~45s — *the centre of the video*
**On screen:** `fig1_reliability_curve.svg`. Let it sit. Then
`fig3_outcome_composition.svg`.
**Point:** L1–L3 flat in the mid-nineties, L4 drops to 55%, L5 climbs back to
85%. The level built to be hardest has **zero outright failures**. If language
difficulty drove reliability that ordering is impossible.
Give this beat silence after the curve appears. It is the one thing you want
remembered.

### 5 — Why · ~40s
**On screen:** the two terminal captures side by side, v2 then v3.
**Point:** same command, same model, only the schema differs. v2 emits two steps
and visits zone B every time; the condition ends up in a `reason` field nothing
executes. v3 emits one step with `fallback_target`.
Your own line from the blog is the strongest thing you can say here:
**"the robot reads the actions, not the reasons."**

### 6 — Honesty · ~15s
**On screen:** plain text, or you to camera.
**Point:** simulation only, no hardware. Plans graded rather than all 100
executed. Single grader. v3 evaluated structurally, and semantically only if you
finish `results/v3_grading_sheet.html` first.
Ending on limitations reads as confidence, not weakness — and it pre-empts three
of the four questions in `docs/viva-question-bank.md`.

---

## Recording notes

**Narrate separately.** Record the screen silently, then lay voice over it.
Talking while driving a demo produces worse versions of both, every time.

**Screen-record with the existing script** — full desktop is fine for figures
and terminal work:

```powershell
.\setup\record-demo.ps1 -Seconds 90 -Fps 24
```

⚠️ It captures **the whole desktop**. Close anything you would not want an
assessor to see. A previous run recorded a game instead of the simulation.

**Figures are SVG** — open them in a browser and zoom to fill the frame rather
than embedding at small size. They stay sharp at any scale.

**Serve the replay over localhost**, not `file://`:

```bash
cd docs && python -m http.server 8766     # then localhost:8766/warehouse-run.html
```

---

## Order to build it

1. Screen-record beat 5 first — two terminal commands, 40 seconds, and it is the
   strongest content. If everything else slips, you still have the finding on film.
2. Then beat 3, the replay playback.
3. Then the figure beats, which are just screen captures.
4. Narration last, over the finished cut.

Beats 1 and 6 need no capture at all — text slides or you to camera.

---

## Do not forget

- The video is a **blog** deliverable (40%), not part of the report.
- Keep it to three minutes.
- If the AI-use declaration covers tooling, the video is tooling-assisted too —
  be accurate about that in the declaration, not just about the written work.
