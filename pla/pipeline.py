"""Feature -> proposition -> candidate-rule pipeline for tabular fraud data.

Turns a credit-card-schema CSV (Time, V1..V28, Amount, Class — real or the
E1 synthetic sample) into:

- **examples** for the learner: (facts, context, label) triples, where facts
  are quantile propositions like ``V3_high``/``V7_low`` and the context
  carries transaction circumstances (currently ``Amount_high``);
- **candidate rules**: single- and pair-antecedent RuleSpecs selected by
  empirical precision with a minimum-support floor, each carrying the
  context variable;
- a **scenario JSON** for one example, with rule probabilities set to the
  rules' empirical precisions (numbers from data, never invented) and
  neutral context weights (1.0 in legacy mode) until they are learned.

Everything is deterministic given the input rows.
"""

import csv
import json

from .learn import RuleSpec

FEATURES = [f"V{i}" for i in range(1, 29)]
CONTEXT_FEATURE = "Amount"
CONTEXT_VAR = "Amount_high"
TARGET = "Fraud"


class Schema:
    """Dataset schema: numeric feature columns to discretize, the label
    column, and the context source — either a quantile flag on a numeric
    column (active when the value reaches the upper threshold) or a binary
    column (active when it equals "1"). Rows whose feature values fail to
    parse are skipped by build_examples (complete-case)."""

    def __init__(self, features, label, quantile_context=None, binary_context=None):
        self.features = list(features)
        self.label = label
        self.quantile_context = quantile_context  # (column, context var name)
        self.binary_context = binary_context      # (column, context var name)

    @property
    def context_var(self):
        if self.quantile_context:
            return self.quantile_context[1]
        if self.binary_context:
            return self.binary_context[1]
        return None

    @property
    def numeric_columns(self):
        """Feature columns plus the context source, for raw-feature models."""
        columns = list(self.features)
        if self.quantile_context:
            columns.append(self.quantile_context[0])
        if self.binary_context:
            columns.append(self.binary_context[0])
        return columns


CREDITCARD = Schema(FEATURES, "Class", quantile_context=(CONTEXT_FEATURE, CONTEXT_VAR))

# Bao et al. (2020, JAR) accounting-fraud replication data: the paper's 14
# financial ratios, with the binary issuance indicator as the context
# variable and the other 13 as discretized features.
BAO2020 = Schema(
    ["dch_wc", "ch_rsst", "dch_rec", "dch_inv", "soft_assets", "dpi",
     "reoa", "EBIT", "bm", "ch_cs", "ch_cm", "ch_roa", "ch_fcf"],
    "misstate",
    binary_context=("issue", "Issuance"),
)

SCHEMAS = {"creditcard": CREDITCARD, "bao2020": BAO2020}


def load_rows(path):
    with open(path, newline="") as handle:
        return [dict(record) for record in csv.DictReader(handle)]


def _quantile(sorted_values, q):
    index = int(q * (len(sorted_values) - 1))
    return sorted_values[index]


def fit_discretizer(rows, q_low=0.1, q_high=0.9, schema=CREDITCARD):
    """Per-feature (low, high) thresholds from quantiles of the given rows.
    Rows with unparseable values are ignored per feature (complete-case)."""
    thresholds = {}
    columns = list(schema.features)
    if schema.quantile_context:
        columns.append(schema.quantile_context[0])
    for feature in columns:
        values = []
        for record in rows:
            try:
                values.append(float(record[feature]))
            except ValueError:
                continue
        values.sort()
        thresholds[feature] = (_quantile(values, q_low), _quantile(values, q_high))
    return thresholds


def propositionalize(record, thresholds, schema=CREDITCARD):
    """Map one row to (facts, context) proposition sets.
    Raises ValueError when a feature value does not parse."""
    facts = set()
    for feature in schema.features:
        low, high = thresholds[feature]
        value = float(record[feature])
        if value >= high:
            facts.add(f"{feature}_high")
        elif value <= low:
            facts.add(f"{feature}_low")
    context = set()
    if schema.quantile_context:
        column, var = schema.quantile_context
        if float(record[column]) >= thresholds[column][1]:
            context.add(var)
    if schema.binary_context:
        column, var = schema.binary_context
        if record[column].strip() == "1":
            context.add(var)
    return frozenset(facts), frozenset(context)


def build_examples(rows, thresholds, schema=CREDITCARD):
    """(facts, context, label) triples; rows with unparseable feature
    values are skipped (complete-case) — compare len() against the input."""
    examples = []
    for record in rows:
        try:
            facts, context = propositionalize(record, thresholds, schema)
        except ValueError:
            continue
        label = 1 if record[schema.label].strip() in ("1", "1.0") else 0
        examples.append((facts, context, label))
    return examples


def _precision(examples, antecedents):
    hits = positives = 0
    for facts, _, label in examples:
        if all(a in facts for a in antecedents):
            hits += 1
            positives += label
    return (positives / hits if hits else 0.0), hits


def generate_rule_specs(examples, top_singles=8, top_pairs=3,
                        min_single_support=20, min_pair_support=10,
                        context_vars=(CONTEXT_VAR,)):
    """Precision-ranked candidate rules with support floors. Deterministic."""
    propositions = sorted({p for facts, _, _ in examples for p in facts})

    singles = []
    for proposition in propositions:
        precision, support = _precision(examples, (proposition,))
        if support >= min_single_support:
            singles.append((precision, proposition, support))
    singles.sort(key=lambda item: (-item[0], item[1]))
    selected_singles = singles[:top_singles]

    pairs = []
    seeds = [proposition for _, proposition, _ in selected_singles[:5]]
    for i, first in enumerate(seeds):
        for second in seeds[i + 1:]:
            precision, support = _precision(examples, (first, second))
            if support >= min_pair_support:
                pairs.append((precision, (first, second), support))
    pairs.sort(key=lambda item: (-item[0], item[1]))
    selected_pairs = pairs[:top_pairs]

    specs, precisions = [], []
    for precision, proposition, _ in selected_singles:
        specs.append(RuleSpec((proposition,), context_vars=context_vars))
        precisions.append(precision)
    for precision, antecedents, _ in selected_pairs:
        specs.append(RuleSpec(antecedents, context_vars=context_vars))
        precisions.append(precision)
    return specs, precisions


def noisy_or_probability(rule_specs, precisions, facts):
    """Noisy-OR over fired rules — the engine's default aggregation."""
    p = 0.0
    for spec, precision in zip(rule_specs, precisions):
        if all(a in facts for a in spec.antecedents):
            p = 1.0 - (1.0 - p) * (1.0 - precision)
    return p


def export_scenario(rule_specs, precisions, example_facts, example_context, path):
    """Write one example as a loadable scenario file; returns the dict."""
    scenario = {
        "facts": sorted(example_facts),
        "rules": [
            {
                "condition": list(spec.antecedents),
                "result": TARGET,
                "probability": round(precision, 6),
                "context": {var: 1.0 for var in spec.context_vars},
            }
            for spec, precision in zip(rule_specs, precisions)
        ],
        "queries": [TARGET],
        "contexts": {"1": sorted(example_context)},
    }
    with open(path, "w") as handle:
        json.dump(scenario, handle, indent=2)
    return scenario


def run_pipeline(data_path, scenario_path=None, schema=CREDITCARD):
    """End to end: rows -> thresholds -> examples -> rules (+ scenario)."""
    rows = load_rows(data_path)
    thresholds = fit_discretizer(rows, schema=schema)
    examples = build_examples(rows, thresholds, schema=schema)
    context_vars = (schema.context_var,) if schema.context_var else ()
    specs, precisions = generate_rule_specs(examples, context_vars=context_vars)

    scenario = None
    if scenario_path is not None:
        positive = next(
            ((f, c) for f, c, label in examples if label == 1 and f),
            (examples[0][0], examples[0][1]),
        )
        scenario = export_scenario(specs, precisions, positive[0], positive[1], scenario_path)
    return {
        "examples": examples,
        "thresholds": thresholds,
        "rule_specs": specs,
        "precisions": precisions,
        "scenario": scenario,
    }
