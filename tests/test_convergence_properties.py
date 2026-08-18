"""Property-based convergence guarantees for the fixpoint iteration.

For random rule systems — cyclic ones included — and each aggregation
method, we check four properties against a reference implementation of one
inference round G:

1. the trajectory x0, G(x0), G(G(x0)), ... is pointwise non-decreasing;
2. every value stays in [0, 1];
3. the trajectory reaches an epsilon-fixpoint (max delta <= EPSILON);
4. the engine's result agrees with the reference limit, and applying one
   more round to the engine's result changes nothing beyond tolerance.

350 examples x 3 aggregation methods = 1050 random cases per run.
"""

import math

import pytest
from hypothesis import given, settings, strategies as st

from pla.prob import EPSILON, ProbKB, ProbRule, ProbSymbol, aggregate_supports

EXAMPLES_PER_METHOD = 350
AGGREGATION_METHODS = ["max", "noisy_or", "sum_cap"]
PROBS = [round(0.05 * i, 2) for i in range(1, 20)]  # 0.05 .. 0.95
MAX_REFERENCE_ROUNDS = 20000


@st.composite
def rule_systems(draw):
    n_facts = draw(st.integers(2, 4))
    n_derived = draw(st.integers(2, 4))
    facts = [f"F{i}" for i in range(n_facts)]
    derived = [f"D{i}" for i in range(n_derived)]
    symbols = facts + derived

    n_rules = draw(st.integers(1, 6))
    rules = []
    for _ in range(n_rules):
        antecedents = draw(
            st.lists(st.sampled_from(symbols), min_size=1, max_size=3, unique=True)
        )
        head = draw(st.sampled_from(derived))
        rules.append((antecedents, head, draw(st.sampled_from(PROBS))))

    if draw(st.booleans()):  # force an explicit seeded 2-cycle
        rules.append(([facts[0]], "D0", draw(st.sampled_from([0.1, 0.5, 0.9]))))
        rules.append((["D0"], "D1", draw(st.sampled_from([0.3, 0.6, 0.9]))))
        rules.append((["D1"], "D0", draw(st.sampled_from([0.3, 0.6, 0.9]))))

    return facts, rules


def build_kb(facts, rules, method):
    kb = ProbKB(aggregation_method=method)
    for fact in facts:
        kb.add_fact(ProbSymbol(fact))
    for antecedents, head, prob in rules:
        kb.add_rule(
            ProbRule([ProbSymbol(a) for a in antecedents], ProbSymbol(head), prob)
        )
    return kb


def reference_round(kb, prev):
    """One inference round G, mirroring ProbKB._forward_chain exactly."""
    nxt = {fact: 1.0 for fact in kb.facts}
    for rule in kb.rules:
        if all(c in prev for c in rule.condition):
            candidate = rule.adjusted_probability(
                kb.current_context, kb.context_mode
            ) * min(prev[c] for c in rule.condition)
            nxt[rule.result] = aggregate_supports(
                nxt.get(rule.result, 0.0), candidate, kb.aggregation_method
            )
    return nxt


def max_delta(a, b):
    keys = set(a) | set(b)
    return max(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


@pytest.mark.parametrize("method", AGGREGATION_METHODS)
@settings(max_examples=EXAMPLES_PER_METHOD, deadline=None)
@given(system=rule_systems())
def test_fixpoint_properties(method, system):
    facts, rules = system
    kb = build_kb(facts, rules, method)

    # Reference trajectory from the base-facts vector.
    x = {fact: 1.0 for fact in kb.facts}
    converged = False
    for _ in range(MAX_REFERENCE_ROUNDS):
        nxt = reference_round(kb, x)
        # Property 1: pointwise monotone (new keys only ever appear).
        for key, value in x.items():
            assert nxt[key] >= value - 1e-12
        # Property 2: bounded.
        assert all(0.0 <= v <= 1.0 + 1e-12 for v in nxt.values())
        if max_delta(nxt, x) <= EPSILON:
            x = nxt
            converged = True
            break
        x = nxt

    # Property 3: an epsilon-fixpoint is reached.
    assert converged

    # Property 4: the engine agrees with the reference limit, and the
    # engine's own answer is itself an epsilon-fixpoint.
    engine_probs, _ = kb._forward_chain()
    assert max_delta(engine_probs, x) <= 1e-6
    assert max_delta(reference_round(kb, engine_probs), engine_probs) <= 1e-8


def test_slow_cycle_still_converges_within_engine_budget():
    # Regression: high-probability cycle with a weak seed converges slowly
    # (geometric rate close to 1); the old 10*rules cap was too small for
    # cases like this.
    kb = build_kb(
        ["F0"],
        [
            (["F0"], "D0", 0.05),
            (["D0"], "D1", 0.95),
            (["D1"], "D0", 0.95),
        ],
        "noisy_or",
    )
    engine_probs, _ = kb._forward_chain()
    assert max_delta(reference_round(kb, engine_probs), engine_probs) <= 1e-8
    # Closed form: d0 = 1-(1-0.05)(1-0.95*d1), d1 = 0.95*d0.
    d0 = 0.05 / (1 - 0.95 * 0.95 * (1 - 0.05))
    assert math.isclose(engine_probs[ProbSymbol("D0")], d0, abs_tol=1e-6)
