#!/usr/bin/env python3
"""
Sampling Distributions
======================

Demonstrates:
1. Population and sample statistics
2. Sampling distributions of the sample mean
3. Standard error
4. Central Limit Theorem (CLT)
5. Law of Large Numbers (LLN)
6. Sampling with and without replacement
7. Confidence intervals
8. Simulation validation and reproducibility

Uses only the Python standard library.
"""

from __future__ import annotations

import math
import random
import statistics
import json
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence


class SamplingMethod(Enum):
    WITH_REPLACEMENT = "with_replacement"
    WITHOUT_REPLACEMENT = "without_replacement"


class SamplingError(Exception):
    """Raised when a sampling operation is invalid."""


@dataclass(frozen=True)
class PopulationStatistics:
    size: int
    mean: float
    variance: float
    standard_deviation: float


@dataclass(frozen=True)
class SamplingResult:
    sample_size: int
    repetitions: int
    theoretical_standard_error: float
    empirical_standard_error: float
    sampling_mean: float
    population_mean: float
    bias: float
    minimum: float
    maximum: float
    method: str


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float


class SamplingDistribution:
    def __init__(
        self,
        population: Sequence[float],
        seed: int = 42
    ) -> None:
        if not population:
            raise SamplingError("Population cannot be empty.")

        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in population
        ):
            raise SamplingError("Population must contain finite numeric values.")

        self.population = tuple(float(value) for value in population)
        self.rng = random.Random(seed)
        self.stats = self._calculate_population_statistics()

    def _calculate_population_statistics(self) -> PopulationStatistics:
        size = len(self.population)
        mean = statistics.fmean(self.population)

        # Population variance divides by N, not N - 1.
        variance = sum(
            (value - mean) ** 2 for value in self.population
        ) / size

        return PopulationStatistics(
            size=size,
            mean=mean,
            variance=variance,
            standard_deviation=math.sqrt(variance)
        )

    def calculate_sample_statistics(
        self,
        sample: Sequence[float]
    ) -> dict[str, float]:
        if not sample:
            raise SamplingError("Sample cannot be empty.")

        if len(sample) < 2:
            sample_variance = 0.0
        else:
            sample_variance = statistics.variance(sample)

        return {
            "sample_size": len(sample),
            "sample_mean": statistics.fmean(sample),
            "sample_variance": sample_variance,
            "sample_standard_deviation": math.sqrt(sample_variance)
        }

    def theoretical_standard_error(
        self,
        sample_size: int,
        method: SamplingMethod = SamplingMethod.WITH_REPLACEMENT
    ) -> float:
        if sample_size <= 0:
            raise SamplingError("Sample size must be positive.")

        if (
            method == SamplingMethod.WITHOUT_REPLACEMENT
            and sample_size > self.stats.size
        ):
            raise SamplingError(
                "Sample size cannot exceed population size "
                "without replacement."
            )

        standard_error = (
            self.stats.standard_deviation / math.sqrt(sample_size)
        )

        # Finite population correction for simple random sampling
        # without replacement.
        if method == SamplingMethod.WITHOUT_REPLACEMENT:
            correction = math.sqrt(
                (self.stats.size - sample_size)
                / (self.stats.size - 1)
            ) if self.stats.size > 1 else 0.0

            standard_error *= correction

        return standard_error

    def draw_sample(
        self,
        sample_size: int,
        method: SamplingMethod
    ) -> list[float]:
        if sample_size <= 0:
            raise SamplingError("Sample size must be positive.")

        if (
            method == SamplingMethod.WITHOUT_REPLACEMENT
            and sample_size > self.stats.size
        ):
            raise SamplingError("Sample exceeds population size.")

        if method == SamplingMethod.WITH_REPLACEMENT:
            return self.rng.choices(
                self.population,
                k=sample_size
            )

        return self.rng.sample(
            self.population,
            k=sample_size
        )

    def simulate_sampling_distribution(
        self,
        sample_size: int,
        repetitions: int = 10000,
        method: SamplingMethod = SamplingMethod.WITH_REPLACEMENT
    ) -> SamplingResult:
        if repetitions < 2:
            raise SamplingError(
                "At least two repetitions are required."
            )

        if (
            method == SamplingMethod.WITHOUT_REPLACEMENT
            and sample_size > self.stats.size
        ):
            raise SamplingError("Invalid sample size.")

        sample_means = [
            statistics.fmean(
                self.draw_sample(sample_size, method)
            )
            for _ in range(repetitions)
        ]

        empirical_mean = statistics.fmean(sample_means)
        empirical_se = statistics.stdev(sample_means)

        return SamplingResult(
            sample_size=sample_size,
            repetitions=repetitions,
            theoretical_standard_error=self.theoretical_standard_error(
                sample_size, method
            ),
            empirical_standard_error=empirical_se,
            sampling_mean=empirical_mean,
            population_mean=self.stats.mean,
            bias=empirical_mean - self.stats.mean,
            minimum=min(sample_means),
            maximum=max(sample_means),
            method=method.value
        )

    def law_of_large_numbers(
        self,
        sample_sizes: Sequence[int],
        method: SamplingMethod = SamplingMethod.WITH_REPLACEMENT
    ) -> list[dict[str, float]]:
        results = []

        for sample_size in sample_sizes:
            sample = self.draw_sample(sample_size, method)
            sample_mean = statistics.fmean(sample)

            results.append({
                "sample_size": sample_size,
                "sample_mean": sample_mean,
                "population_mean": self.stats.mean,
                "absolute_error": abs(sample_mean - self.stats.mean)
            })

        return results

    def central_limit_theorem(
        self,
        sample_sizes: Sequence[int],
        repetitions: int = 10000
    ) -> dict[int, dict[str, float]]:
        results = {}

        for sample_size in sample_sizes:
            simulation = self.simulate_sampling_distribution(
                sample_size=sample_size,
                repetitions=repetitions,
                method=SamplingMethod.WITH_REPLACEMENT
            )

            results[sample_size] = {
                "sampling_mean": simulation.sampling_mean,
                "theoretical_standard_error":
                    simulation.theoretical_standard_error,
                "empirical_standard_error":
                    simulation.empirical_standard_error
            }

        return results

    @staticmethod
    def confidence_interval(
        estimate: float,
        standard_error: float,
        confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        if not math.isfinite(estimate):
            raise SamplingError("Estimate must be finite.")

        if not math.isfinite(standard_error) or standard_error < 0:
            raise SamplingError("Invalid standard error.")

        if not 0 < confidence_level < 1:
            raise SamplingError(
                "Confidence level must be between 0 and 1."
            )

        # Normal approximation critical values.
        critical_values = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }

        critical_value = critical_values.get(confidence_level)

        if critical_value is None:
            raise SamplingError(
                "Supported confidence levels: 0.90, 0.95, 0.99."
            )

        margin = critical_value * standard_error

        return ConfidenceInterval(
            estimate=estimate,
            lower_bound=estimate - margin,
            upper_bound=estimate + margin,
            confidence_level=confidence_level
        )


def export_results(
    results: dict,
    filename: str = "sampling_results.json"
) -> None:
    path = Path(filename)

    # Avoid writing outside the current working directory.
    if path.name != filename or path.suffix.lower() != ".json":
        raise ValueError("Use a JSON filename in the current directory.")

    with path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)


def run_tests() -> None:
    population = [10, 20, 30, 40, 50]

    model = SamplingDistribution(population, seed=123)

    assert model.stats.size == 5
    assert math.isclose(model.stats.mean, 30.0)
    assert math.isclose(model.stats.variance, 200.0)

    assert math.isclose(
        model.theoretical_standard_error(4),
        math.sqrt(200 / 4)
    )

    without_replacement_se = model.theoretical_standard_error(
        4,
        SamplingMethod.WITHOUT_REPLACEMENT
    )

    assert without_replacement_se < model.theoretical_standard_error(4)

    interval = model.confidence_interval(30, 2)

    assert interval.lower_bound < 30
    assert interval.upper_bound > 30

    try:
        model.draw_sample(10, SamplingMethod.WITHOUT_REPLACEMENT)
        raise AssertionError("Invalid sample size was accepted.")
    except SamplingError:
        pass

    try:
        model.draw_sample(0, SamplingMethod.WITH_REPLACEMENT)
        raise AssertionError("Zero sample size was accepted.")
    except SamplingError:
        pass

    print("All tests passed.")


def main() -> None:
    run_tests()

    # A skewed population demonstrates why sampling distributions
    # are useful when the original population is not normal.
    population = (
        [5.0] * 500
        + [15.0] * 250
        + [30.0] * 150
        + [100.0] * 100
    )

    model = SamplingDistribution(population, seed=2026)

    print("\nPOPULATION STATISTICS")
    print(json.dumps(asdict(model.stats), indent=4))

    print("\nSAMPLE STATISTICS")
    sample = model.draw_sample(
        30,
        SamplingMethod.WITH_REPLACEMENT
    )
    print(json.dumps(
        model.calculate_sample_statistics(sample),
        indent=4
    ))

    print("\nSAMPLING DISTRIBUTION AND CENTRAL LIMIT THEOREM")

    clt_results = model.central_limit_theorem(
        sample_sizes=[2, 5, 10, 30, 50, 100],
        repetitions=10000
    )

    for size, result in clt_results.items():
        print(f"\nSample size: {size}")
        for key, value in result.items():
            print(f"{key}: {value:.5f}")

    print("\nLAW OF LARGE NUMBERS")

    lln_results = model.law_of_large_numbers(
        sample_sizes=[10, 50, 100, 500, 1000, 5000]
    )

    for result in lln_results:
        print(
            f"n={result['sample_size']:5d} | "
            f"mean={result['sample_mean']:9.4f} | "
            f"error={result['absolute_error']:9.4f}"
        )

    print("\nFINITE POPULATION CORRECTION")

    for size in [10, 50, 100, 250]:
        with_replacement = model.theoretical_standard_error(
            size,
            SamplingMethod.WITH_REPLACEMENT
        )

        without_replacement = model.theoretical_standard_error(
            size,
            SamplingMethod.WITHOUT_REPLACEMENT
        )

        print(
            f"n={size:3d} | "
            f"with replacement={with_replacement:.4f} | "
            f"without replacement={without_replacement:.4f}"
        )

    print("\n95% CONFIDENCE INTERVAL")

    sample_size = 100
    sample_mean = statistics.fmean(
        model.draw_sample(
            sample_size,
            SamplingMethod.WITH_REPLACEMENT
        )
    )

    se = model.theoretical_standard_error(sample_size)

    interval = model.confidence_interval(
        sample_mean,
        se,
        0.95
    )

    print(json.dumps(asdict(interval), indent=4))

    export_results({
        "population": asdict(model.stats),
        "clt": clt_results,
        "lln": lln_results
    })

    print("\nResults exported to sampling_results.json")


if __name__ == "__main__":
    main()
