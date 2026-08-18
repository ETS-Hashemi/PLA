"""L2: the learner recovers known ground-truth weights from sampled data.

Datasets are generated from a fixed true model (tests/synthetic.py); the
fitted parameters must land within tolerance of the truth on three
different seeds. Seeds and optimizer are deterministic, so this test has
no flake surface — the tolerances absorb sampling error only.
"""

import pytest

from pla.learn import RuleWeightLearner
from synthetic import RULES, TRUE_CTX, TRUE_THETA, make_dataset

THETA_TOLERANCE = 0.35
CTX_TOLERANCE = 0.45


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_learner_recovers_ground_truth_weights(seed):
    dataset = make_dataset(n=3000, seed=seed)
    learner = RuleWeightLearner(RULES)
    history = learner.fit(dataset, epochs=1200, learning_rate=2.0)

    # Optimization made real progress and effectively converged.
    assert history[-1] < history[0]
    assert abs(history[-1] - history[-2]) < 1e-7

    for index, true_theta in enumerate(TRUE_THETA):
        assert abs(learner.theta[index] - true_theta) <= THETA_TOLERANCE, (
            f"seed {seed}: theta[{index}]={learner.theta[index]:.3f} "
            f"vs true {true_theta}"
        )
    for index, true_ctx in enumerate(TRUE_CTX):
        for var, true_weight in true_ctx.items():
            got = learner.context_weights[index][var]
            assert abs(got - true_weight) <= CTX_TOLERANCE, (
                f"seed {seed}: w[{index}][{var}]={got:.3f} vs true {true_weight}"
            )
