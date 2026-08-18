# PLA Reading List — NeSy/StarAI and AI-in-Auditing

Annotated map for the two-week literature pass (see `PROJECT_FEEDBACK.md` and
`research/GAP_STATEMENT.md`). Each entry says why it matters *for PLA
specifically*.

**Link status.** This file was authored in a sandbox whose network policy
blocks scholarly hosts (arxiv.org, doi.org, publisher sites), so URLs below
could not be resolved from here. Run `python3 scripts/check_links.py` on a
machine with open network access; it checks every URL in this file and fails
loudly on dead ones. Entries where the exact identifier could not be
confirmed carry a full text citation and no URL — resolve those via the title.

**Suggested order.** Week 1: sections A–C (know the incumbents and PLA's true
lineage). Week 2: sections D–F (the timely angle and the application
grounding).

---

## A. Foundational systems — the baseline pool

1. **De Raedt, L., Kimmig, A., & Toivonen, H. (2007).** "ProbLog: A
   Probabilistic Prolog and its Application in Link Discovery." *IJCAI 2007*,
   2462–2467. Project: https://dtai.cs.kuleuven.be/problog/
   *The direct competitor: Python-implemented probabilistic logic with proper
   distribution semantics. PLA's related-work section stands or falls on
   engaging this line seriously.*

2. **Fierens, D., Van den Broeck, G., Renkens, J., et al. (2015).** "Inference
   and Learning in Probabilistic Logic Programs using Weighted Boolean
   Formulas." *Theory and Practice of Logic Programming* 15(3), 358–401.
   https://arxiv.org/abs/1304.6810
   *The ProbLog 2 machinery (knowledge compilation). Contrast with PLA's
   fixpoint forward chaining — this is the "how is your inference different"
   answer reviewers will demand.*

3. **Richardson, M., & Domingos, P. (2006).** "Markov Logic Networks."
   *Machine Learning* 62, 107–136. https://doi.org/10.1007/s10994-006-5833-1
   *The undirected weighted-logic alternative. Note: weights are static —
   exactly the gap PLA's context-conditioned weights attack.*

4. **Bach, S. H., Broecheler, M., Huang, B., & Getoor, L. (2017).**
   "Hinge-Loss Markov Random Fields and Probabilistic Soft Logic." *JMLR*
   18(109), 1–67. https://jmlr.org/papers/v18/15-631.html — project:
   https://psl.linqs.org
   *Continuous truth values with a principled semantics; the nearest formal
   cousin of PLA's soft calculus, and the `pslpython` baseline for Phase 5.*

5. **Kimmig, A., Van den Broeck, G., & De Raedt, L. (2011).** "An Algebraic
   Prolog for Reasoning about Possible Worlds." *AAAI 2011*. (No verified URL
   from sandbox — resolve by title.)
   *aProbLog generalizes ProbLog to arbitrary semirings. This is the citation
   that legitimizes a non-probability confidence calculus like PLA's — if PLA's
   operators form a semiring-style algebra, say so through this lens.*

6. **Ankan, A., & Panda, A. (2015).** "pgmpy: Probabilistic Graphical Models
   using Python." *SciPy 2015*. https://github.com/pgmpy/pgmpy
   *The standard educational Bayesian-network library and a Phase 5 baseline;
   also the bar for what "usable Python probabilistic tooling" already means.*

## B. Neural-symbolic systems — the modern field

7. **Manhaeve, R., Dumančić, S., Kimmig, A., Demeester, T., & De Raedt, L.
   (2018).** "DeepProbLog: Neural Probabilistic Logic Programming."
   *NeurIPS 2018*. https://arxiv.org/abs/1805.10872 — repo:
   https://github.com/ML-KULeuven/deepproblog
   *Shows what "learnable weights through a logic layer" looks like done
   rigorously; Phase 4's design should be defensible against this standard.*

8. **Riegel, R., Gray, A., Luus, F., et al. (2020).** "Logical Neural
   Networks." https://arxiv.org/abs/2006.13155 — repo: https://github.com/IBM/LNN
   *IBM's differentiable weighted real-valued logic. Their treatment of
   truth-value bounds is a useful contrast to PLA's single-point confidences.*

9. **Li, Z., Huang, J., & Naik, M. (2023).** "Scallop: A Language for
   Neurosymbolic Programming." *PLDI 2023*. https://arxiv.org/abs/2304.04812
   — repo: https://github.com/scallop-lang/scallop
   *Provenance semirings for differentiable reasoning — technically the closest
   thing to "configurable aggregation semantics" done formally.*

10. **Marra, G., Dumančić, S., Manhaeve, R., & De Raedt, L. (2024).** "From
    Statistical Relational to Neurosymbolic Artificial Intelligence: A Survey."
    *Artificial Intelligence* 328. https://arxiv.org/abs/2108.11451
    *The field map. Use its taxonomy to place PLA precisely — being placeable
    on someone else's map is what "positioned" means.*

11. **Garcez, A. d'Avila, & Lamb, L. C. (2023).** "Neurosymbolic AI: The 3rd
    Wave." *Artificial Intelligence Review* 56, 12387–12406.
    https://arxiv.org/abs/2012.05876
    *The programmatic argument for why this area is hot now; useful framing
    for the introduction.*

12. **Nyga, D., et al.** pracmln — Markov Logic Networks in Python.
    https://github.com/danielnyga/pracmln
    *Python MLN implementation; with problog/pslpython/pgmpy it completes the
    "Python competitors" table in PROJECT_FEEDBACK.md.*

## C. Certainty factors and uncertainty calculi — PLA's true lineage

13. **Shortliffe, E. H., & Buchanan, B. G. (1975).** "A Model of Inexact
    Reasoning in Medicine." *Mathematical Biosciences* 23(3–4), 351–379.
    https://doi.org/10.1016/0025-5564(75)90047-4
    *The origin of rule-attached confidences (MYCIN certainty factors). PLA is
    structurally a modern descendant and must say so explicitly — claiming the
    lineage is a strength; hiding it is a desk-reject.*

14. **Heckerman, D. (1986).** "Probabilistic Interpretations for MYCIN's
    Certainty Factors." In Kanal & Lemmer (eds.), *Uncertainty in Artificial
    Intelligence 1*, North-Holland, 167–196. (No verified URL from sandbox —
    resolve by title.)
    *The coherence critique: CF calculus is only probabilistically sound under
    restrictive independence assumptions. Every reviewer who knows this paper
    will apply it to PLA — SEMANTICS.md (item S2) must answer it head-on.*

15. **Heckerman, D., & Shortliffe, E. H. (1992).** "From Certainty Factors to
    Belief Networks." *Artificial Intelligence in Medicine* 4(1), 35–52.
    https://doi.org/10.1016/0933-3657(92)90036-O
    *The retrospective on why the field moved from CF-style calculi to
    Bayesian networks. Understand this to argue when a CF-style system is
    still the right engineering trade (transparency, no joint distribution
    needed).*

16. **Zadeh, L. A. (1965).** "Fuzzy Sets." *Information and Control* 8(3),
    338–353. https://doi.org/10.1016/S0019-9958(65)90241-X
    *PLA's min() over antecedents is the Gödel t-norm — fuzzy conjunction, not
    probability. Cite the source rather than letting a reviewer point it out.*

## D. LLM + symbolic verification — the timely angle (2023–2026)

17. **Pan, L., Albalak, A., Wang, X., & Wang, W. Y. (2023).** "Logic-LM:
    Empowering Large Language Models with Symbolic Solvers for Faithful
    Logical Reasoning." *Findings of EMNLP 2023*.
    https://arxiv.org/abs/2305.12295
    *LLM translates natural language to a formal program; a solver reasons.
    PLA could be exactly such a solver for uncertain rules — candidate RQ3.*

18. **Olausson, T., Gu, A., Lipkin, B., et al. (2023).** "LINC: A
    Neurosymbolic Approach for Logical Reasoning by Combining Language Models
    with First-Order Logic Provers." *EMNLP 2023*.
    https://arxiv.org/abs/2310.15164
    *Same pattern with FOL provers; note their error analysis method — reusable
    for evaluating a PLA-as-verifier pipeline.*

19. **Ye, X., Chen, Q., Dillig, I., & Durrett, G. (2023).** "SatLM:
    Satisfiability-Aided Language Models Using Declarative Prompting."
    *NeurIPS 2023*. https://arxiv.org/abs/2305.09656
    *Declarative specification + SAT solving; the "declarative beats
    procedural" argument transfers to PLA's JSON scenarios.*

20. **Xu, J., et al. (2024).** "Faithful Logical Reasoning via Symbolic
    Chain-of-Thought." *ACL 2024*. https://arxiv.org/abs/2405.18357
    *Faithfulness of reasoning chains — directly relevant to PLA's
    trace-fidelity claims (item E5).*

21. **Kambhampati, S., Valmeekam, K., Guan, L., et al. (2024).** "LLMs Can't
    Plan, But Can Help Planning in LLM-Modulo Frameworks." *ICML 2024*.
    https://arxiv.org/abs/2402.01817
    *The general architecture argument: LLMs generate, sound external critics
    verify. PLA's niche in this architecture is "critic for uncertain
    domain rules."*

## E. Interpretability and explanation fidelity

22. **Rudin, C. (2019).** "Stop Explaining Black Box Machine Learning Models
    for High Stakes Decisions and Use Interpretable Models Instead." *Nature
    Machine Intelligence* 1, 206–215. https://arxiv.org/abs/1811.10154
    *The motivation for PLA's whole existence in regulated domains
    (audit/medical): inherently interpretable models over post-hoc
    explanations. Anchor citation for the introduction.*

23. **Jacovi, A., & Goldberg, Y. (2020).** "Towards Faithfully Interpretable
    NLP Systems: How Should We Define and Evaluate Faithfulness?" *ACL 2020*.
    https://arxiv.org/abs/2004.03685
    *The faithfulness-vs-plausibility distinction and evaluation criteria —
    the conceptual basis for the explanation-fidelity metric (item E5).*

## F. Auditing, fraud, and drift — application grounding

24. **Bao, Y., Ke, B., Li, B., Yu, Y. J., & Zhang, J. (2020).** "Detecting
    Accounting Fraud in Publicly Traded U.S. Firms Using a Machine Learning
    Approach." *Journal of Accounting Research* 58(1), 199–235.
    https://doi.org/10.1111/1475-679X.12292
    *The reference ML-for-accounting-fraud study, with public replication
    data — a candidate dataset for Phase 5 alongside the credit-card data.*

25. **Appelbaum, D., Kogan, A., & Vasarhelyi, M. A. (2017).** "Big Data and
    Analytics in the Modern Audit Engagement: Research Needs." *Auditing: A
    Journal of Practice & Theory* 36(4), 1–27. https://doi.org/10.2308/ajpt-51684
    *What the audit profession actually needs from analytics — the domain
    requirements PLA's explainability story should be written against.*

26. **West, J., & Bhattacharya, M. (2016).** "Intelligent Financial Fraud
    Detection: A Comprehensive Review." *Computers & Security* 57, 47–66.
    https://doi.org/10.1016/j.cose.2015.09.005
    *Survey of fraud-detection ML; use it to pick baselines and to justify the
    interpretability constraint.*

27. **Dal Pozzolo, A., Caelen, O., Johnson, R. A., & Bontempi, G. (2015).**
    "Calibrating Probability with Undersampling for Unbalanced
    Classification." *IEEE SSCI 2015*. https://doi.org/10.1109/SSCI.2015.33
    *Provenance of the public credit-card fraud dataset (item E1) and the
    calibration-under-imbalance issue PLA's evaluation must handle.*

28. **Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., & Bouchachia, A.
    (2014).** "A Survey on Concept Drift Adaptation." *ACM Computing Surveys*
    46(4). https://doi.org/10.1145/2523813
    *Context-conditioned rule weights are, in drift language, an adaptation
    mechanism — this survey connects candidate RQ1 to an established
    literature.*
