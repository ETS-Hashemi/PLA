"""Gradient learning of rule and context weights. Pure Python, no deps.

This trains the engine's differentiable path. For a rule
``r = (A_r -> T, p_r, w_r)`` evaluated on binary facts, the engine in
``context_mode="logit"`` with ``aggregation_method="logit_pool"`` computes

    z_r    = logit(p_r) + sum of w_r[v] over active context variables v
    c(T)   = sigmoid( sum of z_r over rules whose antecedents all hold )

so prediction is logistic regression whose features are rule firings and
context interactions. That makes the loss (binary cross-entropy) convex in
the parameters theta_r = logit(p_r) and w_r[v], and full-batch gradient
descent decreases it monotonically for a small enough learning rate.

The learner is exactly tied to the engine: ``to_prob_kb()`` exports the
learned parameters as a ProbKB, and predictions agree with ``kb.query``
(see tests/test_learning.py). When no rule fires the engine reports 0.0;
the learner uses a small floor instead so the loss stays finite, and such
examples contribute no gradient.

Training data format: each example is
``({"active", "propositions"}, {"active", "context", "vars"}, label01)``.
"""

import math


def _sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


class RuleSpec:
    """Structure of one learnable rule: antecedents and context variables."""

    def __init__(self, antecedents, context_vars=()):
        self.antecedents = tuple(antecedents)
        self.context_vars = tuple(context_vars)

    def __repr__(self):
        return f"RuleSpec({self.antecedents}, ctx={self.context_vars})"


class RuleWeightLearner:
    """Fit rule base weights (theta = logit of rule confidence) and context
    weights (log-odds deltas) by full-batch gradient descent on BCE."""

    NO_FIRE_FLOOR = 1e-3

    def __init__(self, rules):
        self.rules = list(rules)
        self.theta = [0.0] * len(self.rules)
        self.context_weights = [
            {var: 0.0 for var in rule.context_vars} for rule in self.rules
        ]

    def _fired(self, facts):
        return [
            index
            for index, rule in enumerate(self.rules)
            if all(a in facts for a in rule.antecedents)
        ]

    def _z(self, index, context):
        weights = self.context_weights[index]
        return self.theta[index] + sum(
            weight for var, weight in weights.items() if var in context
        )

    def predict_proba(self, facts, context=()):
        fired = self._fired(facts)
        if not fired:
            return self.NO_FIRE_FLOOR
        return _sigmoid(sum(self._z(index, context) for index in fired))

    def loss(self, dataset):
        total = 0.0
        for facts, context, label in dataset:
            p = min(max(self.predict_proba(facts, context), 1e-9), 1.0 - 1e-9)
            total += -(label * math.log(p) + (1 - label) * math.log(1.0 - p))
        return total / len(dataset)

    def fit(self, dataset, epochs=300, learning_rate=0.5):
        """Full-batch gradient descent. Returns the per-epoch loss history,
        starting with the pre-training loss."""
        history = [self.loss(dataset)]
        n = len(dataset)
        for _ in range(epochs):
            grad_theta = [0.0] * len(self.rules)
            grad_ctx = [{var: 0.0 for var in w} for w in self.context_weights]
            for facts, context, label in dataset:
                fired = self._fired(facts)
                if not fired:
                    continue  # floor prediction: no parameters involved
                p = _sigmoid(sum(self._z(index, context) for index in fired))
                err = (p - label) / n  # d BCE / d z, averaged
                for index in fired:
                    grad_theta[index] += err
                    for var in self.context_weights[index]:
                        if var in context:
                            grad_ctx[index][var] += err
            for index in range(len(self.rules)):
                self.theta[index] -= learning_rate * grad_theta[index]
                for var in self.context_weights[index]:
                    self.context_weights[index][var] -= learning_rate * grad_ctx[index][var]
            history.append(self.loss(dataset))
        return history

    def to_prob_kb(self, target="Target"):
        """Export learned parameters as a ProbKB on the engine's logit path."""
        from .prob import ProbKB, ProbRule, ProbSymbol

        kb = ProbKB(aggregation_method="logit_pool", context_mode="logit")
        head = ProbSymbol(target)
        for index, rule in enumerate(self.rules):
            kb.add_rule(
                ProbRule(
                    [ProbSymbol(a) for a in rule.antecedents],
                    head,
                    _sigmoid(self.theta[index]),
                    context=dict(self.context_weights[index]),
                )
            )
        return kb
