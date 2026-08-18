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
that contrast is what makes the metric informative, and is what the tests
check.
"""


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
