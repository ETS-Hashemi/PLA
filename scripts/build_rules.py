"""CLI for the feature -> rule pipeline (pla/pipeline.py).

Usage:
    python scripts/build_rules.py --data data/creditcard_synthetic_seed0.csv \
        --scenario data/generated_fraud_scenario.json
"""

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pla.pipeline import run_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="input CSV (E1 real or synthetic)")
    parser.add_argument("--scenario", help="optional path for the exported scenario JSON")
    args = parser.parse_args()

    result = run_pipeline(args.data, args.scenario)
    positives = sum(label for _, _, label in result["examples"])
    print(f"examples:   {len(result['examples'])} ({positives} positive)")
    print(f"rules:      {len(result['rule_specs'])}")
    for spec, precision in zip(result["rule_specs"], result["precisions"]):
        antecedents = " and ".join(spec.antecedents)
        print(f"  - {antecedents} -> Fraud (empirical precision {precision:.3f})")
    if args.scenario:
        print(f"scenario:   {args.scenario}")


if __name__ == "__main__":
    main()
