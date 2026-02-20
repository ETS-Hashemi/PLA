import json
from prob import ProbSymbol, ProbRule, ProbKB

def load_scenario(config_path):
    """Load a scenario from a JSON configuration file."""
    with open(config_path, "r") as file:
        config = json.load(file)

    # Initialize the knowledge base
    kb = ProbKB()

    # Add facts
    for fact in config["facts"]:
        kb.add_fact(ProbSymbol(fact))

    # Add rules
    for rule in config["rules"]:
        condition = [ProbSymbol(c) for c in rule["condition"]]
        result = ProbSymbol(rule["result"])
        probability = rule["probability"]
        kb.add_rule(ProbRule(condition, result, probability))

    return kb, [ProbSymbol(query) for query in config["queries"]]