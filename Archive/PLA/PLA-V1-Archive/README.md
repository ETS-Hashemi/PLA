# Probabilistic Logic Agent Framework

## Overview

The **Probabilistic Logic Agent Framework** is a Python-based system that integrates **symbolic propositional logic** with **probabilistic reasoning**. It enables reasoning in **uncertain environments** using **weighted logical rules** to infer probabilistic outcomes. Designed for **explainability** and **modularity**, this framework is ideal for domains like auditing, legal reasoning, medical AI, and decision support systems.

---

## Features

- **Hybrid Reasoning**: Combines symbolic logic with probabilistic reasoning.
- **Explainability**: Provides detailed reasoning chains for every query.
- **Modular Design**: Easily extendable for different domains.
- **Lightweight**: No heavy dependencies, works with pure Python.
- **JSON Configurations**: Define facts, rules, and queries in simple JSON files.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/probabilistic-logic-agent.git
   cd probabilistic-logic-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Use the Framework

### 1. Modify the JSON Configuration File

The framework uses JSON files to define the knowledge base (facts and rules) and queries. Here's an example configuration file:

```json
{
  "facts": [
    "AdverseReaction",
    "NewDrug"
  ],
  "rules": [
    {
      "condition": ["AdverseReaction", "NewDrug"],
      "result": "RecallRequired",
      "probability": 0.7
    },
    {
      "condition": ["RecallRequired"],
      "result": "PublicNotification",
      "probability": 0.95
    }
  ],
  "queries": [
    "PublicNotification"
  ]
}
```

#### Explanation:
- **Facts**: A list of known facts (e.g., `"AdverseReaction"`, `"NewDrug"`).
- **Rules**: A list of probabilistic rules. Each rule has:
  - `condition`: A list of facts that must be true for the rule to apply.
  - `result`: The fact inferred if the rule applies.
  - `probability`: The probability of the result being true if the condition is satisfied.
- **Queries**: A list of facts to query the knowledge base for.

### 2. Run the Framework

Use the `main.py` script to load a JSON configuration file and query the knowledge base.

```bash
python main.py <path_to_json_config>
```

For example:
```bash
python main.py scenario_pharmaceutical_complex.json
```

### 3. Sample Output

Here’s an example output for the `scenario_pharmaceutical_complex.json` file:

```
==================================================
                KNOWLEDGE BASE
==================================================
Facts:
  • AdverseReaction
  • NewDrug
  • MultipleReports
  • RegulatoryWarning

Rules:
  • If AdverseReaction and NewDrug -> RecallRequired (0.7)
  • If MultipleReports and RegulatoryWarning -> RecallRequired (0.9)
  • If RecallRequired -> PublicNotification (0.95)
==================================================

                QUERIES AND RESULTS
==================================================
Query: PublicNotification
  Probability: 0.855
  Explanation:
    - AdverseReaction and NewDrug triggered RecallRequired with P=0.7.
    - MultipleReports and RegulatoryWarning reinforced RecallRequired with P=0.9.
    - RecallRequired led to PublicNotification with P=0.855.
--------------------------------------------------
```

---

## How to Modify the JSON Configuration File

1. **Add Facts**:
   - Add new facts to the `"facts"` list.
   - Example:
     ```json
     "facts": ["HighRiskClient", "LateSubmission"]
     ```

2. **Add Rules**:
   - Add new rules to the `"rules"` list.
   - Example:
     ```json
     {
       "condition": ["HighRiskClient", "LateSubmission"],
       "result": "AuditFlag",
       "probability": 0.8
     }
     ```

3. **Add Queries**:
   - Add new queries to the `"queries"` list.
   - Example:
     ```json
     "queries": ["AuditFlag"]
     ```

---

## Example Scenarios

### Scenario 1: Pharmaceutical Recall

**JSON Configuration**:
```json
{
  "facts": ["AdverseReaction", "NewDrug"],
  "rules": [
    {
      "condition": ["AdverseReaction", "NewDrug"],
      "result": "RecallRequired",
      "probability": 0.7
    },
    {
      "condition": ["RecallRequired"],
      "result": "PublicNotification",
      "probability": 0.95
    }
  ],
  "queries": ["PublicNotification"]
}
```

**Command**:
```bash
python main.py scenario_pharmaceutical_simple.json
```

**Output**:
```
==================================================
                KNOWLEDGE BASE
==================================================
Facts:
  • AdverseReaction
  • NewDrug

Rules:
  • If AdverseReaction and NewDrug -> RecallRequired (0.7)
  • If RecallRequired -> PublicNotification (0.95)
==================================================

                QUERIES AND RESULTS
==================================================
Query: PublicNotification
  Probability: 0.665
  Explanation:
    - AdverseReaction and NewDrug triggered RecallRequired with P=0.7.
    - RecallRequired led to PublicNotification with P=0.665.
--------------------------------------------------
```

---

## Advanced Usage

### Using the Hybrid Engine

The framework supports hybrid reasoning by combining symbolic and probabilistic reasoning. For example:

```python
from engine import HybridEngine
from kb import KnowledgeBase
from prob import ProbKB, ProbSymbol, ProbRule

# Symbolic KB
symbolic_kb = KnowledgeBase()
symbolic_kb.add_fact("A")
symbolic_kb.add_fact("B")
symbolic_kb.add_rule("A and B -> C")

# Probabilistic KB
prob_kb = ProbKB()
large = ProbSymbol("LargeTransaction")
no_receipt = ProbSymbol("NoReceipt")
fraud = ProbSymbol("Fraud")
rule = ProbRule([large, no_receipt], fraud, 0.85)
prob_kb.add_fact(large)
prob_kb.add_fact(no_receipt)
prob_kb.add_rule(rule)

# Hybrid Engine
hybrid_engine = HybridEngine(symbolic_kb, prob_kb)
result, explanation = hybrid_engine.query("C")
print(f"Result: {result}")
print(f"Explanation: {explanation}")
```

---

## Applications

- **Auditing & Accounting**: Detect fraud based on transaction patterns.
- **Medical Diagnosis**: Infer diagnoses from symptoms with known probabilities.
- **Legal Reasoning**: Evaluate liability or guilt from structured case facts.
- **Educational AI**: Infer student understanding from indirect indicators.

---

## Roadmap

### Phase 1: Core Framework
- [x] Implement `ProbSymbol`, `ProbRule`, `ProbKB`.
- [x] Build inference engine with model checking.
- [x] Add traceable explanations.

### Phase 2: Modular Extensions
- [ ] Add forward chaining and probabilistic facts.
- [ ] Integrate `pgmpy` or `pomegranate` for advanced inference.
- [ ] Optimize performance for large rule sets.

### Phase 3: Evaluation
- [ ] Benchmark in domains like auditing, medical, and legal reasoning.
- [ ] Collect feedback on transparency and usability.

### Phase 4: Publication
- [ ] Write research paper for venues like IJCAI or RuleML.
- [ ] Prepare polished GitHub repo and Colab demo.

---

## License

Licensed under the **Apache License 2.0**.  
© 2025 Seyed Masoud Hashemi Ahmadi.

---

## Contact

For collaboration or inquiries:  
📧 [contact@AiCentralLab.com](mailto:contact@AiCentralLab.com)

