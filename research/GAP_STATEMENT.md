# Gap Statement — Where PLA Can Contribute

Skeleton to be filled in during the two-week literature pass
(`research/READING_LIST.md`). Citations `[R1-n]` refer to entry *n* in that
list. The rule for this document: **every claim about prior work carries a
citation; every hypothesis names the evidence that would kill it.**

## 0. Status update (August 2026): RQ1 executed — kill criterion fired

RQ1 below was run to completion on both planned datasets. **The kill
criterion fired** — the pre-specified, directional AUC criterion (this
document, as committed at `8f2dd2e`, named no equivalence margin, so
the manuscript reports interval bounds rather than a formal
equivalence claim): on the credit-card data the paired ablation ΔAUC
contains zero on all ten splits; on the accounting data the strict
design shows a small paired-real effect between two below-chance
models (+0.0172 [0.0019, 0.0373]) and the SOX-boundary design — built
specifically so the context weight is identifiable — bounds the effect
to ΔAUC 0.0011 [−0.0071, 0.0140]. One post-hoc observation is held
apart as a new hypothesis, not a verdict revision: a credit-card-only
average-precision edge for the context variant, paired CI excluding
zero on all ten splits, absent under both drift designs. Per the
criterion, the negative is reported as such in the journal manuscript
(`paper/`), which recenters on what *was* demonstrated: near-frontier
ranking from 11 auditable rules, calibration as the value of learning,
measured trace fidelity, and the intercept lesson. The follow-ups:
confirming or refuting the post-hoc AP edge on new data, richer
context features than single-bit indicators, rule re-mining under
vocabulary drift, and the full serial-fraud protocol of [R1-24]. RQ2
and RQ3 remain open candidates, unchanged.

## 1. Starting point (honest one-paragraph summary)

PLA today is a small, fully transparent Python engine that forward-chains
rule confidences (min-conjunction, configurable support aggregation,
multiplicative context weights) over propositional facts, with per-rule
explanation traces. Structurally it is a modern descendant of MYCIN-style
certainty factors [R1-13], using the Gödel t-norm for conjunction [R1-16],
and it is *not* a probabilistic semantics in the distribution sense that
ProbLog established [R1-1, R1-2]. Its defensible assets are transparency
(readable end-to-end), trace-first output, and a context-adjustment
mechanism that mainstream SRL systems lack.

## 2. The gaps this project can attack

- **G1 — Static weights.** MLNs [R1-3], PSL [R1-4], and ProbLog [R1-1] attach
  fixed weights/probabilities to rules; adapting rule reliability to context
  is handled, if at all, by re-learning. Concept-drift research [R1-28] treats
  adaptation, but not inside an interpretable logic calculus.
- **G2 — Unmeasured explanation fidelity.** Interpretable-model advocacy
  [R1-22] and faithfulness theory [R1-23] exist, but trace-based SRL
  explanations are rarely evaluated for fidelity, and essentially never with
  audit practitioners, whose requirements are documented in [R1-25].
- **G3 — Uncertainty-aware verification for LLMs.** The LLM+solver pattern
  (Logic-LM [R1-17], LINC [R1-18], SatLM [R1-19], LLM-Modulo [R1-21]) uses
  *crisp* solvers; a verifier that handles weighted, uncertain domain rules
  is an open slot in that architecture.

## 3. Candidate research questions

### RQ1 — Context-conditioned learnable rule weights (primary candidate)

**Question.** Do context-conditioned rule weights, learned in log-odds space,
outperform static-weight rule systems on non-stationary fraud/audit data,
at equal interpretability?

**Hypothesis.** On data whose generating conditions shift (seasonality,
regime changes), a PLA model whose rule weights are functions of context
variables will dominate its own static-weight ablation and be competitive
with PSL [R1-4] and ProbLog [R1-2] learned weights, while black-box
gradient boosting remains the accuracy ceiling.

**Prior work to beat/position against.** Static-weight learning in MLNs
[R1-3] and ProbLog [R1-2]; drift adaptation outside logic [R1-28];
semiring-parameterized semantics as the formal umbrella [R1-5, R1-9].

**Method sketch.** Item S1 (log-odds context adjustment) + Phase 4 learner;
ablation = same model, context weights frozen; report AUC, calibration
[R1-27], and trace complexity.

**Datasets.** Credit-card fraud [R1-27]; accounting fraud replication data
[R1-24].

**Kill criterion.** If the context-conditioned model fails to beat its own
static ablation on drifting splits, the mechanism has no measurable value —
report the negative result and pivot to RQ2.

**Outcome (recorded August 2026).** Fired — see the status update at the
top of this document and `paper/sections/06-evaluation.tex` for the
regenerable numbers.

**Venue.** Knowledge-Based Systems / ESWA / Information Sciences (Q1
applied); workshop cut first (NeSy or RuleML+RR).

### RQ2 — Do faithful traces help auditors decide?

**Question.** Do PLA-style reasoning traces improve human audit decisions
(accuracy, time, calibrated trust) compared to feature-importance
explanations of an equally accurate black-box model?

**Hypothesis.** For flag-or-clear decisions on fraud alerts, rule traces
beat post-hoc feature attributions on decision accuracy and appropriate
reliance, consistent with the interpretability argument in [R1-22] and the
faithfulness/plausibility distinction of [R1-23]; audit-domain requirements
per [R1-25].

**Method sketch.** Controlled study, 30–60 participants (accounting
students or practitioners), within-subject, two explanation conditions on
matched cases from [R1-24, R1-27]-derived scenarios. Requires ethics
approval and recruiting — the one RQ that cannot be done by code alone.

**Kill criterion.** No difference in decision quality → traces are a
developer feature, not a user-facing contribution; report as such.

**Venue.** Computers & Education / IEEE Transactions on Education (if framed
as teaching instrument), or an XAI venue; AAAI EAAI as the fast first shot.

### RQ3 — PLA as the uncertain-rule verifier in LLM-modulo pipelines

**Question.** Can a weighted-rule verifier reduce hallucinated conclusions
when an LLM extracts facts/rules from audit narratives, compared to direct
LLM judgment and to crisp-logic verification?

**Hypothesis.** In the generate-and-verify architecture [R1-21], replacing
crisp solvers [R1-17, R1-18, R1-19] with a confidence-propagating verifier
improves precision on conclusions drawn from noisy extracted facts, because
extraction confidence can be carried through the inference [R1-20] instead
of being thresholded away.

**Method sketch.** LLM extracts structured facts from case narratives →
PLA scores conclusions → compare against LLM-only and crisp-gate baselines
on precision/recall of correct conclusions.

**Kill criterion.** If thresholding extraction confidence + crisp logic
matches confidence propagation, the uncertainty machinery adds nothing.

**Venue.** NeSy workshop first; then an LLM+reasoning track.

## 4. Fit assessment (to discuss with supervisor)

| | Effort | Risk | Needs beyond code | Thesis fit |
|---|---|---|---|---|
| RQ1 | Medium (Phases 3–5 of TODO) | Medium — honest ablation may be negative | Public data only | Core AI contribution |
| RQ2 | Medium code + high logistics | Medium — null results common in XAI studies | Ethics approval, participants | Human-centered contribution |
| RQ3 | Medium | Higher — crowded, fast-moving | LLM API budget | Timeliness, visibility |

Recommended default: **RQ1 as the thesis spine** (it reuses everything in
TODO Phases 3–5), RQ2 as the human-evidence chapter if resources allow,
RQ3 as a workshop-scale probe.

## 5. Checkpoints for the two-week reading pass

- After section A+C of the reading list: rewrite §1 above in sharper terms —
  exactly which semantics PLA has, in aProbLog/semiring vocabulary [R1-5].
- After section B: place PLA on the survey taxonomy of [R1-10]; note the
  nearest neighbors and what they cannot do.
- After sections D–F: confirm or kill RQ3's novelty claim; collect 3–5
  additional citations per RQ; fill the empty citation slots in
  `paper_draft.md`'s related work (TODO item P1).
- End: pick the primary RQ with the supervisor; convert its method sketch
  into a full experimental protocol.
