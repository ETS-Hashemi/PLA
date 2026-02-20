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
        self.assertIn("Rule:", explanation)

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

if __name__ == "__main__":
    unittest.main()