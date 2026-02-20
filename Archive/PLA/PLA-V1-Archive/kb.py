from logic import And, Implication, Symbol, model_check

class KnowledgeBase:
    def __init__(self):
        self.facts = set()
        self.rules = []

    def add_fact(self, fact):
        """Add a fact to the knowledge base."""
        self.facts.add(Symbol(fact))

    def add_rule(self, rule):
        """Add a rule to the knowledge base."""
        antecedent, consequent = rule.split("->")
        antecedent = And(*[Symbol(s.strip()) for s in antecedent.split("and")])
        consequent = Symbol(consequent.strip())
        self.rules.append(Implication(antecedent, consequent))

    def query(self, query):
        """Check if the knowledge base entails the query."""
        knowledge = And(*self.facts, *self.rules)
        query_symbol = Symbol(query)
        return model_check(knowledge, query_symbol)
