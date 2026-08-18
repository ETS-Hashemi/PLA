"""Reproduce the README logistics scenario and print support aggregation details."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pla.prob import ProbKB, ProbRule, ProbSymbol


def main():
    delayed = ProbSymbol("DelayedShipment")
    high_priority = ProbSymbol("HighPriorityOrder")
    weather = ProbSymbol("WeatherDisruption")
    escalation = ProbSymbol("EscalationRequired")
    customer_notification = ProbSymbol("CustomerNotification")

    kb = ProbKB(aggregation_method="noisy_or")

    kb.add_fact(delayed)
    kb.add_fact(high_priority)
    kb.add_fact(weather)

    kb.set_context({"DriverShortage": True, "WeatherDisruption": True})

    rule_1 = ProbRule(
        condition=[delayed, high_priority],
        result=escalation,
        probability=0.8,
        context={"DriverShortage": 0.9, "WeatherDisruption": 0.7},
    )
    rule_2 = ProbRule(
        condition=[weather, delayed],
        result=escalation,
        probability=0.7,
        context={"WeatherDisruption": 0.7},
    )
    rule_3 = ProbRule(
        condition=[escalation],
        result=customer_notification,
        probability=0.95,
    )

    kb.add_rule(rule_1)
    kb.add_rule(rule_2)
    kb.add_rule(rule_3)

    escalation_detail = kb.query_detailed(escalation)
    notification_detail = kb.query_detailed(customer_notification)

    print("=== README Scenario (aggregation=noisy_or) ===")
    print("Escalation supports:")
    for support in escalation_detail["supports"]:
        print(f"  - {support['rule']}: candidate_p={support['candidate_p']:.3f}")

    print(f"Aggregated EscalationRequired probability: {escalation_detail['probability']:.6f}")
    print(f"CustomerNotification probability: {notification_detail['probability']:.6f}")

    print("\nExplanation trace for CustomerNotification:")
    prob, explanation = kb.query(customer_notification)
    print(f"  Probability: {prob:.6f}")
    print(explanation)


if __name__ == "__main__":
    main()
