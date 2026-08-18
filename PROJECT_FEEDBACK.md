# PLA Project Review

An end-to-end review of this repository: the three code generations
(`Archive/PLA/PLA-V1-Archive/`, `Archive/PLA/`, `PLA-advanced/`), the engine,
KB and probabilistic modules, the paper draft, methodology, tests, and
scenario files. Both test suites were run (7/7 pass) and the README example
(`examples/run_readme_scenario.py`) reproduces its documented numbers exactly.

## Overall

This is a coherent, working research prototype with genuinely good instincts —
small readable modules, explanation traces built in from the start, scenario
configs as data, and a recently much-improved probabilistic core. But there is
a real gap between what the code **is** (a well-built educational
confidence-propagation system) and what the README/paper **claim** it is (a
novel probabilistic framework with "VERY HIGH" publication chance). There is
also one concrete bug: the headline context-aware feature silently never
activates for most of the shipped scenarios.

## What is genuinely good

- **The PR #1 semantics work was a big step up.** Explicit, configurable
  support aggregation (`max`, `noisy_or`, `sum_cap`, `logit_pool`), fixpoint
  iteration with epsilon convergence, per-rule support traces, and
  `examples/run_readme_scenario.py` as the single source of truth for README
  numbers. That last one is a practice most research code never adopts — the
  README numbers actually reproduce.
- Everything runs and tests pass with essentially zero dependencies. For the
  stated educational goal, the codebase is legitimately teachable.
- Explainability is real, not aspirational: `ProbKB.query_detailed()` returns
  per-rule candidates, antecedents, and the context used.

## The two biggest risks for the research goal

### 1. Positioning against the literature

The root README claims this would be the "first lightweight Python framework
combining symbolic logic with uncertainty," and the paper draft's related-work
section cites only Pearl, Russell & Norvig, and Clarke. A RuleML/IJCAI
reviewer will immediately ask about:

- **ProbLog / DeepProbLog** — Python, exactly symbolic + probabilistic, with
  proper distribution semantics;
- **Markov Logic Networks** and **Probabilistic Soft Logic**;
- **MYCIN-style certainty factors** (1970s) — the closest ancestor of the
  mechanism implemented here.

The novelty claim as written will not survive review. The defensible
contributions are different ones: pedagogical transparency, trace-first
explanations, and the context-adjustment mechanism. Position the paper there.

### 2. The semantics are not probabilities

- `min()` over antecedents (`prob.py`, `_forward_chain`) is the Gödel t-norm
  (fuzzy logic), not probabilistic conjunction.
- Multiplying by context weights > 1 and capping at 1.0
  (`ProbRule.adjusted_probability`) is ad hoc — the project's own test asserts
  P = 1.0 after 0.7 × 1.2 × 1.5 saturates the cap, i.e. the cap destroys
  information.
- There is no underlying event space, so calling the outputs "probabilities"
  invites the harshest reviewer question there is.

Two honest paths: adopt distribution semantics (hard — and then it competes
head-on with ProbLog), or reframe as a **confidence/plausibility propagation
system** with explicitly stated operators and cited lineage (certainty
factors, fuzzy logic). Note the `logit_pool` machinery already exists — doing
context adjustment additively in log-odds instead of multiply-and-cap would
fix the saturation problem elegantly.

## Bug: context-aware reasoning mostly does not fire

Two context formats coexist in the scenario files:

- **flat** — `"context": {"SmokingHistory": 1.5}` — used by all
  `scenario_context_aware_*.json` files;
- **nested** — `"context": {"1": {...}, "2": {...}}` — used by the
  `*_parallel.json` files.

Both `PLA-advanced/main.py` (context build loop) and
`PLA-advanced/rest_api.py` (`/load`) build the active context by checking
`context_number in rule.context`, which only matches the nested format.
Consequences, verified by running the code:

1. `python main.py scenario_context_aware_medical.json` activates **no
   context at all** ("ACTIVE CONTEXT" comes back empty). The weights in every
   flagship `scenario_context_aware_*` file are dead data.
2. The REST API is worse: it never flattens `rule.context` the way
   `main.py` does after setting the context, so even nested-format scenarios
   get no adjustment through the API — `adjusted_probability` checks keys like
   `"1"` against a context of variable names and never matches.

Context adjustment currently only works when driving `ProbKB`
programmatically, as the tests and the example script do. Given
"context-aware reasoning" is contribution #1 in `paper_draft.md`, this is the
first thing to fix: pick one format, migrate the scenario files, make CLI and
REST behave identically, and add a test that loads a scenario **file** and
asserts an adjusted probability.

## Smaller items

- **`paper_draft.md`'s results table looks fabricated** — 0.28–0.5 s for
  scenarios this size (they execute in microseconds), and case studies with
  invented outcomes. If it is placeholder scaffolding, label it as such; do
  not let it survive into a submission.
- The README says Apache 2.0 but there is **no LICENSE file** — the grant is
  not effective without the license text.
- `__pycache__/*.pyc` files are committed (a `.gitignore` is added alongside
  this review; the already-tracked bytecode still needs `git rm --cached`).
- Three near-full copies of the codebase in one repo (`PLA-advanced/`,
  `Archive/PLA/`, `Archive/PLA/PLA-V1-Archive/`) plus
  `scenario_supply_chain_optimization copy.json` and a `.docx` binary. Git
  history/tags are the archive; the copies triple the surface a reader must
  disambiguate.
- Dead/confusing code: `ProbabilisticReasoner` in `prob.py` uses a completely
  different rule syntax (`P(A,B)=0.8`) and an odd membership test, and is
  unused by `main.py`/`rest_api.py`; `ProbRule.context_weight` is never used.
- The hybrid engine's shipped examples gate **disjoint symbol spaces** (the
  symbolic KB knows `A, B, C`; the probabilistic KB knows fraud symbols), so
  the gating never demonstrates anything — the README hybrid example returns
  probability 0.0 for `C`. One scenario where both layers model the same
  symbols would make the hybrid story real. The symbolic layer also has no
  negation, so `constraint` gate mode is (as the code comment admits) a no-op.
- The root README timeline (paper by June–July 2025) is stale, and `main.tex`
  is still an empty skeleton.
- `requirements.txt` pins `unittest2` — a Python 2-era backport that nothing
  imports; drop it.

## Suggested order of work

1. Fix the context-format bug (one format, migrated scenarios, identical CLI
   and REST behavior, a file-loading test that asserts an adjusted
   probability).
2. Rewrite related work against ProbLog, MLNs, PSL, and certainty factors,
   and recast the contribution claims accordingly.
3. Decide the semantics story (honest confidence-propagation framing, or
   log-odds context adjustment as a principled middle ground) and make the
   paper's terminology match.
4. Repo hygiene pass: LICENSE file, remove archives/dead code/tracked
   bytecode, strip placeholder results.

The foundation is worth building on — the discipline shown in PR #1 (explicit
operators, reproducible README numbers, tests) is exactly the right
trajectory. The project's risk is not the code; it is overclaiming in the
framing while the flagship feature has a wiring bug.

## Publishability assessment: is this Q1-journal material?

**Not in its current form — and the gap is the contribution itself, not the
writing.** Scored against what Q1 venues (JAIR, AIJ, Machine Learning;
Q1-applied: Knowledge-Based Systems, Expert Systems with Applications,
Information Sciences) actually require:

- **Novelty.** The mechanisms are textbook model checking plus a confidence
  calculus structurally equivalent to MYCIN certainty factors (1975) with
  configurable aggregation. ProbLog/DeepProbLog, MLNs, PSL, LNN, and Scallop
  are mature, uncited, and unbeaten on any axis. Known trap: Heckerman (1986)
  showed the certainty-factor calculus is only probabilistically coherent
  under restrictive conditions — reviewers will apply that critique to the
  multiply-and-cap scheme directly. The only potentially novel element is
  context-modulated rule weights + trace-first explanations, and only if
  formalized and evaluated.
- **Theory.** No formal semantics, no theorems (soundness, fixpoint
  convergence, complexity). Outputs are not probabilities of any defined
  event space.
- **Evidence.** No real data, no baselines, placeholder benchmark numbers.
  The O(2^n) truth-table checker caps the symbolic layer at ~20 propositions,
  contradicting the scalability claims.
- **Artifact soundness.** Contribution #1 (context-aware reasoning) does not
  currently fire through the CLI or REST API (see the bug above).

The current `paper_draft.md` would likely be desk-rejected at a Q1 journal.

### Realistic venue ladder

1. **Now (weeks):** workshop/tool/demo paper — NeSy, XAI workshops,
   RuleML+RR tool track, AAAI EAAI (the education angle is the strongest
   current claim: a transparent, dependency-free engine students can read
   end-to-end is something ProbLog is not). JOSS or SoftwareX for a citable
   software paper.
2. **6–12 months:** Q1-applied journals (ESWA, KBS, Information Sciences)
   become plausible with a real application study.
3. **12–24 months:** JAIR/AIJ/MLJ only with a genuine formal contribution.

### Recipe for a credible Q1 submission

1. **Formalize the calculus.** Context adjustment in log-odds (the
   `logit_pool` machinery already exists) — additive evidence weights fix
   cap saturation and give a defensible semantics. Prove fixpoint
   convergence for the monotone aggregators, give complexity bounds, and
   position explicitly against certainty factors, including why the scheme
   escapes Heckerman's incoherence critique.
2. **Make the weights learnable.** Logit-pool is differentiable; fitting
   rule and context weights from labeled data turns PLA from a hand-authored
   demo into a benchmarkable model. This is the step that converts the
   project into publishable science.
3. **Evaluate for real.** Public fraud / financial-statement datasets;
   baselines: ProbLog, PSL, a Bayesian network, logistic regression,
   gradient boosting; metrics: AUC plus explanation fidelity, ideally a
   small domain-expert study.
4. **Resulting honest claim:** "an interpretable, context-modulated
   rule-confidence model with learnable weights, competitive accuracy on
   real fraud/audit data, and faithful reasoning traces" — a credible
   Q1-applied submission.

Practical sequencing: fix the context bug, submit a workshop/tool paper this
cycle to collect expert reviews and a citable artifact, and treat the
learnable-weights + real-data study as the Q1 campaign. Venue strategy is
also a PhD-milestone question — pressure-test this plan with the supervisor.

### A note on "but the competitors are not in Python"

That claim is factually wrong and must not appear in any submission —
verified on PyPI (2026-08-18):

| Package | Version | What it is |
|---|---|---|
| `problog` | 2.2.10 | ProbLog 2 — probabilistic logic programming, Python implementation and API (KU Leuven, used in teaching) |
| `deepproblog` | 2.0.6 | ProbLog + neural networks |
| `pracmln` | 1.2.4 | Markov Logic Networks in Python |
| `pgmpy` | 1.1.2 | Standard educational Bayesian-network / causal library |
| `pslpython` | 2.4.0 | Official Python interface to PSL (Java core) |
| `scallopy` | 0.1.0 | Python bindings for Scallop (Rust core) |

The defensible version of the argument is usability/pedagogy, not language:
ProbLog requires Prolog syntax and distribution semantics and its engine
(knowledge compilation, SDDs) is unreadable to students, whereas PLA is
JSON-in / trace-out with a ~500-line engine a student can step through.
Two consequences:

1. In AI venues, "friendlier API, readable source" is a tool-track
   contribution (JOSS, SoftwareX), never a Q1 journal contribution on its
   own.
2. The ease-of-use claim becomes science only when measured: a controlled
   study (30–60 students, same reasoning tasks in PLA vs. ProbLog; task
   completion time, error rates, comprehension) turns PLA into the
   instrument of an education paper — Computers & Education (Q1 in its
   category), IEEE Transactions on Education, or AAAI EAAI.

Either way, ProbLog gets cited prominently; claiming it does not exist in
Python is a one-minute refutation for any reviewer.
