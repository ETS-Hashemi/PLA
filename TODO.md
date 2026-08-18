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
- [x] **C2. REST API parity with CLI.** The API applies the same context resolution
  (today it never applies adjustments). (`80724b7`; shared code path landed in C1)
  *Verify: passed — five parametrized Flask test-client cases assert API == CLI
  probabilities on flat and nested scenarios, plus an exact loader match (0.84);
  26/26 tests green.*
- [x] **C3. Coherent hybrid demo.** Add one scenario where symbolic and probabilistic
  layers share symbols so gating actually demonstrates something; document that
  constraint mode is a no-op without negation. (`2be25dd`)
  *Verify: passed — hard gate blocks RegulatorReport (raw 0.51 → 0.0) and passes
  entailed AuditRequired at 0.85; soft (0.255) and constraint (pass-through +
  warning) modes covered; limitation documented in engine.py, README, and demo;
  30/30 tests green.*
- [x] **C4. Delete dead code.** Remove `ProbabilisticReasoner` (incompatible rule
  syntax) and the unused `ProbRule.context_weight`. (`2ba75a8`)
  *Verify: passed — grep clean across PLA-advanced/, tests/, examples/ (Archive
  copies are deleted wholesale in H3); 30/30 tests green.*

## Phase 2 — Hygiene & packaging

- [x] **H1. LICENSE file** (Apache 2.0, matching README claims). (`02f28a7`)
  *Verify: passed — all 9 sections + appendix present, canonical word/byte count
  (1581 words / 11362 chars), copyright line for the author included.*
- [x] **H2. `.gitignore` + purge tracked `__pycache__`/`.pyc`.** (`45079d6`)
  *Verify: passed — 20 tracked bytecode files removed from the index, 0 remain;
  status clean after a full 30-test run; packaging/coverage ignores added for H4.*
- [x] **H3. Remove duplicates:** `scenario_supply_chain_optimization copy.json`,
  `Archive/` trees (git history is the archive; tag the old state first). (`c9767b6`)
  *Verify (amended — tag pushes are 403-denied in this environment, like branch
  deletion): pre-removal state anchored at commit `b16e843` (local tag
  `legacy-archive`; recreate remotely with `git tag legacy-archive b16e843 &&
  git push origin legacy-archive`); directories gone from index and disk ✓;
  30/30 tests pass ✓.*
- [x] **H4. Installable package.** Restructure `PLA-advanced/` into a `pla/` package
  with `pyproject.toml`, console entry point, scenarios under `scenarios/`. (`c7b8e09`)
  *Verify: passed — fresh venv `pip install -e ".[api,dev]"` clean;
  `pla scenarios/scenario_context_aware_medical.json 1` reports 0.840; 30/30
  tests pass from repo root both installed and uninstalled.*
- [x] **H5. Dependency cleanup.** Drop `unittest2` (Python-2 era), move Flask to an
  optional extra, sane pins. (`1c6b69a`)
  *Verify: passed — fresh core-only venv installs with zero dependencies, CLI
  works, suite runs 20 passed + REST module skipped without Flask; full suite
  30/30 with the [api] extra.*
- [x] **H6. CI.** GitHub Actions: pytest on Python 3.9–3.12. (`856b43e`)
  *Verify: passed — YAML parses; run #1 (id 32169345240) concluded success on the
  3.9/3.10/3.11/3.12 matrix, including CLI and example smoke steps.*
- [x] **H7. Honest README rewrite.** Remove "first ever" claims and the stale 2025
  timeline; add install, quickstart, semantics summary, and a positioning paragraph
  that cites ProbLog/PSL/pracmln instead of denying them. (`10a181d`)
  *Verify: passed — fresh venv ran every quickstart command as written: both
  installs, CLI (0.840), both examples (output matches the quoted block), pytest
  30/30, and the REST /load + /query round-trip (0.84).*
- [x] **H8. Purge fabricated results.** Remove the invented benchmark/case-study
  numbers from `paper_draft.md`; add `scripts/benchmark.py` that regenerates the
  table from real runs. (`adcc151`)
  *Verify: passed — table between markers in paper/paper_draft.md diffs clean
  against `scripts/benchmark.py --paper-table`; no residual invented numbers;
  case studies replaced by an explicit Phase 5 placeholder; 30/30 tests green.*

## Phase 3 — Semantics (the research core)

- [x] **S1. Log-odds context adjustment.** Additive evidence weights in logit space
  as a new context mode (fixes cap-saturation information loss); multiply-and-cap
  kept as `legacy`. (`3a56202`)
  *Verify: passed — in legacy two strong combos both cap at 1.0, in logit they
  stay distinct and < 1.0 (closed-form checked); negative weights weaken; p∈{0,1}
  fixed points; legacy default reproduces all values (37/37 tests green).*
- [x] **S2. `docs/SEMANTICS.md`.** Formal operator definitions; explicit lineage
  (certainty factors, Gödel t-norm, noisy-OR); positioning against Heckerman's
  1986 coherence critique; guidance on aggregator choice. (`10cee8f`)
  *Verify: passed — tests/test_semantics_doc.py extracts and executes all 6
  formula blocks (F1–F5d, fixpoint, non-distribution caveat) against the engine;
  44/44 tests green.*
- [x] **S3. Convergence guarantees.** Property-based tests (hypothesis) that the
  fixpoint iteration converges and is monotone for `max`/`noisy_or`/`sum_cap` on
  random cyclic KBs; proof sketch added to SEMANTICS.md. (`df5f9b9`)
  *Verify: passed — 350 examples × 3 aggregators = 1050 random systems (seeded
  cycles included): monotone, bounded, ε-fixpoint reached, engine ≡ reference;
  slow-cycle regression matches closed form under the raised iteration cap;
  48/48 tests green.*
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
