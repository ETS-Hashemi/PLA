"""Unit tests for calibration metrics against hand-computed values."""

import math

import pytest

from pla.metrics import (
    average_precision,
    brier_score,
    log_loss,
    reliability_summary,
    roc_auc,
)


def test_brier_score_hand_computed():
    # ((0.8-1)^2 + (0.4-0)^2) / 2 = (0.04 + 0.16) / 2 = 0.10
    assert math.isclose(brier_score([1, 0], [0.8, 0.4]), 0.10, abs_tol=1e-12)
    assert brier_score([1, 0], [1.0, 0.0]) == 0.0  # perfect


def test_log_loss_hand_computed():
    expected = -(math.log(0.8) + math.log(0.6)) / 2
    assert math.isclose(log_loss([1, 0], [0.8, 0.4]), expected, abs_tol=1e-12)
    assert log_loss([1, 0], [1.0, 0.0]) < 1e-12  # perfect, clipped


def test_reliability_summary_hand_computed():
    y = [1, 0, 1, 1]
    p = [0.95, 0.05, 0.65, 0.75]
    result = reliability_summary(y, p, n_bins=10)

    bin0 = result["bins"][0]  # [0.0, 0.1): the 0.05 prediction
    assert bin0["count"] == 1
    assert math.isclose(bin0["mean_predicted"], 0.05, abs_tol=1e-12)
    assert bin0["observed_frequency"] == 0.0

    bin6 = result["bins"][6]  # [0.6, 0.7): the 0.65 prediction, label 1
    assert bin6["count"] == 1
    assert bin6["observed_frequency"] == 1.0

    # ECE = (1/4)(|0.05-0| + |0.65-1| + |0.75-1| + |0.95-1|) = 0.175
    assert math.isclose(result["ece"], 0.175, abs_tol=1e-12)

    empty_bins = [b for b in result["bins"] if b["count"] == 0]
    assert all(b["mean_predicted"] is None for b in empty_bins)


def test_reliability_p_equal_one_lands_in_last_bin():
    result = reliability_summary([1], [1.0], n_bins=10)
    assert result["bins"][9]["count"] == 1


def test_roc_auc_hand_computed():
    # pairs: (0.9,0.1)+ (0.9,0.8)+ (0.7,0.1)+ (0.7,0.8)- -> 3/4
    assert math.isclose(roc_auc([1, 0, 0, 1], [0.9, 0.1, 0.8, 0.7]), 0.75, abs_tol=1e-12)
    # tie -> half credit
    assert roc_auc([1, 0], [0.5, 0.5]) == 0.5
    # perfect separation
    assert roc_auc([1, 1, 0], [0.9, 0.8, 0.2]) == 1.0


def test_average_precision_hand_computed():
    # Descending: 0.9(+) P=1 R=1/2 -> +0.5*1; 0.8(-); 0.7(+) P=2/3 R=1 -> +0.5*2/3
    assert math.isclose(
        average_precision([1, 0, 1], [0.9, 0.8, 0.7]), 0.5 + 0.5 * (2 / 3),
        abs_tol=1e-12,
    )
    # Perfect ranking puts every positive first: AP = 1.
    assert average_precision([1, 1, 0], [0.9, 0.8, 0.2]) == 1.0
    # Ties are grouped into one block: both examples land at the single
    # threshold 0.5 with P=1/2, R=1 -> AP = 1/2.
    assert average_precision([1, 0], [0.5, 0.5]) == 0.5


def test_average_precision_matches_sklearn():
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    import random

    rng = random.Random(11)
    y = [rng.random() < 0.3 and 1 or 0 for _ in range(400)]
    y[0], y[1] = 1, 0  # both classes guaranteed
    p = [round(rng.random(), 3) for _ in y]  # rounding forces score ties
    assert math.isclose(
        average_precision(y, p),
        float(sklearn_metrics.average_precision_score(y, p)),
        abs_tol=1e-12,
    )


def test_validation_errors():
    with pytest.raises(ValueError):
        brier_score([1, 0], [0.5])
    with pytest.raises(ValueError):
        log_loss([], [])
    with pytest.raises(ValueError):
        brier_score([2], [0.5])
    with pytest.raises(ValueError):
        log_loss([1], [1.5])
    with pytest.raises(ValueError):
        roc_auc([1, 1], [0.5, 0.6])  # one class only
    with pytest.raises(ValueError):
        reliability_summary([1], [0.5], n_bins=0)
