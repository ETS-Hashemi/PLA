"""E4 head-to-head: PLA (static) vs PLA (learned) vs baselines.

Adds two PLA rows to the E3 baseline suite:

- ``pla_static``: the E2 candidate rules with their empirical precisions,
  aggregated by noisy-OR (exactly the engine's default semantics; the
  ProbLog row cross-checks this on a subsample), neutral context;
- ``pla_learned``: rule base weights and the Amount_high context weight
  fitted on the training split through the logit path (RuleWeightLearner).

Everything is deterministic: the synthetic sample is regenerated from its
seed, the split seed is fixed, and every model is seeded — so the script
reproduces the committed results byte for byte.

Usage:
    python scripts/run_experiments.py --synthetic 2000 --seed 0
    python scripts/run_experiments.py --data data/creditcard.csv --tag real
    python scripts/run_experiments.py --synthetic 800 --seed 1 --fast  # tests

Outputs results/experiment_<tag>.csv and .md (committed; regenerate, never
hand-edit).
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

from pla.learn import RuleWeightLearner  # noqa: E402
from pla.pipeline import (  # noqa: E402
    CREDITCARD,
    SCHEMAS,
    build_examples,
    fit_discretizer,
    generate_rule_specs,
    load_rows,
    noisy_or_probability as pla_static_probability,
)

RESULTS_DIR = ROOT / "results"

# Temporal splits. bao2020: train through fiscal 2001, gap 2002 (fraud
# revelation lag), test from 2003. bao2020sox: training spans the 2003 SOX
# regime change (so the PostSOX context weight is learnable), gap 2006-07,
# test 2008+ — the design that isolates whether context conditioning helps.
TEMPORAL_SPLITS = {
    "bao2020": ("fyear", 2001, 2003),
    "bao2020sox": ("fyear", 2005, 2008),
}


def split_rows_temporal(rows, column, train_end, test_start):
    train = [r for r in rows if int(r[column]) <= train_end]
    test = [r for r in rows if int(r[column]) >= test_start]
    return train, test


def drop_post_first_fraud(train_rows, id_col="gvkey", year_col="fyear",
                          label_col="misstate"):
    """Serial-fraud handling (approximation of Bao et al.): within training,
    drop a firm's observations after its first fraud year, so multi-year
    frauds are not counted repeatedly. Returns (kept_rows, n_dropped)."""
    first_fraud = {}
    for record in train_rows:
        if record[label_col].strip() == "1":
            firm, year = record[id_col], int(record[year_col])
            if firm not in first_fraud or year < first_fraud[firm]:
                first_fraud[firm] = year
    kept = [
        record for record in train_rows
        if record[id_col] not in first_fraud
        or int(record[year_col]) <= first_fraud[record[id_col]]
    ]
    return kept, len(train_rows) - len(kept)


def pla_rows(rule_specs, precisions, train_examples, test_examples):
    y_true = [label for _, _, label in test_examples]

    static_probs = [
        pla_static_probability(rule_specs, precisions, facts)
        for facts, _, _ in test_examples
    ]
    static_row = rb.evaluate("pla_static", y_true, static_probs,
                             note="empirical precisions, noisy-OR, neutral context")

    learner = RuleWeightLearner(rule_specs, use_bias=True)
    learner.fit(train_examples, epochs=400, learning_rate=1.0)
    learned_probs = [
        learner.predict_proba(facts, context) for facts, context, _ in test_examples
    ]
    learned_row = rb.evaluate("pla_learned", y_true, learned_probs,
                              note="logit path + bias, fitted rule + context weights")

    # Ablation isolating the context mechanism: identical rules and bias,
    # but no context variables at all.
    from pla.learn import RuleSpec
    stripped = [RuleSpec(spec.antecedents) for spec in rule_specs]
    ablation = RuleWeightLearner(stripped, use_bias=True)
    ablation.fit(train_examples, epochs=400, learning_rate=1.0)
    ablation_probs = [
        ablation.predict_proba(facts, context) for facts, context, _ in test_examples
    ]
    ablation_row = rb.evaluate("pla_learned_noctx", y_true, ablation_probs,
                               note="ablation: context weights disabled")
    return [static_row, learned_row, ablation_row]


def run(data_path, tag, fast=False, schema=CREDITCARD, temporal=None, split_seed=42):
    rows = rb.parseable_rows(load_rows(data_path), schema)
    if temporal:
        column, train_end, test_start = temporal
        train_rows, test_rows = split_rows_temporal(rows, column, train_end, test_start)
        split_note = f"temporal split: train {column}<={train_end}, test {column}>={test_start}"
    else:
        train_rows, test_rows = rb.split_rows(rows, seed=split_seed)
        split_note = f"Split seed {split_seed}, 30% test."

    if schema.label == "misstate":
        train_rows, dropped = drop_post_first_fraud(train_rows)
        split_note += f" Serial-fraud handling: {dropped} post-first-fraud firm-years dropped from training."

    thresholds = fit_discretizer(train_rows, schema=schema)
    train_examples = build_examples(train_rows, thresholds, schema=schema)
    test_examples = build_examples(test_rows, thresholds, schema=schema)
    context_vars = schema.all_context_vars
    rule_specs, precisions = generate_rule_specs(train_examples, context_vars=context_vars)

    results = rb.sklearn_rows(train_rows, test_rows, schema)
    results.extend(pla_rows(rule_specs, precisions, train_examples, test_examples))
    if not fast:
        results.append(rb.problog_row(rule_specs, precisions, test_examples))
        propositions = sorted({a for spec in rule_specs for a in spec.antecedents})
        results.append(rb.pgmpy_row(train_examples, test_examples, propositions))

    for row in results:
        row["n_train"] = len(train_rows)

    RESULTS_DIR.mkdir(exist_ok=True)
    fields = ["model", "n_train", "n_test", "auc", "auc_lo", "auc_hi",
              "ap", "ap_lo", "ap_hi", "brier", "log_loss", "ece", "note"]
    csv_path = RESULTS_DIR / f"experiment_{tag}.csv"
    with open(csv_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    md_path = RESULTS_DIR / f"experiment_{tag}.md"
    lines = [
        f"# Experiment: {tag}",
        "",
        f"Generated by `python scripts/run_experiments.py` — do not edit by hand.",
        f"Dataset: `{pathlib.Path(data_path).name}`. {split_note}",
        "",
        "| Model | n_train | n_test | AUC | AUC 95% CI | AP | AP 95% CI | Brier | log-loss | ECE | Note |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in results:
        auc_ci = f"[{row['auc_lo']}, {row['auc_hi']}]" if row["auc_lo"] != "" else ""
        ap_ci = f"[{row['ap_lo']}, {row['ap_hi']}]" if row["ap_lo"] != "" else ""
        lines.append(
            f"| {row['model']} | {row['n_train']} | {row['n_test']} | {row['auc']} "
            f"| {auc_ci} | {row['ap']} | {ap_ci} | {row['brier']} | {row['log_loss']} "
            f"| {row['ece']} | {row['note']} |"
        )
    md_path.write_text("\n".join(lines) + "\n")
    return results, csv_path, md_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="existing CSV (e.g. the real dataset)")
    parser.add_argument("--synthetic", type=int, metavar="N",
                        help="regenerate the seeded synthetic sample and use it")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tag", help="results file tag (default derived)")
    parser.add_argument("--fast", action="store_true",
                        help="skip the slow problog/pgmpy baselines")
    parser.add_argument("--schema", choices=sorted(SCHEMAS), default="creditcard",
                        help="dataset schema (bao schemas use their temporal splits)")
    parser.add_argument("--split-seed", type=int, default=42,
                        help="random-split seed (multi-seed robustness runs)")
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

    if args.split_seed != 42:
        tag = f"{tag}_seed{args.split_seed}"
    schema = SCHEMAS[args.schema]
    temporal = TEMPORAL_SPLITS.get(args.schema)
    results, csv_path, md_path = run(data_path, tag, fast=args.fast,
                                     schema=schema, temporal=temporal,
                                     split_seed=args.split_seed)
    for row in results:
        print(row)
    print(f"written: {csv_path} and {md_path}")


if __name__ == "__main__":
    main()
