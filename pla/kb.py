import itertools
from collections import defaultdict


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
    Propositional entailment by truth-table model checking — O(2^n).

    Kept as the reference oracle for differential tests; the production
    query path is forward_chain_entails below.
    KB |= query iff every model that satisfies KB also satisfies query.
    """
    all_symbols = sorted(symbols(knowledge) | symbols(query), key=lambda s: s.name)

    for values in itertools.product([False, True], repeat=len(all_symbols)):
        model = dict(zip(all_symbols, values))
        if evaluate(knowledge, model) and not evaluate(query, model):
            return False

    return True


def forward_chain_entails(facts, rules, query):
    """
    Entailment of an atomic query by forward chaining (AIMA PL-FC-Entails).

    Sound and complete for definite-clause KBs — the only sentences
    KnowledgeBase accepts — and linear in the KB size, versus O(2^n) for
    truth-table model checking. Membership in the least model decides
    entailment.
    """
    unsatisfied = {}
    heads = {}
    where_antecedent = defaultdict(list)
    for index, rule in enumerate(rules):
        antecedents = set(rule.antecedent.args)
        unsatisfied[index] = len(antecedents)
        heads[index] = rule.consequent
        for antecedent in antecedents:
            where_antecedent[antecedent].append(index)

    inferred = set()
    agenda = list(facts)
    while agenda:
        symbol = agenda.pop()
        if symbol == query:
            return True
        if symbol in inferred:
            continue
        inferred.add(symbol)
        for index in where_antecedent[symbol]:
            unsatisfied[index] -= 1
            if unsatisfied[index] == 0:
                agenda.append(heads[index])
    return False


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
        """Check if the knowledge base entails the query.

        Uses forward chaining, which is sound and complete for the
        definite clauses this KB accepts and scales linearly;
        model_check remains available as the exponential reference oracle.
        """
        return forward_chain_entails(self.facts, self.rules, Symbol(query))
