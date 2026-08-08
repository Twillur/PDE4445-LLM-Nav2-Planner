"""Build the blind grading sheet for the v3 Level-4 re-run.

    python src/make_v3_grading_sheet.py
    cd results && python -m http.server 8765     # then open localhost:8765

Writes results/v3_grading_sheet.html.

Why this exists: v3 currently has no semantic pass rate. Section V-E can only
claim schema adherence (55/60 -> 60/60) and structural branch encoding
(0/9 -> 7/9). Grading these items is what would let the report state whether v3
actually recovers the L4 score, rather than only that the schema stopped
breaking.

Design decisions, both aimed at not flattering the result:

  1. The v2 output is hidden behind a toggle, collapsed by default. Grade the v3
     plan against the dataset rubric on its own terms first. Seeing "before and
     after" side by side invites scoring the improvement rather than the plan.
  2. Items are shuffled with a fixed seed (4445, matching the original grading
     sheet) so the order carries no signal.

Marking standard is the one already used for v2, restated on the page: Pass only
if the rubric is satisfied AND the executed behaviour matches the command's
intent; rubric satisfied but behaviour deviating scores Partial.
"""

import html
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
V2 = RESULTS / "20260801_151047_openai_gpt-4o-mini_v2.jsonl"
DATASET = ROOT / "dataset" / "commands.json"
SEED = 4445


def load(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def pretty(raw):
    try:
        return json.dumps(json.loads(raw), indent=2)
    except Exception:
        return raw or "(no output)"


def main():
    runs = sorted(RESULTS.glob("*_v3.jsonl"))
    if not runs:
        raise SystemExit("no v3 run found - see docs/report-outline.md section V-E")
    v3 = load(runs[-1])
    v2 = {r["id"]: r for r in load(V2) if r["trial"] == 0}
    dataset = {c["id"]: c for c in json.loads(DATASET.read_text(encoding="utf-8"))["commands"]}

    # One card per item; show trial 0, note whether all three trials agreed.
    items = []
    for iid in sorted({r["id"] for r in v3 if r["semantic"] == "manual"}):
        trials = sorted((r for r in v3 if r["id"] == iid), key=lambda r: r["trial"])
        t0 = trials[0]
        stable = len({t["raw"] for t in trials}) == 1
        v2rec = v2.get(iid)
        items.append({
            "id": iid,
            "command": t0["command"],
            "criteria": dataset.get(iid, {}).get("expected", {}).get("criteria", "—"),
            "v3": pretty(t0["raw"]),
            "v2": pretty(v2rec["raw"]) if v2rec else "(no v2 record)",
            "v2_schema_error": bool(v2rec and v2rec.get("schema_error")),
            "stable": stable,
            "n_trials": len(trials),
        })

    random.Random(SEED).shuffle(items)

    cards = []
    for i in items:
        warn = ""
        if i["v2_schema_error"]:
            warn = ('<p class="warn">⚠️ v2 failed schema validation on this item, so it was '
                    'never semantically graded. v3 makes it gradeable — this item has no v2 '
                    'counterpart score, so exclude it from any like-for-like comparison.</p>')
        stab = ("identical across all %d trials" % i["n_trials"]) if i["stable"] \
               else ("⚠️ output VARIED across %d trials — grade trial 0, note the instability" % i["n_trials"])
        cards.append(f"""
<article class="card" data-id="{i['id']}">
  <header><span class="id">{html.escape(i['id'])}</span>
          <span class="stab">{html.escape(stab)}</span></header>
  <p class="cmd">{html.escape(i['command'])}</p>
  {warn}
  <h4>Dataset rubric</h4>
  <p class="crit">{html.escape(i['criteria'])}</p>
  <h4>v3 output (trial 0)</h4>
  <pre>{html.escape(i['v3'])}</pre>
  <div class="score">
    <label><input type="radio" name="s-{i['id']}" value="pass"> Pass</label>
    <label><input type="radio" name="s-{i['id']}" value="partial"> Partial</label>
    <label><input type="radio" name="s-{i['id']}" value="fail"> Fail</label>
  </div>
  <label class="lbl" for="j-{i['id']}">Justification — why this score</label>
  <textarea id="j-{i['id']}" data-id="{i['id']}" rows="3"
            placeholder="One or two sentences you could say out loud in the viva."></textarea>
  <details><summary>Reveal v2 output for comparison (after scoring)</summary>
    <pre>{html.escape(i['v2'])}</pre></details>
</article>""")

    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>v3 Level-4 grading — PDE4445</title>
<style>
:root {{ --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
         --grid:#e1e0d9; --s1:#2a78d6; --s2:#eb6834; }}
* {{ box-sizing:border-box }}
body {{ margin:0; padding:24px; background:var(--surface); color:var(--ink);
        font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif }}
.wrap {{ max-width:1000px; margin:0 auto }}
h1 {{ font-size:19px; margin:0 0 4px }}
.sub {{ color:var(--muted); margin:0 0 14px }}
.standard {{ border-left:3px solid var(--s1); padding:10px 14px; background:#fff;
             margin:0 0 18px; border-radius:0 6px 6px 0 }}
.bar {{ position:sticky; top:0; background:var(--surface); border-bottom:1px solid var(--grid);
        padding:10px 0; margin-bottom:18px; display:flex; gap:14px; align-items:center;
        flex-wrap:wrap; z-index:5 }}
button {{ font:inherit; padding:6px 12px; border:1px solid var(--grid); border-radius:6px;
          background:#fff; cursor:pointer }}
button:hover {{ border-color:var(--s1); color:var(--s1) }}
#prog {{ font-weight:600 }}
.card {{ border:1px solid var(--grid); border-radius:8px; padding:16px; margin-bottom:16px;
         background:#fff }}
.card.done {{ border-left:3px solid var(--s1) }}
.card header {{ display:flex; gap:12px; align-items:baseline; margin-bottom:6px }}
.id {{ font-weight:700 }}
.stab {{ font-size:11.5px; color:var(--muted) }}
.cmd {{ font-size:15px; font-weight:600; margin:0 0 10px }}
.warn {{ background:#fff6f0; border:1px solid #f0d0bd; border-radius:6px; padding:8px 10px;
         font-size:12.5px; color:#7a3b18; margin:0 0 10px }}
h4 {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted);
      margin:12px 0 5px }}
.crit {{ margin:0 }}
pre {{ margin:0; padding:10px; background:var(--surface); border:1px solid var(--grid);
       border-radius:6px; font-size:11.5px; overflow-x:auto; max-height:320px }}
.score {{ display:flex; gap:18px; margin:14px 0 4px }}
.score label {{ cursor:pointer }}
.lbl {{ display:block; margin:10px 0 5px; font-size:11px; text-transform:uppercase;
        letter-spacing:.06em; color:var(--muted) }}
textarea {{ width:100%; font:inherit; padding:9px; border:1px solid var(--grid);
            border-radius:6px; resize:vertical; background:var(--surface) }}
textarea:focus {{ outline:2px solid var(--s1); outline-offset:-1px; background:#fff }}
details {{ margin-top:12px }}
summary {{ cursor:pointer; font-size:12px; color:var(--s2) }}
</style></head><body><div class="wrap">
<h1>v3 Level-4 grading — {len(items)} items</h1>
<p class="sub">Shuffled with seed {SEED}. The other 9 L4 items were scored automatically.</p>
<div class="standard">
  <strong>Marking standard</strong> (same as the v2 grading, keep it identical):
  <strong>Pass</strong> only if the rubric is satisfied <em>and</em> the executed behaviour
  matches the command's intent. Rubric satisfied but behaviour deviating → <strong>Partial</strong>,
  with the limitation recorded. Deliberately strict, so schema limitations surface as findings.
  <br><br>
  Grade the v3 plan on its own terms first. The v2 output is collapsed at the bottom of each
  card — open it only after you have scored, or you will be grading the improvement rather
  than the plan.
</div>
<div class="bar">
  <span id="prog"></span>
  <button id="next">Jump to next ungraded</button>
  <button id="exp">Export JSON</button>
  <span class="sub" style="margin:0">Serve over localhost — autosave fails on file://</span>
</div>
{''.join(cards)}
</div>
<script>
const KEY='pde4445-v3-grades';
const store=JSON.parse(localStorage.getItem(KEY)||'{{}}');
const cards=[...document.querySelectorAll('.card')];
function save(){{ localStorage.setItem(KEY,JSON.stringify(store)); paint(); }}
function paint(){{
  let done=0;
  cards.forEach(c=>{{
    const id=c.dataset.id, e=store[id]||{{}};
    const ok=!!e.score;
    if(ok) done++;
    c.classList.toggle('done',ok);
  }});
  document.getElementById('prog').textContent=`${{done}} / ${{cards.length}} graded`;
}}
cards.forEach(c=>{{
  const id=c.dataset.id;
  const e=store[id]||{{}};
  if(e.score){{ const r=c.querySelector(`input[value="${{e.score}}"]`); if(r) r.checked=true; }}
  const ta=c.querySelector('textarea');
  if(e.justification) ta.value=e.justification;
  c.querySelectorAll('input[type=radio]').forEach(r=>r.addEventListener('change',()=>{{
    store[id]=Object.assign({{}},store[id],{{score:r.value}}); save();
  }}));
  ta.addEventListener('input',()=>{{
    store[id]=Object.assign({{}},store[id],{{justification:ta.value}}); save();
  }});
}});
document.getElementById('next').onclick=()=>{{
  const c=cards.find(c=>!(store[c.dataset.id]||{{}}).score);
  if(c){{ c.scrollIntoView({{block:'center',behavior:'smooth'}}); }}
}};
document.getElementById('exp').onclick=()=>{{
  const out=cards.map(c=>({{id:c.dataset.id,
                           score:(store[c.dataset.id]||{{}}).score||null,
                           justification:(store[c.dataset.id]||{{}}).justification||''}}));
  const b=new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b); a.download='v3_l4_grades.json'; a.click();
}};
paint();
</script></body></html>"""

    out = RESULTS / "v3_grading_sheet.html"
    out.write_text(doc, encoding="utf-8")
    n_var = sum(1 for i in items if not i["stable"])
    n_warn = sum(1 for i in items if i["v2_schema_error"])
    print(f"wrote {out}")
    print(f"  {len(items)} items to grade; {n_var} varied across trials; "
          f"{n_warn} have no v2 counterpart score")


if __name__ == "__main__":
    main()
