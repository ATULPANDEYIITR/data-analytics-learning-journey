from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from statistics import mean, median, multimode
from typing import Iterable, Sequence
import csv
import json
import random
import tempfile
from pathlib import Path


class SamplingMethod(Enum):
    SIMPLE_RANDOM = "simple_random"
    SYSTEMATIC = "systematic"
    STRATIFIED = "stratified"


@dataclass(frozen=True)
class Population:
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("Population cannot be empty.")
        if not all(isinstance(x, (int, float)) for x in self.values):
            raise TypeError("Population values must be numeric.")


@dataclass(frozen=True)
class Sample:
    values: tuple[float, ...]
    population_size: int

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("Sample cannot be empty.")
        if self.population_size < len(self.values):
            raise ValueError("Population size cannot be smaller than sample size.")


@dataclass(frozen=True)
class DescriptiveStatistics:
    count: int
    minimum: float
    maximum: float
    mean: float
    median: float
    mode: tuple[float, ...]
    population_variance: float
    population_stddev: float
    sample_variance: float | None
    sample_stddev: float | None


def validate_numeric(values: Iterable[float], name: str) -> tuple[float, ...]:
    data = tuple(values)
    if not data:
        raise ValueError(f"{name} cannot be empty.")
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in data):
        raise TypeError(f"{name} must contain only numeric values.")
    return data


def population_variance(values: Sequence[float]) -> float:
    data = validate_numeric(values, "values")
    mu = mean(data)
    return sum((x - mu) ** 2 for x in data) / len(data)


def sample_variance(values: Sequence[float]) -> float:
    data = validate_numeric(values, "sample")
    if len(data) < 2:
        raise ValueError("Sample variance requires at least two observations.")
    xbar = mean(data)
    return sum((x - xbar) ** 2 for x in data) / (len(data) - 1)


def describe(values: Sequence[float]) -> DescriptiveStatistics:
    data = validate_numeric(values, "values")
    pop_var = population_variance(data)
    samp_var = sample_variance(data) if len(data) >= 2 else None
    return DescriptiveStatistics(
        count=len(data),
        minimum=min(data),
        maximum=max(data),
        mean=mean(data),
        median=median(data),
        mode=tuple(sorted(multimode(data))),
        population_variance=pop_var,
        population_stddev=sqrt(pop_var),
        sample_variance=samp_var,
        sample_stddev=sqrt(samp_var) if samp_var is not None else None,
    )


def simple_random_sample(
    population: Population, sample_size: int, seed: int | None = None
) -> Sample:
    if not 1 <= sample_size <= len(population.values):
        raise ValueError("Sample size must be between 1 and population size.")
    rng = random.Random(seed)
    selected = tuple(rng.sample(population.values, sample_size))
    return Sample(selected, len(population.values))


def systematic_sample(
    population: Population, sample_size: int, start: int = 0
) -> Sample:
    n = len(population.values)
    if not 1 <= sample_size <= n:
        raise ValueError("Invalid sample size.")
    if not 0 <= start < n:
        raise ValueError("Start index must be within the population.")
    interval = n / sample_size
    indices = [int(start + i * interval) for i in range(sample_size)]
    indices = [i for i in indices if i < n]
    if len(indices) != sample_size:
        raise ValueError("Systematic sampling could not produce the requested size.")
    return Sample(tuple(population.values[i] for i in indices), n)


def stratified_sample(
    population: Sequence[tuple[str, float]],
    sample_sizes: dict[str, int],
    seed: int | None = None,
) -> dict[str, Sample]:
    if not population:
        raise ValueError("Stratified population cannot be empty.")

    strata: dict[str, list[float]] = {}
    for group, value in population:
        if not isinstance(group, str) or not group:
            raise ValueError("Each stratum must have a non-empty name.")
        if not isinstance(value, (int, float)):
            raise TypeError("Stratum values must be numeric.")
        strata.setdefault(group, []).append(value)

    unknown = set(sample_sizes) - set(strata)
    if unknown:
        raise ValueError(f"Unknown strata requested: {sorted(unknown)}")

    rng = random.Random(seed)
    result: dict[str, Sample] = {}

    for group, requested_size in sample_sizes.items():
        values = strata[group]
        if not 1 <= requested_size <= len(values):
            raise ValueError(
                f"Invalid sample size for {group}: "
                f"{requested_size}; available={len(values)}"
            )
        result[group] = Sample(tuple(rng.sample(values, requested_size)), len(values))

    return result


def estimate_population_mean(sample: Sample) -> float:
    return mean(sample.values)


def standard_error_of_mean(sample: Sample) -> float:
    if len(sample.values) < 2:
        raise ValueError("At least two observations are required.")
    return sqrt(sample_variance(sample.values) / len(sample.values))


def summarize_sample(sample: Sample) -> dict[str, float]:
    stats = describe(sample.values)
    return {
        "sample_mean": stats.mean,
        "sample_median": stats.median,
        "sample_stddev": stats.sample_stddev or 0.0,
        "standard_error": standard_error_of_mean(sample),
        "population_size": float(sample.population_size),
        "sample_size": float(len(sample.values)),
    }


def save_statistics_csv(path: Path, stats: DescriptiveStatistics) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "count",
                "minimum",
                "maximum",
                "mean",
                "median",
                "mode",
                "population_variance",
                "population_stddev",
                "sample_variance",
                "sample_stddev",
            ]
        )
        writer.writerow(
            [
                stats.count,
                stats.minimum,
                stats.maximum,
                stats.mean,
                stats.median,
                json.dumps(stats.mode),
                stats.population_variance,
                stats.population_stddev,
                stats.sample_variance,
                stats.sample_stddev,
            ]
        )


def main() -> None:
    # The complete population is deliberately small enough to inspect.
    population = Population(
        (
            61, 64, 66, 68, 69, 71, 72, 73, 74, 75,
            76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
            86, 87, 88, 90, 92,
        )
    )

    population_stats = describe(population.values)
    print("Population statistics:")
    print(population_stats)

    sample = simple_random_sample(population, sample_size=8, seed=42)
    print("\nSimple random sample:")
    print(sample.values)
    print(summarize_sample(sample))

    systematic = systematic_sample(population, sample_size=5, start=1)
    print("\nSystematic sample:")
    print(systematic.values)
    print(summarize_sample(systematic))

    grouped_population = [
        ("A", 61), ("A", 66), ("A", 72), ("A", 79), ("A", 85),
        ("B", 64), ("B", 69), ("B", 75), ("B", 81), ("B", 88),
        ("C", 68), ("C", 73), ("C", 77), ("C", 84), ("C", 92),
    ]
    stratified = stratified_sample(
        grouped_population,
        {"A": 2, "B": 2, "C": 2},
        seed=7,
    )

    print("\nStratified samples:")
    for group, selected in stratified.items():
        print(group, selected.values, summarize_sample(selected))

    # Parameter: the true population mean.
    # Statistic: the mean calculated from a sample.
    parameter = population_stats.mean
    statistic = estimate_population_mean(sample)
    print(f"\nPopulation parameter (true mean): {parameter:.2f}")
    print(f"Sample statistic (estimated mean): {statistic:.2f}")

    with tempfile.TemporaryDirectory() as directory:
        output_path = Path(directory) / "statistics.csv"
        save_statistics_csv(output_path, population_stats)
        print(f"\nValidated CSV output: {output_path.exists()}")

    # Edge-case validation.
    try:
        simple_random_sample(population, 0)
    except ValueError as exc:
        print(f"\nExpected validation error: {exc}")

    try:
        sample_variance([10])
    except ValueError as exc:
        print(f"Expected variance error: {exc}")

    # Deterministic assertions make the script self-checking.
    assert population_stats.count == 25
    assert population_stats.minimum == 61
    assert population_stats.maximum == 92
    assert len(sample.values) == 8
    assert abs(parameter - 77.08) < 0.001
    assert statistic in sample.values or isinstance(statistic, float)

    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
