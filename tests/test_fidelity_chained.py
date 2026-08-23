"""The chained fidelity study (scripts/run_fidelity_chained.py): the
setting where the local trace ranking is genuinely fallible. These tests
pin determinism and the structural invariants; the paper-scale numbers
regenerate from the script with its defaults."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_fidelity_chained import run, run_program  # noqa: E402


def test_deterministic_across_runs(tmp_path):
    rows_a, _, _ = run(n_programs=2, n_examples=60, seed=0,
                       results_dir=tmp_path / "a")
    rows_b, _, _ = run(n_programs=2, n_examples=60, seed=0,
                       results_dir=tmp_path / "b")
    assert rows_a == rows_b


def test_oracle_is_a_ceiling_and_impacts_are_nonnegative():
    values, agreements, chance, fired_counts = run_program(
        program_seed=0, n_examples=80)
    n = len(values["trace"])
    assert n > 0 and len(fired_counts) == n
    for label in ("trace", "reversed_control", "random_control"):
        for oracle, other in zip(values["oracle"], values[label]):
            assert oracle >= other - 1e-12  # oracle maximizes deletion impact
    # Monotone system: deleting a rule can only lower the target.
    assert all(v >= -1e-12 for label in values for v in values[label])
    assert all(a in (0, 1) for a in agreements)
    assert all(0.0 < c <= 1.0 for c in chance)


def test_agreement_is_not_trivially_perfect():
    # The whole point of the chained design: nothing forces the local
    # ranking to find the oracle rule. If agreement were 1.0 the study
    # would have silently degenerated into the exact (flat) case.
    values, agreements, _, _ = run_program(program_seed=0, n_examples=150)
    assert 0 < sum(agreements) < len(agreements)
