"""Differential and performance tests for the symbolic entailment layer.

Forward chaining (production path) must agree with truth-table model
checking (the exponential oracle) on random definite-clause KBs, and must
handle KBs far beyond the truth table's reach.
"""

import time

from hypothesis import given, settings, strategies as st

from pla.kb import And, KnowledgeBase, Symbol, model_check

EXAMPLES = 150


@st.composite
def definite_kbs(draw):
    n_symbols = draw(st.integers(2, 15))
    names = [f"S{i}" for i in range(n_symbols)]

    facts = draw(st.lists(st.sampled_from(names), max_size=3, unique=True))
    n_rules = draw(st.integers(0, 10))
    rules = []
    for _ in range(n_rules):
        antecedents = draw(
            st.lists(st.sampled_from(names), min_size=1, max_size=3, unique=True)
        )
        head = draw(st.sampled_from(names))
        rules.append((antecedents, head))

    queries = draw(st.lists(st.sampled_from(names), min_size=1, max_size=3, unique=True))
    return facts, rules, queries


@settings(max_examples=EXAMPLES, deadline=None)
@given(system=definite_kbs())
def test_forward_chaining_agrees_with_truth_table_oracle(system):
    facts, rules, queries = system

    kb = KnowledgeBase()
    for fact in facts:
        kb.add_fact(fact)
    for antecedents, head in rules:
        kb.add_rule(f"{' and '.join(antecedents)} -> {head}")

    knowledge = And(*kb.facts, *kb.rules)
    for query in queries:
        assert kb.query(query) == model_check(knowledge, Symbol(query))


def test_known_entailments():
    kb = KnowledgeBase()
    kb.add_fact("A")
    kb.add_fact("B")
    kb.add_rule("A and B -> C")
    kb.add_rule("C -> D")

    assert kb.query("A") is True          # base fact
    assert kb.query("C") is True          # one step
    assert kb.query("D") is True          # chained
    assert kb.query("E") is False         # unknown symbol
    assert KnowledgeBase().query("A") is False  # empty KB entails nothing


def test_200_symbol_chain_under_one_second():
    kb = KnowledgeBase()
    kb.add_fact("S0")
    for i in range(199):
        kb.add_rule(f"S{i} -> S{i + 1}")
    # A few multi-antecedent rules across the chain.
    for i in range(0, 190, 10):
        kb.add_rule(f"S{i} and S{i + 5} -> S{i + 9}")

    start = time.perf_counter()
    assert kb.query("S199") is True
    assert kb.query("Unreachable") is False
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"entailment took {elapsed:.3f}s"
