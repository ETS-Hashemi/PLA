import itertools


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


def symbols(sentence):
    """Collect all propositional symbols appearing in a sentence."""
    if isinstance(sentence, Symbol):
        return {sentence}
    if isinstance(sentence, And):
        result = set()
        for arg in sentence.args:
            result |= symbols(arg)
        return result
    if isinstance(sentence, Implication):
        return symbols(sentence.antecedent) | symbols(sentence.consequent)
    return set()


def evaluate(sentence, model):
    """Evaluate a sentence under a specific boolean model."""
    if isinstance(sentence, Symbol):
        return model[sentence]
    if isinstance(sentence, And):
        return all(evaluate(arg, model) for arg in sentence.args)
    if isinstance(sentence, Implication):
        return (not evaluate(sentence.antecedent, model)) or evaluate(sentence.consequent, model)
    raise ValueError(f"Unsupported sentence type: {type(sentence)}")


def model_check(knowledge, query):
    """
    Propositional entailment by truth-table model checking.
    KB |= query iff every model that satisfies KB also satisfies query.
    """
    all_symbols = sorted(symbols(knowledge) | symbols(query), key=lambda s: s.name)

    for values in itertools.product([False, True], repeat=len(all_symbols)):
        model = dict(zip(all_symbols, values))
        if evaluate(knowledge, model) and not evaluate(query, model):
            return False

    return True


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
