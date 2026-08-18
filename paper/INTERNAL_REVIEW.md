# Internal referee reviews and dispositions

Adversarial pre-submission reviews of `paper/main.tex`, run before any
external submission. Each round lists findings the way a journal referee
would; the disposition column records what the revision did. Regenerate
nothing here by script — this file is the review log.

## Round 1

Reviewed at commit `8cb5d17` (29-page elsarticle `review` build).
Recommendation if this were a real submission: **major revision** —
sound core, honest negative result, but the manuscript under-documents
its own method, overstates one headline number, contains one false
formal claim and one dangling reference, and has no figures.

### Major

| # | Finding | Disposition |
|---|---|---|
| M1 | **Headline overstated.** Abstract and Conclusion claim "AUC 0.96–0.97 across three split seeds — within 0.02 of the interpretable accuracy frontier". The committed CSVs give static 0.9525–0.9687 (0.9525 rounds to 0.95, not 0.96) and per-seed frontier gaps up to 0.022 (static, seed 44) and 0.026 (learned, seed 44). "Within 0.02" is false on one of three seeds. | Abstract, §6, §8, workshop cut, and all READMEs restated with the true ranges (0.95–0.97; 0.01–0.03 below the frontier). |
| M2 | **Method not reproducible from the manuscript.** The rule-mining procedure behind "an 11-rule model" (decile thresholds fit on train; precision-ranked top-8 single-proposition rules + top-3 pair rules with support floors 20/10), the learner configuration (400 epochs, lr 1.0, intercept), baseline configurations, and the CI protocol appear nowhere in the paper — only in code. A referee cannot assess or reproduce the setup from the text. | New §6.1 "Experimental setup" specifying propositionalization, mining, learner and baseline configs, metrics, and the bootstrap protocol. |
| M3 | **Proposition 1 is false as stated.** It asserts every aggregator of Eq. (2) is monotone, but `logit_pool` is not: candidates below 1/2 contribute negative log-odds (they *lower* accumulated support), and the zero-support convention is discontinuous at the boundary (f(0,n)=n but f(ε,n)→0). The property harness itself only covers the three monotone operators. | Proposition restated for max/noisy-OR/sum-cap; explicit remark that logit-pool is deliberately non-monotone (sub-½ candidates are negative evidence), is excluded from the Kleene argument, terminates via the iteration cap, and is exercised in practice on the acyclic learning path where inference is a single fold. |
| M4 | **ROC AUC alone under 0.17% prevalence.** Fraud reviewers will demand a precision-oriented metric; ROC AUC can look flattering under extreme imbalance. | Average precision (area under the precision–recall curve) added to every model/design with the same seeded bootstrap 95% CIs; tables and text updated; ranking conclusions re-checked under AP. |
| M5 | **Dangling reference and stale provenance.** Appendix B cites `Table~\ref{tab:suite}`, which does not exist in this manuscript (renders as "Table ??"); the provenance table also predates the real-data campaign — no rows for the credit-card, Bao, SOX, multi-seed, or case-study artifacts. | Dangling row removed; provenance table extended to every real-data table, figure, and the case study. |
| M6 | **Gradient-boosting strawman.** The untuned HistGB row (0.7159 on credit card) will be read as a weak-baseline construction even though the text flags it. | Class-weighted gradient-boosting row (`class_weight="balanced"`, otherwise defaults) added to every design; limitations text updated. |
| M7 | **Fidelity claims lack dispersion and half the metric.** Table 4 reports means only, with no uncertainty, and omits sufficiency although §6 introduces it. Per-example paired deltas exist in the pipeline. | Seeded paired-bootstrap 95% CI on the trace-minus-control comprehensiveness difference added per dataset; sufficiency columns added; claim restated as CI-backed. |
| M8 | **No figures.** A 29-page journal manuscript with zero figures: no system overview, no visual for the headline comparison, no calibration evidence for the paper's central "learning buys calibration" claim. | Added: engine/learning-loop overview (TikZ); AUC forest plots with CIs for credit card and the SOX design (the ablation overlap is the visual verdict); reliability diagram, static vs. learned, credit card. Figures regenerate from `scripts/make_figures.py`. |

### Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | Seven keywords; Knowledge-Based Systems allows six. | Trimmed to six. |
| m2 | "86 tests" — the suite collects 87 (one network-dependent test self-skips in CI). | Stated precisely in §5 and the workshop cut. |
| m3 | Mixed 3/4-decimal AUCs in tables, patched over by a display-convention sentence. | All metrics now emitted at uniform four decimals by the scripts; results regenerated; caveat sentence deleted. |
| m4 | "lands by PLA static" (synthetic ProbLog row) is vague. | Replaced with CI-overlap phrasing. |
| m5 | The Introduction motivates context-conditioned weights without signalling the paper's own negative verdict until contribution 2. | Motivation paragraph now frames the mechanism as a hypothesis the paper tests and, for coarse contexts, rejects. |
| m6 | §5 mentions a "scenario-suite table" that is not in this paper (workshop artifact). | Reworded to name the artifacts the journal paper actually contains. |
| m7 | No computational-cost statement anywhere. | Single-core wall-time magnitudes for the learner fit and engine queries added to §5. |
| m8 | Subset rows (ProbLog n=150, pgmpy n=2000) typeset amid full-test rows in Table 2. | Separated below a rule with an explicit subset block. |
| m9 | Abstract says training is "provably monotone"; §4 says monotonicity is test-asserted. | Abstract softened to match §4. |

## Round 2

Reviewed after the round-1 revision landed (regenerated results, new
figures, new §6.1). Recommendation if this were a real submission:
**minor revision** — the round-1 issues are resolved; what remains is
consistency polish.

| # | Finding | Disposition |
|---|---|---|
| R2-1 | Verify every number that round 1 touched (ranges, AP values, CI endpoints, fidelity CIs) against the regenerated CSVs; no stale 3-decimal forms may survive anywhere in main, workshop, draft, or READMEs. | Swept and fixed; the claim-provenance appendix now lists the exact generating file for each table and figure. |
| R2-2 | New §6.1 must match the code defaults exactly (support floors, quantiles, epochs, learning rate, seeds). | Cross-checked against `pla/pipeline.py`, `pla/learn.py`, and the scripts. |
| R2-3 | Figures: axes labelled, CIs drawn, readable in grayscale, referenced from the text in order, and consistent with table values. | Verified against the CSVs that generate them. |
| R2-4 | Compile hygiene: zero undefined references/citations, bibtex clean, no overfull boxes above cosmetic level, hyperref anchors fine. | Verified in the round-2 compile log. |
| R2-5 | Elsevier submission completeness: highlights, CRediT, declaration of interests, data availability. | Added (see `submission/`). |

Both rounds' fixes are in the git history; the CI `paper` job compiles
the revised manuscript and the packaging job assembles the Overleaf and
submission archives on every push.
