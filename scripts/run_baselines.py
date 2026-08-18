"""Train and evaluate baselines on E1-format data; emit a metrics CSV.

Baselines:
- logistic_regression, gradient_boosting (scikit-learn) on raw numeric
  features V1..V28 + Amount;
- problog (if installed): the E2 candidate rules with their empirical
  precisions run as a ProbLog program per example (independent rules =
  noisy-OR), on a deterministic test subsample for speed;
- pgmpy_naive_bayes (if installed): Bernoulli naive Bayes over the E2
  propositions.

Rows that cannot run (missing package, API failure) are recorded in the
CSV with a "skipped:" note instead of crashing the run. Metrics: ROC AUC,
Brier, log-loss, ECE (pla.metrics).

Usage:
    python scripts/run_baselines.py --data data/creditcard_synthetic_seed0.csv \
        --out data/baseline_metrics.csv
"""

import argparse
import csv
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pla.metrics import brier_score, log_loss, reliability_summary, roc_auc  # noqa: E402
from pla.pipeline import (  # noqa: E402
    FEATURES,
    build_examples,
    fit_discretizer,
    generate_rule_specs,
    load_rows,
)

SLOW_SUBSAMPLE = 150  # per-example ProbLog compilation is ~0.1s each


def split_rows(rows, test_fraction=0.3, seed=42):
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    cut = int(len(rows) * (1 - test_fraction))
    return [rows[i] for i in order[:cut]], [rows[i] for i in order[cut:]]


def labels_of(rows):
    return [1 if r["Class"].strip() in ("1", "1.0") else 0 for r in rows]


def numeric_matrix(rows):
    return [[float(r[f]) for f in FEATURES + ["Amount"]] for r in rows]


def evaluate(name, y_true, y_prob, note=""):
    return {
        "model": name,
        "n_test": len(y_true),
        "auc": round(roc_auc(y_true, y_prob), 4),
        "brier": round(brier_score(y_true, y_prob), 4),
        "log_loss": round(log_loss(y_true, y_prob), 4),
        "ece": round(reliability_summary(y_true, y_prob)["ece"], 4),
        "note": note,
    }


def skipped(name, reason):
    return {"model": name, "n_test": 0, "auc": "", "brier": "", "log_loss": "",
            "ece": "", "note": f"skipped: {reason}"}


def sklearn_rows(train_rows, test_rows):
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
    except ImportError as err:
        return [skipped("logistic_regression", err), skipped("gradient_boosting", err)]

    X_train, X_test = numeric_matrix(train_rows), numeric_matrix(test_rows)
    y_train, y_test = labels_of(train_rows), labels_of(test_rows)

    rows = []
    for name, model in [
        ("logistic_regression", LogisticRegression(max_iter=2000)),
        ("gradient_boosting", HistGradientBoostingClassifier(random_state=0)),
    ]:
        model.fit(X_train, y_train)
        probs = [float(p[1]) for p in model.predict_proba(X_test)]
        rows.append(evaluate(name, y_test, probs))
    return rows


def problog_probability(rule_specs, precisions, facts):
    """Score one example with ProbLog: independent rules over given facts."""
    from problog import get_evaluatable
    from problog.program import PrologString

    lines = []
    body_atoms = set()
    for spec, precision in zip(rule_specs, precisions):
        if precision <= 0.0:
            continue
        body_atoms.update(a.lower() for a in spec.antecedents)
        body = ", ".join(a.lower() for a in spec.antecedents)
        lines.append(f"{min(precision, 0.999999):.6f}::fraud :- {body}.")
    present = {fact.lower() for fact in facts}
    lines.extend(f"{atom}." for atom in sorted(present & body_atoms))
    # ProbLog rejects undefined atoms: declare absent ones as 0-probability.
    lines.extend(f"0.0::{atom}." for atom in sorted(body_atoms - present))
    lines.append("query(fraud).")
    result = get_evaluatable().create_from(PrologString("\n".join(lines))).evaluate()
    return next((v for k, v in result.items() if str(k) == "fraud"), 0.0)


def problog_row(rule_specs, precisions, test_examples, limit=SLOW_SUBSAMPLE):
    try:
        import problog  # noqa: F401
    except ImportError as err:
        return skipped("problog_rules", err)
    try:
        subset = test_examples[:limit]
        y_true = [label for _, _, label in subset]
        y_prob = [
            problog_probability(rule_specs, precisions, facts)
            for facts, _, _ in subset
        ]
        return evaluate("problog_rules", y_true, y_prob, note=f"subset n={len(subset)}")
    except Exception as err:  # noqa: BLE001 — record, don't crash the run
        return skipped("problog_rules", err)


def pgmpy_row(train_examples, test_examples, propositions):
    try:
        import pandas as pd
        try:
            from pgmpy.models import DiscreteBayesianNetwork as Network
        except ImportError:
            from pgmpy.models import BayesianNetwork as Network
    except ImportError as err:
        return skipped("pgmpy_naive_bayes", err)

    try:
        def frame(examples):
            return pd.DataFrame(
                [
                    {**{p: int(p in facts) for p in propositions}, "Class": label}
                    for facts, _, label in examples
                ]
            )

        train_df = frame(train_examples)
        test_df = frame(test_examples)
        model = Network([("Class", p) for p in propositions])
        model.fit(train_df)  # default estimator: maximum likelihood
        posterior = model.predict_probability(test_df.drop(columns=["Class"]))
        column = "Class_1" if "Class_1" in posterior.columns else posterior.columns[-1]
        y_prob = [float(v) for v in posterior[column]]
        y_true = [label for _, _, label in test_examples]
        return evaluate("pgmpy_naive_bayes", y_true, y_prob)
    except Exception as err:  # noqa: BLE001 — record, don't crash the run
        return skipped("pgmpy_naive_bayes", err)


def run_all(data_path, out_path, fast=False):
    rows = load_rows(data_path)
    train_rows, test_rows = split_rows(rows)

    thresholds = fit_discretizer(train_rows)  # thresholds from training data only
    train_examples = build_examples(train_rows, thresholds)
    test_examples = build_examples(test_rows, thresholds)
    rule_specs, precisions = generate_rule_specs(train_examples)

    results = sklearn_rows(train_rows, test_rows)
    if not fast:
        results.append(problog_row(rule_specs, precisions, test_examples))
        propositions = sorted({a for spec in rule_specs for a in spec.antecedents})
        results.append(pgmpy_row(train_examples, test_examples, propositions))

    for row in results:
        row["n_train"] = len(train_rows)

    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["model", "n_train", "n_test", "auc", "brier", "log_loss", "ece", "note"]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fast", action="store_true",
                        help="sklearn baselines only (used by tests)")
    args = parser.parse_args()

    results = run_all(args.data, args.out, fast=args.fast)
    for row in results:
        print(row)
    print(f"metrics written to {args.out}")


if __name__ == "__main__":
    main()
