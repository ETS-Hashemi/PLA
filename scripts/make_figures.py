"""Generate the paper's data figures from the committed results.

Outputs (paper/figures/):
- fig_creditcard_auc.pdf — AUC forest plot with bootstrap 95% CIs,
  credit-card seed 42, full-test models only (subset rows excluded);
- fig_sox_auc.pdf — the same for the SOX-boundary accounting design,
  where the learned/no-context overlap is the visual verdict;
- fig_reliability_creditcard.pdf — reliability diagram (fixed
  log-spaced bins, log-log) for PLA static vs. learned on the seed-42 test split,
  recomputed with the same seeded pipeline as run_experiments.py.

Figure *content* is deterministic (seeded pipeline, committed CSVs);
PDF bytes may differ across matplotlib versions, so figures are exempt
from the byte-for-byte discipline that governs the results tables.

Usage:
    python scripts/make_figures.py                    # all figures
    python scripts/make_figures.py --skip-reliability # fast: forest plots only
"""

import argparse
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "paper" / "figures"

# Okabe-Ito blue/vermillion: colorblind-safe print pair (validated), with
# marker shape as the secondary encoding. Neutral inks for everything else.
PLA_COLOR = "#0072B2"
LEARNED_COLOR = "#D55E00"
BASELINE_COLOR = "#4a4a4a"
GRID_COLOR = "#d9d9d9"

DISPLAY_NAMES = {
    "logistic_regression": "logistic regression",
    "gradient_boosting": "gradient boosting (untuned)",
    "gradient_boosting_balanced": "gradient boosting (class-weighted)",
    "decision_tree": "decision tree (depth 4)",
    "ebm_interpretml": "EBM",
    "pla_static": "PLA static",
    "pla_learned": "PLA learned",
    "pla_learned_noctx": "PLA learned, no context",
}

plt.rcParams.update({
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8,
    "axes.linewidth": 0.7,
    "pdf.fonttype": 42,  # embed TrueType so journals can edit text
})


def _read_full_test_rows(csv_name):
    """Rows for models evaluated on the full test split; skipped rows,
    subset rows, and the constant-prevalence baseline (AUC 0.5 by
    construction — it would only stretch the axis) are excluded; sorted
    by AUC descending."""
    with open(RESULTS_DIR / csv_name, newline="") as handle:
        rows = [r for r in csv.DictReader(handle)
                if r["auc"] != "" and r["model"] != "constant_prevalence"]
    full_n = max(int(r["n_test"]) for r in rows)
    rows = [r for r in rows if int(r["n_test"]) == full_n]
    return sorted(rows, key=lambda r: -float(r["auc"]))


def forest_plot(csv_name, out_name):
    rows = _read_full_test_rows(csv_name)
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(rows) + 0.8))

    for position, row in enumerate(rows):
        auc = float(row["auc"])
        lo, hi = float(row["auc_lo"]), float(row["auc_hi"])
        is_pla = row["model"].startswith("pla")
        color = PLA_COLOR if is_pla else BASELINE_COLOR
        marker = "s" if is_pla else "o"
        y = len(rows) - 1 - position
        ax.plot([lo, hi], [y, y], color=color, linewidth=1.4,
                solid_capstyle="butt", zorder=2)
        ax.plot(auc, y, marker=marker, color=color, markersize=5, zorder=3)
        ax.annotate(f"{auc:.4f}", (hi, y), textcoords="offset points",
                    xytext=(5, -2.6), fontsize=7.5, color="#333333")

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(
        [DISPLAY_NAMES.get(r["model"], r["model"]) for r in reversed(rows)])
    for label, row in zip(ax.get_yticklabels(), reversed(rows)):
        if row["model"].startswith("pla"):
            label.set_color(PLA_COLOR)
    ax.set_xlabel("ROC AUC (point estimate and bootstrap 95% CI)")
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(left=False)
    ax.margins(x=0.09)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / out_name)
    plt.close(fig)
    print(f"wrote {FIG_DIR / out_name}")


# Log-spaced bin edges: equal-count bins zigzag under the heavy score
# ties these models produce (most examples fire no rule), so bin by
# predicted-probability decade instead. The first bin catches exact zeros.
BIN_EDGES = [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 0.01, 0.03, 0.1, 0.3, 1.0]


def _log_bins(y_true, y_prob, edges=BIN_EDGES, min_count=1):
    """Reliability points (mean predicted, observed rate, count) for the
    fixed log-spaced bins; empty bins are skipped, x is monotone."""
    points = []
    for lo, hi in zip(edges, edges[1:]):
        members = [(p, y) for p, y in zip(y_prob, y_true)
                   if lo <= p < hi or (hi == 1.0 and p == 1.0)]
        if len(members) < min_count:
            continue
        mean_predicted = sum(p for p, _ in members) / len(members)
        observed = sum(y for _, y in members) / len(members)
        points.append((mean_predicted, observed, len(members)))
    return points


def reliability_figure(data_path, out_name):
    import run_baselines as rb
    from pla.learn import RuleWeightLearner
    from pla.pipeline import (
        CREDITCARD,
        build_examples,
        fit_discretizer,
        generate_rule_specs,
        load_rows,
        noisy_or_probability,
    )

    rows = rb.parseable_rows(load_rows(data_path), CREDITCARD)
    train_rows, test_rows = rb.split_rows(rows)  # split seed 42, like E4
    thresholds = fit_discretizer(train_rows, schema=CREDITCARD)
    train_examples = build_examples(train_rows, thresholds, schema=CREDITCARD)
    test_examples = build_examples(test_rows, thresholds, schema=CREDITCARD)
    rule_specs, precisions = generate_rule_specs(
        train_examples, context_vars=CREDITCARD.all_context_vars)

    learner = RuleWeightLearner(rule_specs, use_bias=True)
    learner.fit(train_examples, epochs=400, learning_rate=1.0)

    y_true = [label for _, _, label in test_examples]
    static_probs = [noisy_or_probability(rule_specs, precisions, facts)
                    for facts, _, _ in test_examples]
    learned_probs = [learner.predict_proba(facts, context)
                     for facts, context, _ in test_examples]

    fig, ax = plt.subplots(figsize=(4.0, 4.0))
    floor = 5e-5  # display floor: log axes cannot show exact zeros
    ax.plot([floor, 1], [floor, 1], color=GRID_COLOR, linewidth=1.0,
            zorder=1, label="perfect calibration")
    for label, probs, color, marker in [
        ("PLA static", static_probs, PLA_COLOR, "s"),
        ("PLA learned", learned_probs, LEARNED_COLOR, "o"),
    ]:
        points = _log_bins(y_true, probs)
        xs = [max(p, floor) for p, _, _ in points]
        ys = [max(o, floor) for _, o, _ in points]
        ax.plot(xs, ys, marker=marker, markersize=5, linewidth=1.2,
                color=color, label=label, zorder=3)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("mean predicted probability (log-spaced bins)")
    ax.set_ylabel("observed fraud rate")
    ax.grid(True, which="major", color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / out_name)
    plt.close(fig)
    print(f"wrote {FIG_DIR / out_name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-reliability", action="store_true",
                        help="forest plots only (no model refits)")
    parser.add_argument("--reliability-data", default="data/creditcard.csv")
    args = parser.parse_args()

    forest_plot("experiment_creditcard_real.csv", "fig_creditcard_auc.pdf")
    forest_plot("experiment_bao2020_sox.csv", "fig_sox_auc.pdf")
    if not args.skip_reliability:
        reliability_figure(args.reliability_data,
                           "fig_reliability_creditcard.pdf")


if __name__ == "__main__":
    main()
