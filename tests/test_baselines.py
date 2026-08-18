"""E3: the baselines script trains, evaluates, and emits a metrics CSV."""

import csv
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_fraud_data as ffd  # noqa: E402


def make_sample(tmp_path, n=1500, seed=3):
    path = tmp_path / "sample.csv"
    ffd.generate_synthetic(n, seed=seed, destination=path)
    return path


def test_sklearn_baselines_emit_metrics_csv(tmp_path):
    pytest.importorskip("sklearn")
    import run_baselines

    data = make_sample(tmp_path)
    out = tmp_path / "metrics.csv"
    results = run_baselines.run_all(data, out, fast=True)

    with open(out, newline="") as handle:
        rows = list(csv.DictReader(handle))
    models = {row["model"] for row in rows}
    assert {"logistic_regression", "gradient_boosting"} <= models

    for row in rows:
        assert row["note"] == ""  # nothing skipped in fast mode
        auc = float(row["auc"])
        # The synthetic data has planted logistic structure: real signal.
        assert 0.7 < auc <= 1.0, row
        assert 0.0 <= float(row["brier"]) <= 0.3
        assert int(row["n_train"]) + int(row["n_test"]) == 1500
    assert results


def test_problog_scoring_matches_noisy_or_closed_form():
    pytest.importorskip("problog")
    from pla.learn import RuleSpec
    import run_baselines

    specs = [RuleSpec(("V17_high",)), RuleSpec(("V17_high", "V20_low"))]
    precisions = [0.279, 0.722]
    prob = run_baselines.problog_probability(
        specs, precisions, {"V17_high", "V20_low"}
    )
    # Independent ProbLog rules combine exactly like PLA's noisy-OR.
    assert math.isclose(prob, 1 - (1 - 0.279) * (1 - 0.722), abs_tol=1e-6)

    # No firing rule -> no support.
    assert run_baselines.problog_probability(specs, precisions, {"V1_low"}) == 0.0
