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

## Round 5 — author's final corrections on the submitted Overleaf version

The corresponding author edited the Overleaf project directly (adding
Julio Montecinos as second author) and returned eight final
corrections. The edited sources were adopted as the new base and the
corrections applied on top.

| # | Correction | Disposition |
|---|---|---|
| 5-1 | "in general undefinable" (per-rule decomposition) overstates. | §2 and §3.5 now say an additive per-rule decomposition of a marginal is **not uniquely determined by the distribution semantics without an additional attribution rule**; §3.5 adds the inclusion–exclusion reading and notes Shapley-style attributions can be imposed but import assumptions. |
| 5-2 | "ProbLog is right and PLA is not" too self-deprecating. | §2's price sentence now reads: *ProbLog is the appropriate choice when possible-world semantics and evidence conditioning are required.* |
| 5-3 | Step-size notation: define L̄ and derive the bound. | §4: L̄ = max‖x‖²/4 with ‖x‖² ≤ 2R+1 = 23, so L̄ = 23/4 and any constant step 0 < η < 2/L̄ = 8/23 ≈ 0.348 provably decreases the loss; η = 1.0 sits above the bound and is covered by the (never-fired) backtracking guard. |
| 5-4 | State what ŷ *is* probabilistically. | §4 now says ŷ on the learned classification path is a **discriminative conditional-probability estimate** for the target — licensing cross-entropy training and the calibration metrics — even though the engine defines no joint distribution over all propositions. |
| 5-5 | Presentation: dangling author superscript; "expressivity ," splice; §4 punctuation; split finding-3 sentence; Fig-3 caption run-on; "re-mining, not reweighting" punctuation; conclusion "are in"; CRediT labels. | All fixed: corresponding-author `\corref` mark replaces the dangling superscript; the intro splice is now a colon; finding 3 split into three sentences; Fig-3 caption split; discussion comma repaired; conclusion reads "The real-data studies show that…"; CRediT entries use standard taxonomy labels ("Writing – original draft"; "Validation, Writing – review & editing"). |
| 5-6 | "paired-significant" is not a statistic. | Abstract, discussion, and both READMEs now say the paired-bootstrap confidence interval **excluded zero** on nine of ten splits. |
| 5-7 | ProbLog per-example compilation cost is our harness's, not ProbLog's. | §2 deployment bullet and §6 setup both scope it: a cost of the per-example evaluation harness, not an inherent property of ProbLog deployments. |
| 5-8 | Archive the exact submitted version (tag or DOI) and link the pre-registration commit directly. | Data availability now links the pre-registration commit URL (full hash) and names tag `v1.0-submission`. The tag is created locally on the submission commit; the hosting environment's credentials cannot push tags (HTTP 403 on `git push origin <tag>`), so the author must publish it once from any checkout: `git fetch && git tag v1.0-submission <submission-commit> && git push origin v1.0-submission`, or create a GitHub Release with that tag name on the submission commit. |

Also in this round: cover letter pluralized to "The authors declare";
the workshop cut intentionally remains single-author (the author's
call); Montecinos's CRediT roles are as the author assigned them —
only the labels were standardized.

## Round 6 — external review (third pass), and its disposition

Six points; all accepted. One required a new experiment across every
design.

| # | Reviewer point | Disposition |
|---|---|---|
| 6-1 | Comprehensiveness and sufficiency never defined mathematically; cite the defining literature (ERASER). | §6.5 now carries display equations for both metrics at both levels, exactly matching `pla/fidelity.py`: fact-level comp = s(F) − s(F∖A₁), suff = s(F) − s(F∩A₁); rule-level comp = τ(s(F)) − τ(s₋ᵣ₁(F)), suff = τ(s(F)) − τ(s_{r₁}(F)), with τ the identity or the ε-clipped logit (ε=10⁻⁹), averaged over examples with ≥1 fired rule. DeYoung et al. 2020 (ERASER) cited at the definitions and at the intro's first mention; Jacovi & Goldberg 2020 kept for the faithfulness framing. |
| 6-2 | No direct rule-model baseline despite discussing RuleFit/RIPPER/BRL/CORELS. | **RuleFit added and run on every design** (imodels implementation, cited): configured as a pure rule ensemble — max_rules=30, include_linear=False, fixed seed — a configuration itself verified by a claims test. Ten-split credit card: AUC 0.9437 ± 0.0134 (below PLA static on all ten splits), AP 0.8013 ± 0.0293 (above PLA static on all ten); strict drift 0.5825 and SOX 0.6065 (degrades like every thresholded rule model while continuous-feature models hold 0.65–0.70 — corroborating the vocabulary-drift lesson from outside PLA); synthetic 0.8294 (between the fixed-decile propositional block and the raw-feature models, as the discretization-tax reading predicts). All tables, figures, findings, discussion, READMEs, and the workshop cut updated; every regenerated file is an add-only diff (pre-existing rows byte-identical). |
| 6-3 | Terminology: Appendix A says "probability", package named probabilistic-logic-agent, paper says values are not probabilities. | `"confidence"` is now the canonical scenario rule-value key and the documented preferred accessor (`ProbRule.confidence`); `"probability"` is a documented deprecated alias (both-keys-disagree fails loud); query results carry a `"confidence"` key with `"probability"` kept as a deprecated duplicate; all 34 scenario files, the scenario exporter, docs, README, Appendix A, and SEMANTICS.md updated, and both now state the distribution name is historical. Six new tests. |
| 6-4 | Abstract ~285 words; reduce to 230–250. | Rewritten at 249 words; no claim dropped. |
| 6-5 | Put the intercept into Eq. (6). | Eq. (6) is now ŷ = σ(b + Σ_{r fired} z_r), with the base-rate-prior-rule reading stated at the equation, the interceptless variant identified as b = 0, and the later intercept paragraph rewritten to reference the equation instead of re-deriving it. |
| 6-6 | Conclusion's "calibration beats the constant-prevalence null baseline" is not true for every accounting design. | Reworded to the reviewer's sentence: *on the credit-card study, the learned model's log-loss beats the constant-prevalence baseline*; the abstract, cover letter, and both READMEs now attribute the log-loss win to the learned weights on credit card specifically. |

Test count after this round: 101 (swept in README, §5, and the
workshop cut).

## Round 7 — external review (fourth pass), and its disposition

One mathematical catch (accepted in full — it reshaped Section 6.5), one
inconsistency, and submission-hygiene items.

| # | Reviewer point | Disposition |
|---|---|---|
| 7-1 | For flat static noisy-OR, s − s₋ᵢ = pᵢ·∏_{j≠i}(1−pⱼ): within a fired set, ranking by precision **is** ranking by deletion impact — Table 4 is algebra, not independent evidence; the "heuristic that could have failed" framing is wrong. | Accepted completely. §6.5 now states the identity as Eq. (noisyor-deletion), declares **both** rankings exact by construction in the flat crisp experiments, and re-captions/reads Table 4 as *implementation-concordance validation* (pipeline vs. algebra, with the controls calibrating the metric's range). The "genuine heuristic" language was swept from the intro, limitations, discussion, table caption, module docstrings, and READMEs. |
| 7-2 | (Reviewer's alternative, adopted as well) Add a graded/chained/multi-step experiment where the ranking is genuinely nontrivial. | **New study**: `scripts/run_fidelity_chained.py` — 20 independently seeded three-step programs (facts → 4 intermediates → deep node → target; graded antecedent minima), every fired rule's true target impact computed by brute-force deletion with fixpoint re-run, trace's local-candidate ranking scored against that oracle plus reversed/random controls. **Verdict: a measured negative.** Pooled n=6,348: top-1 oracle agreement 32.4% vs. tie-aware chance 25.8%; trace captures 49% of oracle impact (0.1597 vs. 0.3238); beats reversed overall (+0.0767 [0.0708, 0.0814]) but the margin over random flips sign across programs (CI above zero in 9/20, below in 7/20). Mechanism: the load-bearing rule is typically an upstream non-redundant one that local candidate magnitude cannot identify. Design consequence stated in §6.5, discussion, and intro contribution 3: within one fold candidates are exact; across folds the trustworthy attribution is the deletion counterfactual (the case study's leave-one-rule-out table). Three tests pin determinism, the oracle ceiling, and non-degeneracy; results in `results/fidelity_chained_synthetic.{csv,md}`. |
| 7-3 | §4.1: Eq. (6) with no fired rules and b=0 gives σ(0)=0.5, but the text says "fixed small floor". | Fixed: the floor (10⁻³, `NO_FIRE_FLOOR`) is now described as a deliberate out-of-model implementation convention of the interceptless configuration — the pure reduction would give σ(0)=½ — and every reported experiment uses the intercept, where the model itself gives σ(b). `pla/learn.py` docstring matched. |
| 7-4 | Replace "archived immutably at GitHub" with a Zenodo/OSF archive + DOI. | Data availability now says the submitted revision is tagged and deposited as a citable archive on Zenodo with the DOI stated in the repository README, and carries an AUTHOR ACTION comment with the exact steps (enable repo at zenodo.org/account/settings/github, create release `v1.0-submission`, paste the DOI badge). The deposit cannot be made from this environment; it is a required pre-submission author step. |
| 7-5 | Add a funding declaration. | Added: "No funding was received for conducting this study," with an AUTHOR ACTION comment to replace with scholarship/grant numbers if applicable. |
| 7-6 | If submitting to Applied Intelligence, convert to Springer `smallcondensed` with a Declarations section. | **Deferred by decision, not oversight**: the manuscript targets Knowledge-Based Systems (elsarticle); a Springer conversion is mechanical and should happen only if the venue decision changes. Logged here so the requirement is not lost. |
| 7-7 | Move Appendix B / implementation detail to supplementary material; shorten the 47-page PDF. | The claim-provenance table moved to a standalone `paper/supplementary.tex` (Table S1), compiled by the build script and shipped in both packages; the manuscript keeps a one-line pointer in §1 and §5. Appendix A (scenario format) stays in the paper. |
| 7-8 | Add 2025–2026 references (list ended at 2024). | Four verified additions, each checked against its venue page before citing: F-Fidelity (ICLR 2025) at the fidelity definitions — with the note that rule-level deletion is less exposed to the OOD critique than input-space perturbation; Di Marino et al., ACM Computing Surveys 57(10) 2025, at the intro's interpretability claim; Colelough & Regli's 2025 systematic review (arXiv:2501.05435) in §2; ProverGen (ICLR 2025) at the conclusion's LLM generate-and-verify direction. An MDPI 2025 fraud paper was found but its author list could not be verified through the egress proxy, so it was not cited. |

Also in this round (author request): a footnote at the first use of
\pla{} states the name abbreviates *Probabilistic Logic Agent*, kept
for continuity with the released package, recording lineage rather
than a semantic claim.

## Round 8 — prose naturalness pass (author request)

Style-only edit across the manuscript, workshop cut, and READMEs: no
claim, number, citation, table cell, or equation changed. What moved:
overused intensifiers thinned ("exactly" 22 → 9, keeping only identity
claims such as "reduces exactly to logistic regression"; "genuinely"
0; "deliberately" and "provably" kept only in formal register),
em-dash interpolations converted to commas, parentheses, or separate
sentences (14 → 1, matching the author's own earlier punctuation
preference), repeated signature phrasings varied ("drawn honestly" →
"made explicit", "the honest headline" → "the number to quote",
"measured negative" → "clear negative", "ships" → "exports"), and two
"exactly why … exactly why" / double-"exactly" constructions
rewritten. Diff is reviewable as prose-only.

## Round 9 — author's final revision adopted

The author's Overleaf export (5th) was adopted as the new base. The
author's own decisions in it, recorded here:

- **Single authorship.** Julio Montecinos removed from the author
  list and CRediT; the corresponding-author markup dropped as
  unnecessary. Consistency sweep applied: "The author declares"
  (manuscript and cover letter), singular wording in the AI
  declaration, supplementary title page.
- **Generative-AI declaration added by the author** (Claude and
  ChatGPT; language editing, LaTeX restructuring, code error
  checking), satisfying the Elsevier disclosure requirement.
- **Data availability simplified** to the repository URL alone: the
  round-7 tag/Zenodo archival sentence was withdrawn by the author,
  so the section now makes no claim that requires a pre-submission
  step. The pre-registration commit remains cited in Section 6. The
  Zenodo option is kept as a comment for the author to take up or
  not.
- Remaining em-dash interpolations converted to commas across the
  abstract, introduction, calculus, implementation, evaluation, and
  discussion, completing the author's punctuation pass.
