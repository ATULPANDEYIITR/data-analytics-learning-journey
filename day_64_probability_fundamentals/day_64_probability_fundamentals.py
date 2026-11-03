from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import comb
from typing import FrozenSet, Iterable, Mapping


class ProbabilityError(ValueError):
    """Raised when a probability model is invalid."""


class EventRelation(Enum):
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"
    DISJOINT = "disjoint"
    OVERLAPPING = "overlapping"


@dataclass(frozen=True)
class ProbabilitySpace:
    outcomes: FrozenSet[str]
    probabilities: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.outcomes:
            raise ProbabilityError("Sample space cannot be empty.")

        if set(self.probabilities) != set(self.outcomes):
            raise ProbabilityError(
                "Every outcome must have exactly one probability."
            )

        if any(p < 0 or p > 1 for p in self.probabilities.values()):
            raise ProbabilityError("Outcome probabilities must be between 0 and 1.")

        total = sum(self.probabilities.values())
        if abs(total - 1.0) > 1e-12:
            raise ProbabilityError(
                f"Outcome probabilities must sum to 1; received {total:.12f}."
            )

    def probability(self, event: Iterable[str]) -> float:
        event_set = frozenset(event)

        if not event_set <= self.outcomes:
            invalid = event_set - self.outcomes
            raise ProbabilityError(f"Unknown outcomes: {sorted(invalid)}")

        return sum(self.probabilities[x] for x in event_set)

    def complement(self, event: Iterable[str]) -> FrozenSet[str]:
        event_set = frozenset(event)
        if not event_set <= self.outcomes:
            raise ProbabilityError("Event contains outcomes outside the sample space.")
        return self.outcomes - event_set

    def conditional_probability(
        self,
        event: Iterable[str],
        given: Iterable[str],
    ) -> float:
        event_set = frozenset(event)
        given_set = frozenset(given)

        p_given = self.probability(given_set)
        if p_given == 0:
            raise ProbabilityError(
                "Conditional probability is undefined when P(given) = 0."
            )

        return self.probability(event_set & given_set) / p_given

    def are_independent(
        self,
        first: Iterable[str],
        second: Iterable[str],
        tolerance: float = 1e-12,
    ) -> bool:
        a = frozenset(first)
        b = frozenset(second)

        lhs = self.probability(a & b)
        rhs = self.probability(a) * self.probability(b)
        return abs(lhs - rhs) <= tolerance

    def relation(
        self,
        first: Iterable[str],
        second: Iterable[str],
    ) -> EventRelation:
        a = frozenset(first)
        b = frozenset(second)

        if not a.isdisjoint(b):
            return (
                EventRelation.INDEPENDENT
                if self.are_independent(a, b)
                else EventRelation.OVERLAPPING
            )

        return EventRelation.DISJOINT


def fair_die_space() -> ProbabilitySpace:
    outcomes = frozenset(str(i) for i in range(1, 7))
    probabilities = {outcome: 1 / 6 for outcome in outcomes}
    return ProbabilitySpace(outcomes, probabilities)


def binomial_probability(n: int, successes: int, p: float) -> float:
    if n < 0:
        raise ProbabilityError("n must be non-negative.")
    if not 0 <= successes <= n:
        raise ProbabilityError("successes must be between 0 and n.")
    if not 0 <= p <= 1:
        raise ProbabilityError("p must be between 0 and 1.")

    return comb(n, successes) * (p ** successes) * ((1 - p) ** (n - successes))


def demonstrate_probability_rules() -> None:
    space = fair_die_space()

    even = frozenset({"2", "4", "6"})
    greater_than_four = frozenset({"5", "6"})
    odd = frozenset({"1", "3", "5"})

    print("=== Probability Fundamentals ===")
    print(f"Sample space: {sorted(space.outcomes)}")
    print(f"P(even): {space.probability(even):.4f}")
    print(f"P(>4): {space.probability(greater_than_four):.4f}")
    print(f"P(not even): {space.probability(space.complement(even)):.4f}")

    union = even | greater_than_four
    intersection = even & greater_than_four

    print(f"P(even ∪ >4): {space.probability(union):.4f}")
    print(f"P(even ∩ >4): {space.probability(intersection):.4f}")

    p_a = space.probability(even)
    p_b = space.probability(greater_than_four)
    p_intersection = space.probability(intersection)

    # Inclusion-exclusion:
    # P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
    print(
        "Inclusion-exclusion check:",
        abs(space.probability(union) - (p_a + p_b - p_intersection)) < 1e-12,
    )

    # Conditional probability:
    # P(A | B) = P(A ∩ B) / P(B)
    print(
        f"P(even | >4): "
        f"{space.conditional_probability(even, greater_than_four):.4f}"
    )

    print(f"Relation between even and odd: {space.relation(even, odd).value}")
    print(
        "Even and >4 independent:",
        space.are_independent(even, greater_than_four),
    )

    # Law of total probability using the partition:
    # B = {odd}, B^c = {even}
    target = greater_than_four
    p_target_given_odd = space.conditional_probability(target, odd)
    p_target_given_even = space.conditional_probability(target, even)
    total = (
        p_target_given_odd * space.probability(odd)
        + p_target_given_even * space.probability(even)
    )

    print(f"Law of total probability check: {total:.4f}")
    print(f"Direct P(>4): {space.probability(target):.4f}")

    print("\n=== Independent Bernoulli Trials ===")
    p_at_least_one = 1 - binomial_probability(10, 0, 0.2)
    print(f"P(at least one success in 10 trials, p=0.2): {p_at_least_one:.6f}")
    print(f"P(exactly 3 successes): {binomial_probability(10, 3, 0.2):.6f}")


def demonstrate_bayes_rule() -> None:
    print("\n=== Bayes' Rule ===")

    # Two production lines have different defect rates.
    line_a_prior = 0.60
    line_b_prior = 0.40
    defect_given_a = 0.02
    defect_given_b = 0.05

    p_defect = (
        defect_given_a * line_a_prior
        + defect_given_b * line_b_prior
    )

    posterior_a_given_defect = (
        defect_given_a * line_a_prior / p_defect
    )

    print(f"P(defect): {p_defect:.4f}")
    print(f"P(Line A | defect): {posterior_a_given_defect:.4f}")


def demonstrate_validation() -> None:
    print("\n=== Validation and Failure Handling ===")

    try:
        ProbabilitySpace(
            outcomes=frozenset({"H", "T"}),
            probabilities={"H": 0.7, "T": 0.7},
        )
    except ProbabilityError as exc:
        print(f"Rejected invalid probability space: {exc}")

    try:
        space = fair_die_space()
        space.conditional_probability({"1"}, set())
    except ProbabilityError as exc:
        print(f"Rejected invalid conditional probability: {exc}")


if __name__ == "__main__":
    demonstrate_probability_rules()
    demonstrate_bayes_rule()
    demonstrate_validation()
