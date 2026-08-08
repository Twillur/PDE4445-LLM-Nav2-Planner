# Recording the simulation demo

For the summary video (blog requirement) and the viva demo. **This only works on
the PC** — the WSL2/ROS2/Gazebo stack does not travel to the laptop, so record
the footage before you leave it.

Verified working 2026-08-07: Cyclone DDS active, domain 30, waffle model,
`nl_nav2_executor` resolves, `warehouse_sim.launch.py` present.

---

## The two things worth filming

**1. The v2-vs-v3 planner comparison — 30 seconds, no Gazebo needed.**
Same command, two schema versions, visibly different output. This is the whole
finding and it needs nothing but a terminal.

**2. The robot actually driving.** Gazebo running the five-waypoint patrol.
Slower to set up but it is the only footage that shows a robot.

Do (1) first. It is quick, it is the stronger evidence, and it does not depend
on the sim coming up cleanly.

---

## Recording

`setup/record-demo.ps1` wraps the Windows ffmpeg (already installed) using
gdigrab. Nothing to install in WSL.

```powershell
.\setup\record-demo.ps1                       # full desktop, Q to stop
.\setup\record-demo.ps1 -Window "Gazebo"      # just the Gazebo window
.\setup\record-demo.ps1 -Seconds 60 -Fps 24   # fixed length, smaller file
```

Output lands in `results/demo-footage/` as `sim_<timestamp>.mp4`.

⚠️ **`results/demo-footage/` is gitignored** — video does not belong in the
repo. Copy anything you want to keep somewhere that travels with you.

Ordinary screenshot tools render WSLg windows black (PrintWindow). gdigrab reads
the composited screen, which is why it works.

---

## Demo 1 — planner comparison (no simulation)

Start recording, then in a terminal:

```powershell
cd C:\Users\willi\source\repos\PDE4445-LLM-Nav2-Planner
$env:OPENAI_API_KEY = (Get-Content .env | Where-Object { $_ -match 'OPENAI_API_KEY=' } |
                       ForEach-Object { $_.Split('=',2)[1] })

$env:PROMPT_VERSION = "v2"
venv\Scripts\python src\planner.py "inspect storage zone A; if it's unreachable, inspect storage zone B instead"

$env:PROMPT_VERSION = "v3"; $env:SCHEMA_VERSION = "v3"
venv\Scripts\python src\planner.py "inspect storage zone A; if it's unreachable, inspect storage zone B instead"
```

v2 returns two steps and visits zone B every time. v3 returns one step with
`goto_fallback` + `fallback_target`. **Keep `$env:PROMPT_VERSION` visible in
frame** — it proves which version produced which output.

---

## Demo 2 — Gazebo

Everything must be sourced explicitly. `wsl.exe bash -c` does **not** read
`~/.bashrc`, which is what `setup/sim-env.sh` exists to solve.

**Terminal 1 — bring up the simulation:**

```bash
wsl -d Ubuntu-22.04
cd /mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner/ros2_ws
source ../setup/sim-env.sh
ros2 launch nl_nav2_executor warehouse_sim.launch.py
```

Give it a minute or two. Sourcing over `/mnt/c` is slow — a plain environment
check took over two minutes, so Gazebo coming up unhurriedly is normal, not a
failure.

**Terminal 2 — generate a plan and drive it:**

```bash
wsl -d Ubuntu-22.04
cd /mnt/c/Users/willi/source/repos/PDE4445-LLM-Nav2-Planner
source setup/sim-env.sh
ros2 run nl_nav2_executor execute_plan --plan results/last_plan.json --localization ground_truth
```

Use `"Patrol aisles 1 and 3, then return to base"` — it is the five-waypoint
plan already reported in §IV-D, so the footage matches the report.

### If it misbehaves

| Symptom | Cause | Fix |
|---|---|---|
| `ros2 topic list` empty while sim runs | stale daemon on the wrong RMW | `ros2 daemon stop`, or add `--no-daemon` |
| Discovery works, no data arrives | Fast DDS under WSL2 mirrored networking | `sim-env.sh` already forces Cyclone DDS — check `$RMW_IMPLEMENTATION` |
| Long goals abort mid-drive, recovery loops | un-composed Nav2 action handshake timeout | launch file already composes the stack; do not run nodes separately |
| Gazebo window is black in captures | PrintWindow cannot read WSLg | use `record-demo.ps1` (gdigrab), not a screenshot tool |

🔴 **Hardware:** the i9-14900KS is a degraded Raptor Lake part, stable only with
the 40x clock-ratio cap. Gazebo plus Nav2 is real sustained load. If the machine
hard-crashes or processes start segfaulting, stop — do not just relaunch — and
check the BIOS cap is still applied.

---

## Shot list for the summary video

Roughly three minutes, in this order:

1. **The problem** — a command in plain English, and what a waypoint GUI would demand instead
2. **The architecture** — `fig0_architecture.svg` on screen while you narrate the one-call design
3. **It works** — Gazebo, five-waypoint patrol, robot driving
4. **The finding** — `fig1_reliability_curve.svg`, the dip at L4
5. **Why** — the v2-vs-v3 terminal comparison from Demo 1
6. **Honesty** — one line on what is not shown: simulation only, plans graded rather than all executed

Record narration separately and lay it over the footage. Talking while driving a
demo produces worse versions of both.

---

## Known failure: map_server configures but never activates

Symptom: Gazebo is up, `lifecycle_manager_navigation` reports "Managed nodes are
active", but the robot never moves and the executor sits on
`Waiting for Nav2 (ground_truth) to become active...` indefinitely.

Check the launch log:

```
[global_costmap]: Can't update static costmap layer, no map received
```

`map_server` is managed by `lifecycle_manager_localization`, which is a
*different* manager from the navigation one. The script waits for
"Managed nodes are active" from the navigation manager, which can report ready
while `map_server` is still stuck at "Creating" and never publishes `/map`.
With no map the global costmap cannot plan, and `--localization ground_truth`
keys executor readiness off `map_server`, so both sides wait forever.

Observed on a second launch after several kill/relaunch cycles; the first launch
of a session worked correctly. Suspected stale lifecycle or daemon state rather
than configuration - the map file and paths were unchanged between runs.

**Not a hardware fault.** The launch log contained no "process has died", no
signal, no segfault and no core dump. Worth checking explicitly given the CPU
cap caveat, but this was not it.

If it happens: full teardown (`setup/_killsim.sh`), `ros2 daemon stop`, then a
single clean launch. Verify `/map` has a publisher before running the executor.
