# Probabilistic Logic Agent Framework

## Overview

The **Probabilistic Logic Agent Framework** is a Python-based system that integrates **symbolic reasoning**, **probabilistic reasoning**, and **context-aware adjustments** to model uncertainty in real-world scenarios. It supports **parallel scenario modeling** across diverse domains such as accounting, auditing, pharmaceutical, oncology, and logistics. The framework is designed to handle uncertainty, provide explainable reasoning, and adapt dynamically to external contexts.

This framework is ideal for applications in:
- **Supply Chain Optimization**: Manage disruptions and delays dynamically.
- **Medical Diagnosis**: Infer diagnoses and treatment plans based on clinical indicators.
- **Fraud Detection**: Identify high-risk transactions and recommend audits.
- **Auditing**: Evaluate compliance and flag irregularities.
- **Pharmaceutical Decision-Making**: Model drug recalls and regulatory actions.
- **Oncology Treatment Planning**: Develop comprehensive treatment plans for cancer patients.

---

## Features

### Core Features
- **Hybrid Reasoning**: Combines symbolic logic with probabilistic reasoning for comprehensive decision-making.
- **Context-Aware Reasoning**: Dynamically adjusts rule probabilities using context variables, enabling real-time adaptability.
- **Parallel Scenario Modeling**: Define and manage complex domain-specific scenarios in separate JSON files for modularity and scalability.
- **Explainability**: Provides clear reasoning chains for each query, making the decision-making process transparent.
- **REST API**: Programmatic access to load scenarios and query the knowledge base.
- **Benchmarking**: Measure the performance of reasoning over complex scenarios.

### Advanced Features
- **Scenario Validation**: Automatically checks for unused facts, unreachable rules, and missing queries.
- **Dynamic Context Flattening**: Ensures only the active context is applied during reasoning.
- **Scalability**: Handles complex scenarios with multiple rules, facts, and queries across various domains.
- **Customizable Contexts**: Easily define and modify context variables for domain-specific applications.
- **Caching**: Optimizes performance by caching intermediate results for repeated queries.

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/probabilistic-logic-agent.git
   cd probabilistic-logic-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify the installation:
   ```bash
   python main.py --help
   ```

---

## How to Use the Framework

### 1. Configure Scenarios

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

### 2. Run the Framework

Run the framework with the desired scenario configuration:
```bash
python main.py <scenario_config.json> [context_number]
```
If the context number is omitted, it defaults to "1".

---

## Semantics

The probabilistic layer uses explicit operators:

- **Antecedent conjunction**: `min(p(a1), ..., p(an))`
- **Context adjustment**: `p_rule_adjusted = min(1, p_rule * Π active_context_weights)`
- **Support candidate from one rule**: `candidate = p_rule_adjusted * min_antecedent`
- **Support aggregation (configurable)**:
  - `max`: `max(existing, candidate)`
  - `noisy_or` (default): `1 - (1-existing)(1-candidate)`
  - `sum_cap`: `min(1, existing + candidate)`
  - `logit_pool`: additive in log-odds space

Use `examples/run_readme_scenario.py` as the single source of truth for the README numbers.

---

## Sample Outputs

### Example: Reproducible README Scenario (with multi-support aggregation)
Run:
```bash
python examples/run_readme_scenario.py
```

Output:
```
=== README Scenario (aggregation=noisy_or) ===
Escalation supports:
  - rule_1: If DelayedShipment and HighPriorityOrder -> EscalationRequired (P=0.8): candidate_p=0.504
  - rule_2: If WeatherDisruption and DelayedShipment -> EscalationRequired (P=0.7): candidate_p=0.490
Aggregated EscalationRequired probability: 0.747040
CustomerNotification probability: 0.709688
```

Computation notes:
- `candidate_1 = (0.8 * 0.9 * 0.7) * min(1, 1) = 0.504`
- `candidate_2 = (0.7 * 0.7) * min(1, 1) = 0.490`
- noisy-OR aggregation: `1 - (1-0.504)(1-0.490) = 0.74704`
- `CustomerNotification = 0.95 * 0.74704 = 0.709688`

---

## Advanced Features

### Context-Aware Reasoning

The framework supports **context-aware reasoning**, where rule probabilities are dynamically adjusted based on the current context. For example:

```python
# Set the context
context = {"DriverShortage": True, "WeatherDisruption": True}
kb.set_context(context)
```

Rules can define context variables and their weights. For example:
```json
{
  "condition": ["DelayedShipment", "HighPriorityOrder"],
  "result": "EscalationRequired",
  "probability": 0.8,
  "context": {
    "DriverShortage": 0.9,
    "WeatherDisruption": 0.7
  }
}
```

---

### Using the Hybrid Engine

The hybrid engine gates probabilistic conclusions with symbolic entailment.
Gating is only meaningful when **both layers model the same symbols**; the
runnable version of this example is `examples/run_hybrid_demo.py`.

```python
from engine import HybridEngine
from kb import KnowledgeBase
from prob import ProbKB, ProbSymbol, ProbRule

# Symbolic policy: a large transaction without a receipt requires an audit.
symbolic_kb = KnowledgeBase()
symbolic_kb.add_fact("LargeTransaction")
symbolic_kb.add_fact("NoReceipt")
symbolic_kb.add_rule("LargeTransaction and NoReceipt -> AuditRequired")

# Probabilistic strengths for the SAME symbols, plus one conclusion
# (RegulatorReport) the policy does not entail.
prob_kb = ProbKB()
large, no_receipt = ProbSymbol("LargeTransaction"), ProbSymbol("NoReceipt")
audit, report = ProbSymbol("AuditRequired"), ProbSymbol("RegulatorReport")
prob_kb.add_fact(large)
prob_kb.add_fact(no_receipt)
prob_kb.add_rule(ProbRule([large, no_receipt], audit, 0.85))
prob_kb.add_rule(ProbRule([audit], report, 0.6))

engine = HybridEngine(symbolic_kb, prob_kb, gate_mode="hard")
print(engine.query("AuditRequired")["probability"])    # 0.85  (entailed, passes)
print(engine.query("RegulatorReport")["probability"])  # 0.0   (not entailed, blocked)
```

Gate modes: `hard` blocks non-entailed queries to 0.0; `soft` multiplies them
by `gate_penalty`; `constraint` is intended to zero out *contradicted*
queries, but the symbolic layer has no negation yet, so it currently passes
probabilities through with a warning only (documented no-op).

---

## Benchmarking

The framework includes a benchmarking script to measure the performance of reasoning over complex scenarios. To benchmark a scenario, use the `benchmark.py` script:

```bash
python benchmark.py <scenario_config.json> [context_number]
```

Example:
```bash
python benchmark.py scenario_logistics_very_complex.json
```

The script will output the probabilities for each query and the total execution time.

---

## REST API

The framework provides a REST API for loading scenarios and querying the knowledge base. To start the API server, run:

```bash
python rest_api.py
```

### Endpoints

1. **Load Scenario**
   - **URL**: `/load`
   - **Method**: `POST`
   - **Body**:
     ```json
     {
       "config_path": "scenario_logistics_very_complex.json"
     }
     ```
   - **Response**:
     ```json
     {
       "message": "Scenario loaded successfully"
     }
     ```

2. **Query Knowledge Base**
   - **URL**: `/query`
   - **Method**: `POST`
   - **Body**:
     ```json
     {
       "query": "CustomerNotification"
     }
     ```
   - **Response**:
     ```json
     {
       "query": "CustomerNotification",
       "probability": 0.718,
       "explanation": "DelayedShipment and HighPriorityOrder triggered EscalationRequired with P=0.756..."
     }
     ```

This API allows integration with external systems for real-time reasoning.

---

## Use Cases

### 1. Supply Chain Optimization
- **Scenario**: A delayed shipment with high-priority orders and traffic congestion.
- **Goal**: Determine whether escalation is required and notify customers.
- **Outcome**: The framework dynamically adjusts probabilities based on context variables like driver shortages and weather disruptions.

### 2. Medical Diagnosis
- **Scenario**: A patient with persistent cough, weight loss, and chest pain.
- **Goal**: Infer the likelihood of lung cancer and recommend a biopsy.
- **Outcome**: The framework provides an explainable reasoning chain for medical professionals.

### 3. Fraud Detection
- **Scenario**: A large transaction with no receipt and an unusual vendor.
- **Goal**: Identify fraud risk and recommend an audit.
- **Outcome**: The framework flags high-risk transactions and explains the reasoning.

### 4. Pharmaceutical Decision-Making
- **Scenario**: A new drug with adverse reactions and multiple reports.
- **Goal**: Determine whether a recall is required and notify the public.
- **Outcome**: The framework models recall decisions based on severity and regulatory warnings.

---

## Collaboration

We welcome contributions and discussions to improve the framework. You can review the shared chat below for context and ongoing discussions:

<a href="https://chatgpt.com/share/68044841-8b70-8010-8dc6-6b95e9d1c411" target="_blank">ChatGPT Discussion on Probabilistic Logic Agent Framework</a>

Feel free to provide feedback or contribute to the project by submitting issues or pull requests.

---

## License

Licensed under the **Apache License 2.0**.  
© 2025 Seyed Masoud Hashemi Ahmadi.

---

## Contact

For collaboration or inquiries:  
📧 [contact@AiCentralLab.com](mailto:contact@AiCentralLab.com)

