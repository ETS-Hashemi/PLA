"""E4: the head-to-head experiment runs, includes both PLA variants, and is
byte-for-byte reproducible."""

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_fraud_data as ffd  # noqa: E402


def test_experiment_is_reproducible_and_includes_pla(tmp_path, monkeypatch):
    pytest.importorskip("sklearn")
    import run_experiments

    monkeypatch.setattr(run_experiments, "RESULTS_DIR", tmp_path)

    data = tmp_path / "sample.csv"
    ffd.generate_synthetic(800, seed=1, destination=data)

    results, csv_path, md_path = run_experiments.run(data, "t", fast=True)
    first_csv = csv_path.read_bytes()
    first_md = md_path.read_bytes()

    models = {row["model"] for row in results}
    assert {"pla_static", "pla_learned", "logistic_regression"} <= models
    for row in results:
        if row["model"].startswith("pla"):
            assert 0.5 < float(row["auc"]) <= 1.0  # real signal, not noise

    # From scratch again: identical bytes.
    results2, csv_path2, md_path2 = run_experiments.run(data, "t", fast=True)
    assert csv_path2.read_bytes() == first_csv
    assert md_path2.read_bytes() == first_md
    assert results2 is not results
