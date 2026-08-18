"""PLA — a transparent probabilistic-logic agent.

Rule confidences with configurable support aggregation, context-conditioned
weights, symbolic entailment gating, and explanation traces.
"""

from .engine import HybridEngine
from .kb import KnowledgeBase, forward_chain_entails, model_check
from .prob import InferenceEngine, ProbKB, ProbRule, ProbSymbol, aggregate_supports
from .scenario_loader import Scenario, ScenarioFormatError, load_scenario

__version__ = "0.1.0"

__all__ = [
    "HybridEngine",
    "InferenceEngine",
    "KnowledgeBase",
    "ProbKB",
    "ProbRule",
    "ProbSymbol",
    "Scenario",
    "ScenarioFormatError",
    "aggregate_supports",
    "load_scenario",
    "forward_chain_entails",
    "model_check",
    "__version__",
]
