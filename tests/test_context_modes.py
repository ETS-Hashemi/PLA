import json
import math
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

from pla.prob import ProbKB, ProbRule, ProbSymbol  # noqa: E402
from pla.scenario_loader import ScenarioFormatError, load_scenario  # noqa: E402


def build_kb(context_mode, weights):
    a = ProbSymbol("A")
    b = ProbSymbol("B")
    kb = ProbKB(context_mode=context_mode)
    kb.add_fact(a)
    kb.add_rule(ProbRule([a], b, 0.7, context=weights))
    kb.set_context({var: True for var in weights})
    return kb, b


def logit_expected(p, *deltas):
    return 1.0 / (1.0 + math.exp(-(math.log(p / (1.0 - p)) + sum(deltas))))


def test_legacy_saturates_identically_but_logit_distinguishes():
    # Two different strong-evidence combinations…
    strong = {"V": 1.2, "W": 1.5}    # 0.7*1.2*1.5 = 1.26 -> capped
    stronger = {"V": 1.2, "W": 3.0}  # 0.7*1.2*3.0 = 2.52 -> capped

    # …are indistinguishable in legacy mode (both cap at 1.0)…
    kb1, b = build_kb("legacy", strong)
    kb2, _ = build_kb("legacy", stronger)
    assert kb1.query(b)[0] == 1.0 == kb2.query(b)[0]

    # …but stay distinct and below 1.0 in logit mode.
    kb3, _ = build_kb("logit", {"V": 1.0, "W": 2.0})
    kb4, _ = build_kb("logit", {"V": 1.0, "W": 4.0})
    p3, p4 = kb3.query(b)[0], kb4.query(b)[0]
    assert p3 < p4 < 1.0
    assert math.isclose(p3, logit_expected(0.7, 1.0, 2.0), abs_tol=1e-12)
    assert math.isclose(p4, logit_expected(0.7, 1.0, 4.0), abs_tol=1e-12)


def test_logit_negative_weight_weakens_the_rule():
    kb, b = build_kb("logit", {"V": -1.0})
    prob, _ = kb.query(b)
    assert math.isclose(prob, logit_expected(0.7, -1.0), abs_tol=1e-12)
    assert prob < 0.7


def test_logit_extreme_base_probabilities_are_fixed_points():
    for base in (0.0, 1.0):
        a = ProbSymbol("A")
        b = ProbSymbol("B")
        kb = ProbKB(context_mode="logit")
        kb.add_fact(a)
        kb.add_rule(ProbRule([a], b, base, context={"V": 5.0}))
        kb.set_context({"V": True})
        assert kb.query(b)[0] == base


def test_legacy_mode_reproduces_existing_expected_values():
    # The canonical numbers from the context-bug fix (C1).
    kb, b = build_kb("legacy", {"V": 1.2})
    assert math.isclose(kb.query(b)[0], 0.84, abs_tol=1e-9)

    kb, b = build_kb("legacy", {"V": 1.2, "W": 1.5})
    assert math.isclose(kb.query(b)[0], 1.0, abs_tol=1e-9)


def test_invalid_context_mode_raises():
    with pytest.raises(ValueError):
        ProbKB(context_mode="bayesian")

    rule = ProbRule([ProbSymbol("A")], ProbSymbol("B"), 0.7, context={"V": 1.0})
    with pytest.raises(ValueError):
        rule.adjusted_probability({"V": True}, mode="nonsense")


def test_scenario_file_can_select_logit_mode(tmp_path):
    config = {
        "facts": ["A"],
        "rules": [
            {"condition": ["A"], "result": "B", "probability": 0.7,
             "context": {"V": 1.0}}
        ],
        "queries": ["B"],
        "context_mode": "logit",
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))

    scenario = load_scenario(path)
    scenario.activate("1")
    prob, _ = scenario.kb.query("B")
    assert math.isclose(prob, logit_expected(0.7, 1.0), abs_tol=1e-12)


def test_scenario_file_rejects_unknown_context_mode(tmp_path):
    config = {"facts": [], "rules": [], "queries": [], "context_mode": "fuzzy"}
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config))

    with pytest.raises(ScenarioFormatError):
        load_scenario(path)
