from .prob import InferenceEngine


class HybridEngine:
    """Combine a symbolic entailment layer with a probabilistic layer.

    Gating is only meaningful when both layers model the same symbols —
    a query the probabilistic KB knows nothing about scores 0.0 regardless
    of the gate (see examples/run_hybrid_demo.py for a coherent setup).

    Gate modes:

    - "hard": a query not entailed by the symbolic KB is forced to 0.0.
    - "soft": a non-entailed query's probability is multiplied by
      ``gate_penalty``.
    - "constraint": intended to zero out queries the symbolic KB
      *contradicts*. The current symbolic layer has no negation, so nothing
      can be contradicted: this mode passes probabilities through unchanged
      and only attaches a warning. It is a documented no-op until the
      symbolic layer supports negation.
    """

    def __init__(self, kb, prob_kb, gate_mode="hard", gate_penalty=0.5):
        self.kb = kb
        self.prob_engine = InferenceEngine(prob_kb)
        self.gate_mode = gate_mode
        self.gate_penalty = gate_penalty

    def query(self, query):
        """Query both symbolic and probabilistic systems with configurable gating."""
        symbolic_entails = self.kb.query(query)
        prob_result, explanation = self.prob_engine.query(query)

        final_probability = prob_result
        warning = None

        if self.gate_mode == "hard":
            if not symbolic_entails:
                final_probability = 0.0
                warning = "hard_gate_blocked"
        elif self.gate_mode == "soft":
            if not symbolic_entails:
                final_probability = prob_result * self.gate_penalty
                warning = "soft_gate_penalty_applied"
        elif self.gate_mode == "constraint":
            # Current symbolic layer supports entailment but not contradiction checks.
            if not symbolic_entails:
                warning = "constraint_mode_no_symbolic_support"
        else:
            raise ValueError(f"Unsupported gate mode: {self.gate_mode}")

        return {
            "query": query,
            "symbolic_entails": symbolic_entails,
            "probability": final_probability,
            "raw_probabilistic": prob_result,
            "gate_mode": self.gate_mode,
            "warning": warning,
            "explanation": explanation,
        }
