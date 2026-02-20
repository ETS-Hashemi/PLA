class ProbabilisticReasoner:
    def __init__(self):
        self.rules = {}

    def add_rule(self, rule):
        """Add a probabilistic rule to the reasoner."""
        condition, probability = rule.split("=")
        condition = condition.strip()[2:-1]  # Extract condition inside P()
        probability = float(probability.strip())
        self.rules[condition] = probability

    def query(self, query, facts):
        """
        Return the probability of the query if conditions are satisfied.
        :param query: The query symbol.
        :param facts: A set of facts from the knowledge base.
        """
        for condition, probability in self.rules.items():
            # Split the condition into individual symbols
            condition_symbols = [symbol.strip() for symbol in condition.split(",")]
            if query in condition_symbols:
                # Check if all other symbols in the condition are in the facts
                if all(symbol in facts for symbol in condition_symbols if symbol != query):
                    return probability, f"Rule P({condition}) = {probability}"
        return 0.0, f"No rule found for P({query})"

class ProbSymbol:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, ProbSymbol) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name

class ProbRule:
    def __init__(self, condition, result, probability, context=None, context_weight=1.0):
        """
        Initialize a probabilistic rule.
        :param condition: List of ProbSymbols representing the rule's antecedents.
        :param result: ProbSymbol representing the rule's consequent.
        :param probability: Base probability of the rule.
        :param context: Optional dictionary of context variables and their weights.
        :param context_weight: Default weight for the context adjustment.
        """
        self.condition = condition
        self.result = result
        self.probability = probability
        self.context = context or {}
        self.context_weight = context_weight

    def adjusted_probability(self, current_context):
        """
        Adjust the rule's probability based on the current context.
        :param current_context: Dictionary of active context variables.
        :return: Adjusted probability.
        """
        adjusted_prob = self.probability
        for var, weight in self.context.items():
            if var in current_context:
                adjusted_prob *= weight
        return min(adjusted_prob, 1.0)  # Ensure probability does not exceed 1.0

    def __repr__(self):
        conditions = " and ".join([str(c) for c in self.condition])
        return f"If {conditions} -> {self.result} (P={self.probability})"

class ProbKB:
    def __init__(self):
        self.facts = set()
        self.rules = []
        self.cache = {}
        self.current_context = {}  # Store the current context variables

    def add_fact(self, fact):
        if isinstance(fact, str):
            fact = ProbSymbol(fact)
        self.facts.add(fact)

    def add_rule(self, rule):
        self.rules.append(rule)

    def set_context(self, context):
        """
        Set the current context for reasoning.
        :param context: Dictionary of context variables and their values.
        """
        self.current_context = context

    def query(self, query):
        if isinstance(query, str):
            query = ProbSymbol(query)

        # Check cache for previously computed results
        if query in self.cache:
            return self.cache[query]

        # Forward chaining to infer new facts with probabilities
        inferred_facts = {fact: 1.0 for fact in self.facts}  # Facts with certainty
        explanations = []
        while True:
            new_facts = {}
            for rule in self.rules:
                if rule.result not in inferred_facts:
                    # Check if all conditions are satisfied
                    conditions_met = all(c in inferred_facts for c in rule.condition)
                    if conditions_met:
                        # Adjust the probability based on the current context
                        prob = rule.adjusted_probability(self.current_context) * min(
                            inferred_facts[c] for c in rule.condition
                        )
                        new_facts[rule.result] = prob
                        explanations.append(
                            f"{' and '.join(map(str, rule.condition))} triggered {rule.result} with P={prob:.3f} (Context Adjusted)"
                        )
            if not new_facts:
                break
            inferred_facts.update(new_facts)

        # Check if the query is in the inferred facts
        if query in inferred_facts:
            explanation = "\n".join(explanations)
            result = (inferred_facts[query], explanation)
            self.cache[query] = result
            return result

        result = (0.0, "No matching rule found.")
        self.cache[query] = result
        return result

class InferenceEngine:
    def __init__(self, kb):
        self.kb = kb

    def query(self, query):
        return self.kb.query(query)
