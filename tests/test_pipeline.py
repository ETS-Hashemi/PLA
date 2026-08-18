"""E2: the feature->rule pipeline runs end to end on E1-format data and its
exported scenario loads in the engine."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_fraud_data as ffd  # noqa: E402

from pla.pipeline import (  # noqa: E402
    build_examples,
    fit_discretizer,
    generate_rule_specs,
    load_rows,
    propositionalize,
    run_pipeline,
)
from pla.scenario_loader import load_scenario  # noqa: E402


def make_sample(tmp_path, n=2000, seed=0):
    path = tmp_path / "sample.csv"
    ffd.generate_synthetic(n, seed=seed, destination=path)
    return path


def test_discretizer_and_propositions(tmp_path):
    path = make_sample(tmp_path, n=500)
    rows = load_rows(path)
    thresholds = fit_discretizer(rows)

    for feature, (low, high) in thresholds.items():
        assert low <= high, feature

    facts, context = propositionalize(rows[0], thresholds)
    assert all(p.endswith(("_high", "_low")) for p in facts)
    assert context <= {"Amount_high"}


def test_pipeline_end_to_end_produces_loadable_scenario(tmp_path):
    data = make_sample(tmp_path)
    scenario_path = tmp_path / "generated.json"
    result = run_pipeline(data, scenario_path)

    assert len(result["examples"]) == 2000
    assert len(result["rule_specs"]) >= 5
    # Empirical precisions are real numbers from the data.
    assert all(0.0 <= p <= 1.0 for p in result["precisions"])

    scenario = load_scenario(scenario_path)
    scenario.activate("1")
    prob, explanation = scenario.kb.query("Fraud")
    assert 0.0 <= prob <= 1.0
    assert explanation


def test_pipeline_is_deterministic(tmp_path):
    data = make_sample(tmp_path)
    first = run_pipeline(data)
    second = run_pipeline(data)
    assert [s.antecedents for s in first["rule_specs"]] == [
        s.antecedents for s in second["rule_specs"]
    ]
    assert first["precisions"] == second["precisions"]


def test_rules_beat_base_rate_on_average(tmp_path):
    # Selection by precision must produce rules more precise than chance.
    data = make_sample(tmp_path)
    result = run_pipeline(data)
    labels = [label for _, _, label in result["examples"]]
    base_rate = sum(labels) / len(labels)
    top_precision = max(result["precisions"])
    assert top_precision > base_rate
