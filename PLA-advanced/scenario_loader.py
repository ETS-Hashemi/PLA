import json
from prob import ProbSymbol, ProbRule, ProbKB

def load_scenario(config_path):
    """Load a scenario from a JSON configuration file."""
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Scenario file '{config_path}' not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Scenario file '{config_path}' is not a valid JSON file.")

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
        context = rule.get("context", {})
        kb.add_rule(ProbRule(condition, result, probability, context))

    return kb, [ProbSymbol(query) for query in config["queries"]]