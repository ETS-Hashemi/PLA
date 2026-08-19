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

## Round 3 — external review (major revision), and its disposition

An external reviewer assessed the round-2 manuscript as needing major
revision (reject-and-resubmit at a selective AI/ML venue; plausible at
an applied XAI / research-software venue after revision), with eight
numbered blockers. Two described an intermediate CI build rather than
the round-2 PDF (Tables 3–4 bodies and the Figure-2 model set were
present at `003dacf`); the remaining six were real and drove this
round.

| # | Reviewer point | Disposition |
|---|---|---|
| 3-1 | Missing table bodies (pp. 22–23). | Artifact of an intermediate build that carried the `%%FILL` placeholders mid-campaign; the round-2 PDF has both bodies. The placeholder CI gate now prevents any such build from ever reading as final. |
| 3-2 | Statistical evidence insufficient: AP CIs not displayed; "no reliable benefit" from overlapping individual CIs; three seeds; "near-perfect calibration" vs the ~0.0125 constant-prevalence floor; equal-width ECE weak. | All five sub-points addressed with new computation. AP interval columns are displayed in every experiment table. Every difference claim now cites a **paired-bootstrap CI of the difference** (new `_diffs` files): SOX ablation ΔAUC 0.0011 [−0.0071, 0.0140] — an equivalence bound; credit-card ablation ΔAUC contains zero on 10/10 splits. The study runs **ten** random splits with a committed aggregator (mean ± sd, min–max, per-split paired diffs). A **constant-prevalence baseline row** appears in every table (credit-card log-loss 0.0127, exactly the reviewer's floor; its ECE of 0.0000 is quoted as the demonstration that equal-width ECE is blunt here); "near-perfect calibration" is deleted everywhere and replaced by floor-relative statements, with the log-binned reliability diagram as primary evidence. Bonus finding the paired instrument surfaced: the strict-design context effect is real (+0.0172 [0.0019, 0.0373]) — between two below-chance models; and the post-hoc credit-card AP edge is paired-significant on 10/10 splits, still reported as hypothesis-generating only. |
| 3-3 | Fidelity near-tautological; fact deletion confounded by overlapping rules; wants leave-one-rule-out, random controls, log-odds metrics, exact attributions. | Fidelity v2: **rule-level deletion** (top rule removed from the fold, facts untouched) is now the primary instrument — it quantifies the confound (fact-level comprehensiveness runs ~7–10% higher than rule-level); a deterministic **random-ranking control** joins the reversed one, margins carry paired CIs; **log-odds-scale** variants are computed throughout; the case study gains a **leave-one-rule-out table**; and the learned model's rule ranking is proven **exact by construction** on log-odds (contribution ≡ z_r; unit-tested), which §6.5 states up front as the boundary of what deletion metrics can certify — internal consistency, not external explanation quality (also now a limitation item). |
| 3-4 | PCA features are not domain rules. | Claim narrowed explicitly, in §6, the intro contribution, and a new limitation: credit card demonstrates computational traceability; the accounting ratios carry the domain vocabulary (top mined rules pair receivables changes with divergent cash sales / free cash flow — named in the text); neither dataset alone carries the full claim. |
| 3-5 | Novelty modest; ANFIS / fuzzy rule-based systems missing from positioning. | New related-work subsection on adaptive fuzzy rule systems (ANFIS; evolving-fuzzy-systems survey) stating what is shared (fitted rule strength, discretization tension) and what differs (trace-first packaging, named aggregation semantics, measured fidelity). Novelty language across abstract/intro/conclusion already recentred in rounds 1–2 on the system + measurement + honest-negative contribution — the framing the reviewer deems publishable. |
| 3-6 | Formal overclaims: Kleene needs continuity; randomized tests ≠ guarantees; 200-epoch monotonicity ≠ proof; reduction needs flat/crisp restriction; zero-rule text conflicts with intercept. | All repaired: Proposition 1 now states continuity of the three operators and why it licenses the Kleene step; "machine-checked guarantees" replaced by proof + property-based corroboration everywhere (abstract, intro, §3, §5, workshop, highlights); descent claims carry the explicit bound η ≤ 2/L with L ≤ max‖x‖²/4 ≤ 3.5 (η ≈ 0.57 guaranteed; our η = 1.0 asserted per-epoch by tests); the reduction is restricted to flat rule sets over crisp facts; the zero-rule paragraph now distinguishes the interceptless floor (no gradient) from the intercept path (σ(b), trains b). |
| 3-7 | Semiring claim incorrect (min does not distribute over noisy-OR). | Correct, and adopted: §2 now states aProbLog is a reference point, **not** an umbrella containing PLA, with the reviewer's counterexample (0.5 vs 0.64) in the text and as an executable block in `docs/SEMANTICS.md` run by the test suite. |
| 3-8 | Production errors: Figure 2 model set; "Appendix Appendix"; double periods; Appendix B collision. | Figure 2 and "Appendix Appendix" were already fixed in round 2 (the former only ever affected the intermediate build). The **double periods were real**: elsarticle appends its own period after `\paragraph` titles; all trailing periods stripped. Appendix B refloated off the page number. |

Net effect on the results narrative: the ten-split, paired-difference
analysis *strengthened* the paper's claims rather than weakening them —
the pre-registered null is now an interval bound, the AP trade is
paired-significant, and the one place the mechanism does something
(strict design) is shown to be real but useless. 93 tests pass; all
regeneration is committed.

## Round 4 — external review (second pass), and its disposition

The same external reviewer re-reviewed the round-3 build and found
seven remaining defect groups. All accepted; none required walking back
a result.

| # | Reviewer point | Disposition |
|---|---|---|
| 4-1 | Optimization guarantee still wrong: convexity does not give uniqueness or arbitrary-step convergence (nor a finite optimum under separation), and the norm bound omitted rule–context interactions — ‖x‖² ≤ 2R+1 = 23, so the safe constant step is ≈0.348, not covering η=1.0. | §4 rewritten: convexity stated as "local = global" only, with non-uniqueness, step-size, and separation caveats explicit; the bound corrected to 2R+1=23 (η_safe ≈ 0.35); and the reviewer's third option implemented in code — `fit()` now carries a **backtracking guard** (accept an epoch only if the loss does not increase, else roll back and halve the rate; unit-tested against a deliberately oversized step). The guard is inert at the reported rates: regenerating the seeded synthetic experiment after the change reproduces the committed file byte-for-byte except the new ProbLog note field. |
| 4-2 | "Equivalence" requires a prespecified margin and test. | Correct — the preregistration (gap statement, commit `8f2dd2e`) was directional only and named no margin. The manuscript now reports the paired interval as a **bound**, states explicitly that no equivalence test is licensed, and cites the commit; README/results wording matched. |
| 4-3 | Context conclusion too broad given the 10/10 AP edge and AP's audit-queue billing. | The reviewer's sentence adopted nearly verbatim as the verdict: *no practically useful improvement on the pre-specified AUC endpoint; the consistent post-hoc AP improvement on credit card requires confirmation.* The verdict paragraph now names the tension openly instead of hiding it in a footnote clause. Propagated to abstract, conclusion, workshop, READMEs, and the gap statement. |
| 4-4 | Stale statements: three seeds (p16), three-seed AP range (p29), "machine-checked convergence" (p33 + highlights + cover letter), Appendix B seed list, "marginal-entropy floor", "skill baseline" typo, Figure-4 caption still arguing from overlap. | All fixed: ten splits in §5; ten-split AP sentence in the discussion; the last "machine-checked" instances replaced in conclusion, highlights, and cover letter; Appendix B row now lists seeds 43–51, the seed summary, and the `_diffs` files; "floor"→"null baseline" everywhere with the explicit note that better predictors score below it; "skill baseline"→"null baseline"; Figure 4's caption now labels its per-model intervals descriptive and points to the paired interval for inference. |
| 4-5 | Novelty framing: context conditioning is interaction features other systems can encode; the contribution is the engine/export/discipline/trace interface. | Stated in the paper's own voice at both sites: §2's gap paragraph now calls it an *interface* gap, not an expressivity gap, and §4 opens the reduction with the deflationary reading (context-conjoined rules suffice in fixed-weight systems; the contribution is exposure, exact export, and tracing). Intro contribution 2 says the same. |
| 4-6 | Presentation: Appendix-B/page-number collision; "equal-interpretability" unquantified; Table-4 inclusion criterion undefined; single deterministic random permutation; ProbLog "cross-validation" via subset CIs. | Appendix table moved to a float page and set single-spaced; baselines renamed "interpretable competitors of comparable but not identical complexity" with the tree's ≤15 splits and EBM's per-feature shape functions quantified against 11 rules; Table-4 caption defines n (examples with ≥1 fired rule); the random control is now the **average over ten seeded permutations** (per-example averaging, so paired CIs compare against the averaged control); the ProbLog cross-check is **direct same-example agreement** — max per-example gap vs the engine's fold recorded in every generated file (7.1×10⁻⁷ on the synthetic subset) — with the subset row's interval labeled descriptive. |
| 4-7 | (Implicit) regeneration burden of the above. | Credit-card seeds 42–44, both Bao designs, and all four fidelity files regenerated under the new note and control; fast seeds 45–51 are untouched by construction (they skip the ProbLog row and are not fidelity inputs). |
