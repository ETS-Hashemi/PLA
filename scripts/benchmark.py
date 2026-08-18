"""Benchmark scenarios and generate the paper's results table.

Usage:
    python scripts/benchmark.py <scenario.json> [context_set]   # timing run
    python scripts/benchmark.py --paper-table                   # deterministic
                                                                # Markdown table

The --paper-table output is the scenario-suite benchmark table (34
scenarios; deterministic quantities only — scenario sizes and query
probabilities — so any document embedding it can be byte-for-byte
verified against this script). Wall-clock timings are
machine-dependent and are printed by the timing mode instead of being
embedded anywhere.
"""

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pla.prob import InferenceEngine  # noqa: E402
from pla.scenario_loader import load_scenario  # noqa: E402

PAPER_SCENARIOS = [
    "scenario_accounting_very_complex.json",
    "scenario_auditing_complex.json",
    "scenario_pharmaceutical_very_complex.json",
    "scenario_oncology_complex.json",
    "scenario_logistics_very_complex.json",
]


def paper_table():
    lines = [
        "| Scenario | Facts | Rules | Query | Probability |",
        "|---|---|---|---|---|",
    ]
    for name in PAPER_SCENARIOS:
        scenario = load_scenario(ROOT / "scenarios" / name)
        scenario.activate("1")
        label = name.removeprefix("scenario_").removesuffix(".json")
        for query in scenario.queries:
            prob, _ = scenario.kb.query(query)
            lines.append(
                f"| {label} | {len(scenario.kb.facts)} | "
                f"{len(scenario.kb.rules)} | {query} | {prob:.6f} |"
            )
    print("\n".join(lines))


def benchmark_scenario(config_path, context_set="1"):
    scenario = load_scenario(config_path)
    scenario.activate(context_set)

    engine = InferenceEngine(scenario.kb)

    start_time = time.time()
    for query in scenario.queries:
        prob, explanation = engine.query(query)
        print(f"Query: {query}, Probability: {prob:.3f}")
    end_time = time.time()

    print(f"Benchmark completed in {end_time - start_time:.4f} seconds.")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--paper-table":
        paper_table()
    elif len(sys.argv) >= 2:
        context_set = sys.argv[2] if len(sys.argv) >= 3 else "1"
        benchmark_scenario(sys.argv[1], context_set)
    else:
        print("Usage: python scripts/benchmark.py <scenario.json> [context_set]")
        print("       python scripts/benchmark.py --paper-table")
        sys.exit(1)
