from collections import defaultdict
import math


EPSILON = 1e-9


def aggregate_supports(existing_p, new_p, method="noisy_or"):
    """Aggregate two supports for the same fact."""
    existing_p = max(0.0, min(1.0, existing_p))
    new_p = max(0.0, min(1.0, new_p))

    if method == "max":
        return max(existing_p, new_p)
    if method == "noisy_or":
        return 1.0 - (1.0 - existing_p) * (1.0 - new_p)
    if method == "sum_cap":
        return min(1.0, existing_p + new_p)
    if method == "logit_pool":
        if existing_p <= 0:
            return new_p
        if new_p <= 0:
            return existing_p
        if existing_p >= 1 or new_p >= 1:
            return 1.0

        def _logit(p):
            return math.log(p / (1 - p))

        def _sigmoid(x):
            return 1 / (1 + math.exp(-x))

        return _sigmoid(_logit(existing_p) + _logit(new_p))

    raise ValueError(f"Unsupported aggregation method: {method}")


class ProbabilisticReasoner:
    def __init__(self, aggregation_method="noisy_or"):
        self.rules = {}
        self.aggregation_method = aggregation_method

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
        aggregated_probability = 0.0
        explanations = []

        for condition, probability in self.rules.items():
            condition_symbols = [symbol.strip() for symbol in condition.split(",")]
            if query in condition_symbols:
                if all(symbol in facts for symbol in condition_symbols if symbol != query):
                    aggregated_probability = aggregate_supports(
                        aggregated_probability,
                        probability,
                        self.aggregation_method,
                    )
                    explanations.append(f"Rule P({condition}) = {probability}")

        if explanations:
            return aggregated_probability, " | ".join(explanations)

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
    def __init__(self, aggregation_method="noisy_or"):
        self.facts = set()
        self.rules = []
        self.cache = {}
        self.current_context = {}
        self.aggregation_method = aggregation_method

    def add_fact(self, fact):
        if isinstance(fact, str):
            fact = ProbSymbol(fact)
        self.facts.add(fact)
        self.cache.clear()

    def add_rule(self, rule):
        self.rules.append(rule)
        self.cache.clear()

    def set_context(self, context):
        """
        Set the current context for reasoning.
        :param context: Dictionary of context variables and their values.
        """
        self.current_context = context
        self.cache.clear()

    def _forward_chain(self):
        base_fact_probs = {fact: 1.0 for fact in self.facts}
        fact_probs = dict(base_fact_probs)
        support_map = defaultdict(dict)

        max_iterations = max(1, len(self.rules) * 10)
        for _ in range(max_iterations):
            next_fact_probs = dict(base_fact_probs)

            for idx, rule in enumerate(self.rules):
                conditions_met = all(c in fact_probs for c in rule.condition)
                if not conditions_met:
                    continue

                antecedent_probs = [fact_probs[c] for c in rule.condition]
                adjusted_rule_prob = rule.adjusted_probability(self.current_context)
                candidate_p = adjusted_rule_prob * min(antecedent_probs)

                existing = next_fact_probs.get(rule.result, 0.0)
                next_fact_probs[rule.result] = aggregate_supports(existing, candidate_p, self.aggregation_method)

                support_map[rule.result][f"rule_{idx + 1}"] = {
                    "rule": f"rule_{idx + 1}: {rule}",
                    "candidate_p": candidate_p,
                    "antecedents": [str(c) for c in rule.condition],
                    "context": dict(self.current_context),
                    "adjusted_rule_probability": adjusted_rule_prob,
                }

            all_facts = set(fact_probs) | set(next_fact_probs)
            max_delta = max(abs(next_fact_probs.get(f, 0.0) - fact_probs.get(f, 0.0)) for f in all_facts)
            fact_probs = next_fact_probs

            if max_delta <= EPSILON:
                break

        supports = defaultdict(list)
        for result, per_rule in support_map.items():
            supports[result] = list(per_rule.values())

        return fact_probs, supports

    def query(self, query):
        if isinstance(query, str):
            query = ProbSymbol(query)

        if query in self.cache:
            return self.cache[query]

        fact_probs, supports = self._forward_chain()

        if query in fact_probs:
            explanation_lines = []
            for support in supports.get(query, []):
                explanation_lines.append(
                    f"{support['rule']} candidate={support['candidate_p']:.3f} "
                    f"(antecedents={support['antecedents']}, context={support['context']})"
                )

            if not explanation_lines and query in self.facts:
                explanation_lines.append(f"{query} is a base fact with P=1.0")

            result = (
                fact_probs[query],
                "\n".join(explanation_lines) if explanation_lines else "No matching rule found.",
            )
            self.cache[query] = result
            return result

        result = (0.0, "No matching rule found.")
        self.cache[query] = result
        return result

    def query_detailed(self, query):
        if isinstance(query, str):
            query = ProbSymbol(query)

        fact_probs, supports = self._forward_chain()
        return {
            "query": str(query),
            "probability": fact_probs.get(query, 0.0),
            "supports": supports.get(query, []),
            "all_fact_probabilities": {str(k): v for k, v in fact_probs.items()},
            "aggregation_method": self.aggregation_method,
        }


class InferenceEngine:
    def __init__(self, kb):
        self.kb = kb

    def query(self, query):
        return self.kb.query(query)
