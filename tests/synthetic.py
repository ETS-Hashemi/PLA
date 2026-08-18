"""Shared synthetic data generator for the learning tests.

Ground-truth model in the learner's family: two rules over three
propositions, one context variable. Labels are drawn from the true model,
so the learner's MLE should recover the parameters up to sampling error.
"""

import random

from pla.learn import RuleSpec, _sigmoid

RULES = [
    RuleSpec(("LargeTransaction", "NoReceipt"), context_vars=("EconomicDownturn",)),
    RuleSpec(("UnusualVendor",)),
]

TRUE_THETA = [1.5, -0.5]
TRUE_CTX = [{"EconomicDownturn": 1.0}, {}]

PROPOSITIONS = ["LargeTransaction", "NoReceipt", "UnusualVendor"]
CONTEXT_VARS = ["EconomicDownturn"]


def make_dataset(n=400, seed=0):
    rng = random.Random(seed)
    dataset = []
    for _ in range(n):
        facts = frozenset(p for p in PROPOSITIONS if rng.random() < 0.6)
        context = frozenset(v for v in CONTEXT_VARS if rng.random() < 0.5)
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
