import sys
from .scenario_loader import load_scenario, ScenarioFormatError
from .prob import InferenceEngine

def main():
    # Check if scenario file is provided as an argument
    if len(sys.argv) < 2:
        print("Usage: pla <scenario_config.json> [context_set]")
        sys.exit(1)

    config_path = sys.argv[1]
    # Default context set to "1" if not provided
    context_set = sys.argv[2] if len(sys.argv) >= 3 else "1"
    try:
        scenario = load_scenario(config_path)
        scenario.activate(context_set)
    except FileNotFoundError:
        print(f"Error: The file '{config_path}' was not found. Please check the file name and path.")
        sys.exit(1)
    except ScenarioFormatError as e:
        print(f"Error: {e}")
        sys.exit(1)

    kb, queries = scenario.kb, scenario.queries

    # Display the knowledge base
    print("=" * 60)
    print("                  KNOWLEDGE BASE")
    print("=" * 60)
    print("\nFacts:")
    for fact in kb.facts:
        print(f"  - {fact}")
    print("\nRules:")
    for rule in kb.rules:
        print(f"  - {rule}")
    print("=" * 60)

    # Display the active context
    print("\n                  ACTIVE CONTEXT")
    print("=" * 60)
    if scenario.active_variables:
        print(f"  Context set: {scenario.active_set}")
        for var in scenario.active_variables:
            print(f"  - {var}")
    else:
        print("  No active context variables.")
    if scenario.context_sets:
        print(f"  Available sets: {', '.join(sorted(scenario.context_sets))}")
    print("=" * 60)

    # Initialize the inference engine
    engine = InferenceEngine(kb)

    # Query the knowledge base
    print("\n                  QUERIES AND RESULTS")
    print("=" * 60)
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        prob, explanation = engine.query(query)
        print(f"  Probability: {prob:.3f}")
        print("  Explanation:")
        for sentence in explanation.split("\n"):
            print(f"    - {sentence.strip()}")
        print("-" * 60)

if __name__ == "__main__":
    main()
