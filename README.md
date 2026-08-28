# PLA — Probabilistic Logic Agent

[![CI](https://github.com/ETS-Hashemi/PLA/actions/workflows/ci.yml/badge.svg)](https://github.com/ETS-Hashemi/PLA/actions/workflows/ci.yml)

A small, fully transparent Python engine that forward-chains **rule
confidences** over propositional facts — with configurable support
aggregation, a maximum-likelihood **rule-weight learner**, symbolic
entailment gating, and per-rule **explanation traces** as the primary
output.

The engine is a few hundred lines of dependency-free Python you can read
end-to-end, which is the point: PLA is built for **teaching, auditing,
and trace-first prototyping** in domains where you must show a human
exactly why a conclusion was reached. It has been **measured on real
fraud data against strong baselines**, and the results — including one
clean, pre-registered negative — are summarized below and reported in
full in the accompanying manuscript.

## What the studies found

Five findings, all regenerable from the committed scripts (details,
confidence intervals, and caveats in [`results/`](results/README.md) and
[`paper/`](paper/README.md)):

- **Near-frontier ranking from 11 auditable rules.** On the ULB
  credit-card data (284,807 transactions, 0.17% fraud) the accuracy
  frontier is itself interpretable — EBM leads eight of ten random
  splits (mean AUC 0.9795 ± 0.0056) — and an 11-rule PLA model tracks
  it at 0.002–0.034 per split (static 0.9660 ± 0.0076, learned
  0.9602 ± 0.0088 over ten splits), confidence intervals overlapping;
  in average precision the static rules keep most of the frontier's
  early ranking power (0.67 ± 0.04 vs. 0.76 ± 0.03 for LR). The direct
  rule-model competitor splits the difference the honest way: RuleFit
  (pure rule ensemble, 26–30 mined rules) trails PLA static on AUC on
  all ten splits (0.9437 ± 0.0134) while beating it on AP on all ten
  (0.80 ± 0.03) — thresholds mined from raw features buy early
  precision; PLA's decile propositions buy AUC and per-rule provenance.
- **Learning is a measured trade, not a free upgrade.** On the
  credit-card study, fitting the
  weights beats the constant-prevalence null baseline on log-loss (0.0113 vs.
  0.0127) — but average precision exposes a real early-ranking cost
  that AUC hides: static 0.67 vs. learned 0.55 on average, with the
  paired-bootstrap confidence interval excluding zero on nine of ten
  splits. Calibrated scores for
  thresholds and expected-cost decisions; static scores for
  fixed-budget queues.
- **Context-conditioned weights: a pre-registered negative.** Context
  conditioning produced no practically useful improvement on the
  pre-specified AUC endpoint under any of three designs: the SOX paired
  ablation difference is ΔAUC 0.0011 [−0.0071, 0.0140] and ΔAP 0.0001
  [−0.0000, 0.0009] (a bound — no equivalence margin was prespecified,
  so none is claimed), and the credit-card paired ΔAUC contains zero on
  all ten splits. Reported per the kill criterion in
  [`research/GAP_STATEMENT.md`](research/GAP_STATEMENT.md) (commit
  `8f2dd2e`, before the experiments ran). One post-hoc exception is
  recorded honestly: a consistent AP edge for the context variant on
  credit card (paired CI excludes zero on all ten splits, +0.038 to
  +0.096, absent under both drift designs) — a hypothesis requiring
  confirmation, not a revision of the verdict.
- **Drift breaks rule *vocabulary*, not rule *reliability*.** On the Bao
  et al. accounting-fraud data, rules mined before the 2003 regime change
  rank later frauds near chance while raw-ratio logistic regression
  reaches 0.68–0.70 — reweighting (context-conditioned or otherwise)
  cannot rescue antecedents that stopped being informative.
- **Trace fidelity, with its exactness boundary drawn honestly.** In
  the flat experiments both models' rankings are provably the exact
  deletion ranking (noisy-OR gives s − s₋ᵢ = pᵢ·Π(1−pⱼ), monotone in
  pᵢ), so the deletion tables there are implementation-concordance
  checks — and they pass everywhere with paired CIs excluding zero.
  The genuinely fallible case is measured too: across 20 seeded
  chained programs, the local candidate ranking names the most
  load-bearing rule only 32.4% of the time (chance 25.8%) and captures
  ~49% of the oracle deletion impact — so for chained conclusions the
  artifact to trust is the engine's exported deletion counterfactual
  (leave-one-rule-out), not raw candidate magnitudes. The generated
  case study walks one real fraud through
  the engine — 11 rules fire, noisy-OR folds to 0.4929 against a
  0.0017 base rate — with exactly that leave-one-rule-out table, which
  none of the baselines produce.

One engineering lesson worth advertising: **keep the intercept.** Without
the standard logistic bias term, additive log-odds pooling of
strong-lift/low-probability rules *inverted* the ranking on real data
(AUC 0.076); with it, 0.9625. The regression test is
`tests/test_bias_learning.py`, and the pre-fix table is preserved in git
history.

## Install

```bash
pip install -e .                    # core engine + CLI (no dependencies)
pip install -e ".[api,dev]"         # + Flask REST API, pytest, hypothesis
pip install -e ".[experiments]"     # + scikit-learn, ProbLog, EBM baselines
```

## Quickstart

Run a scenario from the command line (context set 1 activates
`PatientAge>60` only):

```bash
pla scenarios/scenario_context_aware_medical.json 1
```

Reproduce the worked example below (its numbers are generated by this
script, not hand-written, and CI smoke-runs it on every push):

```bash
python examples/run_readme_scenario.py
```

```
=== README Scenario (aggregation=noisy_or) ===
Escalation supports:
  - rule_1: If DelayedShipment and HighPriorityOrder -> EscalationRequired (P=0.8): candidate_p=0.504
  - rule_2: If WeatherDisruption and DelayedShipment -> EscalationRequired (P=0.7): candidate_p=0.490
Aggregated EscalationRequired probability: 0.747040
CustomerNotification probability: 0.709688
```

See symbolic gating block, penalize, and pass a conclusion the policy
layer does not entail:

```bash
python examples/run_hybrid_demo.py
```

Serve the REST API (needs the `[api]` extra) and query it:

```bash
python -m pla.rest_api &
curl -X POST -H "Content-Type: application/json" \
     -d '{"config_path": "scenarios/scenario_context_aware_medical.json", "context_number": "1"}' \
     http://127.0.0.1:5000/load
curl -X POST -H "Content-Type: application/json" \
     -d '{"query": "LungCancerRisk"}' http://127.0.0.1:5000/query
```

Run the tests (104 collected; CI runs them on Python 3.9–3.12, where one
network-dependent download test skips itself):

```bash
python -m pytest tests/
```

## Semantics in five lines

- **Antecedent conjunction**: `min(p(a1), ..., p(an))`
- **Context adjustment**: `min(1, p_rule × Π weights)` in the default `legacy`
  mode, or additive log-odds deltas (`sigmoid(logit(p_rule) + Σ weights)`) with
  scenario-level `"context_mode": "logit"` — the latter never saturates at the cap
- **Support from one rule**: `candidate = p_rule_adjusted × min_antecedent`
- **Support aggregation** (configurable): `noisy_or` (default), `max`, `sum_cap`, `logit_pool`
- **Fixpoint**: rules re-fire until probabilities change by < 1e-9

Every formula block in [`docs/SEMANTICS.md`](docs/SEMANTICS.md) is
executed by the test suite, so the documentation cannot drift from the
code. Scenario format and the context-set mechanism: `docs/framework.md`
and `docs/methodology.md`.

## Learning rule weights

`RuleWeightLearner` fits rule confidences (and optional per-rule context
deltas) by maximum likelihood on `(facts, active_contexts, label)`
examples, then exports the fitted model back into the engine so the
learned weights speak the same trace vocabulary:

```python
from pla import RuleSpec, RuleWeightLearner

rules = [
    RuleSpec(("V14_low", "V12_low")),
    RuleSpec(("Amount_high",), context_vars=("NightTime",)),
]
data = [
    ({"V14_low", "V12_low"}, (), 1),          # (facts, active contexts, label)
    ({"Amount_high"}, ("NightTime",), 0),
    # ...
]

learner = RuleWeightLearner(rules, use_bias=True)   # keep the intercept!
learner.fit(data)
p = learner.predict_proba({"V14_low", "V12_low"})
kb = learner.to_prob_kb(target="Fraud")             # back into the engine,
                                                    # bias as a base-rate prior rule
```

On rare-event data, `use_bias=True` is not optional — see the intercept
lesson above. `scripts/build_rules.py` mines candidate rules (quantile
propositions scored by empirical precision) and `pla/pipeline.py` holds
the dataset schemas that turn CSV rows into examples.

## Scenario format

```json
{
  "facts": ["DelayedShipment", "HighPriorityOrder"],
  "rules": [
    {
      "condition": ["DelayedShipment", "HighPriorityOrder"],
      "result": "EscalationRequired",
      "confidence": 0.8,
      "context": {"DriverShortage": 0.9}
    }
  ],
  "queries": ["EscalationRequired"],
  "contexts": {"1": ["DriverShortage"]}
}
```

Context handling is fail-loud: malformed shapes, unknown context sets,
and typo'd variables raise `ScenarioFormatError` instead of silently
applying no adjustment. 34 ready-made scenarios live in `scenarios/`.

## What PLA is 

PLA's calculus sits in the **certainty-factor lineage** (MYCIN, Shortliffe
& Buchanan 1975): rules carry confidences, conjunction is `min(...)` (the
Gödel t-norm), and multiple supports for the same conclusion aggregate by
a configurable operator (noisy-OR by default). It is **not** a
probability distribution over possible worlds.

If you need proper distribution semantics, use
[ProbLog](https://dtai.cs.kuleuven.be/problog/) (`pip install problog`);
for weighted-logic learning at scale, see
[PSL](https://psl.linqs.org) (`pslpython`),
[pracmln](https://github.com/danielnyga/pracmln) (Markov Logic Networks in
Python), [pgmpy](https://github.com/pgmpy/pgmpy) (Bayesian networks), or
[DeepProbLog](https://github.com/ML-KULeuven/deepproblog) (neural-symbolic).
PLA trades their semantic guarantees for a calculus a student can trace
by hand, a JSON scenario format, and weights that remain auditable after
learning. The experiments run ProbLog and pgmpy *on PLA's own rules* as
cross-checks — that comparison is part of the test suite, not just prose.

## Reproducing the studies

Datasets are never committed (see [`data/README.md`](data/README.md) for
provenance, licenses, and integrity checks — row/label invariants plus a
trust-on-first-use sha256 sidecar). With the `[experiments]` extra
installed:

```bash
python scripts/fetch_fraud_data.py                  # ULB credit card (or --file your_download.csv)
python scripts/run_experiments.py --data data/creditcard.csv --tag creditcard_real
python scripts/run_fidelity.py    --data data/creditcard.csv --tag creditcard_real
python scripts/make_case_study.py --data data/creditcard.csv
```

The Bao et al. accounting-fraud runs use the same scripts with
`--schema bao2020` (strict temporal split) or `--schema bao2020sox` (the
SOX-boundary design); `--split-seed` reproduces the multi-seed study.
Every model, split, and bootstrap is seeded, so the scripts regenerate
the committed `results/` files **byte for byte** — regenerate, never
hand-edit. Every AUC carries a seeded percentile-bootstrap 95% CI.


## Repository layout

| Path | Contents |
|---|---|
| `pla/` | The engine: `prob.py`, `kb.py`, `engine.py`, `learn.py`, `pipeline.py`, `fidelity.py`, `metrics.py`, scenario loader, CLI, REST API |
| `scenarios/` | 34 JSON scenarios across audit, medical, logistics, pharma domains |
| `scripts/` | Data fetching, rule mining, experiments, baselines, fidelity, case study — everything that generates `results/` |
| `tests/` | 104-test pytest suite (semantics, property-based convergence, learning, claim verification), run in CI on Python 3.9–3.12 |
| `examples/` | Runnable demos that generate every number quoted in this README |
| `data/` | Dataset cache (gitignored) + provenance README |
| `results/` | Generated experiment, fidelity, and case-study tables (byte-reproducible) |
| `docs/` | Framework overview, executable formal semantics (`SEMANTICS.md`), methodology |
| `research/` | Reading list and the gap statement (hypotheses, baselines, kill criteria) |

## Research program

PLA is developed as part of the PhD research of **Seyed Masoud Hashemi
Ahmadi** at **École de technologie supérieure (ÉTS), Montréal**. The gap
statement in `research/GAP_STATEMENT.md` specifies each research question
with hypotheses, baselines, and kill criteria — and is held to: the
context-conditioning question was answered there **negatively** for the
coarse single-bit contexts tested. The questions it leaves open are
richer context features, rule re-mining under vocabulary drift,
log-odds-scale fidelity metrics, and uncertainty-aware verification of
LLM-extracted facts.

Contact: [seyedmasoud.hashemiahmadi.1@ens.etsmtl.ca](mailto:seyedmasoud.hashemiahmadi.1@ens.etsmtl.ca)

## License

Apache License 2.0 — see [LICENSE](LICENSE). If you use this work in
academic research, a citation is appreciated.
