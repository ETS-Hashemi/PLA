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
| M4 | **ROC AUC alone under 0.17% prevalence.** Fraud reviewers will demand a precision-oriented metric; ROC AUC can look flattering under extreme imbalance. | Average precision (area under the precision–recall curve) added to every model/design with the same seeded bootstrap 95% CIs. The AP view changed the paper's story, and the paper says so: MLE weights cost 0.13–0.19 AP against the static rules on credit card (seed-stable) — a top-of-ranking loss AUC conceals — and the context ablation shows a small credit-card-only AP edge that is reported as a post-hoc, hypothesis-generating observation, not a revision of the pre-registered negative. Discussion §"what MLE buys, what it costs" rewritten accordingly. |
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
figures, new §6.1; 36-page review build). Recommendation if this were a
real submission: **accept with minor polish** — the round-1 issues are
resolved and the round-2 pass found only consistency and typographic
defects, all fixed the same day.

| # | Finding | Disposition |
|---|---|---|
| R2-1 | No stale number forms may survive round 1's edits anywhere (3-decimal AUCs, "within 0.02", old test counts). | Regex sweep over `paper/`, `README.md`, `results/README.md` comes back empty; every table cell is pasted from `scripts/make_paper_tables.py` output, and the claim-provenance appendix names the generating file for each table and figure. |
| R2-2 | §6.1 must match the code defaults exactly. | Verified against `pla/pipeline.py` and the scripts (deciles 0.1/0.9 fit on train; top-8 singles ≥20 support; top-3 pairs ≥10 from top-5 singles; 400 epochs, lr 1.0; B=500 shared resamples, seed 7; ECE 10 bins). The "11 rules per design" claim was additionally verified by running the mining on both Bao designs — 11 rules each. |
| R2-3 | Figures consistent with the tables and honest about what they show. | All four rendered and inspected. The reliability diagram exposed a detail the first caption glossed: the learned model's top bin sits above the diagonal (score compression) — precisely the AP cost's calibration-side view. Caption and §6 now say so instead of only "hugs the diagonal". |
| R2-4 | Compile hygiene. | Zero undefined references/citations, zero multiply-defined labels; worst remaining overfull ≈11pt (was 133pt: fidelity table restructured to 7 columns, tables set at footnote/scriptsize, appendix provenance columns rebalanced, unbreakable `\texttt` strings made breakable); an "Appendix Appendix A" doubling from elsarticle's `\ref` fixed; three bibtex empty-`pages` warnings fixed from known ranges (AAAI'11, NeurIPS'18, PLDI'23), while four recent conference entries (Logic-LM, LINC, SatLM, the ICML'24 position paper) are deliberately left without page fields rather than risk invented ranges — harmless warnings, flagged for the author's link-check pass on an open network. |
| R2-5 | Elsevier submission completeness. | Highlights (5 bullets, all ≤85 chars, compiles to one page), cover letter (one page), CRediT, declaration of competing interest, and data availability are in; funding/acknowledgements is deliberately a marked author-TODO since it cannot be inferred from the repository. |
| R2-6 | The packages must be verified, not assumed. | `scripts/build_paper_package.sh` compiles all four documents, assembles `overleaf_package.zip` and `submission_package.zip`, and re-compiles the Overleaf zip from a clean unpacked copy (36 pages) on every run; CI runs the same script and uploads both archives, and a CI gate fails the build if any `%%FILL` placeholder ever reappears in the sources. |

Both rounds' fixes are in the git history; the CI `paper` job compiles
the revised manuscript and assembles the Overleaf and submission
archives on every push.
