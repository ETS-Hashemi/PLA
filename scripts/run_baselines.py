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
CSV with a "skipped:" note instead of crashing the run. Metrics: ROC AUC
and average precision (both with seeded bootstrap 95% CIs), Brier,
log-loss, ECE (pla.metrics).

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

from pla.metrics import (  # noqa: E402
    average_precision,
    brier_score,
    log_loss,
    reliability_summary,
    roc_auc,
)
from pla.pipeline import (  # noqa: E402
    CREDITCARD,
    build_examples,
    fit_discretizer,
    generate_rule_specs,
    load_rows,
    noisy_or_probability,
)

SLOW_SUBSAMPLE = 150  # per-example ProbLog compilation is ~0.1s each


def split_rows(rows, test_fraction=0.3, seed=42):
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    cut = int(len(rows) * (1 - test_fraction))
    return [rows[i] for i in order[:cut]], [rows[i] for i in order[cut:]]


def parseable_rows(rows, schema):
    """Complete-case filter: keep rows whose numeric columns all parse, so
    every model sees the same population."""
    kept = []
    for record in rows:
        try:
            for column in schema.numeric_columns:
                float(record[column])
        except ValueError:
            continue
        kept.append(record)
    return kept


def labels_of(rows, schema=CREDITCARD):
    return [1 if r[schema.label].strip() in ("1", "1.0") else 0 for r in rows]


def numeric_matrix(rows, schema=CREDITCARD):
    return [[float(r[f]) for f in schema.numeric_columns] for r in rows]


def _bootstrap_cis(y_true, y_prob, n_bootstrap=500, seed=7):
    """Seeded percentile-bootstrap 95% CIs for ROC AUC and average
    precision, from one shared set of resamples. Needs numpy+sklearn;
    returns four "" when unavailable or every resample is single-class."""
    try:
        import numpy as np
        from sklearn.metrics import average_precision_score, roc_auc_score
    except ImportError:
        return "", "", "", ""
    y = np.asarray(y_true)
    p = np.asarray(y_prob)
    rng = np.random.Generator(np.random.PCG64(seed))
    auc_scores, ap_scores = [], []
    for _ in range(n_bootstrap):
        index = rng.integers(0, len(y), len(y))
        if y[index].min() == y[index].max():
            continue
        auc_scores.append(roc_auc_score(y[index], p[index]))
        ap_scores.append(average_precision_score(y[index], p[index]))
    if not auc_scores:
        return "", "", "", ""
    auc_lo, auc_hi = np.percentile(auc_scores, [2.5, 97.5])
    ap_lo, ap_hi = np.percentile(ap_scores, [2.5, 97.5])
    return (f"{auc_lo:.4f}", f"{auc_hi:.4f}", f"{ap_lo:.4f}", f"{ap_hi:.4f}")


def paired_metric_diffs(y_true, probs_a, probs_b, n_bootstrap=500, seed=7):
    """Paired-bootstrap 95% CIs for metric DIFFERENCES between two models
    scored on the same test set (resample example indices once; evaluate
    both models on each resample; difference the metrics). This is the
    inference that supports "no reliable difference" claims — overlapping
    individual CIs are not. Returns {} without numpy/sklearn."""
    try:
        import numpy as np
        from sklearn.metrics import average_precision_score, roc_auc_score
    except ImportError:
        return {}
    y = np.asarray(y_true)
    a = np.asarray(probs_a)
    b = np.asarray(probs_b)
    auc_diff = roc_auc(y_true, probs_a) - roc_auc(y_true, probs_b)
    ap_diff = average_precision(y_true, probs_a) - average_precision(y_true, probs_b)
    rng = np.random.Generator(np.random.PCG64(seed))
    auc_diffs, ap_diffs = [], []
    for _ in range(n_bootstrap):
        index = rng.integers(0, len(y), len(y))
        if y[index].min() == y[index].max():
            continue
        auc_diffs.append(roc_auc_score(y[index], a[index])
                         - roc_auc_score(y[index], b[index]))
        ap_diffs.append(average_precision_score(y[index], a[index])
                        - average_precision_score(y[index], b[index]))
    if not auc_diffs:
        return {}
    auc_lo, auc_hi = np.percentile(auc_diffs, [2.5, 97.5])
    ap_lo, ap_hi = np.percentile(ap_diffs, [2.5, 97.5])
    return {
        "auc_diff": f"{auc_diff:.4f}", "auc_diff_lo": f"{auc_lo:.4f}",
        "auc_diff_hi": f"{auc_hi:.4f}",
        "ap_diff": f"{ap_diff:.4f}", "ap_diff_lo": f"{ap_lo:.4f}",
        "ap_diff_hi": f"{ap_hi:.4f}",
    }


def constant_prevalence_row(train_labels, test_labels):
    """Skill baseline: predict the training prevalence for every example.
    Its log-loss is the marginal-entropy floor any calibration claim must
    beat; its AP is the prevalence; its AUC is 0.5 by the tie rule."""
    prevalence = sum(train_labels) / len(train_labels)
    probs = [prevalence] * len(test_labels)
    return evaluate("constant_prevalence", test_labels, probs,
                    note=f"predicts training prevalence {prevalence:.6f} everywhere")


def evaluate(name, y_true, y_prob, note=""):
    auc_lo, auc_hi, ap_lo, ap_hi = _bootstrap_cis(y_true, y_prob)
    return {
        "model": name,
        "n_test": len(y_true),
        "auc": f"{roc_auc(y_true, y_prob):.4f}",
        "auc_lo": auc_lo,
        "auc_hi": auc_hi,
        "ap": f"{average_precision(y_true, y_prob):.4f}",
        "ap_lo": ap_lo,
        "ap_hi": ap_hi,
        "brier": f"{brier_score(y_true, y_prob):.4f}",
        "log_loss": f"{log_loss(y_true, y_prob):.4f}",
        "ece": f"{reliability_summary(y_true, y_prob)['ece']:.4f}",
        "note": note,
    }


def skipped(name, reason):
    return {"model": name, "n_test": 0, "auc": "", "auc_lo": "", "auc_hi": "",
            "ap": "", "ap_lo": "", "ap_hi": "",
            "brier": "", "log_loss": "", "ece": "", "note": f"skipped: {reason}"}


def sklearn_rows(train_rows, test_rows, schema=CREDITCARD):
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier
    except ImportError as err:
        return [skipped(name, err) for name in
                ("logistic_regression", "gradient_boosting", "decision_tree")]

    X_train, X_test = numeric_matrix(train_rows, schema), numeric_matrix(test_rows, schema)
    y_train, y_test = labels_of(train_rows, schema), labels_of(test_rows, schema)

    models = [
        ("logistic_regression", LogisticRegression(max_iter=2000), ""),
        ("gradient_boosting", HistGradientBoostingClassifier(random_state=0), ""),
        ("gradient_boosting_balanced", HistGradientBoostingClassifier(
            random_state=0, class_weight="balanced"),
         "class_weight=balanced, otherwise defaults"),
        ("decision_tree", DecisionTreeClassifier(
            max_depth=4, class_weight="balanced", random_state=0),
         "interpretable baseline: depth 4, balanced"),
    ]

    rows = []
    for name, model, note in models:
        model.fit(X_train, y_train)
        probs = [float(p[1]) for p in model.predict_proba(X_test)]
        rows.append(evaluate(name, y_test, probs, note=note))

    try:
        from interpret.glassbox import ExplainableBoostingClassifier
        ebm = ExplainableBoostingClassifier(random_state=0)
        ebm.fit(X_train, y_train)
        probs = [float(p[1]) for p in ebm.predict_proba(X_test)]
        rows.append(evaluate("ebm_interpretml", y_test, probs,
                             note="interpretable baseline: EBM defaults"))
    except ImportError as err:
        rows.append(skipped("ebm_interpretml", err))
    except Exception as err:  # noqa: BLE001 — record, don't crash the run
        rows.append(skipped("ebm_interpretml", err))
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
        # On heavily imbalanced data a head subsample can miss the positive
        # class entirely (AUC undefined); deterministically add the first
        # positives from the full test set and rebalance the head.
        if not any(label for _, _, label in subset):
            positives = [e for e in test_examples if e[2] == 1][: max(10, limit // 10)]
            subset = positives + [e for e in test_examples if e[2] == 0][: limit - len(positives)]
        y_true = [label for _, _, label in subset]
        y_prob = [
            problog_probability(rule_specs, precisions, facts)
            for facts, _, _ in subset
        ]
        # Direct same-example agreement with PLA's own noisy-OR fold —
        # the semantics cross-check is this number, not any interval.
        max_gap = max(
            abs(prob - noisy_or_probability(rule_specs, precisions, facts))
            for prob, (facts, _, _) in zip(y_prob, subset)
        )
        return evaluate("problog_rules", y_true, y_prob,
                        note=f"subset n={len(subset)}; "
                             f"max |PLA-ProbLog| = {max_gap:.1e}")
    except Exception as err:  # noqa: BLE001 — record, don't crash the run
        return skipped("problog_rules", err)


def pgmpy_row(train_examples, test_examples, propositions, limit=2000):
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

        note = ""
        if len(test_examples) > limit:
            test_examples = test_examples[:limit]  # deterministic head, like problog
            note = f"subset n={limit}"

        train_df = frame(train_examples)
        test_df = frame(test_examples)
        model = Network([("Class", p) for p in propositions])
        model.fit(train_df)  # default estimator: maximum likelihood
        posterior = model.predict_probability(test_df.drop(columns=["Class"]))
        column = "Class_1" if "Class_1" in posterior.columns else posterior.columns[-1]
        y_prob = [float(v) for v in posterior[column]]
        y_true = [label for _, _, label in test_examples]
        return evaluate("pgmpy_naive_bayes", y_true, y_prob, note=note)
    except Exception as err:  # noqa: BLE001 — record, don't crash the run
        return skipped("pgmpy_naive_bayes", err)


def run_all(data_path, out_path, fast=False, schema=CREDITCARD):
    rows = parseable_rows(load_rows(data_path), schema)
    train_rows, test_rows = split_rows(rows)

    thresholds = fit_discretizer(train_rows, schema=schema)  # train data only
    train_examples = build_examples(train_rows, thresholds, schema=schema)
    test_examples = build_examples(test_rows, thresholds, schema=schema)
    context_vars = schema.all_context_vars
    rule_specs, precisions = generate_rule_specs(train_examples, context_vars=context_vars)

    results = sklearn_rows(train_rows, test_rows, schema)
    if not fast:
        results.append(problog_row(rule_specs, precisions, test_examples))
        propositions = sorted({a for spec in rule_specs for a in spec.antecedents})
        results.append(pgmpy_row(train_examples, test_examples, propositions))

    for row in results:
        row["n_train"] = len(train_rows)

    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["model", "n_train", "n_test", "auc", "auc_lo", "auc_hi",
              "ap", "ap_lo", "ap_hi", "brier", "log_loss", "ece", "note"]
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
