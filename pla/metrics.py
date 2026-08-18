"""Calibration and discrimination metrics. Pure Python, no deps.

Everything the Phase 5 experiments report: Brier score, log-loss, a
reliability (calibration) summary with expected calibration error, and
rank-based ROC AUC.
"""

import math


def _validate(y_true, y_prob):
    if len(y_true) != len(y_prob):
        raise ValueError(
            f"length mismatch: {len(y_true)} labels vs {len(y_prob)} probabilities"
        )
    if not y_true:
        raise ValueError("empty input")
    for y in y_true:
        if y not in (0, 1):
            raise ValueError(f"labels must be 0 or 1, got {y!r}")
    for p in y_prob:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"probabilities must be in [0, 1], got {p!r}")


def brier_score(y_true, y_prob):
    """Mean squared error between probabilities and outcomes. Lower is better."""
    _validate(y_true, y_prob)
    return sum((p - y) ** 2 for y, p in zip(y_true, y_prob)) / len(y_true)


def log_loss(y_true, y_prob, epsilon=1e-15):
    """Mean binary cross-entropy, with probabilities clipped away from 0/1."""
    _validate(y_true, y_prob)
    total = 0.0
    for y, p in zip(y_true, y_prob):
        p = min(max(p, epsilon), 1.0 - epsilon)
        total += -(y * math.log(p) + (1 - y) * math.log(1.0 - p))
    return total / len(y_true)


def reliability_summary(y_true, y_prob, n_bins=10):
    """Equal-width reliability table plus expected calibration error.

    Returns {"bins": [...], "ece": float}. Each bin entry reports its
    half-open interval [lo, hi) (the last bin includes 1.0), the number of
    predictions in it, the mean predicted probability, and the observed
    positive frequency. ECE is the count-weighted mean absolute gap
    between mean prediction and observed frequency.
    """
    _validate(y_true, y_prob)
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")

    binned = [[] for _ in range(n_bins)]
    for y, p in zip(y_true, y_prob):
        index = min(int(p * n_bins), n_bins - 1)  # p == 1.0 -> last bin
        binned[index].append((y, p))

    bins = []
    ece = 0.0
    n = len(y_true)
    for index, members in enumerate(binned):
        entry = {
            "lo": index / n_bins,
            "hi": (index + 1) / n_bins,
            "count": len(members),
            "mean_predicted": None,
            "observed_frequency": None,
        }
        if members:
            mean_pred = sum(p for _, p in members) / len(members)
            observed = sum(y for y, _ in members) / len(members)
            entry["mean_predicted"] = mean_pred
            entry["observed_frequency"] = observed
            ece += (len(members) / n) * abs(mean_pred - observed)
        bins.append(entry)

    return {"bins": bins, "ece": ece}


def roc_auc(y_true, y_prob):
    """Rank-based AUC (Mann-Whitney): P(score(pos) > score(neg)), ties 0.5.

    Requires at least one positive and one negative label.
    """
    _validate(y_true, y_prob)
    positives = [p for y, p in zip(y_true, y_prob) if y == 1]
    negatives = [p for y, p in zip(y_true, y_prob) if y == 0]
    if not positives or not negatives:
        raise ValueError("roc_auc needs both classes present")

    wins = 0.0
    for pos in positives:
        for neg in negatives:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def average_precision(y_true, y_prob):
    """Area under the precision-recall curve, step-wise (no interpolation):
    AP = sum_k (R_k - R_{k-1}) * P_k over descending unique scores, ties
    grouped — the same estimator as scikit-learn's average_precision_score.

    Requires at least one positive and one negative label.
    """
    _validate(y_true, y_prob)
    pairs = sorted(zip(y_prob, y_true), key=lambda item: -item[0])
    total_positives = sum(y for _, y in pairs)
    if total_positives == 0 or total_positives == len(pairs):
        raise ValueError("average_precision needs both classes present")

    ap = 0.0
    true_positives = seen = 0
    previous_recall = 0.0
    index, n = 0, len(pairs)
    while index < n:
        threshold = pairs[index][0]
        while index < n and pairs[index][0] == threshold:
            true_positives += pairs[index][1]
            seen += 1
            index += 1
        recall = true_positives / total_positives
        precision = true_positives / seen
        ap += (recall - previous_recall) * precision
        previous_recall = recall
    return ap
