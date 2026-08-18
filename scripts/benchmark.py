import time
import sys
from pla.scenario_loader import load_scenario
from pla.prob import InferenceEngine

def benchmark_scenario(config_path, context_set="1"):
    scenario = load_scenario(config_path)
    scenario.activate(context_set)

    engine = InferenceEngine(scenario.kb)

    start_time = time.time()
    for query in scenario.queries:
        prob, explanation = engine.query(query)
        print(f"Query: {query}, Probability: {prob:.3f}")
    end_time = time.time()

    print(f"Benchmark completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/benchmark.py <scenario_config.json> [context_set]")
        sys.exit(1)

    config_path = sys.argv[1]
    context_set = sys.argv[2] if len(sys.argv) >= 3 else "1"
    benchmark_scenario(config_path, context_set)
