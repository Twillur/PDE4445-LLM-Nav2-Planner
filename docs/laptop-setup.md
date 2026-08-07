# Working on this project from another machine

Written so the project can move to a laptop and keep going — the PC does not
travel to Dubai. Follow top to bottom on a clean machine.

---

## What lives where

| | Where | Travels? |
|---|---|---|
| Planner + report + figures + eval data | GitHub `PDE4445-LLM-Nav2-Planner` | ✅ `git clone` |
| Blog source | GitHub `PDE4445-Robotics-Dissertation` | ✅ `git clone` |
| ROS2/WSL2 setup scripts + Cyclone DDS config | `setup/` in this repo | ✅ now versioned |
| Python deps | `requirements.txt` | ✅ recreate the venv |
| **`OPENAI_API_KEY`** | `.env`, **gitignored** | ❌ **carry separately — never commit** |
| Claude memory + `CLAUDE.md` | local only | ⚠️ see §4 |
| WSL2 + ROS2 + Gazebo install | the PC | ❌ does not transfer, see §5 |

---

## 1. Clone both repos

```bash
git clone https://github.com/Twillur/PDE4445-LLM-Nav2-Planner.git
git clone https://github.com/Twillur/PDE4445-Robotics-Dissertation.git
```

Everything assessed is in these two: the full report draft (`docs/report-outline.md`),
the bibliography, all five figures, the raw evaluation JSONL, the 27 grades and their
justifications, the viva question bank, and every blog post.

## 2. Recreate the Python environment

```bash
cd PDE4445-LLM-Nav2-Planner
python -m venv venv                 # Python 3.12 on the PC; 3.11+ is fine
venv\Scripts\python -m pip install -r requirements.txt
```

Four dependencies: `openai`, `anthropic`, `jsonschema`, `python-dotenv`.

## 3. The API key

`.env` is gitignored and **must stay that way** — it holds `OPENAI_API_KEY`, and this is
a public assessed repo. Carry the key in a password manager, then on the laptop:

```
# .env in the repo root, one line
OPENAI_API_KEY=sk-...
```

`src/planner.py` does **not** call `load_dotenv`, so load it into the shell first:

```powershell
$env:OPENAI_API_KEY = (Get-Content .env | Where-Object { $_ -match 'OPENAI_API_KEY=' } |
                       ForEach-Object { $_.Split('=',2)[1] })
```

Without the key you can still do everything except make new LLM calls — all recorded
results are committed, so figures, grading and the whole write-up work offline.

## 4. Claude's context (memory + `CLAUDE.md`)

These are **not** in either repo and would be lost with the PC:

- `C:\Users\willi\.claude\projects\C--Users-willi\memory\` — 11 files
- `C:\Users\willi\CLAUDE.md` — project instructions

They contain personal material (job applications, interviews, hardware notes), so they
must **not** go in this public repo. Put them in a **private** repo instead:

```bash
gh auth login                                    # once, interactive
mkdir claude-context && cd claude-context
cp -r "C:/Users/willi/.claude/projects/C--Users-willi/memory" .
cp "C:/Users/willi/CLAUDE.md" .
git init && git add -A && git commit -m "Claude context snapshot"
gh repo create claude-context --private --source=. --push
```

On the laptop, clone it and copy the two paths back into place. Re-push whenever the
context changes materially — it is a snapshot, not a live sync.

## 5. What does NOT transfer: WSL2 + ROS2 + Gazebo

The simulation stack is a full WSL2 Ubuntu 22.04 install with ROS2 Humble, Gazebo
Classic 11, Nav2 and TurtleBot3. Rebuilding it takes hours, and `setup/` now holds the
scripts and configs to do it:

| File | Purpose |
|---|---|
| `setup/install-ros2.sh` | full install |
| `setup/setup-user.sh` | WSL user creation |
| `setup/cyclonedds-wsl.xml` | 🔴 **the critical one** — loopback-pinned Cyclone DDS |
| `setup/fastdds-wsl-unicast.xml` | Fast DDS attempt, kept as a negative result |
| `setup/dds-diag.sh` | middleware diagnostics |
| `setup/warehouse/` | world, launch file, mapping route |

**You almost certainly do not need this on the laptop.** Everything outstanding — the
report, the blog posts, the abstract, the viva prep — is writing against data that is
already committed. Rebuild the sim only if you decide to record the v2-vs-v3 Gazebo
demo, and budget most of a day for it.

Non-negotiable if you do rebuild: `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` plus
`CYCLONEDDS_URI` pointing at `cyclonedds-wsl.xml`. Fast DDS completes discovery under
WSL2 mirrored networking and then silently delivers nothing.

## 6. Verify the laptop is actually working

```bash
venv\Scripts\python src\make_figures.py        # prints the five per-level rates
venv\Scripts\python src\compare_v3.py          # v2 vs v3 comparison
```

`make_figures.py` should print:

```
L1: strict  96.7%   with partial credit  96.7%
L2: strict  95.0%   with partial credit  95.0%
L3: strict  95.0%   with partial credit  95.0%
L4: strict  55.0%   with partial credit  70.0%
L5: strict  85.0%   with partial credit  92.5%
```

Those numbers matching is proof the whole data path survived the move. Neither script
needs an API key or ROS2.

Serve the interactive sheets over localhost — `file://` breaks their autosave:

```bash
cd results && python -m http.server 8765
# justification_sheet.html · grading_sheet.html · figures_preview.html
```

## 7. Two-machine discipline

Both repos were edited from two directions in one evening and content was silently
destroyed four times. With a second machine the risk goes up, not down.

- **`git pull` before you start.** Every session, both repos.
- **`git commit && git push` before you stop.** Never leave work only on one machine.
- **After a wholesale section rewrite, run `git diff --stat`.** If more lines vanished
  than you meant to touch, something adjacent got eaten. That single check would have
  caught all four incidents.
- Don't edit the same file in an editor while a tool is writing to it.
