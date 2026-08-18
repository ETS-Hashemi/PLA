# PLA Semantics

This document defines exactly what PLA's numbers mean, where the calculus
comes from, and what it does **not** claim. Every formula is stated next to
an executable block; `tests/test_semantics_doc.py` extracts and runs every
`python` block in this file, so the document cannot drift from the engine.

## 1. Values

Each proposition `x` carries a **confidence** `c(x) ∈ [0, 1]`. Base facts
have `c = 1`. Confidences are *not* probabilities of a distribution over
possible worlds (see §5); they are evidence-ordered degrees of support in
the certainty-factor tradition (§6).

## 2. Rules

A rule is `(A₁ ∧ … ∧ Aₙ → B, p, w)` with base confidence `p ∈ [0,1]` and
context weights `w : Var → ℝ`.

## 3. Operators

### 3.1 Conjunction and single-rule support

Antecedents combine with the **Gödel t-norm** (minimum), and a rule's
support for its head is the adjusted rule confidence times that minimum:

    min_antecedent = min(c(A₁), …, c(Aₙ))          (F1)
    candidate      = p_adjusted × min_antecedent   (F2)

```python
import math
from pla.prob import ProbKB, ProbRule, ProbSymbol

a, b, c, x = (ProbSymbol(s) for s in "ABCX")
kb = ProbKB()
kb.add_fact(a); kb.add_fact(b)
kb.add_rule(ProbRule([a], x, 0.6))        # c(X) = 0.6
kb.add_rule(ProbRule([x, b], c, 0.5))     # c(C) = 0.5 * min(0.6, 1.0)
assert math.isclose(kb.query(c)[0], 0.5 * min(0.6, 1.0), abs_tol=1e-9)
```

### 3.2 Context adjustment — `legacy` mode (default)

Active context variables multiply the rule confidence; the product is
capped at 1:

    p_adjusted = min(1, p × Π { w(v) : v active })   (F3)

The cap destroys information: distinct strong-evidence combinations can
saturate to the same 1.0.

```python
import math
from pla.prob import ProbRule, ProbSymbol

rule = ProbRule([ProbSymbol("A")], ProbSymbol("B"), 0.7,
                context={"V": 1.2, "W": 1.5})
assert math.isclose(rule.adjusted_probability({"V": True}), 0.7 * 1.2, abs_tol=1e-12)
assert rule.adjusted_probability({"V": True, "W": True}) == 1.0  # 1.26 capped
```

### 3.3 Context adjustment — `logit` mode

Active weights are **additive log-odds deltas** (negative allowed), which
never saturates below 1 and treats strengthening/weakening symmetrically —
the same evidence-combination scheme as naive Bayes / logistic regression:

    p_adjusted = σ( logit(p) + Σ { w(v) : v active } )   (F4)
    where logit(p) = ln(p / (1−p)),  σ(t) = 1 / (1+e^(−t))

```python
import math
from pla.prob import ProbRule, ProbSymbol

rule = ProbRule([ProbSymbol("A")], ProbSymbol("B"), 0.7, context={"V": 1.0, "W": 2.0})
expected = 1 / (1 + math.exp(-(math.log(0.7 / 0.3) + 1.0 + 2.0)))
got = rule.adjusted_probability({"V": True, "W": True}, mode="logit")
assert math.isclose(got, expected, abs_tol=1e-12)
```

### 3.4 Support aggregation

When several rules support the same head, their candidates aggregate with
one of four operators (per-KB choice, default `noisy_or`):

    max        : max(e, n)                    (F5a)
    noisy_or   : 1 − (1−e)(1−n)               (F5b)
    sum_cap    : min(1, e + n)                (F5c)
    logit_pool : σ(logit(e) + logit(n))       (F5d)

```python
import math
from pla.prob import aggregate_supports

e, n = 0.504, 0.490
assert aggregate_supports(e, n, "max") == 0.504
assert math.isclose(aggregate_supports(e, n, "noisy_or"), 1 - (1 - e) * (1 - n), abs_tol=1e-12)
assert math.isclose(aggregate_supports(e, n, "sum_cap"), min(1.0, e + n), abs_tol=1e-12)
logit = lambda p: math.log(p / (1 - p))
sigmoid = lambda t: 1 / (1 + math.exp(-t))
assert math.isclose(aggregate_supports(e, n, "logit_pool"), sigmoid(logit(e) + logit(n)), abs_tol=1e-12)
```

## 4. Inference

Forward chaining runs Jacobi-style: each round recomputes every derived
confidence from the base facts and the previous round's values, and stops
when no confidence changes by more than 1e-9.

### Convergence (proof sketch)

Let `V` be the propositions and order confidence vectors `x ∈ [0,1]^V`
pointwise. One round is `x ↦ G(x)`: start from the base-fact vector, fire
every rule with candidates computed from `x` (F1–F4), and fold candidates
into the head with the aggregator (F5). Every aggregator is monotone in
both arguments and the candidate map is monotone in `x`, so `G` is a
monotone map on the complete lattice `[0,1]^V`. The start vector satisfies
`x₀ ≤ G(x₀)` (base facts are fixed points of every aggregator at 1; derived
coordinates only gain support), so by induction the trajectory
`x₀ ≤ G(x₀) ≤ G²(x₀) ≤ …` is pointwise non-decreasing and bounded by 1.
Each coordinate therefore converges (monotone convergence), the round-max
delta tends to 0, and the ε-stop always triggers; by Kleene's fixpoint
theorem the limit is the least fixpoint of `G` above `x₀`, since all four
aggregators are continuous. The engine caps the rounds at
`max(1000, 10·|rules|)` purely as a safety net — high-probability cycles
with weak seeds converge at a geometric rate close to 1, which the old
`10·|rules|` cap could exhaust.

These properties — monotone trajectory, boundedness, ε-fixpoint reached,
and engine/reference agreement — are machine-checked on 1050 random rule
systems (cycles included, all three bounded aggregators) in
`tests/test_convergence_properties.py`.

End-to-end on the README scenario:

```python
import math
from pla.prob import ProbKB, ProbRule, ProbSymbol

d, h, w = ProbSymbol("Delayed"), ProbSymbol("HighPriority"), ProbSymbol("Weather")
esc, note = ProbSymbol("Escalation"), ProbSymbol("Notify")
kb = ProbKB(aggregation_method="noisy_or")
for f in (d, h, w):
    kb.add_fact(f)
kb.set_context({"DriverShortage": True, "WeatherDisruption": True})
kb.add_rule(ProbRule([d, h], esc, 0.8, context={"DriverShortage": 0.9, "WeatherDisruption": 0.7}))
kb.add_rule(ProbRule([w, d], esc, 0.7, context={"WeatherDisruption": 0.7}))
kb.add_rule(ProbRule([esc], note, 0.95))
assert math.isclose(kb.query(esc)[0], 1 - (1 - 0.504) * (1 - 0.49), abs_tol=1e-9)   # 0.74704
assert math.isclose(kb.query(note)[0], 0.95 * 0.74704, abs_tol=1e-9)                # 0.709688
```

## 5. What the numbers are **not**

PLA has **no distribution semantics**: there is no measure over possible
worlds, and aggregation *chooses* an independence stance rather than
deriving one. Example: two rules driven by the *same* antecedent are
combined by noisy-OR as if their supports were independent —

```python
import math
from pla.prob import ProbKB, ProbRule, ProbSymbol

a, b = ProbSymbol("A"), ProbSymbol("B")
kb = ProbKB(aggregation_method="noisy_or")
kb.add_fact(a)
kb.add_rule(ProbRule([a], b, 0.5))
kb.add_rule(ProbRule([a], b, 0.5))
assert math.isclose(kb.query(b)[0], 0.75, abs_tol=1e-9)  # 1-(1-.5)(1-.5)
```

— whereas a possible-world semantics (ProbLog's, for instance) would let the
rules' dependence determine the answer. If you need that guarantee, use
ProbLog; PLA trades it for hand-traceable inference.

## 6. Lineage and the Heckerman critique

The calculus descends from **MYCIN certainty factors** (Shortliffe &
Buchanan 1975): rule-attached confidences, attenuation by the weakest
antecedent, and parallel combination of co-supporting rules. Indeed,
`noisy_or` *is* MYCIN's parallel-combination rule for positive evidence
(CF = CF₁ + CF₂(1−CF₁) ≡ F5b), and the `min` conjunction is the Gödel
t-norm of fuzzy logic (Zadeh 1965).

**Heckerman (1986)** showed the CF calculus is probabilistically coherent
only under restrictive independence and modularity assumptions. PLA's
answer is not to dispute this but to make the assumptions explicit and
optional:

1. PLA does not claim its outputs are probabilities (§5); they are
   evidence-ordered confidences.
2. The independence stance is a **named, per-KB operator choice** (F5a–d)
   rather than a hidden constant of the system.
3. The `logit` context mode (F4) and `logit_pool` aggregation (F5d) place
   evidence combination in log-odds space, where additive weights have the
   same justification as naive Bayes / logistic regression — the
   probabilistically coherent special case Heckerman himself identified
   for likelihood-ratio updating of a single hypothesis.

## 7. Choosing an aggregator

| Operator | Stance | Use when |
|---|---|---|
| `noisy_or` (default) | Supports are independent causes | Distinct evidence channels, MYCIN-style accumulation |
| `max` | Only the strongest support counts | Possibility/fuzzy reading; correlated or redundant rules |
| `sum_cap` | Supports add linearly until certain | Simple additive scoring, easy to explain |
| `logit_pool` | Independent log-odds evidence | Calibration-minded pipelines; matches the `logit` context mode |

## 8. Symbolic layer

The symbolic KB is a separate, crisp system: definite-clause facts and
rules. Entailment (`KB ⊨ q` iff every model of KB satisfies q) is decided
by forward chaining to the least model — sound and complete for definite
clauses and linear in KB size; the O(2ⁿ) truth-table checker is retained
as the differential-test oracle (`tests/test_symbolic_entailment.py`). The hybrid engine gates confidences with entailment (`hard`,
`soft`, `constraint` modes); constraint mode is a documented no-op until
the symbolic language gains negation. See `pla/engine.py` and
`examples/run_hybrid_demo.py`.
