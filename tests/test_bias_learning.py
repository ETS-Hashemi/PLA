"""The global-intercept option and the inversion pathology it fixes.

On rare-positive data with overlapping rules that are strong *lifts* but
weak absolute probabilities, the no-bias model must give every rule a
negative weight, so examples firing several rules — the most suspicious
ones — score lowest: ranking inverts. This was observed on the real ULB
credit-card data (fitted thetas ~ -2.5, frauds concentrated at five fired
rules, AUC 0.076). With a learnable intercept the weights become positive
lifts around the base rate and ranking is restored.
"""

import math

from pla.learn import RuleSpec, RuleWeightLearner, _sigmoid
from pla.metrics import roc_auc


def imbalanced_overlap_dataset():
    """Deterministic multiset reproducing the real-data pathology: five
    single-antecedent rules, each ~5% precision when firing alone, but
    60% fraud when all five fire together — and, crucially, NO rule for
    the combination, so the additive model can only sum the five weights.
    Mirrors the ULB observation (frauds concentrated at five fired rules)."""
    dataset = []
    dataset += [(frozenset(), frozenset(), 0)] * 9900
    dataset += [(frozenset(), frozenset(), 1)] * 5
    for name in "ABCDE":
        dataset += [(frozenset({name}), frozenset(), 0)] * 190
        dataset += [(frozenset({name}), frozenset(), 1)] * 10
    dataset += [(frozenset("ABCDE"), frozenset(), 0)] * 40
    dataset += [(frozenset("ABCDE"), frozenset(), 1)] * 60
    return dataset


RULES = [RuleSpec((name,)) for name in "ABCDE"]


def test_bias_fixes_the_multi_fired_inversion():
    dataset = imbalanced_overlap_dataset()
    y = [label for _, _, label in dataset]

    plain = RuleWeightLearner(RULES)
    plain.fit(dataset, epochs=600, learning_rate=1.0)
    plain_auc = roc_auc(y, [plain.predict_proba(f, c) for f, c, _ in dataset])

    biased = RuleWeightLearner(RULES, use_bias=True)
    biased.fit(dataset, epochs=600, learning_rate=1.0)
    biased_auc = roc_auc(y, [biased.predict_proba(f, c) for f, c, _ in dataset])

    # Without the intercept, the jointly-strong A+B examples are ranked
    # below the A-only ones; with it, ranking is restored.
    assert biased_auc > plain_auc
    assert biased_auc > 0.9
    # The intercept absorbs the rare base rate...
    assert biased.bias < -2.0
    # ...so rule weights become positive lifts.
    assert all(theta > 0 for theta in biased.theta)


def test_bias_loss_is_monotone_and_no_fire_prediction_is_the_prior():
    dataset = imbalanced_overlap_dataset()
    learner = RuleWeightLearner(RULES, use_bias=True)
    history = learner.fit(dataset, epochs=300, learning_rate=1.0)
    for before, after in zip(history, history[1:]):
        assert after <= before + 1e-12
    assert math.isclose(
        learner.predict_proba(frozenset(), frozenset()),
        _sigmoid(learner.bias),
        abs_tol=1e-12,
    )


def test_bias_exports_to_engine_as_base_rate_prior():
    dataset = imbalanced_overlap_dataset()
    learner = RuleWeightLearner(RULES, use_bias=True)
    learner.fit(dataset, epochs=300, learning_rate=1.0)

    for facts in (frozenset({"A"}), frozenset({"A", "B"}), frozenset()):
        kb = learner.to_prob_kb(target="Fraud")
        for fact in facts:
            kb.add_fact(fact)
        engine_p, _ = kb.query("Fraud")
        assert math.isclose(
            engine_p, learner.predict_proba(facts, frozenset()), abs_tol=1e-9
        ), facts
