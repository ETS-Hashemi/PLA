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
}

RESULTS = ROOT / "results"

FIDELITY_DATASETS = [
    ("synthetic", "fidelity_synthetic_n2000_seed0.csv", ("pla_static", "pla_learned")),
    ("credit card", "fidelity_creditcard_real.csv", ("pla_static",)),
    ("accounting (strict)", "fidelity_bao2020_real.csv", ("pla_static",)),
    ("accounting (SOX)", "fidelity_bao2020_sox.csv", ("pla_static",)),
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

    columns = "lrlrr" + ("r" if with_ece else "")
    header = ("Model & AUC & AUC 95\\% CI & AP & log-loss"
              + (" & ECE" if with_ece else "") + "\\\\")
    lines = [f"\\begin{{tabular}}{{{columns}}}", "\\toprule", header, "\\midrule"]

    def cells(row, name_suffix=""):
        parts = [
            _tex_name(row) + name_suffix,
            row["auc"],
            f"[{row['auc_lo']}, {row['auc_hi']}]",
            row["ap"],
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


def _fidelity_table():
    lines = [
        "\\begin{tabular}{llrrrlrr}",
        "\\toprule",
        "Dataset & Model & $n$ & \\multicolumn{2}{c}{Comprehensiveness} & "
        "$\\Delta$ [95\\% CI] & \\multicolumn{2}{c}{Sufficiency}\\\\",
        " & & & trace & control & & trace & control\\\\",
        "\\midrule",
    ]
    for label, csv_name, models in FIDELITY_DATASETS:
        with open(RESULTS / csv_name, newline="") as handle:
            rows = {(r["model"], r["attribution"]): r
                    for r in csv.DictReader(handle)}
        for model in models:
            trace = rows[(model, "trace")]
            control = rows[(model, "reversed_control")]
            model_name = DISPLAY_NAMES[model].replace("PLA ", "\\pla{} ")  # short form fits
            delta = (f"{trace['comp_minus_control']} "
                     f"[{trace['comp_diff_lo']}, {trace['comp_diff_hi']}]")
            lines.append(
                f"{label} & {model_name} & {int(trace['n_explained']):,} & "
                f"{trace['comprehensiveness']} & {control['comprehensiveness']} & "
                f"{delta} & {trace['sufficiency']} & {control['sufficiency']}\\\\"
                .replace(",", "{,}"))
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
