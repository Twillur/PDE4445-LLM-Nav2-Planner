# ros2_ws — Nav2 execution half

Turns a validated LLM waypoint plan into robot motion. The planner (repo root)
produces a JSON plan of **named** locations; this workspace resolves those names
to metric poses and drives a TurtleBot3 through them in a Gazebo warehouse using
Nav2, honouring each step's `on_blocked` contingency.

## Package: `nl_nav2_executor`

| Path | What |
|---|---|
| `nl_nav2_executor/semantic_map.py` | Load the semantic map; resolve names → poses; perimeter routing. Pure Python. |
| `nl_nav2_executor/plan_runner.py` | The execution logic: step sequencing + `on_blocked` handling (abort / skip / reroute_perimeter / wait_retry). ROS-free, so it is unit-tested and reused by both the sim and the mock. |
| `nl_nav2_executor/executor_node.py` | ROS2 node: wraps `nav2_simple_commander.BasicNavigator` and runs `plan_runner`. Entry point `execute_plan`. |
| `nl_nav2_executor/mock_navigator.py` | In-memory navigator for tests / dry-runs (no ROS). |
| `scripts/gen_warehouse_assets.py` | Regenerates the occupancy map + Gazebo world from one geometry description (keeps them aligned). |
| `scripts/dry_run.py` | Execute a plan against the real map without Gazebo; `--blocked` to test contingencies. |
| `launch/warehouse_sim.launch.py` | Gazebo warehouse + TB3 at the charging dock + full Nav2. |
| `maps/`, `worlds/`, `params/` | Generated occupancy grid, matching Gazebo world, vendored Nav2 params. |
| `test/test_plan_runner.py` | Unit tests for the execution logic (no sim needed). |

## Build

```bash
# in WSL2 Ubuntu-22.04, ROS2 Humble sourced (see repo CLAUDE.md for the CycloneDDS env)
cd ros2_ws
colcon build --packages-select nl_nav2_executor --symlink-install
source install/setup.bash
```

## Run the simulation

```bash
export TURTLEBOT3_MODEL=waffle
ros2 launch nl_nav2_executor warehouse_sim.launch.py            # add gui:=false for headless
```

Wait until Nav2 reports active, then in a second sourced terminal:

```bash
# from an English command, all the way to the robot moving:
python ../src/run_pipeline.py "Patrol aisles 1 and 3, then return to base"
ros2 run nl_nav2_executor execute_plan --plan ../results/last_plan.json
```

## Test without Gazebo

```bash
python -m pytest ros2_ws/src/nl_nav2_executor/test -q
python ros2_ws/src/nl_nav2_executor/scripts/dry_run.py --plan results/last_plan.json --blocked aisle_2_south
```

## The warehouse

20 × 20 m floor, four north-south shelf rows leaving three traversable aisles
centred on x = 6, 9, 12 — matching `map/warehouse_map.json`. The map frame and
the Gazebo world share the same origin (SW corner), so a named location's map
pose is its physical pose. The robot starts at the charging dock (1, 1).
