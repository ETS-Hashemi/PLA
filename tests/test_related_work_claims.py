"""P1: machine-verify the related-work claims that are checkable here.

The paper's Section 2 makes factual claims about competitor systems. The
ones about packages installed in this environment are verified against the
systems themselves; bibliographic claims are covered by the reading list.
"""

import math

import pytest


def test_problog_is_python_with_distribution_semantics():
    """Claim: ProbLog is a Python package computing possible-world marginals."""
    problog = pytest.importorskip("problog")
    from problog import get_evaluatable
    from problog.program import PrologString

    assert problog is not None  # pip-installable Python package

    model = """
    0.3::x. 0.6::y.
    z :- x.
    z :- y.
    query(z).
    """
    result = get_evaluatable().create_from(PrologString(model)).evaluate()
    p_z = next(v for k, v in result.items() if str(k) == "z")
    # Possible worlds: P(z) = 1 - (1-0.3)(1-0.6) = 0.72
    assert math.isclose(p_z, 0.72, abs_tol=1e-9)


def test_problog_supports_evidence_conditioning_which_pla_lacks():
    """Claim: ProbLog conditions on evidence; PLA has no such operation."""
    pytest.importorskip("problog")
    from problog import get_evaluatable
    from problog.program import PrologString

    model = """
    0.3::x. 0.6::y.
    z :- x.
    z :- y.
    evidence(z, true).
    query(x).
    """
    result = get_evaluatable().create_from(PrologString(model)).evaluate()
    p_x_given_z = next(v for k, v in result.items() if str(k) == "x")
    # P(x | z) = P(x) / P(z) = 0.3 / 0.72
    assert math.isclose(p_x_given_z, 0.3 / 0.72, abs_tol=1e-9)

    # And the corresponding PLA fact: the public engine API has no
    # conditioning/evidence operation.
    import pla

    assert not any("evidence" in name.lower() or "condition" == name.lower()
                   for name in dir(pla.ProbKB))


def test_pgmpy_provides_joint_distribution_posteriors():
    """Claim: pgmpy computes Bayes-rule posteriors (PLA does not)."""
    pytest.importorskip("pgmpy")
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.inference import VariableElimination

    try:
        from pgmpy.models import DiscreteBayesianNetwork as Network
    except ImportError:
        from pgmpy.models import BayesianNetwork as Network

    model = Network([("C", "A")])
    model.add_cpds(
        TabularCPD("C", 2, [[0.4], [0.6]]),
        TabularCPD("A", 2, [[0.7, 0.2], [0.3, 0.8]], evidence=["C"], evidence_card=[2]),
    )
    posterior = VariableElimination(model).query(["C"], evidence={"A": 1}).values
    # P(C=1 | A=1) = 0.6*0.8 / (0.6*0.8 + 0.4*0.3) = 0.8
    assert math.isclose(float(posterior[1]), 0.8, abs_tol=1e-9)


def test_noisy_or_is_mycin_parallel_combination():
    """Claim: PLA's noisy_or equals the certainty-factor combination rule
    CF = CF1 + CF2 * (1 - CF1) for positive evidence."""
    from pla.prob import aggregate_supports

    for cf1, cf2 in [(0.3, 0.6), (0.504, 0.49), (0.9, 0.99), (0.0, 0.7)]:
        mycin = cf1 + cf2 * (1 - cf1)
        assert math.isclose(
            aggregate_supports(cf1, cf2, "noisy_or"), mycin, abs_tol=1e-12
        )


def test_rulefit_config_is_a_pure_rule_ensemble():
    """Claim (Sections 2 and 6): the RuleFit baseline is configured as a
    pure rule ensemble — max_rules=30, no linear terms — so every selected
    term is a conjunctive rule, the direct competitor to PLA's rules."""
    pytest.importorskip("imodels")
    import warnings

    from imodels import RuleFitClassifier

    X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]] * 25
    y = [1 if a > 0.5 and b > 0.5 else 0 for a, b in X]
    model = RuleFitClassifier(max_rules=30, include_linear=False,
                              random_state=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(X, y)
        proba = model.predict_proba(X)
    selected = model._get_rules()
    assert len(selected) <= 30
    # No linear terms: every candidate term is a rule (a threshold
    # conjunction), never a bare feature passthrough.
    if "type" in selected.columns:
        assert set(selected["type"]) <= {"rule"}
    assert len(proba) == len(X)
