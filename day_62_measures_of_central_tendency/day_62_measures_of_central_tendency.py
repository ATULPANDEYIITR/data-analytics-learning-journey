from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext
from enum import Enum
from math import prod
from statistics import median
from typing import Iterable, Sequence

getcontext().prec = 40


class MeasureError(ValueError):
    """Raised when a central-tendency measure cannot be computed."""


class MeasureType(Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    WEIGHTED_MEAN = "weighted_mean"
    GEOMETRIC_MEAN = "geometric_mean"
    HARMONIC_MEAN = "harmonic_mean"


@dataclass(frozen=True)
class Dataset:
    values: tuple[Decimal, ...]

    @classmethod
    def from_values(cls, values: Iterable[float | int | str | Decimal]) -> "Dataset":
        converted = tuple(Decimal(str(value)) for value in values)
        if not converted:
            raise MeasureError("Dataset must contain at least one value.")
        if any(not value.is_finite() for value in converted):
            raise MeasureError("All observations must be finite numbers.")
        return cls(converted)


@dataclass(frozen=True)
class WeightedObservation:
    value: Decimal
    weight: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite() or not self.weight.is_finite():
            raise MeasureError("Values and weights must be finite.")
        if self.weight < 0:
            raise MeasureError("Weights cannot be negative.")


class CentralTendency:
    @staticmethod
    def mean(dataset: Dataset) -> Decimal:
        return sum(dataset.values, Decimal(0)) / Decimal(len(dataset.values))

    @staticmethod
    def median(dataset: Dataset) -> Decimal:
        ordered = sorted(dataset.values)
        n = len(ordered)
        middle = n // 2
        if n % 2:
            return ordered[middle]
        return (ordered[middle - 1] + ordered[middle]) / Decimal(2)

    @staticmethod
    def mode(dataset: Dataset) -> tuple[Decimal, ...]:
        frequencies: dict[Decimal, int] = {}
        for value in dataset.values:
            frequencies[value] = frequencies.get(value, 0) + 1

        maximum = max(frequencies.values())
        if maximum == 1:
            return ()

        return tuple(
            sorted(value for value, count in frequencies.items() if count == maximum)
        )

    @staticmethod
    def weighted_mean(observations: Sequence[WeightedObservation]) -> Decimal:
        if not observations:
            raise MeasureError("Weighted observations cannot be empty.")

        total_weight = sum(
            (item.weight for item in observations), Decimal(0)
        )
        if total_weight == 0:
            raise MeasureError("Total weight must be greater than zero.")

        weighted_total = sum(
            (item.value * item.weight for item in observations), Decimal(0)
        )
        return weighted_total / total_weight

    @staticmethod
    def geometric_mean(dataset: Dataset) -> Decimal:
        if any(value <= 0 for value in dataset.values):
            raise MeasureError("Geometric mean requires every value to be positive.")

        logarithmic_sum = sum(
            (value.ln() for value in dataset.values), Decimal(0)
        )
        return (logarithmic_sum / Decimal(len(dataset.values))).exp()

    @staticmethod
    def harmonic_mean(dataset: Dataset) -> Decimal:
        if any(value <= 0 for value in dataset.values):
            raise MeasureError("Harmonic mean requires every value to be positive.")

        reciprocal_sum = sum(
            (Decimal(1) / value for value in dataset.values), Decimal(0)
        )
        return Decimal(len(dataset.values)) / reciprocal_sum


def format_decimal(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f")


def describe_dataset(name: str, dataset: Dataset) -> None:
    print(f"\n{name}")
    print("-" * len(name))
    print("Values:", ", ".join(format_decimal(v) for v in dataset.values))
    print("Mean:", format_decimal(CentralTendency.mean(dataset)))
    print("Median:", format_decimal(CentralTendency.median(dataset)))

    modes = CentralTendency.mode(dataset)
    print(
        "Mode:",
        "No mode" if not modes else ", ".join(format_decimal(v) for v in modes),
    )

    try:
        print("Geometric mean:", format_decimal(CentralTendency.geometric_mean(dataset)))
    except MeasureError as exc:
        print("Geometric mean:", f"Unavailable ({exc})")

    try:
        print("Harmonic mean:", format_decimal(CentralTendency.harmonic_mean(dataset)))
    except MeasureError as exc:
        print("Harmonic mean:", f"Unavailable ({exc})")


def demonstrate_weighted_mean() -> None:
    observations = (
        WeightedObservation(Decimal("78"), Decimal("0.20")),
        WeightedObservation(Decimal("85"), Decimal("0.30")),
        WeightedObservation(Decimal("92"), Decimal("0.50")),
    )

    result = CentralTendency.weighted_mean(observations)

    print("\nWeighted Assessment")
    print("-------------------")
    for item in observations:
        print(
            f"Score={format_decimal(item.value)}, "
            f"Weight={format_decimal(item.weight)}"
        )
    print("Weighted mean:", format_decimal(result))


def demonstrate_failure_conditions() -> None:
    print("\nValidation and Failure Conditions")
    print("---------------------------------")

    cases = [
        ("empty dataset", lambda: Dataset.from_values([])),
        (
            "geometric mean containing zero",
            lambda: CentralTendency.geometric_mean(
                Dataset.from_values([10, 0, 20])
            ),
        ),
        (
            "geometric mean containing negative value",
            lambda: CentralTendency.geometric_mean(
                Dataset.from_values([10, -5, 20])
            ),
        ),
        (
            "harmonic mean containing zero",
            lambda: CentralTendency.harmonic_mean(
                Dataset.from_values([10, 0, 20])
            ),
        ),
        (
            "weighted mean with zero total weight",
            lambda: CentralTendency.weighted_mean(
                (
                    WeightedObservation(10, 0),
                    WeightedObservation(20, 0),
                )
            ),
        ),
        (
            "negative weight",
            lambda: WeightedObservation(10, -1),
        ),
    ]

    for description, operation in cases:
        try:
            operation()
            print(description, "-> unexpectedly accepted")
        except (MeasureError, ValueError) as exc:
            print(description, "-> rejected:", exc)


def compare_measures() -> None:
    dataset = Dataset.from_values([10, 10, 10, 12, 15, 18, 50])

    measures = {
        MeasureType.MEAN: CentralTendency.mean(dataset),
        MeasureType.MEDIAN: CentralTendency.median(dataset),
        MeasureType.GEOMETRIC_MEAN: CentralTendency.geometric_mean(dataset),
        MeasureType.HARMONIC_MEAN: CentralTendency.harmonic_mean(dataset),
    }

    print("\nEffect of an Outlier")
    print("--------------------")
    for measure, value in measures.items():
        print(f"{measure.value:16}: {format_decimal(value)}")


def main() -> None:
    sales = Dataset.from_values([120, 125, 125, 130, 140, 145, 150])
    growth_rates = Dataset.from_values([1.02, 1.05, 1.08, 1.03])
    travel_speeds = Dataset.from_values([40, 50, 60])

    describe_dataset("Sales Values", sales)
    describe_dataset("Growth Multipliers", growth_rates)
    describe_dataset("Travel Speeds", travel_speeds)

    demonstrate_weighted_mean()
    compare_measures()
    demonstrate_failure_conditions()

    assert CentralTendency.mean(Dataset.from_values([2, 4, 6])) == Decimal(4)
    assert CentralTendency.median(Dataset.from_values([1, 2, 3, 4])) == Decimal("2.5")
    assert CentralTendency.mode(Dataset.from_values([1, 2, 2, 3])) == (Decimal(2),)

    print("\nAssertions passed.")


if __name__ == "__main__":
    main()
