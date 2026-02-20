class Symbol:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


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
        return f"Implication({self.antecedent}, {self.consequent})"


def model_check(knowledge, query):
    """A simple model-checking function."""
    def evaluate(expression, model):
        if isinstance(expression, Symbol):
            return model.get(expression, False)
        elif isinstance(expression, And):
            return all(evaluate(arg, model) for arg in expression.args)
        elif isinstance(expression, Implication):
            return not evaluate(expression.antecedent, model) or evaluate(expression.consequent, model)
        return False

    symbols = set()

    def extract_symbols(expression):
        if isinstance(expression, Symbol):
            symbols.add(expression)
        elif isinstance(expression, And):
            for arg in expression.args:
                extract_symbols(arg)
        elif isinstance(expression, Implication):
            extract_symbols(expression.antecedent)
            extract_symbols(expression.consequent)

    extract_symbols(knowledge)
    extract_symbols(query)


    for values in product([False, True], repeat=len(symbols)):
        model = dict(zip(symbols, values))
        if evaluate(knowledge, model) and not evaluate(query, model):
            return False
    return True

from itertools import product

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
