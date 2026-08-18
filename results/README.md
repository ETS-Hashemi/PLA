# Results

Files here are **generated** by `scripts/run_experiments.py` — regenerate,
never hand-edit. The from-scratch reproduction is part of the test suite
and the E4 verification.

- `experiment_synthetic_*.{csv,md}` — development results on the seeded
  synthetic sample (planted logistic ground truth). They validate the
  harness, **not** PLA's real-world performance; real-data results
  (`--data data/creditcard.csv` after running the E1 fetch) replace them
  for any paper claim.

Development finding worth carrying forward (synthetic n2000 seed0): the
learned PLA variant converges to much better calibration than the static
empirical-precision rules (log-loss 0.478 vs 1.091) but a lower AUC
(0.594 vs 0.722) — the discretized rules lose most of the planted
continuous signal, and MLE spends it on calibration. Both trail the raw-
feature baselines, as expected on data whose true model is logistic in the
raw features. The real-data experiment is the one that answers RQ1.
