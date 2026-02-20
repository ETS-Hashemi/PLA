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

## Sample Outputs

### Example: Logistics Very Complex Context-Aware Scenario
Input: `scenario_logistics_very_complex.json` with **Context 1**
```
==================================================
                KNOWLEDGE BASE
==================================================
Facts:
  • DelayedShipment
  • HighPriorityOrder
  • WeatherDisruption
  • WarehouseIssue
  • DriverShortage
  • TrafficCongestion

Rules:
  • If DelayedShipment and HighPriorityOrder -> EscalationRequired (P=0.8)
  • If WeatherDisruption and DelayedShipment -> EscalationRequired (P=0.7)
  • If WarehouseIssue -> DelayedShipment (P=0.6)
  • If DriverShortage and TrafficCongestion -> DelayedShipment (P=0.9)
  • If EscalationRequired -> CustomerNotification (P=0.95)
==================================================

                ACTIVE CONTEXT
==================================================
  • DriverShortage: Weight = 0.9
  • WeatherDisruption: Weight = 0.7
==================================================

                QUERIES AND RESULTS
==================================================
Query: EscalationRequired
--------------------------------------------------
  Probability: 0.756
  Explanation:
    - DelayedShipment and HighPriorityOrder triggered EscalationRequired with P=0.756 (Context Adjusted)
--------------------------------------------------

Query: CustomerNotification
--------------------------------------------------
  Probability: 0.718
  Explanation:
    - DelayedShipment and HighPriorityOrder triggered EscalationRequired with P=0.756 (Context Adjusted)
    - EscalationRequired triggered CustomerNotification with P=0.718 (Context Adjusted)
--------------------------------------------------
```

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

