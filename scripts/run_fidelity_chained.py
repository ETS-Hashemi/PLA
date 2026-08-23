"""Chained-inference fidelity: the setting where the trace ranking can fail.

In the flat single-fold experiments (scripts/run_fidelity.py) ranking rules
by candidate value is provably the exact deletion ranking — noisy-OR gives
s - s_{-i} = c_i * prod_{j!=i}(1 - c_j), monotone in c_i within a fired
set — so those metrics validate implementation concordance. This script
builds the genuinely fallible case: seeded two-and-three-step rule
programs (facts -> intermediates -> deeper intermediate -> target) with
graded antecedents, where a rule's LOCAL trace candidate (adjusted
confidence x weakest antecedent, toward its own head) says nothing
provable about its impact on the TARGET after the fixpoint re-runs.

Because a single random program could accidentally flatter or damn the
trace ranking, the study sweeps PROGRAMS independently generated
programs and reports per-program rows plus a pooled row. For each
example, every fired rule's true target impact is computed by brute
force (delete the rule, re-run inference, difference the target
confidence). Rankings compared:

- trace: fired rules (all layers) ranked by local candidate — the
  magnitudes a reader of the full trace sees;
- oracle: the rule with the largest true impact (the ceiling);
- reversed_control / random_control: the usual wrong-order controls
  (random averaged over RANDOM_PERMUTATIONS crc32-keyed permutations).

Reported per program and pooled: mean top-1 comprehensiveness (target-
confidence drop when the ranking's top rule is deleted) per ranking,
paired-bootstrap 95% CIs for trace - control, the trace-vs-oracle top-1
agreement rate, and the chance agreement baseline (expected agreement of
a uniformly random pick, tie-aware). Nothing forces agreement to 1 here;
whatever it is, it is the honest headline.

Deterministic: program structure, confidences, and examples all derive
from --seed; the random control is crc32-keyed per example. Writes
results/fidelity_chained_synthetic.{csv,md}.

Usage:
    python scripts/run_fidelity_chained.py                 # paper defaults
    python scripts/run_fidelity_chained.py --programs 5 --examples 200
"""

import argparse
import csv
import pathlib
import random
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pla.prob import ProbKB, ProbRule, ProbSymbol  # noqa: E402

RESULTS_DIR = ROOT / "results"
RANDOM_PERMUTATIONS = 10
TARGET = "Target"


def build_program(rng):
    """One seeded rule program: 8 facts, intermediates I0..I3 (two rules
    each over one or two facts), a deeper J0 (fact + intermediate, so its
    antecedent minimum is graded), and six target rules mixing
    intermediates, the deep node, and facts. Returns (facts, rules) with
    rules as (antecedents, head, confidence) triples."""
    facts = [f"F{i}" for i in range(8)]
    rules = []

    def confidence():
        return round(rng.uniform(0.25, 0.9), 3)

    for k in range(4):
        head = f"I{k}"
        for _ in range(2):
            n_antecedents = rng.choice([1, 2])
            rules.append((tuple(rng.sample(facts, n_antecedents)), head,
                          confidence()))

    for _ in range(2):
        rules.append(((f"I{rng.randrange(4)}", rng.choice(facts)), "J0",
                      confidence()))

    target_antecedent_pools = [
        lambda: (f"I{rng.randrange(4)}",),
        lambda: ("J0",),
        lambda: (f"I{rng.randrange(4)}", rng.choice(facts)),
        lambda: tuple(f"I{k}" for k in rng.sample(range(4), 2)),
    ]
    for _ in range(6):
        rules.append((rng.choice(target_antecedent_pools)(), TARGET,
                      confidence()))
    return facts, rules


def make_kb(active_facts, rules, exclude=None):
    kb = ProbKB()
    for fact in sorted(active_facts):
        kb.add_fact(ProbSymbol(fact))
    for index, (antecedents, head, confidence) in enumerate(rules):
        if index == exclude:
            continue
        kb.add_rule(ProbRule([ProbSymbol(a) for a in antecedents],
                             ProbSymbol(head), confidence))
    return kb


def confidences_of(kb):
    detailed = kb.query_detailed(TARGET)
    return detailed["confidence"], detailed["all_fact_probabilities"]


def _paired_diff_ci(trace_values, control_values, n_bootstrap=500, seed=7):
    """Same estimator as scripts/run_fidelity.py."""
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


def run_program(program_seed, n_examples):
    """All per-example measurements for one seeded program."""
    rng = random.Random(program_seed)
    facts, rules = build_program(rng)
    example_rng = random.Random(program_seed + 10_000)

    values = {"trace": [], "oracle": [],
              "reversed_control": [], "random_control": []}
    agreements = []
    chance = []
    fired_counts = []

    for _ in range(n_examples):
        active = frozenset(f for f in facts if example_rng.random() < 0.5)
        if not active:
            continue
        kb = make_kb(active, rules)
        s_full, confidences = confidences_of(kb)
        if s_full <= 0.0:
            continue

        fired = []
        for index, (antecedents, _head, confidence) in enumerate(rules):
            antecedent_values = [confidences.get(a, 0.0)
                                 for a in antecedents]
            if min(antecedent_values) > 0.0:
                fired.append((index, confidence * min(antecedent_values)))
        if not fired:
            continue

        impact = {}
        for index, _candidate in fired:
            s_without, _ = confidences_of(
                make_kb(active, rules, exclude=index))
            impact[index] = s_full - s_without

        by_candidate = sorted(fired, key=lambda item: (-item[1], item[0]))
        trace_top = by_candidate[0][0]
        oracle_comp = max(impact.values())
        ties = sum(1 for v in impact.values()
                   if abs(v - oracle_comp) <= 1e-12)

        order = [index for index, _ in by_candidate]
        key = zlib.crc32(("|".join(sorted(active))).encode())
        random_comps = []
        for permutation_seed in range(RANDOM_PERMUTATIONS):
            shuffled = list(order)
            random.Random(key + permutation_seed).shuffle(shuffled)
            random_comps.append(impact[shuffled[0]])

        values["trace"].append(impact[trace_top])
        values["oracle"].append(oracle_comp)
        values["reversed_control"].append(impact[order[-1]])
        values["random_control"].append(sum(random_comps)
                                        / len(random_comps))
        agreements.append(
            1 if abs(impact[trace_top] - oracle_comp) <= 1e-12 else 0)
        chance.append(ties / len(fired))
        fired_counts.append(len(fired))

    return values, agreements, chance, fired_counts


def _row(label, values, agreements, chance, fired_counts):
    n = len(values["trace"])
    mean = {k: sum(v) / n for k, v in values.items()}
    row = {
        "program": label,
        "n_explained": n,
        "mean_fired": f"{sum(fired_counts) / n:.1f}",
        "agreement": f"{sum(agreements) / n:.4f}",
        "chance_agreement": f"{sum(chance) / n:.4f}",
        "comp_trace": f"{mean['trace']:.4f}",
        "comp_oracle": f"{mean['oracle']:.4f}",
        "comp_reversed": f"{mean['reversed_control']:.4f}",
        "comp_random": f"{mean['random_control']:.4f}",
    }
    for control, tag in (("reversed_control", "rev"),
                         ("random_control", "rand")):
        diff = mean["trace"] - mean[control]
        lo, hi = _paired_diff_ci(values["trace"], values[control])
        row[f"trace_minus_{tag}"] = f"{diff:.4f}"
        row[f"{tag}_lo"], row[f"{tag}_hi"] = lo, hi
    return row


def run(n_programs, n_examples, seed, results_dir=RESULTS_DIR):
    pooled = {"trace": [], "oracle": [],
              "reversed_control": [], "random_control": []}
    pooled_agreements = []
    pooled_chance = []
    pooled_fired = []
    rows = []

    for p in range(n_programs):
        program_seed = seed + p
        values, agreements, chance, fired_counts = run_program(
            program_seed, n_examples)
        rows.append(_row(str(program_seed), values, agreements, chance,
                         fired_counts))
        for k in pooled:
            pooled[k].extend(values[k])
        pooled_agreements.extend(agreements)
        pooled_chance.extend(chance)
        pooled_fired.extend(fired_counts)

    pooled_row = _row("pooled", pooled, pooled_agreements, pooled_chance,
                      pooled_fired)
    rows.append(pooled_row)

    results_dir = pathlib.Path(results_dir)
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / "fidelity_chained_synthetic.csv"
    fields = ["program", "n_explained", "mean_fired", "agreement",
              "chance_agreement", "comp_trace", "comp_oracle",
              "comp_reversed", "comp_random",
              "trace_minus_rev", "rev_lo", "rev_hi",
              "trace_minus_rand", "rand_lo", "rand_hi"]
    with open(csv_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    program_rows = rows[:-1]
    rand_positive = sum(1 for r in program_rows
                        if float(r["trace_minus_rand"]) > 0)
    rand_ci_above = sum(1 for r in program_rows if r["rand_lo"] != ""
                        and float(r["rand_lo"]) > 0)
    rand_ci_below = sum(1 for r in program_rows if r["rand_hi"] != ""
                        and float(r["rand_hi"]) < 0)
    agreements_by_program = sorted(float(r["agreement"])
                                   for r in program_rows)

    md_path = results_dir / "fidelity_chained_synthetic.md"
    lines = [
        "# Chained-inference fidelity (the fallible case)",
        "",
        "Generated by `python scripts/run_fidelity_chained.py` — do not",
        "edit by hand.",
        f"{n_programs} independently seeded programs (8 facts, 4",
        "intermediates + 1 deep node, 16 rules each), base seed"
        f" {seed}, {n_examples} sampled examples per program.",
        "Comprehensiveness = drop in target confidence when the ranking's",
        "top rule is deleted and the fixpoint re-runs. `oracle` is the",
        "brute-force best single deletion (ceiling). The local trace",
        "ranking is NOT algebraically tied to target impact here — in",
        "chained programs the most load-bearing rule is typically an",
        "upstream, non-redundant one, which local candidate magnitude",
        "does not identify.",
        "",
        f"Pooled: agreement {pooled_row['agreement']} (chance"
        f" {pooled_row['chance_agreement']}); per-program agreement"
        f" range {agreements_by_program[0]:.4f}"
        f"–{agreements_by_program[-1]:.4f}.",
        f"trace − random > 0 in {rand_positive}/{n_programs} programs"
        f" (CI above zero in {rand_ci_above}, below zero in"
        f" {rand_ci_below}).",
        "",
        "| Program | n | Agree | Chance | Trace | Oracle | Reversed |"
        " Random | trace−rev [CI] | trace−rand [CI] |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['program']} | {row['n_explained']} "
            f"| {row['agreement']} | {row['chance_agreement']} "
            f"| {row['comp_trace']} | {row['comp_oracle']} "
            f"| {row['comp_reversed']} | {row['comp_random']} "
            f"| {row['trace_minus_rev']} [{row['rev_lo']},"
            f" {row['rev_hi']}] "
            f"| {row['trace_minus_rand']} [{row['rand_lo']},"
            f" {row['rand_hi']}] |")
    md_path.write_text("\n".join(lines) + "\n")
    return rows, csv_path, md_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--programs", type=int, default=20)
    parser.add_argument("--examples", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    rows, csv_path, md_path = run(args.programs, args.examples, args.seed)
    for row in rows:
        print(row)
    print(f"written: {csv_path} and {md_path}")


if __name__ == "__main__":
    main()
