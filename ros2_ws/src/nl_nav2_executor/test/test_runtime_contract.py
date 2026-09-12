"""Runtime regression tests; no model calls and no historical score changes."""

import copy
import importlib.util
import json
import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from jsonschema import Draft7Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nl_nav2_executor.mock_navigator import MockNavigator
from nl_nav2_executor.plan_runner import run_plan
from nl_nav2_executor.plan_validation import PlanValidationError, validate_plan, _SCHEMA
from nl_nav2_executor.semantic_map import Point, SemanticMap

ROOT = Path(__file__).resolve().parents[4]
MAP = SemanticMap({"charging_dock": Point(0, 0), "a": Point(1, 1), "b": Point(2, 2)})


def plan_for(*steps):
    return {"understood": True, "plan": list(steps)}


def fallback_plan():
    return plan_for({"action": "navigate", "target": "a",
                     "on_blocked": "goto_fallback", "fallback_target": "b"})


class RecordingNavigator(MockNavigator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attempts = []

    def navigate_to(self, name, point):
        self.attempts.append(name)
        return super().navigate_to(name, point)


@pytest.mark.parametrize("blocked, attempts, visited, outcome, code", [
    (set(), ["a"], ["a"], "reached", 0),
    ({"a"}, ["a", "b"], ["b"], "fallback_reached", 0),
    ({"a", "b"}, ["a", "b"], [], "failed", 1),
])
def test_fallback_is_conditional_and_bounded(blocked, attempts, visited, outcome, code):
    nav = RecordingNavigator(blocked=blocked)
    plan = fallback_plan()
    before = copy.deepcopy(plan)
    result = run_plan(plan, MAP, nav)
    assert nav.attempts == attempts
    assert nav.visited == visited
    assert result.steps[0].outcome == outcome
    assert result.exit_code == code
    assert result.reached_count == (1 if outcome == "reached" else 0)
    assert result.fallback_count == (1 if outcome == "fallback_reached" else 0)
    assert plan == before


@pytest.mark.parametrize("blocked", [{"a"}, {"a", "b"}])
def test_fallback_then_remaining_plan(blocked):
    plan = fallback_plan()
    plan["plan"].append({"action": "navigate", "target": "charging_dock"})
    nav = RecordingNavigator(blocked=blocked)
    result = run_plan(plan, MAP, nav)
    assert nav.attempts == ["a", "b", "charging_dock"]
    assert result.exit_code == (1 if "b" in blocked else 0)


@pytest.mark.parametrize("bad_step", [
    {"action": "fly", "target": "a"},
    {"action": "navigate"},
    {"action": "navigate", "target": "invented"},
    {"action": "navigate", "target": ["a"]},
    {"action": "navigate", "target": "a", "on_blocked": "try_b"},
    {"action": "navigate", "target": "a", "x": 12, "y": 3},
    {"action": "navigate", "target": "a", "on_blocked": "goto_fallback"},
    {"action": "navigate", "target": "a", "on_blocked": "goto_fallback", "fallback_target": "invented"},
    {"action": "navigate", "target": "a", "on_blocked": "goto_fallback", "fallback_target": "a"},
    {"action": "navigate", "target": "a", "fallback_target": "b"},
    {"action": "wait"},
    {"action": "wait", "duration_s": -1},
    {"action": "wait", "duration_s": True},
    {"action": "wait", "duration_s": float("nan")},
    {"action": "wait", "duration_s": float("inf")},
    {"action": "wait", "duration_s": 10 ** 400},
    {"action": "wait", "duration_s": 1, "target": "a"},
    {"action": "wait", "duration_s": 1, "on_blocked": "abort"},
])
def test_invalid_later_step_prevents_all_movement(bad_step):
    nav = RecordingNavigator()
    plan = plan_for({"action": "navigate", "target": "a"}, bad_step)
    with pytest.raises(PlanValidationError):
        run_plan(plan, MAP, nav)
    assert nav.attempts == []
    assert nav.waits == []


@pytest.mark.parametrize("bad_plan", [
    None, [], {}, {"understood": "false", "plan": []},
    {"understood": True, "plan": []},
    {"understood": False, "plan": []},
    {"understood": False, "plan": [], "clarification_question": "   "},
    {"understood": False, "plan": [{"action": "navigate", "target": "a"}],
     "clarification_question": "Which place?"},
])
def test_invalid_envelope(bad_plan):
    nav = RecordingNavigator()
    with pytest.raises(PlanValidationError):
        run_plan(bad_plan, MAP, nav)
    assert nav.attempts == []


def test_fallback_validated_even_when_primary_would_succeed():
    plan = fallback_plan()
    plan["plan"][0]["fallback_target"] = "invented"
    nav = RecordingNavigator()
    with pytest.raises(PlanValidationError, match="unknown fallback_target"):
        run_plan(plan, MAP, nav)
    assert not nav.attempts


def test_bad_map_coordinates_rejected_before_motion():
    smap = SemanticMap({"a": Point(float("nan"), 0), "b": Point(1, 2)})
    with pytest.raises(PlanValidationError, match="non-finite"):
        validate_plan(fallback_plan(), smap)


def test_reroute_requires_perimeter_points():
    with pytest.raises(PlanValidationError, match="perimeter"):
        validate_plan(plan_for({"action": "navigate", "target": "a",
                                "on_blocked": "reroute_perimeter"}), MAP)


@pytest.mark.parametrize("contingency", [None, "skip", "abort", "wait_retry"])
def test_unreached_goal_is_not_reported_as_success(contingency):
    nav = RecordingNavigator(blocked={"a"})
    result = run_plan(plan_for({"action": "navigate", "target": "a",
                                "on_blocked": contingency}), MAP, nav)
    assert result.exit_code == 1
    assert "COMPLETED:" not in result.summary()


def test_explicit_zero_retry_delay_is_respected():
    nav = RecordingNavigator(blocked={"a"})
    run_plan(plan_for({"action": "navigate", "target": "a",
                       "on_blocked": "wait_retry", "duration_s": 0}), MAP, nav)
    assert nav.waits == [0]
    assert nav.attempts == ["a", "a"]


def test_clarification_is_valid_but_does_not_execute():
    plan = {"understood": False, "plan": [], "clarification_question": "Which aisle?"}
    nav = RecordingNavigator()
    result = run_plan(plan, MAP, nav)
    assert not result.executed and not nav.attempts
    assert result.exit_code == 1


def test_wait_only_plan_can_complete():
    nav = RecordingNavigator()
    result = run_plan(plan_for({"action": "wait", "duration_s": 0}), MAP, nav)
    assert nav.waits == [0] and result.exit_code == 0


def test_runtime_schema_is_valid():
    Draft7Validator.check_schema(_SCHEMA)


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("valid", [True, False])
def test_pipeline_gates_output_before_writing(monkeypatch, tmp_path, valid, capsys):
    pipeline = load_script("runtime_pipeline_test", ROOT / "src" / "run_pipeline.py")
    plan = plan_for({"action": "navigate", "target": "loading_dock" if valid else "invented"})
    calls = []

    def fake_plan(command):
        calls.append(command)
        return {"plan": plan, "raw": json.dumps(plan)}

    monkeypatch.setitem(sys.modules, "planner", SimpleNamespace(
        MODEL="stub", PROVIDER="stub", plan_command=fake_plan))
    monkeypatch.setattr(pipeline, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    out = tmp_path / "plan.json"
    out.write_text("existing output", encoding="utf-8")
    assert pipeline.main(["Go to the loading dock", "--out", str(out)]) == (0 if valid else 2)
    assert calls == ["Go to the loading dock"]
    output = capsys.readouterr()
    if valid:
        assert json.loads(out.read_text()) == plan
        assert "Execute it" in output.out
    else:
        assert out.read_text() == "existing output"
        assert "Execute it" not in output.out
        assert "Plan rejected" in output.err


@pytest.fixture
def executor_entrypoint(monkeypatch):
    """Fake ROS transport only; execute the actual CLI and plan runner."""
    ros = SimpleNamespace(init=Mock(), shutdown=Mock())
    parameter = Mock()
    parameter.Type.BOOL = 1
    modules = {
        "rclpy": ros,
        "rclpy.parameter": SimpleNamespace(Parameter=parameter),
        "geometry_msgs.msg": SimpleNamespace(PoseStamped=Mock()),
        "nav2_simple_commander.robot_navigator": SimpleNamespace(
            BasicNavigator=Mock(), TaskResult=SimpleNamespace(SUCCEEDED=1)),
    }
    for name, value in modules.items():
        monkeypatch.setitem(sys.modules, name, value)
    module = load_script("nl_nav2_executor._entrypoint_test",
                         ROOT / "ros2_ws/src/nl_nav2_executor/nl_nav2_executor/executor_node.py")
    client = Mock()
    module.BasicNavigator.return_value = client
    return module, ros, client


def save_cli_inputs(tmp_path, plan):
    plan_path = tmp_path / "plan.json"
    map_path = tmp_path / "map.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    map_path.write_text(json.dumps({"locations": {
        name: {"x": p.x, "y": p.y} for name, p in MAP.locations.items()
    }}), encoding="utf-8")
    return ["--plan", str(plan_path), "--map", str(map_path)]


@pytest.mark.parametrize("kind", ["invalid", "clarification", "invalid-start"])
def test_executor_rejects_before_ros_initialization(executor_entrypoint, tmp_path, kind):
    module, ros, client = executor_entrypoint
    if kind == "clarification":
        plan = {"understood": False, "plan": [], "clarification_question": "Which place?"}
    else:
        plan = plan_for({"action": "navigate", "target": "invented" if kind == "invalid" else "a"})
    args = save_cli_inputs(tmp_path, plan)
    if kind == "invalid-start":
        args += ["--start", "invented"]
    assert module.main(args) == (1 if kind == "clarification" else 2)
    ros.init.assert_not_called()
    module.BasicNavigator.assert_not_called()


@pytest.mark.parametrize("blocked, code", [(set(), 0), ({"a"}, 0), ({"a", "b"}, 1)])
def test_executor_exit_status_and_client_cleanup(executor_entrypoint, monkeypatch, tmp_path, blocked, code):
    module, ros, client = executor_entrypoint
    nav = RecordingNavigator(blocked=blocked)
    monkeypatch.setattr(module, "Nav2Navigator", lambda client, start: nav)
    assert module.main(save_cli_inputs(tmp_path, fallback_plan())) == code
    client.waitUntilNav2Active.assert_called_once_with(localizer="map_server")
    client.destroy_node.assert_called_once()
    client.lifecycleShutdown.assert_not_called()
    ros.shutdown.assert_called_once()


def test_executor_cleans_up_client_when_navigation_raises(executor_entrypoint, monkeypatch, tmp_path):
    module, ros, client = executor_entrypoint
    nav = RecordingNavigator()
    nav.navigate_to = Mock(side_effect=RuntimeError("transport lost"))
    monkeypatch.setattr(module, "Nav2Navigator", lambda client, start: nav)
    with pytest.raises(RuntimeError, match="transport lost"):
        module.main(save_cli_inputs(tmp_path, fallback_plan()))
    client.destroy_node.assert_called_once()
    ros.shutdown.assert_called_once()


@pytest.mark.parametrize("blocked, code", [("", 0), ("a", 0), ("a,b", 1)])
def test_dry_run_cli_status(tmp_path, blocked, code):
    args = save_cli_inputs(tmp_path, fallback_plan())
    proc = subprocess.run([sys.executable, str(ROOT / "ros2_ws/src/nl_nav2_executor/scripts/dry_run.py"),
                           *args, "--blocked", blocked], capture_output=True, text=True)
    assert proc.returncode == code, proc.stderr
    if blocked == "a":
        assert "1 fallback destinations reached instead" in proc.stdout
        assert "visited: ['b']" in proc.stdout


def test_dry_run_invalid_json_is_input_failure(tmp_path):
    args = save_cli_inputs(tmp_path, fallback_plan())
    (tmp_path / "plan.json").write_text("{broken", encoding="utf-8")
    proc = subprocess.run([sys.executable, str(ROOT / "ros2_ws/src/nl_nav2_executor/scripts/dry_run.py"),
                           *args], capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Plan rejected" in proc.stderr
    assert "visited:" not in proc.stdout
