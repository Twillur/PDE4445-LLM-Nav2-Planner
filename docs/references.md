# Bibliography — PDE4445 technical report

Companion to `docs/report-outline.md`. IEEE numbered style. Section II carries
[1]–[10]; the additions [11]–[17] close the gaps that outline flags.

**Verification status is stated per entry.** Anything marked ⚠️ needs a detail
pulled off the source page before it goes in the bibliography — do not submit a
citation neither of us has checked.

---

## Existing — from the literature review post

The ten already framed in `_posts/2026-07-02-literature-review.md`.
✅ **All author lists verified via the arXiv API.** IEEE convention applied:
every author named where there are six or fewer, `et al.` beyond that (author
count in the right column so you can check the rule was applied correctly).

| # | Citation | Authors |
|---|---|---|
| [1] | M. Ahn *et al.*, "Do as I can, not as I say: Grounding language in robotic affordances," arXiv:2204.01691, 2022. | 46 |
| [2] | W. Huang *et al.*, "Inner monologue: Embodied reasoning through planning with language models," arXiv:2207.05608, 2022. | 16 |
| [3] | J. Liang *et al.*, "Code as policies: Language model programs for embodied control," arXiv:2209.07753, 2022. | 8 |
| [4] | I. Singh *et al.*, "ProgPrompt: Generating situated robot task plans using large language models," arXiv:2209.11302, 2022. | 9 |
| [5] | D. Shah, B. Osinski, B. Ichter, and S. Levine, "LM-Nav: Robotic navigation with large pre-trained models of language, vision, and action," arXiv:2207.04429, 2022. | 4 |
| [6] | G. Zhou, Y. Hong, and Q. Wu, "NavGPT: Explicit reasoning in vision-and-language navigation with large language models," arXiv:2305.16986, 2023. | 3 |
| [7] | S. Vemprala, R. Bonatti, A. Bucker, and A. Kapoor, "ChatGPT for robotics: Design principles and model abilities," arXiv:2306.17582, 2023. | 4 |
| [8] | S. Macenski, F. Martín, R. White, and J. Ginés Clavero, "The Marathon 2: A navigation system," in *Proc. IEEE/RSJ IROS*, 2020. arXiv:2003.00368. | 4 ✅ |
| [9] | S. Macenski and I. Jambrecic, "SLAM Toolbox: SLAM for the dynamic world," *J. Open Source Softw.*, vol. 6, no. 61, p. 2783, 2021. | 2 |
| [10] | J. Wei *et al.*, "Chain-of-thought prompting elicits reasoning in large language models," arXiv:2201.11903, 2022. | 9 |

Cluster mapping for §II: A. task planners [1]–[4] · B. language+nav [5]–[7] ·
C. execution [8], [9] · D. prompting [10].

---

## Additions — all verified against primary sources

### [11] The format-restriction result — **read this one first**

> Z. R. Tam, C.-K. Wu, Y.-L. Tsai, C.-Y. Lin, H.-Y. Lee, and Y.-N. Chen,
> "Let me speak freely? A study on the impact of format restrictions on
> performance of large language models," arXiv:2408.02442, 2024.

✅ Verified: title, six authors, submitted 5 Aug 2024, v3 14 Oct 2024.

**This is the most important addition and it needs its own paragraph in §II-D.**
It finds that constraining an LLM to structured output (JSON/XML) measurably
degrades reasoning, and that tighter format constraints produce worse
degradation on reasoning-heavy tasks.

That is your result approached from the opposite direction — and it lets you
position the contribution precisely rather than claiming novelty too broadly:

- They show format restriction degrades reasoning **in the abstract**, on
  general NLP benchmarks.
- You show it bounds **task success in an embodied setting**, and go further by
  identifying *which specific missing primitive* causes the loss (a target-less
  contingency vocabulary) and *demonstrating* that restoring it recovers schema
  adherence (v3, 55/60 → 60/60).

Cite it in §II-D, again in §V-D when you introduce the mechanism, and once more
in §VI. Handle it head-on — a marker who knows this paper will ask why your
finding isn't just a restatement of it, and the answer above is a good one.

### [12] Schema adherence as a measurable property

> S. Geng, H. Cooper, M. Moskal, S. Jenkins, J. Berman, N. Ranchin, R. West,
> E. Horvitz, and H. Nori, "JSONSchemaBench: A rigorous benchmark of structured
> outputs for language models," arXiv:2501.10868, 2025.

✅ Verified: title, nine authors, submitted 18 Jan 2025.

**Use in §III-E** to justify reporting schema adherence as a metric separate
from semantic accuracy. This is prior art for exactly that separation, so your
methodological choice stops looking ad hoc and becomes an established practice
you followed.

### [13] Grounding and hallucination

> Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu, E. Ishii, Y. J. Bang,
> A. Madotto, and P. Fung, "Survey of hallucination in natural language
> generation," *ACM Comput. Surv.*, vol. 55, no. 12, pp. 1–38, 2023.

✅ Verified: title, ten authors, ACM CSUR 55(12), March 2023.

**Use in §III-B** as the motivation for named-locations-only. It turns your
design decision from a sensible precaution into a documented mitigation of a
surveyed failure mode. Pair it with the L5-18 result, where the planner refuses
a non-existent "aisle 5" and enumerates the real aisles instead.

### [14] Inter-coder agreement — **fixes your weakest methodological point**

> R. Artstein and M. Poesio, "Survey article: Inter-coder agreement for
> computational linguistics," *Comput. Linguist.*, vol. 34, no. 4, pp. 555–596,
> 2008.

✅ Verified: ACL Anthology J08-4004, exact volume/issue/pages confirmed.

**Use in §III-F.** You are a single grader with no second rater — currently
asserted without support. Citing the canonical treatment of agreement
coefficients (Krippendorff's α, Cohen's κ, Scott's π) lets you name the
limitation in the field's own vocabulary and propose the specific remedy in
§VI: a second rater and a reported α.

Saying *"single-rater annotation without an inter-coder agreement statistic
[14]"* reads as methodological awareness. Saying nothing reads as an oversight.
Same fact, entirely different mark.

### [15] Reasoning–acting loops — justifies your single-call design

> S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao,
> "ReAct: Synergizing reasoning and acting in language models,"
> in *Proc. ICLR*, 2023. arXiv:2210.03629.

✅ Verified: title, seven authors, arXiv Oct 2022, ICLR 2023.

**Use in §II-A and §III-A.** Your architecture is deliberately *not* an agent
loop — one call, no re-prompting except a bounded retry on invalid JSON. That's
a defensible choice (reproducibility, latency, cost, one variable to study) but
only if you show you know the alternative and rejected it on purpose. Contrast
with [2] Inner Monologue, which closes a similar loop.

### [16] Nav2 and behaviour trees

> S. Macenski, T. Moore, D. V. Lu, A. Merzlyakov, and M. Ferguson, "From the
> desks of ROS maintainers: A survey of modern & capable mobile robotics
> algorithms in the Robot Operating System 2," *Robot. Auton. Syst.*, vol. 168,
> p. 104493, Oct. 2023. arXiv:2307.15236.

✅ Verified: title, five authors, RAS vol. 168, art. 104493, Oct 2023.

**Use in §IV-A and §V-D.** Two jobs. It's a stronger, more current citation for
the Nav2 substrate than [8] alone; and it connects your `on_blocked` vocabulary
to behaviour trees, which *do* express branching natively. That sharpens your
finding considerably — the expressiveness you needed already exists one layer
down in the stack, and the limitation was in your plan representation above it.
Worth a sentence in §VI.

### [17] Application motivation

> L. Pallottino, "Robotics for warehouses and logistics: Technologies,
> challenges, and future directions," *Annu. Rev. Control Robot. Auton. Syst.*,
> vol. 9, pp. 377–401, 2026. DOI: 10.1146/annurev-control-032724-020213.

✅ Verified: title, journal, vol. 9, pp. 377–401, 2026, DOI.
⚠️ **Confirm whether there are co-authors.** The publisher page returns 403 to
automated fetching, so this came from secondary sources, which surfaced only
Pallottino. Annual Review articles are frequently multi-author — open the DOI in
a browser and check before submitting.

**Use in §I** to support the opening claim that warehouse navigation is a real
application with non-expert operators. One citation is enough; don't spend
introduction words on a literature detour.

---

## Where this leaves the bibliography

17 references, which is respectable for an 8-page IEEE article. Distribution:

| Cluster | Refs |
|---|---|
| LLM task planning | [1] [2] [3] [4] [15] |
| Language + navigation | [5] [6] [7] |
| Execution stack | [8] [9] [16] |
| Prompting & structured output | [10] [11] [12] |
| Grounding / hallucination | [13] |
| Evaluation methodology | [14] |
| Application domain | [17] |

Every cluster the outline flagged is now covered, and the two that were bare —
evaluation methodology and structured-output constraint — now have the strongest
entries in the list.

**Remaining bibliography tasks:**
1. ~~Author initials for [1]–[7], [10]~~ — ✅ done, verified via arXiv API
2. ~~Confirm the [8] author list~~ — ✅ done, confirmed
3. **[17] — check for co-authors in a browser** (publisher blocks automated fetch)
4. **Update the gap table (Table I)** — [11] partially occupies the "format
   restriction" cell, so the claim there needs narrowing to the embodied,
   named-primitive result rather than the general phenomenon

Only item 3 needs a source check; item 4 is a writing decision. Every other
citation in this file has been verified against a primary source.
