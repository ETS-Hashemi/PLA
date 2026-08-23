"""Explanation-fidelity metrics for rule-trace explanations.

Quantifies whether a model's trace names the factors that actually drive
its prediction, using deletion-based metrics in the ERASER style, grounded
in the faithfulness (vs. plausibility) framing of Jacovi & Goldberg 2020:

- **comprehensiveness** = p(full) − p(top factor's facts removed).
  High when the explanation's top-ranked rule is genuinely load-bearing.
- **sufficiency** = p(full) − p(only the top factor's facts kept).
  Near zero when the named factors alone reproduce the prediction.

Interface: ``predict(facts, context) -> prob`` and
``attributions(facts, context) -> [(antecedents, score), ...]`` ranked most
important first, fired rules only. A deliberately wrong ranking (e.g.
reversed) must score worse on comprehensiveness than the faithful one —
that contrast is what the tests check.

Exactness caveat: in a flat single-fold noisy-OR setting, deleting rule i
changes the score by s - s_{-i} = c_i * prod_{j!=i}(1 - c_j), which is
monotone in the candidate c_i within a fired set — so ranking by candidate
(precision, for crisp facts) is provably the exact deletion ranking, and
these metrics there validate implementation concordance rather than test a
fallible ranking. The genuinely fallible, multi-step case is exercised by
``scripts/run_fidelity_chained.py``.

Fact deletion can deactivate several overlapping rules at once, so this
module also provides **rule-level** deletion (``evaluate_rule_fidelity``):
the top-ranked *rule* is removed from the computation while the facts stay
untouched, on the probability scale or on clipped log-odds — the natural
unit for the learned model, whose per-rule log-odds contribution is exactly
``z_r`` by construction. Two controls are provided: the reversed ranking
and a deterministic random ranking.
"""

import math
import random
import zlib

_EPSILON = 1e-9


def _clipped_logit(p, epsilon=_EPSILON):
    p = min(max(p, epsilon), 1.0 - epsilon)
    return math.log(p / (1.0 - p))


def evaluate_fidelity(predict, attributions, examples):
    """Mean comprehensiveness and sufficiency over explainable examples."""
    comprehensiveness = []
    sufficiency = []
    for facts, context, _ in examples:
        ranked = attributions(facts, context)
        if not ranked:
            continue
        top_antecedents = frozenset(ranked[0][0])
        p_full = predict(facts, context)
        p_deleted = predict(frozenset(facts - top_antecedents), context)
        p_only_top = predict(frozenset(facts & top_antecedents), context)
        comprehensiveness.append(p_full - p_deleted)
        sufficiency.append(p_full - p_only_top)

    n = len(comprehensiveness)
    return {
        "n_explained": n,
        "comprehensiveness": sum(comprehensiveness) / n if n else None,
        "sufficiency": sum(sufficiency) / n if n else None,
        # Per-example deltas, in example order over the explained subset —
        # two attribution functions over the same examples explain the same
        # subset, so these lists pair index-by-index (paired bootstrap).
        "comprehensiveness_values": comprehensiveness,
        "sufficiency_values": sufficiency,
    }


def static_attributions(rule_specs, precisions):
    """Rank fired rules by their candidate contribution (precision)."""

    def attributions(facts, _context):
        fired = [
            (spec.antecedents, precision)
            for spec, precision in zip(rule_specs, precisions)
            if all(a in facts for a in spec.antecedents)
        ]
        return sorted(fired, key=lambda item: -item[1])

    return attributions


def learned_attributions(learner):
    """Rank fired rules by their log-odds contribution z_r."""

    def attributions(facts, context):
        fired = []
        for index in learner._fired(facts):
            z = learner._z(index, context)
            fired.append((learner.rules[index].antecedents, z))
        return sorted(fired, key=lambda item: -item[1])

    return attributions


def reversed_attributions(attributions):
    """Control: the same rules deliberately ranked worst-first."""

    def reversed_fn(facts, context):
        return list(reversed(attributions(facts, context)))

    return reversed_fn


def random_attributions(attributions, seed=13):
    """Control: the same fired rules in a deterministic pseudo-random
    order, keyed by the example's facts via crc32 (stable across runs
    and processes, unlike Python's salted hash())."""

    def random_fn(facts, context):
        ranked = list(attributions(facts, context))
        key = zlib.crc32(("|".join(sorted(facts)) + f"#{seed}").encode())
        random.Random(key).shuffle(ranked)
        return ranked

    return random_fn


def reversed_ranking(rank_rules):
    """Rule-index control: worst-first."""

    def ranked(facts, context):
        return list(reversed(rank_rules(facts, context)))

    return ranked


def random_ranking(rank_rules, seed=13):
    """Rule-index control: deterministic random order (crc32-keyed)."""

    def ranked(facts, context):
        order = list(rank_rules(facts, context))
        key = zlib.crc32(("|".join(sorted(facts)) + f"#{seed}").encode())
        random.Random(key).shuffle(order)
        return order

    return ranked


def evaluate_rule_fidelity(predict_without, predict_only, rank_rules,
                           examples, logit_scale=False):
    """Rule-level deletion metrics, free of the fact-overlap confound:
    the top-ranked RULE is removed from the computation while the facts
    stay untouched.

    - ``predict_without(facts, context, excluded_index_or_None) -> prob``
    - ``predict_only(facts, context, index) -> prob`` (top rule alone,
      plus whatever prior term the model carries)
    - ``rank_rules(facts, context) -> [rule_index, ...]`` best first

    comprehensiveness = s(full) - s(without top rule); higher is better.
    sufficiency = s(full) - s(top rule alone); closer to zero is better.
    Scores are probabilities, or clipped log-odds when ``logit_scale`` —
    the scale on which the learned model's per-rule contribution is
    exact (its comprehensiveness equals z_top identically).
    """
    transform = _clipped_logit if logit_scale else (lambda p: p)
    comprehensiveness = []
    sufficiency = []
    for facts, context, _ in examples:
        order = rank_rules(facts, context)
        if not order:
            continue
        top = order[0]
        s_full = transform(predict_without(facts, context, None))
        s_without = transform(predict_without(facts, context, top))
        s_only = transform(predict_only(facts, context, top))
        comprehensiveness.append(s_full - s_without)
        sufficiency.append(s_full - s_only)

    n = len(comprehensiveness)
    return {
        "n_explained": n,
        "comprehensiveness": sum(comprehensiveness) / n if n else None,
        "sufficiency": sum(sufficiency) / n if n else None,
        "comprehensiveness_values": comprehensiveness,
        "sufficiency_values": sufficiency,
    }
