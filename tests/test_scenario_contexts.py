import json
import math
import pathlib
import subprocess
import sys

import pytest

PLA_DIR = pathlib.Path(__file__).resolve().parents[1] / "PLA-advanced"
sys.path.append(str(PLA_DIR))

from scenario_loader import load_scenario, ScenarioFormatError  # noqa: E402


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=PLA_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_flat_scenario_context_actually_applies_via_cli():
    # Set 1: only PatientAge>60 active -> 0.7 * 1.2 = 0.84
    result = run_cli("scenario_context_aware_medical.json", "1")
    assert result.returncode == 0, result.stderr
    assert "Probability: 0.840" in result.stdout

    # Set 2: both variables active -> 0.7 * 1.2 * 1.5 = 1.26, capped at 1.0
    result = run_cli("scenario_context_aware_medical.json", "2")
    assert result.returncode == 0, result.stderr
    assert "Probability: 1.000" in result.stdout


def test_flat_scenario_context_via_loader():
    scenario = load_scenario(PLA_DIR / "scenario_context_aware_medical.json")

    scenario.activate("1")
    prob, _ = scenario.kb.query("LungCancerRisk")
    assert math.isclose(prob, 0.84, abs_tol=1e-9)

    scenario.activate("2")
    prob, _ = scenario.kb.query("LungCancerRisk")
    assert math.isclose(prob, 1.0, abs_tol=1e-9)


def test_flat_scenario_without_contexts_defaults_to_all_active(tmp_path):
    config = {
        "facts": ["A"],
        "rules": [
            {"condition": ["A"], "result": "B", "probability": 0.5,
             "context": {"V": 1.4}}
        ],
        "queries": ["B"],
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))

    scenario = load_scenario(path)
    assert scenario.context_sets == {"1": ["V"]}
    scenario.activate("1")
    prob, _ = scenario.kb.query("B")
    assert math.isclose(prob, 0.7, abs_tol=1e-9)


def test_nested_legacy_scenario_resolves_per_set_weights():
    scenario = load_scenario(PLA_DIR / "scenario_context_parallel.json")

    scenario.activate("1")  # rule 1 weight AgeOver60=1.2 -> 0.7*1.2
    prob, _ = scenario.kb.query("LungCancerRisk")
    assert math.isclose(prob, 0.84, abs_tol=1e-9)

    scenario.activate("2")  # rule 1 weight SmokingHistory=1.3 -> 0.7*1.3
    prob, _ = scenario.kb.query("LungCancerRisk")
    assert math.isclose(prob, 0.91, abs_tol=1e-9)


def test_nested_scenario_with_conflicting_per_set_weights_loads():
    # Same variable with different weights in different sets is legal in
    # the nested shape; each set resolves its own weight.
    scenario = load_scenario(PLA_DIR / "scenario_oncology_parallel.json")
    scenario.activate("1")
    scenario.activate("2")


def test_malformed_context_raises(tmp_path):
    config = {
        "facts": ["A"],
        "rules": [
            {"condition": ["A"], "result": "B", "probability": 0.5,
             "context": {"V": "high"}}
        ],
        "queries": ["B"],
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))

    with pytest.raises(ScenarioFormatError):
        load_scenario(path)


def test_mixed_context_shapes_in_one_rule_raise(tmp_path):
    config = {
        "facts": ["A"],
        "rules": [
            {"condition": ["A"], "result": "B", "probability": 0.5,
             "context": {"V": 1.2, "1": {"W": 1.1}}}
        ],
        "queries": ["B"],
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))

    with pytest.raises(ScenarioFormatError):
        load_scenario(path)


def test_unknown_context_set_raises():
    scenario = load_scenario(PLA_DIR / "scenario_context_aware_medical.json")
    with pytest.raises(ScenarioFormatError) as excinfo:
        scenario.activate("99")
    assert "available sets" in str(excinfo.value)


def test_contexts_section_with_undeclared_variable_raises(tmp_path):
    config = {
        "facts": ["A"],
        "rules": [
            {"condition": ["A"], "result": "B", "probability": 0.5,
             "context": {"V": 1.2}}
        ],
        "queries": ["B"],
        "contexts": {"1": ["Typo"]},
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))

    with pytest.raises(ScenarioFormatError) as excinfo:
        load_scenario(path)
    assert "Typo" in str(excinfo.value)
