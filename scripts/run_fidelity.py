"""E5: explanation-fidelity report for the E4 PLA models.

For pla_static and pla_learned, computes trace-fidelity metrics
(comprehensiveness up, sufficiency near zero — see pla/fidelity.py) plus a
reversed-attribution control per model showing the metric discriminates
faithful rankings from deliberately wrong ones.

Deterministic like E4; writes results/fidelity_<tag>.csv and .md.

Usage:
    python scripts/run_fidelity.py --synthetic 2000 --seed 0
    python scripts/run_fidelity.py --data data/creditcard.csv --tag real
"""

import argparse
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_fraud_data as ffd  # noqa: E402
import run_baselines as rb  # noqa: E402
import run_experiments as rx  # noqa: E402

from pla.fidelity import (  # noqa: E402
    evaluate_fidelity,
    evaluate_rule_fidelity,
    learned_attributions,
    random_attributions,
    random_ranking,
    reversed_attributions,
    reversed_ranking,
    static_attributions,
)
from pla.prob import _sigmoid  # noqa: E402
from pla.learn import RuleWeightLearner  # noqa: E402
from pla.pipeline import (  # noqa: E402
    CREDITCARD,
    SCHEMAS,
    build_examples,
    fit_discretizer,
    generate_rule_specs,
    load_rows,
    noisy_or_probability,
)

RESULTS_DIR = ROOT / "results"


def _paired_diff_ci(trace_values, control_values, n_bootstrap=500, seed=7):
    """Seeded percentile-bootstrap 95% CI for the mean paired difference
    (trace minus reversed control), resampling example indices. The two
    attribution functions explain the same example subset, so the values
    pair index-by-index. Returns ("", "") without numpy."""
    try:
        import numpy as np
    except ImportError:
        return "", ""
    diffs = np.asarray(trace_values) - np.asarray(control_values)
    rng = np.random.Generator(np.random.PCG64(seed))
    means = [
        float(diffs[rng.integers(0, len(diffs), len(diffs))].mean())
        for _ in range(n_bootstrap)
    ]
    lo, hi = np.percentile(means, [2.5, 97.5])
    return f"{lo:.4f}", f"{hi:.4f}"


def run(data_path, tag, schema=CREDITCARD, temporal=None):
    rows = rb.parseable_rows(load_rows(data_path), schema)
    if temporal:
        column, train_end, test_start = temporal
        train_rows, test_rows = rx.split_rows_temporal(rows, column, train_end, test_start)
        split_note = f"Temporal split: train {column}<={train_end}, test {column}>={test_start}."
    else:
        train_rows, test_rows = rb.split_rows(rows)
        split_note = "Split seed 42, 30% test."
    if schema.label == "misstate":
        train_rows, dropped = rx.drop_post_first_fraud(train_rows)
        split_note += f" Serial-fraud handling: {dropped} firm-years dropped from training."
    thresholds = fit_discretizer(train_rows, schema=schema)
    train_examples = build_examples(train_rows, thresholds, schema=schema)
    test_examples = build_examples(test_rows, thresholds, schema=schema)
    context_vars = schema.all_context_vars
    rule_specs, precisions = generate_rule_specs(train_examples, context_vars=context_vars)

    learner = RuleWeightLearner(rule_specs, use_bias=True)
    learner.fit(train_examples, epochs=400, learning_rate=1.0)

    def static_predict(facts, _context):
        return noisy_or_probability(rule_specs, precisions, facts)

    def learned_predict(facts, context):
        return learner.predict_proba(facts, context)

    # Rule-level closures: the top-ranked RULE is removed from the fold
    # while the facts stay untouched — no overlapping-antecedent confound.
    def static_fired(facts):
        return [i for i, spec in enumerate(rule_specs)
                if all(a in facts for a in spec.antecedents)]

    def static_rank(facts, _context):
        return sorted(static_fired(facts), key=lambda i: -precisions[i])

    def static_without(facts, _context, excluded):
        p = 0.0
        for i in static_fired(facts):
            if i != excluded:
                p = 1.0 - (1.0 - p) * (1.0 - precisions[i])
        return p

    def static_only(facts, _context, index):
        return precisions[index]

    def learned_rank(facts, context):
        return sorted(learner._fired(facts),
                      key=lambda i: -learner._z(i, context))

    def learned_without(facts, context, excluded):
        z = sum(learner._z(i, context)
                for i in learner._fired(facts) if i != excluded)
        return _sigmoid(learner.bias + z)

    def learned_only(facts, context, index):
        return _sigmoid(learner.bias + learner._z(index, context))

    models = [
        ("pla_static", static_predict, static_attributions(rule_specs, precisions),
         static_without, static_only, static_rank),
        ("pla_learned", learned_predict, learned_attributions(learner),
         learned_without, learned_only, learned_rank),
    ]

    results = []
    for name, predict, attributions, without, only, rank in models:
        evaluations = [("facts", [
            ("trace", evaluate_fidelity(predict, attributions, test_examples)),
            ("reversed_control", evaluate_fidelity(
                predict, reversed_attributions(attributions), test_examples)),
            ("random_control", evaluate_fidelity(
                predict, random_attributions(attributions), test_examples)),
        ])]
        for level, logit in (("rules", False), ("rules_logit", True)):
            evaluations.append((level, [
                ("trace", evaluate_rule_fidelity(
                    without, only, rank, test_examples, logit_scale=logit)),
                ("reversed_control", evaluate_rule_fidelity(
                    without, only, reversed_ranking(rank), test_examples,
                    logit_scale=logit)),
                ("random_control", evaluate_rule_fidelity(
                    without, only, random_ranking(rank), test_examples,
                    logit_scale=logit)),
            ]))
        for level, rows in evaluations:
            trace_metrics = rows[0][1]
            for label, metrics in rows:
                entry = {
                    "model": name,
                    "level": level,
                    "attribution": label,
                    "n_explained": metrics["n_explained"],
                    "comprehensiveness": f"{metrics['comprehensiveness']:.4f}",
                    "sufficiency": f"{metrics['sufficiency']:.4f}",
                    "trace_minus_this": "", "diff_lo": "", "diff_hi": "",
                }
                if label != "trace":
                    diff = (trace_metrics["comprehensiveness"]
                            - metrics["comprehensiveness"])
                    lo, hi = _paired_diff_ci(
                        trace_metrics["comprehensiveness_values"],
                        metrics["comprehensiveness_values"])
                    entry["trace_minus_this"] = f"{diff:.4f}"
                    entry["diff_lo"], entry["diff_hi"] = lo, hi
                results.append(entry)

    RESULTS_DIR.mkdir(exist_ok=True)
    fields = ["model", "level", "attribution", "n_explained",
              "comprehensiveness", "sufficiency",
              "trace_minus_this", "diff_lo", "diff_hi"]
    csv_path = RESULTS_DIR / f"fidelity_{tag}.csv"
    with open(csv_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    md_path = RESULTS_DIR / f"fidelity_{tag}.md"
    lines = [
        f"# Explanation fidelity: {tag}",
        "",
        "Generated by `python scripts/run_fidelity.py` — do not edit by hand.",
        f"Dataset: `{pathlib.Path(data_path).name}`. {split_note}",
        "Levels: `facts` = ERASER-style fact deletion; `rules` = the top RULE",
        "is removed from the fold with facts untouched (no overlap confound);",
        "`rules_logit` = the same on clipped log-odds — the scale on which the",
        "learned model's per-rule contribution is exact (= z_r).",
        "Comprehensiveness: higher = the trace's top rule is load-bearing.",
        "Sufficiency: closer to 0 = the top rule alone reproduces the score.",
        "Control rows carry the paired-bootstrap 95% CI of (trace − control).",
        "",
        "| Model | Level | Attribution | n | Compr. | Suff. | trace − this | 95% CI |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in results:
        delta_ci = (f"[{row['diff_lo']}, {row['diff_hi']}]"
                    if row["diff_lo"] != "" else "")
        lines.append(
            f"| {row['model']} | {row['level']} | {row['attribution']} "
            f"| {row['n_explained']} | {row['comprehensiveness']} "
            f"| {row['sufficiency']} | {row['trace_minus_this']} | {delta_ci} |"
        )
    md_path.write_text("\n".join(lines) + "\n")
    return results, csv_path, md_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data")
    parser.add_argument("--synthetic", type=int, metavar="N")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tag")
    parser.add_argument("--schema", choices=sorted(SCHEMAS), default="creditcard")
    args = parser.parse_args()

    if bool(args.data) == bool(args.synthetic):
        sys.exit("pass exactly one of --data or --synthetic N")

    if args.synthetic:
        if args.schema != "creditcard":
            sys.exit("--synthetic generates creditcard-schema data only")
        data_path = ffd.DATA_DIR / f"creditcard_synthetic_seed{args.seed}.csv"
        ffd.generate_synthetic(args.synthetic, args.seed, data_path)
        tag = args.tag or f"synthetic_n{args.synthetic}_seed{args.seed}"
        print("SYNTHETIC DATA — development results, not paper results.")
    else:
        data_path = args.data
        tag = args.tag or pathlib.Path(args.data).stem

    schema = SCHEMAS[args.schema]
    temporal = rx.TEMPORAL_SPLITS.get(args.schema)
    results, csv_path, md_path = run(data_path, tag, schema=schema, temporal=temporal)
    for row in results:
        print(row)
    print(f"written: {csv_path} and {md_path}")


if __name__ == "__main__":
    main()
