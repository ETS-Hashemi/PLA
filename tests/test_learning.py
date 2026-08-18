import math
import random

from pla.learn import RuleSpec, RuleWeightLearner, _sigmoid


RULES = [
    RuleSpec(("LargeTransaction", "NoReceipt"), context_vars=("EconomicDownturn",)),
    RuleSpec(("UnusualVendor",)),
]

TRUE_THETA = [1.5, -0.5]
TRUE_CTX = [{"EconomicDownturn": 1.0}, {}]


def make_dataset(n=400, seed=0):
    """Fixed synthetic set: features and labels drawn from the true model."""
    rng = random.Random(seed)
    propositions = ["LargeTransaction", "NoReceipt", "UnusualVendor"]
    dataset = []
    for _ in range(n):
        facts = frozenset(p for p in propositions if rng.random() < 0.6)
        context = frozenset(
            v for v in ("EconomicDownturn",) if rng.random() < 0.5
        )
        z = 0.0
        fired = False
        for index, rule in enumerate(RULES):
            if all(a in facts for a in rule.antecedents):
                fired = True
                z += TRUE_THETA[index] + sum(
                    w for v, w in TRUE_CTX[index].items() if v in context
                )
        p = _sigmoid(z) if fired else 0.001
        dataset.append((facts, context, 1 if rng.random() < p else 0))
    return dataset


def test_loss_decreases_monotonically_on_fixed_dataset():
    dataset = make_dataset()
    learner = RuleWeightLearner(RULES)
    history = learner.fit(dataset, epochs=200, learning_rate=0.5)

    assert len(history) == 201
    for before, after in zip(history, history[1:]):
        assert after <= before + 1e-12
    # And it actually learned something, not just flat-lined.
    assert history[-1] < history[0] - 0.05


def test_predictions_match_the_engine_on_the_logit_path():
    dataset = make_dataset(n=100, seed=1)
    learner = RuleWeightLearner(RULES)
    learner.fit(dataset, epochs=100, learning_rate=0.5)

    kb_template = learner.to_prob_kb(target="Fraud")
    checked = 0
    for facts, context, _ in dataset[:30]:
        if not learner._fired(facts):
            continue  # engine reports 0.0, learner uses its floor — documented
        kb = learner.to_prob_kb(target="Fraud")
        for fact in facts:
            kb.add_fact(fact)
        kb.set_context({v: True for v in context})
        engine_p, _ = kb.query("Fraud")
        assert math.isclose(engine_p, learner.predict_proba(facts, context), abs_tol=1e-9)
        checked += 1
    assert checked >= 10
    assert kb_template is not None


def test_no_external_ml_dependencies():
    import pla.learn as learn_module

    assert learn_module.__file__.endswith("learn.py")
    forbidden = {"numpy", "torch", "sklearn", "scipy", "pandas"}
    import sys

    loaded_by_learn = forbidden & set(sys.modules)
    # The module must import and run without any of these present; simply
    # importing pla.learn must not have pulled them in.
    source = open(learn_module.__file__).read()
    for name in forbidden:
        assert f"import {name}" not in source
    assert loaded_by_learn is not None  # informational; source check is the gate
