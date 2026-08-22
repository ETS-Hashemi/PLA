import json
import math
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "scenarios"

from pla.scenario_loader import load_scenario, ScenarioFormatError  # noqa: E402


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "pla.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_flat_scenario_context_actually_applies_via_cli():
    # Set 1: only PatientAge>60 active -> 0.7 * 1.2 = 0.84
    result = run_cli(str(SCENARIOS / "scenario_context_aware_medical.json"), "1")
    assert result.returncode == 0, result.stderr
    assert "Probability: 0.840" in result.stdout

    # Set 2: both variables active -> 0.7 * 1.2 * 1.5 = 1.26, capped at 1.0
    result = run_cli(str(SCENARIOS / "scenario_context_aware_medical.json"), "2")
    assert result.returncode == 0, result.stderr
    assert "Probability: 1.000" in result.stdout


def test_flat_scenario_context_via_loader():
    scenario = load_scenario(SCENARIOS / "scenario_context_aware_medical.json")

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
    scenario = load_scenario(SCENARIOS / "scenario_context_parallel.json")

    scenario.activate("1")  # rule 1 weight AgeOver60=1.2 -> 0.7*1.2
    prob, _ = scenario.kb.query("LungCancerRisk")
    assert math.isclose(prob, 0.84, abs_tol=1e-9)

    scenario.activate("2")  # rule 1 weight SmokingHistory=1.3 -> 0.7*1.3
    prob, _ = scenario.kb.query("LungCancerRisk")
    assert math.isclose(prob, 0.91, abs_tol=1e-9)


def test_nested_scenario_with_conflicting_per_set_weights_loads():
    # Same variable with different weights in different sets is legal in
    # the nested shape; each set resolves its own weight.
    scenario = load_scenario(SCENARIOS / "scenario_oncology_parallel.json")
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
    scenario = load_scenario(SCENARIOS / "scenario_context_aware_medical.json")
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


# --- "confidence" is the canonical rule-value key; "probability" is a
# --- deprecated alias (PLA values are confidences — docs/SEMANTICS.md).

def _write(tmp_path, rule):
    config = {"facts": ["A"], "rules": [rule], "queries": ["B"]}
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))
    return path


def test_confidence_key_is_canonical(tmp_path):
    path = _write(tmp_path, {"condition": ["A"], "result": "B",
                             "confidence": 0.5})
    prob, _ = load_scenario(path).kb.query("B")
    assert math.isclose(prob, 0.5, abs_tol=1e-9)


def test_legacy_probability_key_loads_identically(tmp_path):
    canonical = _write(tmp_path, {"condition": ["A"], "result": "B",
                                  "confidence": 0.5})
    legacy_path = tmp_path / "legacy.json"
    legacy_path.write_text(json.dumps(
        {"facts": ["A"],
         "rules": [{"condition": ["A"], "result": "B", "probability": 0.5}],
         "queries": ["B"]}))
    p_canonical, _ = load_scenario(canonical).kb.query("B")
    p_legacy, _ = load_scenario(legacy_path).kb.query("B")
    assert p_canonical == p_legacy


def test_conflicting_confidence_and_probability_keys_fail_loud(tmp_path):
    path = _write(tmp_path, {"condition": ["A"], "result": "B",
                             "confidence": 0.5, "probability": 0.6})
    with pytest.raises(ScenarioFormatError):
        load_scenario(path)


def test_missing_rule_value_fails_loud(tmp_path):
    path = _write(tmp_path, {"condition": ["A"], "result": "B"})
    with pytest.raises(ScenarioFormatError):
        load_scenario(path)


def test_probrule_confidence_property_aliases_probability():
    from pla.prob import ProbRule, ProbSymbol

    rule = ProbRule([ProbSymbol("A")], ProbSymbol("B"), 0.5)
    assert rule.confidence == rule.probability == 0.5
    rule.confidence = 0.7
    assert rule.probability == 0.7


def test_query_results_carry_confidence_key():
    from pla.prob import ProbKB, ProbRule, ProbSymbol

    kb = ProbKB()
    kb.add_fact(ProbSymbol("A"))
    kb.add_rule(ProbRule([ProbSymbol("A")], ProbSymbol("B"), 0.5))
    detailed = kb.query_detailed("B")
    assert detailed["confidence"] == detailed["probability"]
