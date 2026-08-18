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

    def __init__(self, rules, use_bias=False):
        """use_bias adds a learnable global intercept b: predictions become
        sigmoid(b + sum of fired z_r), and examples with no fired rule
        predict sigmoid(b) instead of the fixed floor. This is standard
        logistic regression with an intercept; without it, rules that are
        individually weak in absolute terms (precision far below 0.5) but
        strong lifts over a rare base rate are forced to negative weights,
        and stacking several fired rules then *inverts* the ranking —
        observed on real fraud data (see tests). The bias maps exactly onto
        the engine as a base-rate prior rule folded first by logit_pool."""
        self.rules = list(rules)
        self.use_bias = use_bias
        self.bias = 0.0
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
        z = sum(self._z(index, context) for index in fired)
        if self.use_bias:
            return _sigmoid(self.bias + z)
        if not fired:
            return self.NO_FIRE_FLOOR
        return _sigmoid(z)

    def loss(self, dataset):
        total = 0.0
        for facts, context, label in dataset:
            p = min(max(self.predict_proba(facts, context), 1e-9), 1.0 - 1e-9)
            total += -(label * math.log(p) + (1 - label) * math.log(1.0 - p))
        return total / len(dataset)

    def fit(self, dataset, epochs=300, learning_rate=0.5):
        """Full-batch gradient descent. Returns the per-epoch loss history,
        starting with the pre-training loss."""
        n = len(dataset)
        # The dataset is fixed during fit: compile each example once into
        # (fired rule indices, active context vars per fired rule, label).
        compiled = []
        for facts, context, label in dataset:
            fired = self._fired(facts)
            active = [
                tuple(v for v in self.context_weights[i] if v in context)
                for i in fired
            ]
            compiled.append((fired, active, label))

        def compiled_loss():
            total = 0.0
            for fired, active, label in compiled:
                z = sum(
                    self.theta[i] + sum(self.context_weights[i][v] for v in vars_)
                    for i, vars_ in zip(fired, active)
                )
                if self.use_bias:
                    p = _sigmoid(self.bias + z)
                elif fired:
                    p = _sigmoid(z)
                else:
                    p = self.NO_FIRE_FLOOR
                p = min(max(p, 1e-9), 1.0 - 1e-9)
                total += -(label * math.log(p) + (1 - label) * math.log(1.0 - p))
            return total / n

        history = [compiled_loss()]
        for _ in range(epochs):
            grad_bias = 0.0
            grad_theta = [0.0] * len(self.rules)
            grad_ctx = [{var: 0.0 for var in w} for w in self.context_weights]
            for fired, active, label in compiled:
                if not fired and not self.use_bias:
                    continue  # floor prediction: no parameters involved
                z = sum(
                    self.theta[i] + sum(self.context_weights[i][v] for v in vars_)
                    for i, vars_ in zip(fired, active)
                )
                if self.use_bias:
                    z += self.bias
                err = (_sigmoid(z) - label) / n  # d BCE / d z, averaged
                if self.use_bias:
                    grad_bias += err
                for i, vars_ in zip(fired, active):
                    grad_theta[i] += err
                    for var in vars_:
                        grad_ctx[i][var] += err
            if self.use_bias:
                self.bias -= learning_rate * grad_bias
            for index in range(len(self.rules)):
                self.theta[index] -= learning_rate * grad_theta[index]
                for var in self.context_weights[index]:
                    self.context_weights[index][var] -= learning_rate * grad_ctx[index][var]
            history.append(compiled_loss())
        return history

    def to_prob_kb(self, target="Target"):
        """Export learned parameters as a ProbKB on the engine's logit path.

        With use_bias, the intercept exports as a base-rate prior: an
        always-true fact "BaseRate" and a rule BaseRate -> target with
        confidence sigmoid(bias). logit_pool folds it with the fired rules
        as sigmoid(bias + sum z_r) — exactly the learner's prediction."""
        from .prob import ProbKB, ProbRule, ProbSymbol

        kb = ProbKB(aggregation_method="logit_pool", context_mode="logit")
        head = ProbSymbol(target)
        if self.use_bias:
            base = ProbSymbol("BaseRate")
            kb.add_fact(base)
            kb.add_rule(ProbRule([base], head, _sigmoid(self.bias)))
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
