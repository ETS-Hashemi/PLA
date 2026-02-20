import sys
from scenario_loader import load_scenario
from prob import InferenceEngine

def main():
    # Check if scenario file is provided as an argument
    if len(sys.argv) != 2:
        print("Usage: python main.py <scenario_config.json>")
        sys.exit(1)

    # Load the scenario from the configuration file
    config_path = sys.argv[1]
    kb, queries = load_scenario(config_path)

    # Display the knowledge base
    print("=" * 50)
    print("                KNOWLEDGE BASE")
    print("=" * 50)
    print("Facts:")
    for fact in kb.facts:
        print(f"  • {fact}")
    print("\nRules:")
    for rule in kb.rules:
        print(f"  • {rule}")
    print("=" * 50)

    # Initialize the inference engine
    engine = InferenceEngine(kb)

    # Query the knowledge base
    print("\n                QUERIES AND RESULTS")
    print("=" * 50)
    for query in queries:
        print(f"Query: {query}")
        prob, explanation = engine.query(query)
        print(f"  Probability: {prob:.3f}")  # Limit to 3 decimal places
        print("  Explanation:")
        # Ensure consistent indentation for each step
        for sentence in explanation.split("\n"):  # Split by newlines
            print(f"    - {sentence.strip()}")
        print("-" * 50)

if __name__ == "__main__":
    main()