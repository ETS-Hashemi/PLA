import sys
from scenario_loader import load_scenario
from prob import InferenceEngine

def main():
    # Check if scenario file is provided as an argument
    if len(sys.argv) < 2:
        print("Usage: python main.py <scenario_config.json> [context_number]")
        sys.exit(1)

    # Load the scenario from the configuration file
    config_path = sys.argv[1]
    # Default context_number to "1" if not provided
    context_number = sys.argv[2] if len(sys.argv) >= 3 else "1"
    try:
        kb, queries = load_scenario(config_path)
    except FileNotFoundError:
        print(f"Error: The file '{config_path}' was not found. Please check the file name and path.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

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

    # Set the context based on the context number
    context = {}
    try:
        for rule in kb.rules:
            if hasattr(rule, "context") and context_number in rule.context:
                context.update(rule.context[context_number])
    except KeyError:
        print(f"Error: Context number '{context_number}' not found in the scenario.")
        sys.exit(1)

    kb.set_context(context)

    # Flatten rule contexts to use active context directly
    for rule in kb.rules:
        if isinstance(rule.context, dict) and context_number in rule.context:
            rule.context = rule.context[context_number]

    # Display the active context
    print("\n                  ACTIVE CONTEXT")
    print("=" * 60)
    if context:
        for var, weight in context.items():
            print(f"  - {var}: Weight = {weight}")
    else:
        print("  No active context variables.")
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