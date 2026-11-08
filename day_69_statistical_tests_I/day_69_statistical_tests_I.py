#!/usr/bin/env python3
"""
Statistical Tests I
One-sample, two-sample, paired, and independent statistical tests.

Uses only Python standard-library modules.
Implements Student's t-distribution p-values using the regularized
incomplete beta function.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence


class TestType(Enum):
    ONE_SAMPLE = "one_sample_t"
    INDEPENDENT_WELCH = "independent_welch_t"
    INDEPENDENT_POOLED = "independent_pooled_t"
    PAIRED = "paired_t"


@dataclass
class TestResult:
    test_name: str
    statistic: float
    degrees_of_freedom: float
    p_value: float
    alpha: float
    significant: bool
    sample_size: int
    mean_difference: float
    confidence: str
    interpretation: str

    def to_dict(self) -> dict:
        return asdict(self)


def validate_sample(data: Sequence[float], name: str = "sample") -> list[float]:
    if isinstance(data, (str, bytes)) or len(data) < 2:
        raise ValueError(f"{name} must contain at least two observations.")

    values = [float(value) for value in data]

    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{name} contains invalid numeric observations.")

    return values


def mean(data: Sequence[float]) -> float:
    return math.fsum(data) / len(data)


def sample_variance(data: Sequence[float]) -> float:
    if len(data) < 2:
        raise ValueError("At least two observations are required.")

    average = mean(data)
    return math.fsum((x - average) ** 2 for x in data) / (len(data) - 1)


def standard_deviation(data: Sequence[float]) -> float:
    return math.sqrt(sample_variance(data))


def validate_alpha(alpha: float) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError("Alpha must be between zero and one.")


# Lanczos approximation for the logarithm of the gamma function.
def log_gamma(z: float) -> float:
    coefficients = [
        676.5203681218851,
        -1259.1392167224028,
        771.3234287776531,
        -176.6150291621406,
        12.507343278686905,
        -0.13857109526572012,
        9.984369578019572e-6,
        1.5056327351493116e-7,
    ]

    if z < 0.5:
        return (
            math.log(math.pi)
            - math.log(abs(math.sin(math.pi * z)))
            - log_gamma(1.0 - z)
        )

    z -= 1.0
    x = 0.99999999999980993

    for i, coefficient in enumerate(coefficients):
        x += coefficient / (z + i + 1.0)

    t = z + 7.5

    return (
        0.5 * math.log(2.0 * math.pi)
        + (z + 0.5) * math.log(t)
        - t
        + math.log(x)
    )


def beta_continued_fraction(a: float, b: float, x: float) -> float:
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

        aa = m * (b - m) * x / (
            (qam + m2) * (a + m2)
        )

        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny

        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny

        d = 1.0 / d
        h *= d * c

        aa = -((a + m) * (qab + m) * x) / (
            (a + m2) * (qap + m2)
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

    raise ArithmeticError("Incomplete beta calculation did not converge.")


def regularized_beta(x: float, a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        raise ValueError("Beta parameters must be positive.")

    if x <= 0:
        return 0.0

    if x >= 1:
        return 1.0

    log_front = (
        log_gamma(a + b)
        - log_gamma(a)
        - log_gamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )

    front = math.exp(log_front)

    if x < (a + 1.0) / (a + b + 2.0):
        return front * beta_continued_fraction(a, b, x) / a

    return 1.0 - (
        front * beta_continued_fraction(b, a, 1.0 - x) / b
    )


def student_t_p_value(statistic: float, df: float) -> float:
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")

    x = df / (df + statistic * statistic)

    return regularized_beta(x, df / 2.0, 0.5)


def create_result(
    test_name: str,
    statistic: float,
    df: float,
    p_value: float,
    alpha: float,
    sample_size: int,
    difference: float,
) -> TestResult:

    significant = p_value < alpha

    interpretation = (
        "Reject the null hypothesis."
        if significant
        else "Fail to reject the null hypothesis."
    )

    return TestResult(
        test_name=test_name,
        statistic=statistic,
        degrees_of_freedom=df,
        p_value=p_value,
        alpha=alpha,
        significant=significant,
        sample_size=sample_size,
        mean_difference=difference,
        confidence=f"{(1 - alpha) * 100:.1f}%",
        interpretation=interpretation,
    )


def one_sample_t_test(
    sample: Sequence[float],
    population_mean: float,
    alpha: float = 0.05,
) -> TestResult:
    data = validate_sample(sample)
    validate_alpha(alpha)

    if not math.isfinite(population_mean):
        raise ValueError("Population mean must be finite.")

    n = len(data)
    average = mean(data)
    variance = sample_variance(data)

    if variance == 0:
        if average == population_mean:
            raise ValueError("Zero variance produces an undefined t-statistic.")

        statistic = math.copysign(math.inf, average - population_mean)
        p_value = 0.0
    else:
        statistic = (average - population_mean) / math.sqrt(variance / n)
        p_value = student_t_p_value(statistic, n - 1)

    return create_result(
        TestType.ONE_SAMPLE.value,
        statistic,
        n - 1,
        p_value,
        alpha,
        n,
        average - population_mean,
    )


def independent_t_test(
    group_a: Sequence[float],
    group_b: Sequence[float],
    equal_variance: bool = False,
    alpha: float = 0.05,
) -> TestResult:
    a = validate_sample(group_a, "group_a")
    b = validate_sample(group_b, "group_b")
    validate_alpha(alpha)

    n1, n2 = len(a), len(b)
    m1, m2 = mean(a), mean(b)
    v1, v2 = sample_variance(a), sample_variance(b)

    difference = m1 - m2

    if equal_variance:
        df = n1 + n2 - 2

        pooled_variance = (
            ((n1 - 1) * v1 + (n2 - 1) * v2) / df
        )

        standard_error = math.sqrt(
            pooled_variance * (1 / n1 + 1 / n2)
        )

        test_name = TestType.INDEPENDENT_POOLED.value

    else:
        term1 = v1 / n1
        term2 = v2 / n2

        standard_error = math.sqrt(term1 + term2)

        denominator = (
            term1 ** 2 / (n1 - 1)
            + term2 ** 2 / (n2 - 1)
        )

        if denominator == 0:
            raise ValueError("Welch degrees of freedom are undefined.")

        df = (term1 + term2) ** 2 / denominator

        test_name = TestType.INDEPENDENT_WELCH.value

    if standard_error == 0:
        if difference == 0:
            raise ValueError("Both groups have identical zero variance.")
        statistic = math.copysign(math.inf, difference)
        p_value = 0.0
    else:
        statistic = difference / standard_error
        p_value = student_t_p_value(statistic, df)

    return create_result(
        test_name,
        statistic,
        df,
        p_value,
        alpha,
        n1 + n2,
        difference,
    )


def paired_t_test(
    before: Sequence[float],
    after: Sequence[float],
    alpha: float = 0.05,
) -> TestResult:
    x = validate_sample(before, "before")
    y = validate_sample(after, "after")
    validate_alpha(alpha)

    if len(x) != len(y):
        raise ValueError("Paired samples must have equal lengths.")

    differences = [post - pre for pre, post in zip(x, y)]

    n = len(differences)
    average_difference = mean(differences)
    variance = sample_variance(differences)

    if variance == 0:
        if average_difference == 0:
            raise ValueError("All paired differences are zero.")
        statistic = math.copysign(math.inf, average_difference)
        p_value = 0.0
    else:
        statistic = average_difference / math.sqrt(variance / n)
        p_value = student_t_p_value(statistic, n - 1)

    return create_result(
        TestType.PAIRED.value,
        statistic,
        n - 1,
        p_value,
        alpha,
        n,
        average_difference,
    )


class StatisticalTestRunner:
    """Collect and export reproducible statistical test results."""

    def __init__(self, alpha: float = 0.05):
        validate_alpha(alpha)
        self.alpha = alpha
        self.results: list[TestResult] = []

    def execute(self, function, *args, **kwargs) -> TestResult:
        kwargs.setdefault("alpha", self.alpha)
        result = function(*args, **kwargs)
        self.results.append(result)
        return result

    def export_json(self, filename: str) -> None:
        path = Path(filename)
        path.write_text(
            json.dumps(
                [result.to_dict() for result in self.results],
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )

    def export_csv(self, filename: str) -> None:
        if not self.results:
            raise ValueError("No results available for export.")

        with Path(filename).open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(self.results[0].to_dict().keys()),
            )
            writer.writeheader()

            for result in self.results:
                writer.writerow(result.to_dict())

    def report(self) -> None:
        for result in self.results:
            print(f"\n{result.test_name}")
            print(f"t-statistic: {result.statistic:.6f}")
            print(f"Degrees of freedom: {result.degrees_of_freedom:.4f}")
            print(f"p-value: {result.p_value:.8g}")
            print(f"Alpha: {result.alpha}")
            print(f"Mean difference: {result.mean_difference:.6f}")
            print(result.interpretation)


def run_examples() -> None:
    runner = StatisticalTestRunner(alpha=0.05)

    # One-sample: test whether average delivery time differs from 30.
    delivery_times = [28, 31, 29, 32, 30, 27, 34, 31, 29, 30]

    runner.execute(
        one_sample_t_test,
        delivery_times,
        population_mean=30,
    )

    # Independent groups: compare two separate training methods.
    method_a = [72, 75, 78, 74, 71, 80, 77, 76]
    method_b = [81, 84, 79, 86, 82, 83, 85, 80]

    runner.execute(
        independent_t_test,
        method_a,
        method_b,
        equal_variance=False,
    )

    # Pooled independent test: assumes equal population variances.
    runner.execute(
        independent_t_test,
        method_a,
        method_b,
        equal_variance=True,
    )

    # Paired: compare employee performance before and after training.
    before = [65, 70, 72, 68, 75, 71, 69, 73]
    after = [72, 74, 76, 75, 79, 76, 74, 78]

    runner.execute(paired_t_test, before, after)

    runner.report()

    print("\nExporting results...")
    runner.export_json("statistical_results.json")
    runner.export_csv("statistical_results.csv")

    # Basic numerical validation.
    assert abs(student_t_p_value(0.0, 10) - 1.0) < 1e-10
    assert 0.0 <= student_t_p_value(2.0, 10) <= 1.0

    # Input failure validation.
    try:
        one_sample_t_test([1.0], 2.0)
    except ValueError as error:
        print(f"Expected validation error: {error}")

    try:
        paired_t_test([1, 2, 3], [2, 3])
    except ValueError as error:
        print(f"Expected validation error: {error}")


if __name__ == "__main__":
    run_examples()
