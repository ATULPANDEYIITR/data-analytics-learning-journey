#!/usr/bin/env python3
"""
Confidence Intervals
Point estimates, confidence intervals, margin of error, and bootstrap intervals.

Uses only the Python standard library.
"""

from __future__ import annotations

import math
import random
import statistics
import json
import csv
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence


class IntervalMethod(Enum):
    NORMAL = "normal"
    T_INTERVAL = "t_interval"
    BOOTSTRAP = "bootstrap"


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence_level: float
    margin_of_error: float
    method: str
    sample_size: int

    def __post_init__(self):
        if not all(math.isfinite(x) for x in (
            self.estimate, self.lower, self.upper,
            self.confidence_level, self.margin_of_error
        )):
            raise ValueError("Interval values must be finite.")
        if self.lower > self.upper:
            raise ValueError("Lower bound cannot exceed upper bound.")
        if not 0 < self.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1.")
        if self.sample_size < 1:
            raise ValueError("Sample size must be positive.")

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper

    def width(self) -> float:
        return self.upper - self.lower

    def display(self) -> str:
        return (
            f"{self.method}: estimate={self.estimate:.4f}, "
            f"CI=[{self.lower:.4f}, {self.upper:.4f}], "
            f"MOE={self.margin_of_error:.4f}, "
            f"confidence={self.confidence_level:.0%}, "
            f"n={self.sample_size}"
        )


# Two-sided critical values for commonly used confidence levels.
NORMAL_CRITICAL_VALUES = {
    0.90: 1.6448536269514722,
    0.95: 1.959963984540054,
    0.99: 2.5758293035489004,
}


# Student's t critical values for degrees of freedom 1 through 30.
T_95_TABLE = [
    12.706, 4.303, 3.182, 2.776, 2.571,
    2.447, 2.365, 2.306, 2.262, 2.228,
    2.201, 2.179, 2.160, 2.145, 2.131,
    2.120, 2.110, 2.101, 2.093, 2.086,
    2.080, 2.074, 2.069, 2.064, 2.060,
    2.056, 2.052, 2.048, 2.045, 2.042,
]


def validate_sample(data: Sequence[float], minimum: int = 1) -> list[float]:
    if isinstance(data, (str, bytes)):
        raise TypeError("Sample must be a numeric sequence.")

    values = [float(value) for value in data]

    if len(values) < minimum:
        raise ValueError(f"At least {minimum} observations are required.")

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Sample contains non-finite values.")

    return values


def validate_confidence(confidence: float) -> float:
    confidence = float(confidence)

    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("Confidence must be strictly between 0 and 1.")

    return confidence


def mean_estimate(data: Sequence[float]) -> float:
    values = validate_sample(data)
    return statistics.fmean(values)


def sample_variance(data: Sequence[float]) -> float:
    values = validate_sample(data, minimum=2)
    return statistics.variance(values)


def sample_standard_deviation(data: Sequence[float]) -> float:
    return math.sqrt(sample_variance(data))


def normal_critical_value(confidence: float) -> float:
    confidence = validate_confidence(confidence)

    if confidence in NORMAL_CRITICAL_VALUES:
        return NORMAL_CRITICAL_VALUES[confidence]

    alpha = 1.0 - confidence
    p = 1.0 - alpha / 2.0

    # Acklam's rational approximation to the inverse normal CDF.
    a = [
        -3.969683028665376e+01,
        2.209460984245205e+02,
        -2.759285104469687e+02,
        1.383577518672690e+02,
        -3.066479806614716e+01,
        2.506628277459239e+00,
    ]

    b = [
        -5.447609879822406e+01,
        1.615858368580409e+02,
        -1.556989798598866e+02,
        6.680131188771972e+01,
        -1.328068155288572e+01,
    ]

    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e+00,
        -2.549732539343734e+00,
        4.374664141464968e+00,
        2.938163982698783e+00,
    ]

    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e+00,
        3.754408661907416e+00,
    ]

    low = 0.02425
    high = 1.0 - low

    if p < low:
        q = math.sqrt(-2.0 * math.log(p))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
              + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        ) * -1.0

    if p > high:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q
              + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )

    q = p - 0.5
    r = q * q

    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r
          + a[4]) * r + a[5]) * q
        / (((((b[0] * r + b[1]) * r + b[2]) * r
             + b[3]) * r + b[4]) * r + 1)
    )


def t_critical_95(df: int) -> float:
    if df < 1:
        raise ValueError("Degrees of freedom must be positive.")

    if df <= 30:
        return T_95_TABLE[df - 1]

    # Normal approximation for larger degrees of freedom.
    return normal_critical_value(0.95)


def normal_mean_interval(
    data: Sequence[float],
    confidence: float = 0.95,
    population_sd: float | None = None,
) -> ConfidenceInterval:
    values = validate_sample(data, minimum=2)
    confidence = validate_confidence(confidence)

    sd = (
        float(population_sd)
        if population_sd is not None
        else sample_standard_deviation(values)
    )

    if not math.isfinite(sd) or sd < 0:
        raise ValueError("Population standard deviation must be nonnegative.")

    estimate = statistics.fmean(values)
    standard_error = sd / math.sqrt(len(values))
    margin = normal_critical_value(confidence) * standard_error

    return ConfidenceInterval(
        estimate,
        estimate - margin,
        estimate + margin,
        confidence,
        margin,
        "Normal mean interval",
        len(values),
    )


def t_mean_interval(
    data: Sequence[float],
    confidence: float = 0.95,
) -> ConfidenceInterval:
    values = validate_sample(data, minimum=2)
    confidence = validate_confidence(confidence)

    estimate = statistics.fmean(values)
    sd = statistics.stdev(values)
    standard_error = sd / math.sqrt(len(values))

    if confidence != 0.95:
        raise ValueError(
            "The standard-library t table supports 95% confidence only."
        )

    critical = t_critical_95(len(values) - 1)
    margin = critical * standard_error

    return ConfidenceInterval(
        estimate,
        estimate - margin,
        estimate + margin,
        confidence,
        margin,
        "Student t interval",
        len(values),
    )


def proportion_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    confidence = validate_confidence(confidence)

    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("Counts must be integers.")

    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("Counts must be integers.")

    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("Invalid success or trial count.")

    estimate = successes / trials
    z = normal_critical_value(confidence)
    standard_error = math.sqrt(estimate * (1 - estimate) / trials)
    margin = z * standard_error

    # Wilson interval performs better than the basic Wald interval
    # when the sample proportion is close to zero or one.
    denominator = 1 + z * z / trials
    center = (estimate + z * z / (2 * trials)) / denominator

    adjustment = (
        z * math.sqrt(
            estimate * (1 - estimate) / trials
            + z * z / (4 * trials * trials)
        ) / denominator
    )

    lower = max(0.0, center - adjustment)
    upper = min(1.0, center + adjustment)

    return ConfidenceInterval(
        estimate,
        lower,
        upper,
        confidence,
        (upper - lower) / 2,
        "Wilson proportion interval",
        trials,
    )


def bootstrap_interval(
    data: Sequence[float],
    statistic: Callable[[Sequence[float]], float] = statistics.fmean,
    confidence: float = 0.95,
    repetitions: int = 10000,
    seed: int = 42,
) -> ConfidenceInterval:
    values = validate_sample(data, minimum=2)
    confidence = validate_confidence(confidence)

    if repetitions < 100:
        raise ValueError("Use at least 100 bootstrap repetitions.")

    if not callable(statistic):
        raise TypeError("Statistic must be callable.")

    if not isinstance(seed, int):
        raise TypeError("Seed must be an integer.")

    rng = random.Random(seed)
    n = len(values)
    estimates = []

    for _ in range(repetitions):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        estimate = float(statistic(sample))

        if not math.isfinite(estimate):
            raise ValueError("Statistic returned a non-finite value.")

        estimates.append(estimate)

    estimates.sort()

    alpha = (1 - confidence) / 2

    def percentile(p: float) -> float:
        position = p * (len(estimates) - 1)
        lower_index = int(math.floor(position))
        upper_index = int(math.ceil(position))

        if lower_index == upper_index:
            return estimates[lower_index]

        weight = position - lower_index

        return (
            estimates[lower_index] * (1 - weight)
            + estimates[upper_index] * weight
        )

    estimate = float(statistic(values))
    lower = percentile(alpha)
    upper = percentile(1 - alpha)

    return ConfidenceInterval(
        estimate,
        lower,
        upper,
        confidence,
        (upper - lower) / 2,
        "Percentile bootstrap interval",
        n,
    )


def margin_of_error(
    population_sd: float,
    sample_size: int,
    confidence: float = 0.95,
) -> float:
    confidence = validate_confidence(confidence)

    if sample_size <= 0:
        raise ValueError("Sample size must be positive.")

    if not math.isfinite(population_sd) or population_sd < 0:
        raise ValueError("Standard deviation must be nonnegative.")

    return (
        normal_critical_value(confidence)
        * population_sd
        / math.sqrt(sample_size)
    )


def required_sample_size(
    population_sd: float,
    desired_margin: float,
    confidence: float = 0.95,
) -> int:
    confidence = validate_confidence(confidence)

    if population_sd < 0 or not math.isfinite(population_sd):
        raise ValueError("Standard deviation must be nonnegative.")

    if desired_margin <= 0 or not math.isfinite(desired_margin):
        raise ValueError("Desired margin must be positive.")

    z = normal_critical_value(confidence)

    return math.ceil((z * population_sd / desired_margin) ** 2)


def save_results(
    intervals: Sequence[ConfidenceInterval],
    filename: str = "confidence_intervals.json",
) -> None:
    path = Path(filename)

    if path.suffix.lower() != ".json":
        raise ValueError("Only JSON output is supported.")

    payload = [asdict(interval) for interval in intervals]

    # UTF-8 output and a predictable JSON structure.
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def run_tests() -> None:
    data = [12, 14, 15, 13, 16, 18, 14, 15, 17, 16]

    interval = t_mean_interval(data)
    assert interval.lower < interval.estimate < interval.upper
    assert interval.margin_of_error > 0

    proportion = proportion_interval(72, 100)
    assert 0 <= proportion.lower <= proportion.estimate <= proportion.upper <= 1

    bootstrap = bootstrap_interval(data, repetitions=1000)
    assert bootstrap.lower <= bootstrap.estimate <= bootstrap.upper

    assert required_sample_size(10, 2) == 97

    try:
        t_mean_interval([5])
        raise AssertionError("Single observation should fail.")
    except ValueError:
        pass

    try:
        proportion_interval(110, 100)
        raise AssertionError("Invalid proportion should fail.")
    except ValueError:
        pass

    try:
        normal_mean_interval([1, float("nan")])
        raise AssertionError("Non-finite observations should fail.")
    except ValueError:
        pass

    print("All tests passed.")


def main() -> None:
    response_times = [
        12.4, 13.1, 11.8, 14.2, 12.9,
        13.7, 12.1, 14.0, 13.3, 12.7,
        11.9, 13.5, 14.1, 12.6, 13.0,
    ]

    conversion_successes = 735
    conversion_trials = 1000

    print("CONFIDENCE INTERVAL ANALYSIS")
    print("=" * 60)

    print("\n1. Point estimate")
    print(f"Sample mean: {mean_estimate(response_times):.4f}")
    print(f"Sample standard deviation: {sample_standard_deviation(response_times):.4f}")

    print("\n2. Mean confidence intervals")
    intervals = [
        normal_mean_interval(response_times, 0.95),
        t_mean_interval(response_times, 0.95),
    ]

    for result in intervals:
        print(result.display())

    print("\n3. Proportion confidence interval")
    proportion = proportion_interval(
        conversion_successes,
        conversion_trials,
        0.95,
    )
    print(proportion.display())

    print("\n4. Bootstrap confidence interval")
    bootstrap = bootstrap_interval(
        response_times,
        statistic=statistics.median,
        confidence=0.95,
        repetitions=5000,
        seed=42,
    )
    print(bootstrap.display())

    print("\n5. Margin of error")
    moe = margin_of_error(10, 100, 0.95)
    print(f"Margin of error: {moe:.4f}")

    print("\n6. Required sample size")
    required = required_sample_size(10, 2, 0.95)
    print(f"Required observations: {required}")

    print("\n7. Interval interpretation")
    print(
        "A 95% confidence procedure produces intervals that contain "
        "the fixed population parameter in approximately 95% of "
        "repeated samples under its assumptions."
    )

    print("\n8. Export")
    save_results([*intervals, proportion, bootstrap])
    print("Results saved to confidence_intervals.json")

    print("\n9. Tests")
    run_tests()


if __name__ == "__main__":
    main()
