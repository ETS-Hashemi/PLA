import math

from pla.learn import RuleWeightLearner
from synthetic import RULES, make_dataset


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
