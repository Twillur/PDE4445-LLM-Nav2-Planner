# Presentation asset catalogue

Open [the portfolio](index.html) in a browser for previews and an interactive route replay. Files work locally without a build service or external JavaScript libraries. The GitHub README embeds static figures directly.

## Figures

Every figure is available in `assets/` as PNG (slides), SVG (editable vector), and PDF (print). Build with [build-portfolio-figures.py](../../setup/build-portfolio-figures.py). The plots use Matplotlib and actual saved records or geometry, not image generation.

| Filename stem | What it shows | Provenance / limitation |
|---|---|---|
| `semantic-map` | All 20 names and warehouse geometry | `map/warehouse_map.json`, SDF collision boxes; two names share the southwest position |
| `recorded-routes` | Direct, east-wall, and multi-step trajectories | Recorded September odometry from `gazebo-20260911T213643Z`; pre-fix executor |
| `reliability` | Strict outcomes across L1–L5 | Mixed record/item denominators are explicitly separated; original grades unchanged |
| `prompt-comparison` | v1→v2 on L1–L3 | August JSONL records; 3-trial means |
| `latency` | v2 planner-call timing distribution | 300 saved calls; not mission duration |
| `architecture` | Current corrected execution pipeline | September runtime implementation; not a diagram of the historical evaluation code |
| `fallback` | Representation and execution cases | Saved L4-12 and controlled software checks; not full v3 semantic evaluation |
| `hardware-architecture` | Proposed physical interfaces | Unbuilt concept, not an electrical schematic or purchased robot |

The interactive replay uses `assets/routes.json` and the same data embedded in `assets/route-data.js` so opening the HTML directly does not require a server. Playback is at eight times stored simulation time. It shows recorded positions, not a live simulation.

## Genuine simulation media

- `media/warehouse-overview.png`: complete Gazebo window, actual warehouse at the charging-dock start.
- `media/warehouse-goal.png`: same window at the end of the loading-dock run.
- `media/warehouse-navigation.mp4`: H.264, 1440×960, 130 frames at 15 fps; 8.67-second time-compressed sequence. Capture intervals include screenshot overhead, so no exact wall-time speed-up factor is claimed. There is no audio.
- `media/warehouse-navigation.vtt`: text description of the silent clip.
- `media/navigation-log.txt`: executor output for the filmed run, reported 1/1 reached. This capture did not record a new odometry bag.
- `media/robot-detail.png`: static close view inside the warehouse. No navigation is executed for that close-up.

Overview and video source: `docs/validation/portfolio-capture-20260912T094720Z`. Robot close-up source: `docs/validation/portfolio-capture-20260912T095914Z`; an earlier obstructed view is retained in `portfolio-capture-20260912T095144Z` but not used in the gallery. The generated capture worlds add only a GUI camera to the original SDF; physics and obstacle geometry remain unchanged. Camera/launch copies and hashes are retained. [Capture script](../../setup/capture-portfolio.sh) uses an isolated X display and captures the Gazebo window, not the Windows desktop. Raw frame sequences and ROS logs are local intermediates and excluded from Git.

## Hardware references

`media/hardware/` contains public vendor-page screenshots and a [timestamped source manifest](media/hardware/sources.json). Product photographs, branding and page content belong to ROBOTIS, Seeed Studio, DFRobot and Adafruit respectively; they are attributed comparison references, not project-built hardware. Keep that attribution if reusing them in slides. Do not present them as photographs of the dissertation robot.

Listed costs are recorded in [hardware-costs.csv](hardware-costs.csv), with source URLs and date. Compare the [hardware page](hardware.html) for exclusions and estimates. No purchases were made.

## Report and bundle

The eight-page [report PDF](../../report/revised/main.pdf) is a draft snapshot. It predates the later runtime corrections; include [review notes](../../report/revised/REVIEW_NOTES.md) when sharing it. `media/presentation-pack.zip` collects the eight figure families, original simulation screenshots, video, report snapshot and these notes. Vendor-page screenshots remain separately attributed in the repository.

Suggested slide sequence: typed-command question → architecture → warehouse map → reliability with denominators → fallback failure mechanism → recorded routes and simulation clip → limitations and next validation step. Proposed hardware belongs after the completed study, as future work.

## Local preview and publishing

Open `docs/portfolio/index.html` directly, or serve the repository root with `python -m http.server 8765 --bind 127.0.0.1` and visit `/docs/portfolio/`. Use [reproduction instructions](reproduce.html) for the robot software.

The repository's manually triggered Pages workflow is prepared for later publication. No GitHub push, Pages configuration or deployment was performed as part of preparing these files. The existing dissertation journal is a separate repository and was not changed.
