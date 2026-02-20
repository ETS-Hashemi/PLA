import time
from scenario_loader import load_scenario
from prob import InferenceEngine

def benchmark_scenario(config_path):
    kb, queries = load_scenario(config_path)
    engine = InferenceEngine(kb)

    start_time = time.time()
    for query in queries:
        prob, explanation = engine.query(query)
        print(f"Query: {query}, Probability: {prob:.3f}")
    end_time = time.time()

    print(f"Benchmark completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    # Example: Benchmark the pharmaceutical complex scenario
    benchmark_scenario("scenario_pharmaceutical_complex.json")
