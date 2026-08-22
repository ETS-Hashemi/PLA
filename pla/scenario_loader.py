"""Scenario loading with explicit, fail-loud context semantics.

Scenario JSON structure:

    {
      "facts": ["Fact1", ...],
      "rules": [
        {"condition": [...], "result": "...", "confidence": 0.8,
         "context": <rule context>},
        ...
      ],
      "queries": ["Fact2", ...],
      "contexts": {"1": ["VarA", "VarB"], ...}        # optional
    }

The rule value key is ``"confidence"`` — PLA values are confidences, not
probabilities (docs/SEMANTICS.md, "What the numbers are not"). The legacy
key ``"probability"`` is accepted as a deprecated alias for backward
compatibility with older scenario files; supplying both keys with
different values is an error.

A rule's "context" takes one of two shapes:

- **flat**: ``{"Var": weight, ...}`` — the weight multiplies the rule's
  probability whenever ``Var`` is active, in every context set.
- **nested** (legacy): ``{"1": {"Var": weight}, "2": {...}}`` — per-set
  weights; selecting set "1" gives this rule the weights of sub-dict "1"
  (and no adjustment from other sets). The same variable may carry
  different weights in different sets.

Which variables are *active* comes from the selected context set:

- If the scenario declares a top-level ``"contexts"`` mapping
  (set name -> list of variable names), those are the available sets.
- Otherwise, if any rule uses the nested shape, the set names are taken
  from the rules and set *n* activates every variable appearing in some
  rule's sub-dict *n*.
- Otherwise, if rules declare flat context variables, a single default
  set "1" activates all of them.

Anything else — mixed shapes inside one rule, non-numeric weights,
unknown variables in "contexts", selecting an undeclared set — raises
``ScenarioFormatError`` instead of silently applying no adjustment.
"""

import json
import numbers

from .prob import ProbSymbol, ProbRule, ProbKB


class ScenarioFormatError(ValueError):
    """Raised when a scenario file's structure is invalid."""


def _is_weight(value):
    return isinstance(value, numbers.Real) and not isinstance(value, bool)


def _classify_rule_context(context, rule_index):
    """Return ("flat"|"nested"|"empty", normalized dict)."""
    if context in (None, {}):
        return "empty", {}
    if not isinstance(context, dict):
        raise ScenarioFormatError(
            f"Rule {rule_index}: 'context' must be an object, got {type(context).__name__}."
        )

    flat = all(_is_weight(v) for v in context.values())
    nested = all(isinstance(v, dict) for v in context.values())
    if flat:
        return "flat", dict(context)
    if nested:
        for set_name, sub in context.items():
            for var, weight in sub.items():
                if not _is_weight(weight):
                    raise ScenarioFormatError(
                        f"Rule {rule_index}: context set {set_name!r} has "
                        f"non-numeric weight for {var!r}: {weight!r}."
                    )
        return "nested", {str(k): dict(v) for k, v in context.items()}
    raise ScenarioFormatError(
        f"Rule {rule_index}: 'context' mixes weights and sub-objects; use either "
        "the flat {var: weight} shape or the nested {set: {var: weight}} shape."
    )


class Scenario:
    def __init__(self, kb, queries, rule_contexts, context_sets):
        self.kb = kb
        self.queries = queries
        self._rule_contexts = rule_contexts  # per rule: (shape, normalized)
        self.context_sets = context_sets  # {set name: [active variable, ...]}
        self.active_set = None
        self.active_variables = []

    def activate(self, set_name="1"):
        """Select a context set: resolve rule weights and active variables."""
        set_name = str(set_name)
        if not self.context_sets:
            if set_name == "1":  # no contexts anywhere: nothing to activate
                self.active_set = None
                self.active_variables = []
                self.kb.set_context({})
                return self
            raise ScenarioFormatError(
                f"Context set {set_name!r} requested but this scenario declares no contexts."
            )
        if set_name not in self.context_sets:
            available = ", ".join(sorted(self.context_sets))
            raise ScenarioFormatError(
                f"Unknown context set {set_name!r}; available sets: {available}."
            )

        for rule, (shape, ctx) in zip(self.kb.rules, self._rule_contexts):
            if shape == "nested":
                rule.context = dict(ctx.get(set_name, {}))
            elif shape == "flat":
                rule.context = dict(ctx)
            else:
                rule.context = {}

        self.active_set = set_name
        self.active_variables = list(self.context_sets[set_name])
        self.kb.set_context({var: True for var in self.active_variables})
        return self


def _build_context_sets(config, rule_contexts):
    declared_flat_vars = set()
    nested_sets = {}
    for shape, ctx in rule_contexts:
        if shape == "flat":
            declared_flat_vars.update(ctx)
        elif shape == "nested":
            for set_name, sub in ctx.items():
                nested_sets.setdefault(set_name, set()).update(sub)

    explicit = config.get("contexts")
    if explicit is not None:
        if not isinstance(explicit, dict):
            raise ScenarioFormatError("'contexts' must map set names to lists of variables.")
        known_vars = declared_flat_vars | {v for s in nested_sets.values() for v in s}
        sets = {}
        for name, variables in explicit.items():
            if not isinstance(variables, list) or not all(isinstance(v, str) for v in variables):
                raise ScenarioFormatError(
                    f"Context set {name!r} must be a list of variable names."
                )
            unknown = [v for v in variables if v not in known_vars]
            if unknown:
                raise ScenarioFormatError(
                    f"Context set {name!r} activates variables no rule declares: {unknown}."
                )
            sets[str(name)] = list(variables)
        return sets

    if nested_sets:
        return {name: sorted(variables) for name, variables in nested_sets.items()}
    if declared_flat_vars:
        return {"1": sorted(declared_flat_vars)}
    return {}


def _rule_confidence(rule, index):
    """The rule's value under the canonical key ``"confidence"``, or the
    deprecated legacy alias ``"probability"``; both present must agree."""
    has_confidence = "confidence" in rule
    has_probability = "probability" in rule
    if has_confidence and has_probability:
        if rule["confidence"] != rule["probability"]:
            raise ScenarioFormatError(
                f"Rule {index}: 'confidence' ({rule['confidence']!r}) and "
                f"legacy 'probability' ({rule['probability']!r}) disagree; "
                "keep only 'confidence'."
            )
        return rule["confidence"]
    if has_confidence:
        return rule["confidence"]
    if has_probability:
        return rule["probability"]
    raise ScenarioFormatError(
        f"Rule {index}: missing 'confidence' (or legacy 'probability')."
    )


def load_scenario(config_path):
    """Load a scenario file into a Scenario (kb, queries, context sets)."""
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Scenario file '{config_path}' not found.")
    except json.JSONDecodeError:
        raise ScenarioFormatError(f"Scenario file '{config_path}' is not valid JSON.")

    context_mode = config.get("context_mode", "legacy")
    if context_mode not in ("legacy", "logit"):
        raise ScenarioFormatError(
            f"'context_mode' must be 'legacy' or 'logit', got {context_mode!r}."
        )

    kb = ProbKB(context_mode=context_mode)
    for fact in config.get("facts", []):
        kb.add_fact(ProbSymbol(fact))

    rule_contexts = []
    for index, rule in enumerate(config.get("rules", [])):
        shape, ctx = _classify_rule_context(rule.get("context"), index)
        condition = [ProbSymbol(c) for c in rule["condition"]]
        result = ProbSymbol(rule["result"])
        kb.add_rule(ProbRule(condition, result, _rule_confidence(rule, index),
                             context={}))
        rule_contexts.append((shape, ctx))

    context_sets = _build_context_sets(config, rule_contexts)
    queries = [ProbSymbol(q) for q in config.get("queries", [])]
    return Scenario(kb, queries, rule_contexts, context_sets)
