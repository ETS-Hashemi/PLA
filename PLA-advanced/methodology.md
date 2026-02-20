# Methodology and Algorithms

This document provides a detailed description of the algorithms and methodologies used in the **Probabilistic Logic Agent Framework**. It includes formal definitions and explanations of probabilistic reasoning, symbolic reasoning, hybrid reasoning, and context-aware reasoning.

---

## **1. Probabilistic Reasoning**

Probabilistic reasoning is used to infer outcomes in uncertain environments by propagating probabilities through a set of rules. The framework employs **forward chaining** to infer new facts and calculate their probabilities.

### **1.1 Forward Chaining**
Forward chaining is a data-driven reasoning approach where known facts are used to infer new facts by applying rules. The process continues until no new facts can be inferred.

#### **Algorithm: Forward Chaining**
1. Initialize the set of **inferred facts** with the given facts.
2. For each rule:
   - Check if all conditions (antecedents) of the rule are satisfied by the inferred facts.
   - If satisfied, calculate the probability of the result (consequent) using the rule's probability and the probabilities of the conditions.
   - Add the result to the set of inferred facts.
3. Repeat until no new facts can be inferred.

#### **Example**
Given:
- Facts: `LargeTransaction` (P=1.0), `NoReceipt` (P=1.0)
- Rule: `If LargeTransaction and NoReceipt -> Fraud (P=0.85)`

Steps:
1. Both `LargeTransaction` and `NoReceipt` are true.
2. Apply the rule: `P(Fraud) = 0.85 * min(P(LargeTransaction), P(NoReceipt)) = 0.85`.
3. Infer `Fraud` with `P=0.85`.

---

### **1.2 Probability Propagation**
The probability of a result is calculated as the product of the rule's probability and the minimum probability of its conditions. This ensures that the weakest link in the chain determines the overall probability.

#### **Formula**
For a rule:
```
If A1 and A2 and ... and An -> B (P=Prule)
```
The probability of `B` is:
```
P(B) = Prule * min(P(A1), P(A2), ..., P(An))
```

---

## **2. Symbolic Reasoning**

Symbolic reasoning is used to infer logical conclusions based on a set of facts and rules expressed in propositional logic. The framework uses **model checking** to determine whether a query is entailed by the knowledge base.

### **2.1 Propositional Logic**
Propositional logic is a formal system where statements (propositions) are either true or false. Logical operators (e.g., AND, OR, NOT, IMPLIES) are used to combine propositions.

#### **Definitions**
- **Symbol**: A basic proposition (e.g., `A`, `B`).
- **And**: `A AND B` is true if both `A` and `B` are true.
- **Implication**: `A -> B` is true if `A` is false or `B` is true.

#### **Example**
Given:
- Facts: `A`, `B`
- Rule: `A AND B -> C`

The query `C` is true because both `A` and `B` are true.

---

### **2.2 Model Checking**
Model checking verifies whether a query is true in all models (interpretations) where the knowledge base is true.

#### **Algorithm: Model Checking**
1. Represent the knowledge base as a conjunction of facts and rules.
2. Represent the query as a proposition.
3. Evaluate whether the query is true in all models where the knowledge base is true.

#### **Example**
Given:
- Facts: `A`, `B`
- Rule: `A AND B -> C`
- Query: `C`

Steps:
1. Combine facts and rules: `KB = A AND B AND (A AND B -> C)`.
2. Check if `KB -> C` is true in all models.

---

## **3. Hybrid Reasoning**

Hybrid reasoning combines symbolic and probabilistic reasoning to leverage the strengths of both approaches. Symbolic reasoning provides logical guarantees, while probabilistic reasoning handles uncertainty.

### **3.1 Combining Symbolic and Probabilistic Systems**
The framework uses a **hybrid engine** that queries both the symbolic and probabilistic systems and combines their results.

#### **Algorithm: Hybrid Reasoning**
1. Query the symbolic knowledge base:
   - If the query is entailed, proceed to probabilistic reasoning.
   - If not, return a probability of `0.0`.
2. Query the probabilistic knowledge base:
   - Calculate the probability of the query using forward chaining and probability propagation.
3. Combine the results:
   - If symbolic reasoning supports the query, return the probabilistic result.
   - Otherwise, return a probability of `0.0`.

#### **Example**
Given:
- Symbolic KB: `A AND B -> C`
- Probabilistic KB: `If LargeTransaction AND NoReceipt -> Fraud (P=0.85)`

Steps:
1. Query `C` in the symbolic KB:
   - If `A` and `B` are true, `C` is true.
2. Query `Fraud` in the probabilistic KB:
   - If `LargeTransaction` and `NoReceipt` are true, `P(Fraud) = 0.85`.
3. Combine results:
   - Return the symbolic result for `C` and the probabilistic result for `Fraud`.

---

## **4. Context-Aware Reasoning**

Context-aware reasoning dynamically adjusts rule probabilities based on the current context. This feature allows the framework to adapt to external conditions in real time.

### **4.1 Context Variables and Adjustment**

Each rule can specify context variables along with their weights. The adjusted probability of a rule is computed as:
```
P_adjusted = P_rule * ∏(weight for each active context variable)
```
If the computed value exceeds 1.0, it is capped at 1.0.

### **4.2 Context Flattening**

A new step, **Context Flattening**, has been introduced within the framework. After loading a scenario and setting a global context (by specifying a context number), each rule's context is “flattened” so that only the active context dictionary is used during probability adjustment. This ensures that the `adjusted_probability` method multiplies the base probability by the correct weight directly.

For example, if a rule defines:
```
"context": {
    "1": {"AgeOver60": 1.2},
    "2": {"SmokingHistory": 1.3}
}
```
and the active context is `"1"`, the rule's context is flattened to:
```
{"AgeOver60": 1.2}
```
Then the adjusted probability is:  
`0.7 * 1.2 = 0.84`.

### **4.3 Parallel Scenario Modeling**

In addition to context-aware reasoning, the framework supports the modeling of complex parallel scenarios that span different domains (e.g., accounting, auditing, pharmaceutical, oncology, logistics). Each domain scenario is defined in a separate JSON configuration file with its own facts, rules, and queries. This approach allows:
- Domain-specific customization of rules and context.
- Comparison between different scenarios across domains.
- Scalability and modularity in scenario management.

For example, an accounting scenario might include rules for fraud detection based on transaction patterns, while a pharmaceutical scenario may model recall and market withdrawal decisions. Both leverage the same probabilistic reasoning core.

---

## **5. Summary**

The **Probabilistic Logic Agent Framework** integrates symbolic, probabilistic, and context-aware reasoning to handle both logical guarantees and uncertainty. Key methodologies include:
- **Forward Chaining**: Data-driven reasoning to infer new facts.
- **Probability Propagation**: Calculating probabilities based on rule strengths and conditions.
- **Model Checking**: Verifying logical entailment in symbolic reasoning.
- **Hybrid Reasoning**: Combining symbolic and probabilistic systems for comprehensive reasoning.
- **Context-Aware Reasoning**: Dynamically adjusting probabilities based on external conditions.

This combination makes the framework suitable for complex domains like auditing, accounting, logistics, and medical diagnosis.

---

## **6. Benchmarking**

The framework includes a benchmarking module to evaluate the performance of probabilistic reasoning over complex scenarios. The benchmarking script measures:
- Query execution time.
- Total execution time for all queries in a scenario.

This helps identify performance bottlenecks and optimize reasoning for large-scale scenarios.

---

## **7. REST API**

The REST API provides programmatic access to the framework, enabling integration with external systems. It supports:
1. **Loading Scenarios**: Dynamically load JSON scenarios into the knowledge base.
2. **Querying the Knowledge Base**: Retrieve probabilities and explanations for specific queries.

The API is built using Flask and can be extended to support additional endpoints.

---
