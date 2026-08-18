"""Hybrid gating demo where both layers model the SAME symbols.

The symbolic KB holds crisp policy ("a large transaction without a receipt
requires an audit"); the probabilistic KB holds uncertain strengths for the
same propositions plus one conclusion (RegulatorReport) that the policy does
NOT entail. That makes the gate observable:

- hard:       non-entailed conclusions are blocked to 0.0
- soft:       non-entailed conclusions are multiplied by a penalty
- constraint: probabilities pass through with a warning only — with no
              negation in the symbolic layer there is nothing to contradict,
              so this mode cannot block anything yet (documented limitation)
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "PLA-advanced"))

from engine import HybridEngine
from kb import KnowledgeBase
from prob import ProbKB, ProbRule, ProbSymbol


def build_kbs():
    symbolic = KnowledgeBase()
    symbolic.add_fact("LargeTransaction")
    symbolic.add_fact("NoReceipt")
    symbolic.add_rule("LargeTransaction and NoReceipt -> AuditRequired")

    prob = ProbKB()
    large = ProbSymbol("LargeTransaction")
    no_receipt = ProbSymbol("NoReceipt")
    audit = ProbSymbol("AuditRequired")
    report = ProbSymbol("RegulatorReport")
    prob.add_fact(large)
    prob.add_fact(no_receipt)
    prob.add_rule(ProbRule([large, no_receipt], audit, 0.85))
    prob.add_rule(ProbRule([audit], report, 0.6))
    return symbolic, prob


def main():
    symbolic, prob = build_kbs()
    print("=== Hybrid gating demo (shared symbols) ===")
    for mode in ("hard", "soft", "constraint"):
        engine = HybridEngine(symbolic, prob, gate_mode=mode, gate_penalty=0.5)
        print(f"\n-- gate_mode={mode} --")
        for query in ("AuditRequired", "RegulatorReport"):
            result = engine.query(query)
            print(
                f"{query}: entailed={result['symbolic_entails']} "
                f"probability={result['probability']:.3f} "
                f"(raw={result['raw_probabilistic']:.3f}, warning={result['warning']})"
            )


if __name__ == "__main__":
    main()
