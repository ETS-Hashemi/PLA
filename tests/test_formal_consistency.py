import math
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "PLA-advanced"))

from prob import ProbKB, ProbRule, ProbSymbol
from kb import KnowledgeBase
from engine import HybridEngine


def _build_multi_support_kb(aggregation_method):
    a = ProbSymbol("A")
    b = ProbSymbol("B")
    c = ProbSymbol("C")

    kb = ProbKB(aggregation_method=aggregation_method)
    kb.add_fact(a)
    kb.add_fact(c)
    kb.set_context({"W": True})

    kb.add_rule(ProbRule([a], b, 0.8, context={"W": 1.2}))
    kb.add_rule(ProbRule([c], b, 0.5, context={"W": 1.2}))
    return kb, b


def test_multi_support_aggregation_max_and_noisy_or():
    kb_max, b = _build_multi_support_kb("max")
    max_prob, _ = kb_max.query(b)
    assert math.isclose(max_prob, 0.96, rel_tol=0, abs_tol=1e-9)

    kb_or, b = _build_multi_support_kb("noisy_or")
    noisy_prob, _ = kb_or.query(b)
    assert math.isclose(noisy_prob, 0.984, rel_tol=0, abs_tol=1e-9)


def test_symbolic_entailment_truth_table():
    kb = KnowledgeBase()
    kb.add_fact("A")
    kb.add_rule("A -> B")

    assert kb.query("B") is True


def test_hybrid_engine_returns_structured_output():
    symbolic_kb = KnowledgeBase()
    symbolic_kb.add_fact("A")
    symbolic_kb.add_rule("A -> B")

    prob_kb = ProbKB(aggregation_method="max")
    a = ProbSymbol("A")
    b = ProbSymbol("B")
    prob_kb.add_fact(a)
    prob_kb.add_rule(ProbRule([a], b, 0.7))

    engine = HybridEngine(symbolic_kb, prob_kb, gate_mode="soft", gate_penalty=0.5)
    result = engine.query("B")

    assert isinstance(result, dict)
    assert "symbolic_entails" in result
    assert "probability" in result
