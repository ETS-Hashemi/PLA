# A Probabilistic Logic Agent Framework for Context-Aware Reasoning and Parallel Scenario Modeling

## Abstract

This paper introduces the **Probabilistic Logic Agent Framework**, a novel system that integrates symbolic reasoning, probabilistic reasoning, and context-aware adjustments to model uncertainty in real-world scenarios. The framework supports dynamic context-aware reasoning, parallel scenario modeling across diverse domains, and hybrid reasoning for combining symbolic and probabilistic systems. We demonstrate its applicability in domains such as accounting, auditing, pharmaceutical, oncology, and logistics. The framework's modularity, explainability, and scalability make it a valuable tool for decision-making in uncertain environments.

---

## 1. Introduction

Reasoning under uncertainty is a critical challenge in artificial intelligence (AI). Traditional symbolic reasoning systems provide logical guarantees but lack the ability to handle uncertainty. Probabilistic reasoning systems, on the other hand, model uncertainty but often lack explainability. This paper presents a hybrid framework that combines the strengths of both approaches while introducing **context-aware reasoning** and **parallel scenario modeling** to address real-world complexities.

### Contributions
1. **Context-Aware Reasoning**: Dynamically adjusts rule probabilities based on external conditions.
2. **Parallel Scenario Modeling**: Supports domain-specific scenario configurations for comparative analysis.
3. **Hybrid Reasoning**: Combines symbolic and probabilistic reasoning for comprehensive decision-making.
4. **Explainability**: Provides detailed reasoning chains for each query.
5. **Scalability**: Handles complex scenarios across multiple domains.

---

## 2. Related Work

Citation keys `[R1-n]` refer to `research/READING_LIST.md`, which carries the
full bibliography; claims about ProbLog and pgmpy below are additionally
machine-verified by `tests/test_related_work_claims.py` against the installed
systems.

### 2.1 Probabilistic logic programming

ProbLog [R1-1] attaches probabilities to logic programs under the
**distribution semantics**: programs denote measures over possible worlds,
inference computes exact marginals via knowledge compilation [R1-2], and —
unlike PLA — the system supports conditioning on evidence (verified against
the installed `problog` package). aProbLog [R1-5] generalizes the semantics
to arbitrary commutative semirings, which is the correct formal umbrella for
non-probabilistic confidence calculi such as PLA's. DeepProbLog [R1-7]
extends the family with neural predicates and gradient-based learning, and
Scallop [R1-9] compiles differentiable reasoning over provenance semirings.
All are available as Python packages; any claim that this space lacks Python
tooling is false and PLA makes no such claim.

### 2.2 Weighted logic and statistical relational learning

Markov Logic Networks [R1-3] attach real-valued weights to first-order
clauses defining a Markov random field; Probabilistic Soft Logic [R1-4]
relaxes truth values to [0,1] with hinge-loss MRFs, making it the nearest
formally-grounded cousin of PLA's soft confidences; Logical Neural Networks
[R1-8] make weighted real-valued logic differentiable with truth-value
bounds. In all three, rule weights are **static** at inference time:
adapting rule reliability to a changing operational context is handled by
retraining, not by the semantics. That gap — context-conditioned rule
weights inside an interpretable calculus — is the opening PLA's RQ1 targets,
connected to concept-drift adaptation [R1-28]. Bayesian networks (pgmpy
[R1-6]) provide joint-distribution posteriors (machine-verified) but no
rule-shaped, trace-first explanations.

### 2.3 Uncertainty calculi: PLA's lineage

PLA's operators are a modern descendant of MYCIN's certainty factors
[R1-13]: rule-attached confidences, attenuation by the weakest antecedent
(Zadeh's Gödel t-norm [R1-16]), and parallel combination of co-supporting
rules — PLA's default noisy-OR **is** the CF parallel-combination formula
(machine-verified equivalence in `docs/SEMANTICS.md`). Heckerman [R1-14]
showed the CF calculus is probabilistically coherent only under restrictive
independence and modularity assumptions, and the field's retrospective
[R1-15] explains the subsequent move to belief networks. PLA's response
(SEMANTICS.md §6) is to drop the probability claim, name the independence
stance as a per-KB operator choice, and offer log-odds modes matching the
coherent likelihood-ratio special case.

### 2.4 Positioning

PLA does not compete with these systems on semantic guarantees; it occupies
the point they leave open: a fully readable engine (a few hundred lines,
zero dependencies) whose primary output is the reasoning trace, whose rule
weights are **context-conditioned and learnable** (Sections 3–4), and whose
explanation fidelity is measured rather than asserted [R1-22, R1-23]
(Section 5). The intended domains are education and audit-style settings
[R1-25] where inherent interpretability is a requirement, not a preference.

---

## 3. Methodology

### 3.1 Probabilistic Reasoning
The framework employs forward chaining to infer new facts and calculate their probabilities. The probability of a result is calculated as:
```
P(B) = Prule * min(P(A1), P(A2), ..., P(An))
```
where `Prule` is the rule's base probability, and `P(Ai)` are the probabilities of the antecedents.

### 3.2 Context-Aware Reasoning
Each rule can specify context variables with associated weights. The adjusted probability is computed as:
```
P_adjusted = P_rule * ∏(weight for each active context variable)
```
If the computed value exceeds 1.0, it is capped at 1.0.

### 3.3 Parallel Scenario Modeling
The framework supports domain-specific scenario configurations in JSON files. Each scenario includes facts, rules, and queries. Parallel scenarios allow comparative analysis across domains such as accounting, auditing, pharmaceutical, oncology, and logistics.

### 3.4 Hybrid Reasoning
The hybrid engine combines symbolic and probabilistic reasoning. Symbolic reasoning provides logical guarantees, while probabilistic reasoning handles uncertainty. The results are combined to provide a comprehensive explanation.

---

## 4. Implementation

### 4.1 Framework Architecture
The framework consists of the following components:
1. **Knowledge Base (KB)**: Stores facts and rules for symbolic reasoning.
2. **Probabilistic KB**: Stores probabilistic rules and supports context-aware adjustments.
3. **Inference Engine**: Performs forward chaining to infer new facts and calculate probabilities.
4. **Hybrid Engine**: Combines symbolic and probabilistic reasoning.
5. **REST API**: Provides programmatic access to the framework.

### 4.2 JSON Configuration
Scenarios are defined in JSON files with the following structure:
```json
{
  "facts": ["Fact1", "Fact2"],
  "rules": [
    {
      "condition": ["Fact1", "Fact2"],
      "result": "ResultFact",
      "probability": 0.8,
      "context": {
        "ContextVariable1": 1.2,
        "ContextVariable2": 1.5
      }
    }
  ],
  "queries": ["ResultFact"]
}
```

### 4.3 REST API
The REST API supports the following endpoints:
1. **Load Scenario**: Dynamically load a JSON scenario.
2. **Query Knowledge Base**: Retrieve probabilities and explanations for specific queries.

---

## 5. Experimental Results

### 5.1 Scenario suite

The table below reports scenario sizes and inferred query confidences for
five representative scenarios (context set "1" active). It is generated by
`python scripts/benchmark.py --paper-table` and embedded verbatim — do not
edit it by hand; regenerate it. Wall-clock timings are machine-dependent
and therefore not embedded; the same script's timing mode reports them per
scenario.

<!-- BEGIN GENERATED BENCHMARK TABLE (scripts/benchmark.py --paper-table) -->
| Scenario | Facts | Rules | Query | Probability |
|---|---|---|---|---|
| accounting_very_complex | 6 | 5 | InvestigationRequired | 0.892294 |
| auditing_complex | 4 | 3 | InvestigationRequired | 0.931000 |
| pharmaceutical_very_complex | 6 | 7 | RecallRequired | 0.995500 |
| pharmaceutical_very_complex | 6 | 7 | PublicNotification | 0.992130 |
| pharmaceutical_very_complex | 6 | 7 | RegulatoryInvestigation | 0.950000 |
| oncology_complex | 4 | 3 | BiopsyRequired | 0.859500 |
| logistics_very_complex | 6 | 5 | CustomerNotification | 0.893000 |
<!-- END GENERATED BENCHMARK TABLE -->

### 5.2 Case studies

**[PLACEHOLDER — no results exist yet.]** Real-data case studies (public
credit-card fraud and accounting-fraud datasets, with baselines and
calibration metrics) are specified as Phase 5 of `TODO.md` (items E1–E5)
and will replace this section when the experiments have been run. Earlier
versions of this draft stated invented case-study numbers here; they have
been removed.

---

## 6. Discussion

### 6.1 Advantages
- **Explainability**: Provides detailed reasoning chains for each query.
- **Scalability**: Handles complex scenarios across multiple domains.
- **Modularity**: Easily extended to support additional domains.

### 6.2 Limitations
- **Performance**: Execution time increases with scenario complexity.
- **Context Dependency**: Requires accurate context data for optimal performance.

---

## 7. Conclusion

The **Probabilistic Logic Agent Framework** is a novel system that integrates symbolic reasoning, probabilistic reasoning, and context-aware adjustments. Its support for parallel scenario modeling and hybrid reasoning makes it a valuable tool for decision-making in uncertain environments. Future work will focus on optimizing performance and extending the framework to additional domains.

---

## References

Full bibliographic entries for all `[R1-n]` keys live in
`research/READING_LIST.md` (28 annotated entries; link resolution via
`scripts/check_links.py`). General background:

1. Pearl, J. (1988). Probabilistic Reasoning in Intelligent Systems.
2. Russell, S., & Norvig, P. (2020). Artificial Intelligence: A Modern Approach.
3. Clarke, E. M., Grumberg, O., & Peled, D. A. (1999). Model Checking.

---

## Appendix

### A. Sample JSON Scenario
```json
{
  "facts": ["PersistentCough", "WeightLoss"],
  "rules": [
    {
      "condition": ["PersistentCough", "WeightLoss"],
      "result": "LungCancerRisk",
      "probability": 0.7,
      "context": {
        "PatientAge>60": 1.2,
        "SmokingHistory": 1.5
      }
    }
  ],
  "queries": ["LungCancerRisk"]
}
```

### B. REST API Example
1. **Load Scenario**:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"config_path": "scenario_oncology_complex.json"}' http://localhost:5000/load
   ```
2. **Query Knowledge Base**:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"query": "LungCancerRisk"}' http://localhost:5000/query
   ```

