class Symbol:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name


class And:
    def __init__(self, *args):
        self.args = args

    def __repr__(self):
        return f"And({', '.join(map(str, self.args))})"


class Implication:
    def __init__(self, antecedent, consequent):
        self.antecedent = antecedent
        self.consequent = consequent

    def __repr__(self):
        return f"({self.antecedent} -> {self.consequent})"


def model_check(knowledge, query):
    """
    Perform a simple model check to verify if the query is entailed by the knowledge base.
    :param knowledge: A list of facts and rules.
    :param query: The query to check.
    :return: True if the query is entailed, False otherwise.
    """
    # Simplified model checking: Check if the query is in the knowledge base
    if isinstance(knowledge, And):
        return query in knowledge.args
    return query == knowledge


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
