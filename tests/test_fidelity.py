"""E5: fidelity metrics — hand-computed values and discrimination."""

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_fraud_data as ffd  # noqa: E402

from pla.fidelity import (  # noqa: E402
    evaluate_fidelity,
    reversed_attributions,
    static_attributions,
)
from pla.learn import RuleSpec  # noqa: E402
from pla.pipeline import noisy_or_probability  # noqa: E402


SPECS = [RuleSpec(("A",)), RuleSpec(("B",))]
PRECISIONS = [0.8, 0.3]


def predict(facts, _context):
    return noisy_or_probability(SPECS, PRECISIONS, facts)


def test_fidelity_hand_computed():
    examples = [(frozenset({"A", "B"}), frozenset(), 1)]
    attributions = static_attributions(SPECS, PRECISIONS)

    metrics = evaluate_fidelity(predict, attributions, examples)
    p_full = 1 - (1 - 0.8) * (1 - 0.3)  # 0.86
    assert metrics["n_explained"] == 1
    # Top rule is A (0.8). Deleting A leaves only B: p = 0.3.
    assert math.isclose(metrics["comprehensiveness"], p_full - 0.3, abs_tol=1e-12)
    # Keeping only A: p = 0.8.
    assert math.isclose(metrics["sufficiency"], p_full - 0.8, abs_tol=1e-12)


def test_single_rule_example_is_fully_explained():
    examples = [(frozenset({"A"}), frozenset(), 1)]
    attributions = static_attributions(SPECS, PRECISIONS)
    metrics = evaluate_fidelity(predict, attributions, examples)
    assert math.isclose(metrics["comprehensiveness"], 0.8, abs_tol=1e-12)
    assert math.isclose(metrics["sufficiency"], 0.0, abs_tol=1e-12)


def test_examples_with_no_fired_rules_are_excluded():
    examples = [(frozenset({"C"}), frozenset(), 0)]
    attributions = static_attributions(SPECS, PRECISIONS)
    metrics = evaluate_fidelity(predict, attributions, examples)
    assert metrics["n_explained"] == 0
    assert metrics["comprehensiveness"] is None


def test_faithful_ranking_beats_reversed_control(tmp_path):
    """On pipeline data, the trace ranking must out-score a wrong ranking."""
    from pla.pipeline import build_examples, fit_discretizer, generate_rule_specs, load_rows

    data = tmp_path / "sample.csv"
    ffd.generate_synthetic(1500, seed=5, destination=data)
    rows = load_rows(data)
    thresholds = fit_discretizer(rows)
    examples = build_examples(rows, thresholds)
    specs, precisions = generate_rule_specs(examples)

    def model(facts, _context):
        return noisy_or_probability(specs, precisions, facts)

    attributions = static_attributions(specs, precisions)
    faithful = evaluate_fidelity(model, attributions, examples)
    control = evaluate_fidelity(model, reversed_attributions(attributions), examples)

    assert faithful["n_explained"] == control["n_explained"] > 100
    assert faithful["comprehensiveness"] > control["comprehensiveness"]
