# PLA — Rebuild Roadmap

Working checklist derived from the full project review in `PROJECT_FEEDBACK.md`.

**Conventions**
- An item is ticked `[x]` only when it is implemented, its **Verify** step passes,
  and the work is committed to `claude/project-feedback-5b3369` (commit hash noted
  beside the item).
- No hand-written numbers anywhere: every table/metric in docs must be generated
  by a committed script.
- Phases are ordered by dependency, but items within a phase are independent
  unless noted.

---

## Phase 0 — Research framing (unblocks the human reading work)

- [x] **R1. `research/READING_LIST.md`** — annotated list (28 entries) covering
  NeSy/StarAI 2023–2026 (ProbLog/DeepProbLog line, PSL, LNN, Scallop, LLM+symbolic
  verification) and AI-in-auditing/fraud literature, each with 1–2 sentences on
  why it matters for PLA. (`8a83a87`)
  *Verify (amended — sandbox network policy blocks scholarly hosts, so links
  cannot be resolved from here): coverage of all systems named in
  PROJECT_FEEDBACK.md grep-checked ✓; `scripts/check_links.py --list` extracts
  all 30 URLs ✓; run `python3 scripts/check_links.py` on an open network to
  finish link resolution — uncertain identifiers were omitted in favor of
  text citations.*
- [x] **R2. `research/GAP_STATEMENT.md`** — 2-page skeleton with the three candidate
  research questions (context-conditioned weights vs. static SRL; explanation
  fidelity for auditors; probabilistic-logic verification of LLM-extracted facts),
  each with hypothesis, baseline pool, dataset candidates, and target venue. (`8f2dd2e`)
  *Verify: structure checked (3 RQs × hypothesis/kill-criterion/venue/datasets ✓);
  all 20 distinct [R1-n] citations resolve to READING_LIST entries ✓.*

## Phase 1 — Correctness (before anything else ships)

- [x] **C1. Fix the context-format bug.** One canonical scenario format; the loader
  must accept the existing flat (`{"Var": w}`) and nested (`{"1": {"Var": w}}`)
  formats explicitly — silent no-op contexts become impossible (unknown shapes fail
  loudly). (`321bd87`)
  *Verify: passed — CLI tests assert LungCancerRisk 0.840 (set 1) and 1.000 capped
  (set 2) on `scenario_context_aware_medical.json`; malformed/mixed contexts,
  unknown sets, and undeclared variables all raise ScenarioFormatError; 16/16
  tests green; all 35 scenario files load and activate.*
- [ ] **C2. REST API parity with CLI.** The API applies the same context resolution
  (today it never applies adjustments).
  *Verify: Flask test-client tests assert identical probabilities from CLI and API
  for the same scenario + context.*
- [ ] **C3. Coherent hybrid demo.** Add one scenario where symbolic and probabilistic
  layers share symbols so gating actually demonstrates something; document that
  constraint mode is a no-op without negation.
  *Verify: test asserts hard-gate blocks a non-entailed query and passes an entailed
  one with nonzero probability.*
- [ ] **C4. Delete dead code.** Remove `ProbabilisticReasoner` (incompatible rule
  syntax) and the unused `ProbRule.context_weight`.
  *Verify: grep clean; full test suite passes.*

## Phase 2 — Hygiene & packaging

- [ ] **H1. LICENSE file** (Apache 2.0, matching README claims).
  *Verify: file present with correct text and copyright line.*
- [ ] **H2. `.gitignore` + purge tracked `__pycache__`/`.pyc`.**
  *Verify: `git ls-files | grep pyc` empty; `git status` stays clean after a test run.*
- [ ] **H3. Remove duplicates:** `scenario_supply_chain_optimization copy.json`,
  `Archive/` trees (git history is the archive; tag the old state first).
  *Verify: tag pushed; directories gone; tests pass.*
- [ ] **H4. Installable package.** Restructure `PLA-advanced/` into a `pla/` package
  with `pyproject.toml`, console entry point, scenarios under `scenarios/`.
  *Verify: `pip install -e .` in a fresh venv, `pla scenarios/<file>.json` runs,
  `pytest` passes from repo root.*
- [ ] **H5. Dependency cleanup.** Drop `unittest2` (Python-2 era), move Flask to an
  optional extra, sane pins.
  *Verify: fresh-venv install + tests with core deps only.*
- [ ] **H6. CI.** GitHub Actions: pytest on Python 3.9–3.12.
  *Verify: workflow YAML parses; first push shows green run.*
- [ ] **H7. Honest README rewrite.** Remove "first ever" claims and the stale 2025
  timeline; add install, quickstart, semantics summary, and a positioning paragraph
  that cites ProbLog/PSL/pracmln instead of denying them.
  *Verify: every command in the quickstart executes as written.*
- [ ] **H8. Purge fabricated results.** Remove the invented benchmark/case-study
  numbers from `paper_draft.md`; add `scripts/benchmark.py` that regenerates the
  table from real runs.
  *Verify: doc table matches script output byte-for-byte.*

## Phase 3 — Semantics (the research core)

- [ ] **S1. Log-odds context adjustment.** Additive evidence weights in logit space
  as a new context mode (fixes cap-saturation information loss); multiply-and-cap
  kept as `legacy`.
  *Verify: tests show two strong context signals no longer saturate identically;
  legacy mode reproduces all existing expected values.*
- [ ] **S2. `docs/SEMANTICS.md`.** Formal operator definitions; explicit lineage
  (certainty factors, Gödel t-norm, noisy-OR); positioning against Heckerman's
  1986 coherence critique; guidance on aggregator choice.
  *Verify: every formula in the doc backed by a doctest or unit test.*
- [ ] **S3. Convergence guarantees.** Property-based tests (hypothesis) that the
  fixpoint iteration converges and is monotone for `max`/`noisy_or`/`sum_cap` on
  random cyclic KBs; proof sketch added to SEMANTICS.md.
  *Verify: hypothesis suite passes ≥1000 random cases including cycles.*
- [ ] **S4. Scalable symbolic layer.** Replace O(2^n) truth-table entailment with
  forward chaining for definite clauses; keep the truth-table checker as a test
  oracle.
  *Verify: differential test on random KBs (new engine ≡ oracle, n ≤ 15); 200-symbol
  KB entailment under 1 second.*

## Phase 4 — Learnable weights

- [ ] **L1. Differentiable inference + weight learning.** Gradient fitting of rule
  and context weights through the logit-pool path (numpy only).
  *Verify: loss decreases monotonically on a fixed synthetic training set; no
  external ML deps required.*
- [ ] **L2. Weight-recovery test.** Generate data from known weights; learner
  recovers them.
  *Verify: recovered weights within tolerance of ground truth on ≥3 seeds.*
- [ ] **L3. Calibration utilities.** Brier score / log-loss / reliability summaries.
  *Verify: unit tests against hand-computable values.*

## Phase 5 — Real-data evaluation

- [ ] **E1. Public fraud dataset loader** (OpenML credit-card fraud or equivalent),
  cached download, license noted.
  *Verify: script downloads, checksums, and prints summary stats.*
- [ ] **E2. Feature→rule pipeline.** Discretize features into propositions and
  candidate rules for PLA.
  *Verify: pipeline runs end-to-end on E1 data; produced scenario loads in the engine.*
- [ ] **E3. Baselines.** Logistic regression + gradient boosting (sklearn), and
  ProbLog/pgmpy where installable in this environment.
  *Verify: one script trains and evaluates all baselines, emitting a metrics CSV.*
- [ ] **E4. Head-to-head experiment.** PLA (hand weights) vs. PLA (learned) vs.
  baselines; AUC + calibration; results committed as generated CSV/Markdown.
  *Verify: `scripts/run_experiments.py` reproduces the committed table from scratch.*
- [ ] **E5. Explanation fidelity metric.** Quantify whether traces reflect the
  factors that drive predictions.
  *Verify: metric implemented with tests; report generated for E4 models.*

## Phase 6 — Paper

- [ ] **P1. Related-work rewrite** with verified citations (ProbLog, DeepProbLog,
  PSL, MLN/pracmln, LNN, Scallop, certainty factors, Heckerman 1986).
  *Verify: every cited system's claim checked against its docs/paper.*
- [ ] **P2. Restructure `paper_draft.md`** around the honest contribution
  (context-modulated, learnable, trace-faithful rule confidence model) with only
  generated results.
  *Verify: no orphan claims — each maps to a script output or citation.*
- [ ] **P3. Workshop-paper cut** (4–6 pages) targeting NeSy / RuleML+RR tool track,
  from P2.
  *Verify: compiles via `main.tex`; page budget respected.*
