from prob import InferenceEngine

class HybridEngine:
    def __init__(self, kb, prob_kb):
        self.kb = kb
        self.prob_engine = InferenceEngine(prob_kb)

    def query(self, query):
        """Query both the symbolic and probabilistic systems."""
        # Query the symbolic knowledge base
        symbolic_result = self.kb.query(query)

        # Query the probabilistic reasoner
        prob_result, explanation = self.prob_engine.query(query)

        # Combine results
        if symbolic_result:
            return prob_result, f"Symbolic reasoning supports {query}. {explanation}"
        return 0.0, f"Symbolic reasoning does not support {query}. {explanation}"
