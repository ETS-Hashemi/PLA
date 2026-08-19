# Results

Files here are **generated** by `scripts/run_experiments.py`,
`scripts/run_fidelity.py`, and `scripts/make_case_study.py` — regenerate,
never hand-edit. Every AUC and average precision (AP) carries a seeded
percentile-bootstrap 95% CI; fidelity files carry the paired-bootstrap
CI of the trace-minus-control difference. The paper's tables print from
these files via `scripts/make_paper_tables.py`, and its data figures via
`scripts/make_figures.py`.

| Files | Dataset / design | Nature |
|---|---|---|
| `experiment_synthetic_*`, `fidelity_synthetic_*` | Seeded synthetic (planted logistic ground truth) | Harness validation |
| `experiment_creditcard_real*.{csv,md}` | **Real** ULB credit-card fraud, split seeds 42/43/44 | Real-data study I |
| `fidelity_creditcard_real.*`, `case_study_creditcard.md` | same | Fidelity + worked trace exhibit |
| `experiment_bao2020_real.*`, `fidelity_bao2020_real.*` | **Real** Bao et al. 2020, strict temporal split (≤2001 / ≥2003) | Real-data study II |
| `experiment_bao2020_sox.*`, `fidelity_bao2020_sox.*` | **Real** Bao et al. 2020, SOX-boundary design (train ≤2005 spans the 2003 regime change, test ≥2008) | The context-mechanism test |

Headline findings (full framing and caveats in `paper/`):

- **Credit card:** the interpretable frontier leads on both metrics
  (seed 42: EBM 0.9815 AUC / 0.8642 AP, LR 0.9796 / 0.7849); the
  11-rule PLA model tracks it at 0.013–0.026 AUC across three seeds
  (static 0.9525–0.9687, learned 0.9485–0.9628), CIs overlapping, with
  static AP retaining most of the frontier's early ranking power
  (0.66–0.73 vs. LR's 0.75–0.78).
- **Learning is a measured trade.** MLE weights cut log-loss by ~a third
  and ECE by ~6× (0.0022) — and give up 0.13–0.19 AP vs. the static
  rules across seeds, a top-of-ranking cost AUC conceals. Calibrated
  scores for thresholds/expected-cost decisions; static scores for
  fixed-budget queues.
- **Context-conditioning verdict (pre-registered): negative.** Under the
  SOX design built to make the context weight identifiable: 0.4651 vs
  0.4640 AUC, 0.0038 vs 0.0037 AP; AUC null on credit card (0.9625 vs
  0.9630); within-CI sliver on strict Bao. One post-hoc,
  hypothesis-generating exception recorded honestly: a small seed-stable
  AP edge for the context variant on credit card only (0.53–0.55 vs
  0.49–0.50), absent under both drift designs — and AP was not the
  pre-registered metric.
- **Accounting drift:** all rule models near chance post-boundary while
  raw-ratio LR reaches 0.68–0.70 AUC (but only 0.0112 AP against a
  0.0061 prevalence — thin absolute signal for everyone) — vocabulary
  drift that reweighting cannot rescue; scopes the next iteration (rule
  re-mining, richer context features, full Bao protocol).
- **Fidelity:** static traces beat the reversed control on
  comprehensiveness *and* sufficiency on all four datasets, and the
  paired-bootstrap Δ CIs exclude zero everywhere (Δ 0.0026–0.0358);
  calibrated rare-event deltas compress toward the display floor (move
  to log-odds units next).
- **Baseline honesty:** untuned gradient boosting collapses at 0.17%
  prevalence (0.7159); simple class weighting repairs it (0.9598 AUC /
  0.7899 AP); both rows are reported.
- **Intercept lesson:** without the standard logistic intercept the
  learned model inverted on real data (AUC 0.076 → 0.9625 with it);
  regression test in `tests/test_bias_learning.py`, pre-fix table in git
  history.
- **Case study:** one real fraud fires 11/11 rules → static 0.4929 vs
  base rate 0.0017; deleting the top rule's facts drops it to 0.2552 —
  the trace-plus-counterfactual artifact none of the baselines produce.
