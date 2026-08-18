# Results

Files here are **generated** by `scripts/run_experiments.py` and
`scripts/run_fidelity.py` — regenerate, never hand-edit. From-scratch
reproduction is part of the test suite and the E4 verification.

| Files | Dataset | Nature |
|---|---|---|
| `experiment_synthetic_*`, `fidelity_synthetic_*` | Seeded synthetic (planted logistic ground truth) | Harness validation |
| `experiment_creditcard_real.*`, `fidelity_creditcard_real.*` | **Real** ULB credit-card fraud (invariant-verified; see `data/README.md`) | Real-data study I |
| `experiment_bao2020_real.*`, `fidelity_bao2020_real.*` | **Real** Bao et al. 2020 accounting fraud (temporal split ≤2001 / ≥2003) | Real-data study II |

Headline findings (details and caveats in `paper/`):

- **Credit card:** 11-rule PLA reaches AUC 0.9687 (static) / 0.9625
  (learned, ECE 0.0022) vs 0.9796 for raw-feature logistic regression;
  ProbLog on the same rules cross-validates at 0.9610 (subset).
- **Intercept lesson:** without the standard logistic intercept the
  learned model *inverted* on real data (AUC 0.076 — negative weights on
  jointly-strong rules); the intercept repairs it to 0.9625. Pre-fix
  table preserved in git history; regression test in
  `tests/test_bias_learning.py`.
- **Accounting drift:** honest negative under a simplified temporal
  protocol — PLA rules ≈ chance post-2003 (0.53) vs 0.677 for raw-ratio
  logistic regression; reported per the pre-registered kill criterion,
  with the protocol gaps that scope the next iteration.
- **Fidelity:** static traces beat the reversed control on every
  dataset; calibrated rare-event models compress absolute deletion
  deltas toward zero — move to log-odds units next.

With the intercept, the synthetic learned model matches static ranking
(0.7227 vs 0.7217) and wins calibration (log-loss 0.342 vs 1.091) — the
earlier "calibration-vs-AUC trade-off" was an artifact of the missing
intercept.
