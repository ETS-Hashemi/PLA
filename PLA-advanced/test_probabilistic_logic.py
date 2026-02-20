import unittest
from prob import ProbSymbol, ProbRule, ProbKB, InferenceEngine
from engine import HybridEngine
from kb import KnowledgeBase

class TestProbabilisticLogic(unittest.TestCase):

    def test_probabilistic_reasoning(self):
        # Define symbols
        large = ProbSymbol("LargeTransaction")
        no_receipt = ProbSymbol("NoReceipt")
        fraud = ProbSymbol("Fraud")

        # Define a probabilistic rule
        rule1 = ProbRule(
            condition=[large, no_receipt],
            result=fraud,
            probability=0.85
        )

        # Set up the knowledge base
        prob_kb = ProbKB()
        prob_kb.add_fact(large)
        prob_kb.add_fact(no_receipt)
        prob_kb.add_rule(rule1)

        # Query the KB
        engine = InferenceEngine(prob_kb)
        prob, explanation = engine.query(fraud)

        self.assertAlmostEqual(prob, 0.85)
        self.assertIn("triggered", explanation)

    def test_symbolic_reasoning(self):
        # Initialize symbolic knowledge base
        kb = KnowledgeBase()
        kb.add_rule("A and B -> C")
        kb.add_fact("A")
        kb.add_fact("B")

        # Query the symbolic system
        result = kb.query("C")
        self.assertTrue(result)

    def test_hybrid_reasoning(self):
        # Initialize symbolic knowledge base
        kb = KnowledgeBase()
        kb.add_rule("A and B -> C")
        kb.add_fact("A")
        kb.add_fact("B")

        # Initialize probabilistic knowledge base
        prob_kb = ProbKB()
        large = ProbSymbol("LargeTransaction")
        no_receipt = ProbSymbol("NoReceipt")
        fraud = ProbSymbol("Fraud")

        rule1 = ProbRule(
            condition=[large, no_receipt],
            result=fraud,
            probability=0.85
        )

        prob_kb.add_fact(large)
        prob_kb.add_fact(no_receipt)
        prob_kb.add_rule(rule1)

        # Initialize hybrid engine
        hybrid_engine = HybridEngine(kb, prob_kb)

        # Query the hybrid system
        result, explanation = hybrid_engine.query("C")
        self.assertIn("Symbolic reasoning supports C", explanation)

    def test_context_aware_reasoning(self):
        # Define symbols
        cough = ProbSymbol("PersistentCough")
        weight_loss = ProbSymbol("WeightLoss")
        lung_cancer = ProbSymbol("LungCancerRisk")

        # Define a probabilistic rule with context
        rule = ProbRule(
            condition=[cough, weight_loss],
            result=lung_cancer,
            probability=0.7,
            context={"PatientAge>60": 1.2, "SmokingHistory": 1.5}
        )

        # Set up the knowledge base
        prob_kb = ProbKB()
        prob_kb.add_fact(cough)
        prob_kb.add_fact(weight_loss)
        prob_kb.add_rule(rule)

        # Set the context
        prob_kb.set_context({"PatientAge>60": True, "SmokingHistory": True})

        # Query the KB
        engine = InferenceEngine(prob_kb)
        prob, explanation = engine.query(lung_cancer)

        # Assert the adjusted probability
        self.assertAlmostEqual(prob, 1.0)  # Adjusted probability should be capped at 1.0
        self.assertIn("Context Adjusted", explanation)

if __name__ == "__main__":
    unittest.main()