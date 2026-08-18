import math
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "examples"))


from run_hybrid_demo import build_kbs  # noqa: E402
from pla.engine import HybridEngine  # noqa: E402


def test_hard_gate_passes_entailed_query_with_nonzero_probability():
    symbolic, prob = build_kbs()
    engine = HybridEngine(symbolic, prob, gate_mode="hard")

    result = engine.query("AuditRequired")
    assert result["symbolic_entails"] is True
    assert result["warning"] is None
    assert math.isclose(result["probability"], 0.85, abs_tol=1e-9)


def test_hard_gate_blocks_non_entailed_query():
    symbolic, prob = build_kbs()
    engine = HybridEngine(symbolic, prob, gate_mode="hard")

    result = engine.query("RegulatorReport")
    assert result["symbolic_entails"] is False
    assert result["probability"] == 0.0
    assert result["warning"] == "hard_gate_blocked"
    # The probabilistic layer had real support; the gate is what zeroed it.
    assert math.isclose(result["raw_probabilistic"], 0.51, abs_tol=1e-9)


def test_soft_gate_penalizes_instead_of_blocking():
    symbolic, prob = build_kbs()
    engine = HybridEngine(symbolic, prob, gate_mode="soft", gate_penalty=0.5)

    result = engine.query("RegulatorReport")
    assert result["symbolic_entails"] is False
    assert result["warning"] == "soft_gate_penalty_applied"
    assert math.isclose(result["probability"], 0.255, abs_tol=1e-9)


def test_constraint_mode_is_a_documented_no_op_without_negation():
    symbolic, prob = build_kbs()
    engine = HybridEngine(symbolic, prob, gate_mode="constraint")

    result = engine.query("RegulatorReport")
    # No negation in the symbolic layer means nothing can be contradicted:
    # the probability passes through untouched, flagged by a warning.
    assert result["warning"] == "constraint_mode_no_symbolic_support"
    assert math.isclose(result["probability"], 0.51, abs_tol=1e-9)
