import time
import sys
from scenario_loader import load_scenario
from prob import InferenceEngine

def benchmark_scenario(config_path, context_number="1"):
    kb, queries = load_scenario(config_path)

    # Set the context number
    context = {}
    for rule in kb.rules:
        if hasattr(rule, "context") and context_number in rule.context:
            context.update(rule.context[context_number])
    kb.set_context(context)

    engine = InferenceEngine(kb)

    start_time = time.time()
    for query in queries:
        prob, explanation = engine.query(query)
        print(f"Query: {query}, Probability: {prob:.3f}")
    end_time = time.time()

    print(f"Benchmark completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <scenario_config.json> [context_number]")
        sys.exit(1)

    config_path = sys.argv[1]
    context_number = sys.argv[2] if len(sys.argv) >= 3 else "1"
    benchmark_scenario(config_path, context_number)
