"""Print the paper's results tables (LaTeX bodies) from the committed CSVs.

The manuscript's tables are pasted from this script's output — never
hand-typed — so every cell traces to a generated file. Usage:

    python scripts/make_paper_tables.py            # all tables
    python scripts/make_paper_tables.py sox        # one of: synthetic,
                                                   # creditcard, sox, fidelity
"""

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from make_figures import DISPLAY_NAMES  # noqa: E402

# Tables have room for fuller qualifiers than the figure axes do.
TABLE_NAMES = {
    **DISPLAY_NAMES,
    "logistic_regression": "logistic regression (raw features)",
    "ebm_interpretml": "EBM (raw features)",
    "decision_tree": "decision tree (depth 4, balanced)",
    "pla_static": "PLA static (empirical precisions)",
    "pla_learned": "PLA learned (rules + context + bias)",
    "pla_learned_noctx": "PLA learned, no context (ablation)",
    "pgmpy_naive_bayes": "pgmpy naive Bayes (propositions)",
    "constant_prevalence": "constant-prevalence baseline",
}

RESULTS = ROOT / "results"

FIDELITY_DATASETS = [
    ("synthetic", "fidelity_synthetic_n2000_seed0.csv", ("pla_static", "pla_learned")),
    ("credit card", "fidelity_creditcard_real.csv", ("pla_static",)),
    ("accounting, strict", "fidelity_bao2020_real.csv", ("pla_static",)),
    ("accounting, SOX", "fidelity_bao2020_sox.csv", ("pla_static",)),
]


def _rows(csv_name):
    with open(RESULTS / csv_name, newline="") as handle:
        return [r for r in csv.DictReader(handle) if r["auc"] != ""]


def _tex_name(row):
    name = TABLE_NAMES.get(row["model"], row["model"])
    if row["model"] == "problog_rules":
        name = "ProbLog on \\pla{} rules"
    return name.replace("PLA ", "\\pla{} ")


def _experiment_table(csv_name, with_ece=True, subset_block=True):
    rows = _rows(csv_name)
    full_n = max(int(r["n_test"]) for r in rows)
    full = sorted([r for r in rows if int(r["n_test"]) == full_n],
                  key=lambda r: -float(r["auc"]))
    subset = sorted([r for r in rows if int(r["n_test"]) != full_n],
                    key=lambda r: -float(r["auc"]))

    columns = "lrlrlr" + ("r" if with_ece else "")
    header = ("Model & AUC & AUC 95\\% CI & AP & AP 95\\% CI & log-loss"
              + (" & ECE" if with_ece else "") + "\\\\")
    lines = [f"\\begin{{tabular}}{{{columns}}}", "\\toprule", header, "\\midrule"]

    def _interval(low, high):
        return f"[{low}, {high}]" if low != "" else "---"

    def cells(row, name_suffix=""):
        parts = [
            _tex_name(row) + name_suffix,
            row["auc"],
            _interval(row["auc_lo"], row["auc_hi"]),
            row["ap"],
            _interval(row["ap_lo"], row["ap_hi"]),
            row["log_loss"],
        ]
        if with_ece:
            parts.append(row["ece"])
        return " & ".join(parts) + "\\\\"

    lines.extend(cells(r) for r in full)
    if subset_block and subset:
        lines.append("\\midrule")
        lines.extend(cells(r, f" ($n{{=}}{r['n_test']}$)") for r in subset)
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    return "\n".join(lines)


def _fidelity_table(level="rules", model="pla_static"):
    """Rule-level deletion for the static model (the genuinely tested
    heuristic ranking): trace comprehensiveness/sufficiency plus the
    paired-bootstrap Delta against BOTH controls. The learned model's
    rule ranking is exact by construction on the log-odds scale, so its
    headline lives in the text; all rows are in the generated CSVs."""
    lines = [
        "\\begin{tabular}{lrrllr}",
        "\\toprule",
        "Dataset & $n$ & Compr. & $\\Delta$ vs reversed [95\\% CI] & "
        "$\\Delta$ vs random [95\\% CI] & Suff.\\\\",
        "\\midrule",
    ]
    for label, csv_name, _models in FIDELITY_DATASETS:
        with open(RESULTS / csv_name, newline="") as handle:
            rows = {(r["model"], r["level"], r["attribution"]): r
                    for r in csv.DictReader(handle)}
        trace = rows[(model, level, "trace")]
        reversed_row = rows[(model, level, "reversed_control")]
        random_row = rows[(model, level, "random_control")]
        n_tex = f"{int(trace['n_explained']):,}".replace(",", "{,}")

        def delta(row):
            return (f"{row['trace_minus_this']} "
                    f"[{row['diff_lo']}, {row['diff_hi']}]")

        lines.append(
            f"{label} & {n_tex} & {trace['comprehensiveness']} & "
            f"{delta(reversed_row)} & {delta(random_row)} & "
            f"{trace['sufficiency']}\\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    return "\n".join(lines)


TABLES = {
    "synthetic": lambda: _experiment_table("experiment_synthetic_n2000_seed0.csv"),
    "creditcard": lambda: _experiment_table("experiment_creditcard_real.csv"),
    "sox": lambda: _experiment_table("experiment_bao2020_sox.csv",
                                     with_ece=False, subset_block=False),
    "fidelity": _fidelity_table,
}


def main():
    wanted = sys.argv[1:] or list(TABLES)
    for name in wanted:
        print(f"% ---- {name} ----")
        print(TABLES[name]())
        print()


if __name__ == "__main__":
    main()
