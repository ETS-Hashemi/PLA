# Results

Files here are **generated** by `scripts/run_experiments.py`,
`scripts/run_fidelity.py`, `scripts/make_case_study.py`, and
`scripts/make_seed_summary.py` — regenerate, never hand-edit. Every AUC
and average precision (AP) carries a seeded percentile-bootstrap 95%
CI; `*_diffs.csv` files carry paired-bootstrap CIs for model
differences (the inference behind any no-difference claim); fidelity
files carry paired CIs of trace-minus-control margins at three levels
(fact deletion, rule deletion, rule deletion in log-odds). The paper's
tables print from these files via `scripts/make_paper_tables.py`, and
its data figures via `scripts/make_figures.py`.

| Files | Dataset / design | Nature |
|---|---|---|
| `experiment_synthetic_*`, `fidelity_synthetic_*` | Seeded synthetic (planted logistic ground truth) | Harness validation |
| `experiment_creditcard_real*.{csv,md}` (+`_diffs.csv`) | **Real** ULB credit-card fraud, split seeds 42–51 | Real-data study I |
| `seed_summary_creditcard.*` | same, aggregated over the ten splits | Split-variability summary |
| `fidelity_creditcard_real.*`, `case_study_creditcard.md` | same | Fidelity + worked trace exhibit (incl. leave-one-rule-out) |
| `experiment_bao2020_real.*`, `fidelity_bao2020_real.*` | **Real** Bao et al. 2020, strict temporal split (≤2001 / ≥2003) | Real-data study II |
| `experiment_bao2020_sox.*`, `fidelity_bao2020_sox.*` | **Real** Bao et al. 2020, SOX-boundary design (train ≤2005 spans the 2003 regime change, test ≥2008) | The context-mechanism test |

Headline findings (full framing and caveats in `paper/`):

- **Credit card (ten splits):** the interpretable frontier leads — EBM
  0.9795 ± 0.0056 AUC tops eight of ten splits — and the 11-rule PLA
  model tracks it at 0.002–0.034 per split (static 0.9660 ± 0.0076,
  learned 0.9602 ± 0.0088), CIs overlapping; static AP retains most of
  the frontier's early ranking power (0.67 ± 0.04 vs. LR 0.76 ± 0.03).
- **Learning is a measured trade.** MLE beats the constant-prevalence
  null baseline on log-loss (0.0113 vs. 0.0127; the baseline row appears in every
  table, and it scores ECE 0.0000 — equal-width ECE is a blunt
  instrument at these prevalences) while average precision pays: an AP
  loss vs. static whose paired-bootstrap CI excluded zero on nine of
  ten splits (mean ≈ −0.12).
- **Context-conditioning verdict (pre-registered): negative, with the
  correct inference.** No practically useful improvement on the
  pre-specified AUC endpoint under any design. SOX paired ablation
  difference: ΔAUC 0.0011 [−0.0071, 0.0140], ΔAP 0.0001 [−0.0000,
  0.0009] — reported as a bound (no equivalence margin was
  prespecified; the criterion at commit `8f2dd2e` was directional
  only). Credit-card paired ΔAUC contains zero on 10/10 splits. The
  strict design's small paired-real ΔAUC (+0.0172 [0.0019, 0.0373])
  sits between two below-chance models — detectable, not useful.
  Post-hoc exception, recorded honestly: a credit-card-only AP edge,
  paired CI excluding zero on 10/10 splits (+0.038 to +0.096), absent
  under both drift designs and not the pre-registered metric — a
  hypothesis awaiting confirmation.
- **Accounting drift:** all rule models near or below chance
  post-boundary while raw-ratio LR reaches 0.68–0.70 AUC (but only
  0.0080–0.0112 AP against 0.0040–0.0061 prevalence — thin absolute
  signal for everyone) — vocabulary drift that reweighting cannot
  rescue; scopes the next iteration (rule re-mining, richer context
  features, full Bao protocol).
- **Fidelity (rule level, the confound-free instrument):** static
  traces beat reversed *and* random controls on all four datasets with
  paired ΔCIs excluding zero; fact-level numbers run ~7–10% higher —
  the overlapping-antecedent inflation the rule level removes. The
  learned model's rule ranking is exact on log-odds by construction
  (contribution = z_r, unit-tested).
- **Baseline honesty:** untuned gradient boosting collapses at 0.17%
  prevalence (0.7159); class weighting repairs it (0.9598 AUC seed 42;
  it even tops one of ten splits); both rows reported, plus the
  constant-prevalence baseline everywhere.
- **Intercept lesson:** without the standard logistic intercept the
  learned model inverted on real data (AUC 0.076 → 0.9625 with it);
  regression test in `tests/test_bias_learning.py`, pre-fix table in git
  history.
- **Case study:** one real fraud fires 11/11 rules → static 0.4929 vs
  base rate 0.0017; deleting the top rule's facts drops it to 0.2552;
  the leave-one-rule-out table gives every rule's marginal contribution,
  with the learned log-odds column equal to z_r exactly.
