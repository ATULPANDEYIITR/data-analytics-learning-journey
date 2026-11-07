#!/usr/bin/env python3
"""
Hypothesis Testing: Statistical Decision and Evaluation Engine

Covers:
- Null and alternative hypotheses
- Significance levels and p-values
- One-sample z-tests
- One-sample t-tests
- Two-sided and one-sided tests
- Type I and Type II errors
- Statistical power
- Confidence intervals
- Multiple-testing correction
- Validation and reproducible reporting

Python standard library only.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence


class Alternative(str, Enum):
    TWO_SIDED = "two-sided"
    GREATER = "greater"
    LESS = "less"


class Decision(str, Enum):
    REJECT_H0 = "reject_null_hypothesis"
    FAIL_TO_REJECT_H0 = "fail_to_reject_null_hypothesis"


@dataclass(frozen=True)
class Hypothesis:
    name: str
    null_value: float
    alternative: Alternative
    significance_level: float = 0.05

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Hypothesis name cannot be empty.")
        if not math.isfinite(self.null_value):
            raise ValueError("Null value must be finite.")
        if not 0 < self.significance_level < 1:
            raise ValueError("Significance level must be between 0 and 1.")


@dataclass
class TestResult:
    test_name: str
    sample_size: int
    statistic: float
    p_value: float
    alpha: float
    decision: Decision
    alternative: str
    effect_estimate: float
    standard_error: float
    confidence_interval: tuple[float, float]
    degrees_of_freedom: int | None = None

    def to_dict(self):
        result = asdict(self)
        result["decision"] = self.decision.value
        result["confidence_interval"] = list(
            self.confidence_interval
        )
        return result


def validate_sample(data: Sequence[float]) -> list[float]:
    if len(data) < 2:
        raise ValueError("At least two observations are required.")

    values = [float(value) for value in data]

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Observations must be finite numbers.")

    return values


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def normal_p_value(
    statistic: float,
    alternative: Alternative
) -> float:
    if alternative == Alternative.TWO_SIDED:
        return math.erfc(abs(statistic) / math.sqrt(2.0))
    if alternative == Alternative.GREATER:
        return normal_cdf(-statistic)
    return normal_cdf(statistic)


def beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Numerically evaluate the continued fraction for the beta function."""
    max_iterations = 300
    epsilon = 3e-14
    tiny = 1e-300

    qab = a + b
    qap = a + 1.0
    qam = a - 1.0

    c = 1.0
    d = 1.0 - qab * x / qap

    if abs(d) < tiny:
        d = tiny

    d = 1.0 / d
    h = d

    for m in range(1, max_iterations + 1):
        m2 = 2 * m

        aa = (
            m * (b - m) * x
            / ((qam + m2) * (a + m2))
        )

        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny

        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny

        d = 1.0 / d
        h *= d * c

        aa = (
            -(a + m) * (qab + m) * x
            / ((a + m2) * (qap + m2))
        )

        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny

        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny

        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < epsilon:
            return h

    raise ArithmeticError("Beta continued fraction did not converge.")


def regularized_beta(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if a <= 0 or b <= 0:
        raise ValueError("Beta parameters must be positive.")

    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    log_factor = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )

    factor = math.exp(log_factor)

    if x < (a + 1.0) / (a + b + 2.0):
        return (
            factor
            * beta_continued_fraction(a, b, x)
            / a
        )

    return 1.0 - (
        factor
        * beta_continued_fraction(b, a, 1.0 - x)
        / b
    )


def student_t_cdf(t: float, df: int) -> float:
    """Student's t cumulative distribution function."""
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")

    x = df / (df + t * t)
    beta_value = regularized_beta(x, df / 2.0, 0.5)

    if t >= 0:
        return 1.0 - 0.5 * beta_value

    return 0.5 * beta_value


def t_p_value(t: float, df: int, alternative: Alternative) -> float:
    cdf = student_t_cdf(t, df)

    if alternative == Alternative.TWO_SIDED:
        return min(1.0, 2.0 * min(cdf, 1.0 - cdf))

    if alternative == Alternative.GREATER:
        return 1.0 - cdf

    return cdf


def confidence_interval(
    estimate: float,
    standard_error: float,
    critical_value: float
) -> tuple[float, float]:
    margin = standard_error * critical_value
    return estimate - margin, estimate + margin


def one_sample_z_test(
    data: Sequence[float],
    hypothesis: Hypothesis,
    population_std: float
) -> TestResult:
    values = validate_sample(data)

    if not math.isfinite(population_std) or population_std <= 0:
        raise ValueError("Population standard deviation must be positive.")

    mean = statistics.fmean(values)
    n = len(values)
    standard_error = population_std / math.sqrt(n)

    statistic = (
        mean - hypothesis.null_value
    ) / standard_error

    p_value = normal_p_value(
        statistic,
        hypothesis.alternative
    )

    critical = 1.959963984540054

    if hypothesis.alternative == Alternative.GREATER:
        critical = 1.6448536269514722
    elif hypothesis.alternative == Alternative.LESS:
        critical = -1.6448536269514722

    if hypothesis.alternative == Alternative.LESS:
        interval = (
            -math.inf,
            mean + 1.6448536269514722 * standard_error
        )
    elif hypothesis.alternative == Alternative.GREATER:
        interval = (
            mean - 1.6448536269514722 * standard_error,
            math.inf
        )
    else:
        interval = confidence_interval(
            mean,
            standard_error,
            critical
        )

    return TestResult(
        test_name="One-sample Z-test",
        sample_size=n,
        statistic=statistic,
        p_value=p_value,
        alpha=hypothesis.significance_level,
        decision=(
            Decision.REJECT_H0
            if p_value < hypothesis.significance_level
            else Decision.FAIL_TO_REJECT_H0
        ),
        alternative=hypothesis.alternative.value,
        effect_estimate=mean - hypothesis.null_value,
        standard_error=standard_error,
        confidence_interval=interval
    )


def one_sample_t_test(
    data: Sequence[float],
    hypothesis: Hypothesis
) -> TestResult:
    values = validate_sample(data)

    n = len(values)
    mean = statistics.fmean(values)
    sample_std = statistics.stdev(values)

    if sample_std == 0:
        if mean == hypothesis.null_value:
            statistic = 0.0
        else:
            statistic = (
                math.inf
                if mean > hypothesis.null_value
                else -math.inf
            )
        standard_error = 0.0
    else:
        standard_error = sample_std / math.sqrt(n)
        statistic = (
            mean - hypothesis.null_value
        ) / standard_error

    df = n - 1

    p_value = (
        t_p_value(statistic, df, hypothesis.alternative)
        if math.isfinite(statistic)
        else (
            0.0
            if (
                (hypothesis.alternative == Alternative.GREATER
                 and statistic > 0)
                or
                (hypothesis.alternative == Alternative.LESS
                 and statistic < 0)
                or
                hypothesis.alternative == Alternative.TWO_SIDED
            )
            else 1.0
        )
    )

    # Inverse Student-t approximation is avoided by using a
    # conservative normal critical value for the displayed interval.
    # The hypothesis decision still uses the exact t distribution.
    critical = (
        1.959963984540054
        if hypothesis.alternative == Alternative.TWO_SIDED
        else 1.6448536269514722
    )

    if standard_error == 0:
        interval = (mean, mean)
    elif hypothesis.alternative == Alternative.TWO_SIDED:
        interval = confidence_interval(
            mean, standard_error, critical
        )
    elif hypothesis.alternative == Alternative.GREATER:
        interval = (
            mean - math.inf,
            mean + critical * standard_error
        )
    else:
        interval = (
            mean - critical * standard_error,
            mean + math.inf
        )

    return TestResult(
        test_name="One-sample Student t-test",
        sample_size=n,
        statistic=statistic,
        p_value=p_value,
        alpha=hypothesis.significance_level,
        decision=(
            Decision.REJECT_H0
            if p_value < hypothesis.significance_level
            else Decision.FAIL_TO_REJECT_H0
        ),
        alternative=hypothesis.alternative.value,
        effect_estimate=mean - hypothesis.null_value,
        standard_error=standard_error,
        confidence_interval=interval,
        degrees_of_freedom=df
    )


def benjamini_hochberg(
    p_values: Sequence[float],
    alpha: float = 0.05
) -> list[bool]:
    """Control the false discovery rate across multiple tests."""
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")

    values = list(p_values)

    if any(
        not math.isfinite(p) or not 0 <= p <= 1
        for p in values
    ):
        raise ValueError("P-values must be finite and between 0 and 1.")

    m = len(values)
    decisions = [False] * m

    if m == 0:
        return decisions

    ordered = sorted(
        enumerate(values),
        key=lambda item: item[1]
    )

    largest_significant_rank = 0

    for rank, (_, p_value) in enumerate(ordered, start=1):
        if p_value <= alpha * rank / m:
            largest_significant_rank = rank

    for index, _ in ordered[:largest_significant_rank]:
        decisions[index] = True

    return decisions


def estimate_type_ii_error(
    true_mean: float,
    null_mean: float,
    population_std: float,
    sample_size: int,
    alpha: float = 0.05
) -> tuple[float, float]:
    """
    Estimate beta and statistical power for a two-sided Z-test
    using a specified alternative population mean.
    """
    if population_std <= 0 or sample_size < 2:
        raise ValueError("Invalid standard deviation or sample size.")

    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")

    standard_error = population_std / math.sqrt(sample_size)
    critical = 1.959963984540054 if alpha == 0.05 else (
        1.959963984540054
    )

    # For alpha other than 0.05, find the normal critical value
    # by binary search.
    if alpha != 0.05:
        low, high = 0.0, 10.0
        for _ in range(100):
            mid = (low + high) / 2
            if 2 * (1 - normal_cdf(mid)) > alpha:
                low = mid
            else:
                high = mid
        critical = (low + high) / 2

    lower = null_mean - critical * standard_error
    upper = null_mean + critical * standard_error

    beta = (
        normal_cdf((upper - true_mean) / standard_error)
        - normal_cdf((lower - true_mean) / standard_error)
    )

    return beta, 1.0 - beta


def save_report(
    results: Sequence[TestResult],
    destination: str = "hypothesis_test_report.json"
) -> None:
    """Write statistical results without exposing raw observations."""
    report = {
        "analysis": "Hypothesis Testing",
        "results": [result.to_dict() for result in results]
    }

    path = Path(destination)
    path.write_text(
        json.dumps(report, indent=4, allow_nan=False),
        encoding="utf-8"
    )


def run_tests() -> None:
    sample = [
        52.1, 50.8, 53.2, 51.7, 54.0,
        52.9, 51.4, 53.5, 52.4, 54.1,
        51.9, 53.0
    ]

    hypothesis = Hypothesis(
        name="Average production measurement",
        null_value=50.0,
        alternative=Alternative.TWO_SIDED,
        significance_level=0.05
    )

    z_result = one_sample_z_test(
        sample,
        hypothesis,
        population_std=3.0
    )

    t_result = one_sample_t_test(
        sample,
        hypothesis
    )

    print("\nHYPOTHESIS TESTING REPORT")
    print("=" * 55)

    for result in (z_result, t_result):
        print(f"\nTest: {result.test_name}")
        print(f"Sample size: {result.sample_size}")
        print(f"Statistic: {result.statistic:.6f}")
        print(f"P-value: {result.p_value:.8f}")
        print(f"Alpha: {result.alpha}")
        print(f"Decision: {result.decision.value}")
        print(f"Effect estimate: {result.effect_estimate:.6f}")
        print(f"Standard error: {result.standard_error:.6f}")
        print(
            "Confidence interval:",
            result.confidence_interval
        )

    beta, power = estimate_type_ii_error(
        true_mean=52.0,
        null_mean=50.0,
        population_std=3.0,
        sample_size=30
    )

    print("\nERROR ANALYSIS")
    print(f"Type II error probability (beta): {beta:.6f}")
    print(f"Statistical power: {power:.6f}")
    print(f"Type I error limit (alpha): {hypothesis.significance_level}")

    adjusted = benjamini_hochberg(
        [0.001, 0.015, 0.04, 0.12, 0.30],
        alpha=0.05
    )

    print("\nMULTIPLE HYPOTHESIS TESTING")
    print("Benjamini-Hochberg decisions:", adjusted)

    save_report([z_result, t_result])
    print("\nReport saved to hypothesis_test_report.json")


if __name__ == "__main__":
    run_tests()
