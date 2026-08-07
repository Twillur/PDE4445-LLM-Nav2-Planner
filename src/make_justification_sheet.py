"""Build the grade-justification sheet for viva preparation.

    python src/make_justification_sheet.py
    cd results && python -m http.server 8765     # then open localhost:8765

Writes results/justification_sheet.html — one card per hand-graded L4/L5 item,
pairing the command, the dataset rubric and the model's actual raw output with
the score that was awarded, and a box to record *why*.

The 27 grades were awarded without written notes, so the reasoning currently
exists only in a chat transcript. In a viva the examiner can point at any single
item and ask why it scored what it scored; this exists so that answer is
written down beforehand.

Serve over localhost rather than opening via file:// — Chrome's localStorage is
unreliable on file:// and the autosave will silently do nothing.
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
V2 = RESULTS / "20260801_151047_openai_gpt-4o-mini_v2.jsonl"
GRADES = RESULTS / "l45_grades.json"
DATASET = ROOT / "dataset" / "commands.json"

# Why each grade is contestable - the angle an examiner is most likely to take.
# Keyed by score; shown as a prompt, not an answer.
CHALLENGE = {
    "pass": "Why is this a full pass rather than partial? What would it have had "
            "to get wrong to lose marks?",
    "partial": "Why partial and not fail? What exactly was preserved, and what was "
               "lost? Is the loss caused by the schema or by the model?",
    "fail": "Why fail rather than partial? Was anything salvageable in the output?",
}


def main():
    grades = json.loads(GRADES.read_text(encoding="utf-8"))
    dataset = {c["id"]: c for c in json.loads(DATASET.read_text(encoding="utf-8"))["commands"]}
    runs = {}
    for line in V2.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["trial"] == 0:
            runs[r["id"]] = r

    items = []
    for g in sorted(grades, key=lambda g: g["id"]):
        rec = runs.get(g["id"], {})
        raw = rec.get("raw") or ""
        try:
            raw = json.dumps(json.loads(raw), indent=2)
        except Exception:
            pass
        items.append({
            "id": g["id"], "level": g["level"], "score": g["score"],
            "command": g["command"],
            "criteria": dataset.get(g["id"], {}).get("expected", {}).get("criteria", "—"),
            "raw": raw,
            "challenge": CHALLENGE.get(g["score"], ""),
        })

    n_by = {}
    for i in items:
        n_by[i["score"]] = n_by.get(i["score"], 0) + 1
    summary = " · ".join(f"{v} {k}" for k, v in sorted(n_by.items()))

    cards = []
    for i in items:
        cards.append(f"""
<article class="card" data-score="{i['score']}">
  <header>
    <span class="id">{html.escape(i['id'])}</span>
    <span class="lvl">L{i['level']}</span>
    <span class="score s-{i['score']}">{i['score']}</span>
  </header>
  <p class="cmd">{html.escape(i['command'])}</p>
  <div class="grid">
    <section>
      <h4>Dataset rubric</h4>
      <p class="crit">{html.escape(i['criteria'])}</p>
      <h4>Likely challenge</h4>
      <p class="chal">{html.escape(i['challenge'])}</p>
    </section>
    <section>
      <h4>Model output (v2, trial 0)</h4>
      <pre>{html.escape(i['raw'])}</pre>
    </section>
  </div>
  <label for="j-{i['id']}">Justification — why this score</label>
  <textarea id="j-{i['id']}" data-id="{i['id']}" rows="4"
            placeholder="One or two sentences you could say out loud in the viva."></textarea>
</article>""")

    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grade justifications — PDE4445 viva prep</title>
<style>
:root {{ --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
         --grid:#e1e0d9; --s1:#2a78d6; --s2:#eb6834; }}
* {{ box-sizing:border-box }}
body {{ margin:0; padding:24px; background:var(--surface); color:var(--ink);
        font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
.wrap {{ max-width:1080px; margin:0 auto }}
h1 {{ font-size:19px; margin:0 0 4px }}
.sub {{ color:var(--muted); margin:0 0 18px }}
.bar {{ position:sticky; top:0; background:var(--surface); border-bottom:1px solid var(--grid);
        padding:10px 0; margin-bottom:18px; display:flex; gap:14px; align-items:center;
        flex-wrap:wrap; z-index:5 }}
button {{ font:inherit; padding:6px 12px; border:1px solid var(--grid); border-radius:6px;
          background:#fff; cursor:pointer }}
button:hover {{ border-color:var(--s1); color:var(--s1) }}
#prog {{ font-weight:600 }}
.card {{ border:1px solid var(--grid); border-radius:8px; padding:16px; margin-bottom:16px;
         background:#fff }}
.card header {{ display:flex; gap:10px; align-items:center; margin-bottom:8px }}
.id {{ font-weight:700 }}
.lvl {{ color:var(--muted); font-size:12px }}
.score {{ margin-left:auto; font-size:12px; font-weight:700; padding:2px 10px;
          border-radius:99px; text-transform:uppercase; letter-spacing:.04em }}
.s-pass {{ background:#184f95; color:#fff }}
.s-partial {{ background:#3987e5; color:#fff }}
.s-fail {{ background:#86b6ef; color:var(--ink) }}
.cmd {{ font-size:15px; font-weight:600; margin:0 0 12px }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px }}
@media (max-width:820px) {{ .grid {{ grid-template-columns:1fr }} }}
h4 {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted);
      margin:0 0 5px }}
.crit {{ margin:0 0 12px }}
.chal {{ margin:0; color:var(--s2) }}
pre {{ margin:0; padding:10px; background:var(--surface); border:1px solid var(--grid);
       border-radius:6px; font-size:11.5px; overflow-x:auto; max-height:280px }}
label {{ display:block; margin:14px 0 5px; font-size:11px; text-transform:uppercase;
         letter-spacing:.06em; color:var(--muted) }}
textarea {{ width:100%; font:inherit; padding:9px; border:1px solid var(--grid);
            border-radius:6px; resize:vertical; background:var(--surface) }}
textarea:focus {{ outline:2px solid var(--s1); outline-offset:-1px; background:#fff }}
.card.done {{ border-left:3px solid var(--s1) }}
</style></head><body><div class="wrap">
<h1>Grade justifications — {len(items)} hand-graded items</h1>
<p class="sub">{summary}. Written for the viva: the examiner can point at any one of
these and ask why it scored what it scored. Autosaves locally as you type.</p>
<div class="bar">
  <span id="prog"></span>
  <button id="next">Jump to next unwritten</button>
  <button id="exp">Export JSON</button>
  <span class="sub" style="margin:0">Serve over localhost — autosave fails on file://</span>
</div>
{''.join(cards)}
</div>
<script>
const KEY='pde4445-justifications';
const store=JSON.parse(localStorage.getItem(KEY)||'{{}}');
const tas=[...document.querySelectorAll('textarea')];
function paint(){{
  let done=0;
  tas.forEach(t=>{{
    const filled=t.value.trim().length>0;
    if(filled) done++;
    t.closest('.card').classList.toggle('done',filled);
  }});
  document.getElementById('prog').textContent=`${{done}} / ${{tas.length}} written`;
}}
tas.forEach(t=>{{
  if(store[t.dataset.id]) t.value=store[t.dataset.id];
  t.addEventListener('input',()=>{{
    store[t.dataset.id]=t.value;
    localStorage.setItem(KEY,JSON.stringify(store));
    paint();
  }});
}});
document.getElementById('next').onclick=()=>{{
  const t=tas.find(t=>!t.value.trim());
  if(t){{ t.scrollIntoView({{block:'center',behavior:'smooth'}}); t.focus(); }}
}};
document.getElementById('exp').onclick=()=>{{
  const out=tas.map(t=>({{id:t.dataset.id,justification:t.value.trim()}}));
  const b=new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b); a.download='l45_justifications.json'; a.click();
}};
paint();
</script></body></html>"""

    out = RESULTS / "justification_sheet.html"
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {out}  ({len(items)} items: {summary})")


if __name__ == "__main__":
    main()
