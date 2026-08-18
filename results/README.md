# Results

Files here are **generated** by `scripts/run_experiments.py`,
`scripts/run_fidelity.py`, and `scripts/make_case_study.py` — regenerate,
never hand-edit. Every AUC carries a seeded percentile-bootstrap 95% CI.

| Files | Dataset / design | Nature |
|---|---|---|
| `experiment_synthetic_*`, `fidelity_synthetic_*` | Seeded synthetic (planted logistic ground truth) | Harness validation |
| `experiment_creditcard_real*.{csv,md}` | **Real** ULB credit-card fraud, split seeds 42/43/44 | Real-data study I |
| `fidelity_creditcard_real.*`, `case_study_creditcard.md` | same | Fidelity + worked trace exhibit |
| `experiment_bao2020_real.*`, `fidelity_bao2020_real.*` | **Real** Bao et al. 2020, strict temporal split (≤2001 / ≥2003) | Real-data study II |
| `experiment_bao2020_sox.*`, `fidelity_bao2020_sox.*` | **Real** Bao et al. 2020, SOX-boundary design (train ≤2005 spans the 2003 regime change, test ≥2008) | The context-mechanism test |

Headline findings (full framing and caveats in `paper/`):

- **Credit card:** the interpretable frontier leads (EBM 0.9815, LR
  0.9796); 11-rule PLA sits within 0.013–0.019 of it (static 0.9687,
  learned 0.9625 with ECE 0.0022), stable across three seeds, CIs
  overlapping.
- **Context-conditioning verdict (pre-registered): negative.** Ablations
  (`pla_learned` vs `pla_learned_noctx`) show no reliable ranking
  benefit in any real design — null on credit card (0.9625 vs 0.963),
  within-CI sliver on strict Bao (0.4905 vs 0.4733), and nothing under
  the SOX design built to make the context weight identifiable (0.4651
  vs 0.464). The demonstrated value of learning is calibration.
- **Accounting drift:** all rule models near chance post-boundary while
  raw-ratio LR reaches 0.68–0.70 — vocabulary drift that reweighting
  cannot rescue; scopes the next iteration (rule re-mining, richer
  context features, full Bao protocol).
- **Fidelity:** static traces beat the reversed control on all four
  datasets; calibrated rare-event deltas compress toward zero (move to
  log-odds units next).
- **Intercept lesson:** without the standard logistic intercept the
  learned model inverted on real data (AUC 0.076 → 0.9625 with it);
  regression test in `tests/test_bias_learning.py`, pre-fix table in git
  history.
- **Case study:** one real fraud fires 11/11 rules → static 0.4929 vs
  base rate 0.0017; deleting the top rule's facts drops it to 0.2552 —
  the trace-plus-counterfactual artifact none of the baselines produce.
