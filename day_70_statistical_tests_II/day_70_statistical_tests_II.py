#!/usr/bin/env python3
"""
Statistical Tests II
Chi-square goodness-of-fit, chi-square independence,
one-sample proportion tests, and two-sample proportion tests.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import json
import math
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence, Any


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("statistical_tests")


class StatisticalTestError(ValueError):
    """Raised when statistical test inputs are invalid."""


class TestType(Enum):
    GOODNESS_OF_FIT = "chi_square_goodness_of_fit"
    INDEPENDENCE = "chi_square_independence"
    ONE_PROPORTION = "one_sample_proportion"
    TWO_PROPORTION = "two_sample_proportion"


@dataclass(frozen=True)
class TestResult:
    test_name: str
    statistic: float
    degrees_of_freedom: int
    p_value: float
    alpha: float
    reject_null: bool
    interpretation: str
    sample_size: int
    effect_size: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_alpha(alpha: float) -> None:
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise StatisticalTestError(
            "Significance level must be between 0 and 1."
        )


def validate_counts(values: Sequence[int], name: str) -> None:
    if not values:
        raise StatisticalTestError(f"{name} cannot be empty.")

    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise StatisticalTestError(
                f"{name} must contain integer counts."
            )
        if value < 0:
            raise StatisticalTestError(
                f"{name} cannot contain negative counts."
            )


def regularized_gamma_q(a: float, x: float) -> float:
    """
    Calculate the regularized upper incomplete gamma function Q(a, x).

    Uses a convergent series for x < a + 1 and a continued
    fraction for x >= a + 1.
    """
    if a <= 0 or x < 0:
        raise StatisticalTestError("Invalid gamma function arguments.")

    if x == 0:
        return 1.0

    if math.isinf(x):
        return 0.0

    if x < a + 1:
        ap = a
        term = 1.0 / a
        total = term

        for _ in range(10000):
            ap += 1
            term *= x / ap
            total += term

            if abs(term) < abs(total) * 1e-14:
                break
        else:
            raise ArithmeticError("Gamma series failed to converge.")

        p = total * math.exp(
            -x + a * math.log(x) - math.lgamma(a)
        )
        return min(1.0, max(0.0, 1.0 - p))

    b = x + 1.0 - a
    c = 1e300
    d = 1.0 / b
    h = d

    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0

        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300

        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300

        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < 1e-14:
            break
    else:
        raise ArithmeticError(
            "Gamma continued fraction failed to converge."
        )

    result = math.exp(
        -x + a * math.log(x) - math.lgamma(a)
    ) * h

    return min(1.0, max(0.0, result))


def chi_square_p_value(
    statistic: float,
    degrees_of_freedom: int
) -> float:
    if statistic < 0 or not math.isfinite(statistic):
        raise StatisticalTestError("Invalid chi-square statistic.")

    if degrees_of_freedom <= 0:
        raise StatisticalTestError(
            "Degrees of freedom must be positive."
        )

    return regularized_gamma_q(
        degrees_of_freedom / 2.0,
        statistic / 2.0
    )


def chi_square_goodness_of_fit(
    observed: Sequence[int],
    expected: Sequence[float],
    alpha: float = 0.05
) -> TestResult:
    """
    Test whether observed categorical frequencies match
    a specified theoretical distribution.
    """
    validate_alpha(alpha)
    validate_counts(observed, "Observed frequencies")

    if len(observed) != len(expected) or len(observed) < 2:
        raise StatisticalTestError(
            "Observed and expected arrays must have equal "
            "length and at least two categories."
        )

    if any(
        not math.isfinite(value) or value <= 0
        for value in expected
    ):
        raise StatisticalTestError(
            "Expected frequencies must be positive and finite."
        )

    total_observed = sum(observed)
    total_expected = sum(expected)

    if total_observed == 0:
        raise StatisticalTestError("Sample size must be positive.")

    if not math.isclose(
        total_observed,
        total_expected,
        rel_tol=1e-9,
        abs_tol=1e-9
    ):
        raise StatisticalTestError(
            "Expected frequencies must sum to observed sample size."
        )

    statistic = sum(
        (o - e) ** 2 / e
        for o, e in zip(observed, expected)
    )

    df = len(observed) - 1
    p_value = chi_square_p_value(statistic, df)

    return TestResult(
        test_name=TestType.GOODNESS_OF_FIT.value,
        statistic=statistic,
        degrees_of_freedom=df,
        p_value=p_value,
        alpha=alpha,
        reject_null=p_value < alpha,
        interpretation=(
            "Observed frequencies significantly differ from "
            "the expected distribution."
            if p_value < alpha else
            "Insufficient evidence that observed frequencies "
            "differ from the expected distribution."
        ),
        sample_size=total_observed,
        effect_size=math.sqrt(statistic / total_observed)
    )


def chi_square_independence(
    table: Sequence[Sequence[int]],
    alpha: float = 0.05,
    yates_correction: bool = False
) -> TestResult:
    """
    Test independence between two categorical variables.

    Rows represent the first variable.
    Columns represent the second variable.
    """
    validate_alpha(alpha)

    if len(table) < 2:
        raise StatisticalTestError("At least two rows are required.")

    column_count = len(table[0])

    if column_count < 2:
        raise StatisticalTestError(
            "At least two columns are required."
        )

    for row in table:
        if len(row) != column_count:
            raise StatisticalTestError(
                "Contingency table must be rectangular."
            )
        validate_counts(row, "Contingency table")

    row_totals = [sum(row) for row in table]
    column_totals = [
        sum(table[i][j] for i in range(len(table)))
        for j in range(column_count)
    ]

    grand_total = sum(row_totals)

    if grand_total == 0:
        raise StatisticalTestError("Contingency table is empty.")

    if any(value == 0 for value in row_totals + column_totals):
        raise StatisticalTestError(
            "Every row and column must contain observations."
        )

    statistic = 0.0
    expected_values = []

    for i in range(len(table)):
        for j in range(column_count):
            expected = (
                row_totals[i] * column_totals[j] / grand_total
            )
            expected_values.append(expected)

            difference = abs(table[i][j] - expected)

            if yates_correction and len(table) == 2 and column_count == 2:
                difference = max(0.0, difference - 0.5)

            statistic += difference ** 2 / expected

    df = (len(table) - 1) * (column_count - 1)
    p_value = chi_square_p_value(statistic, df)

    minimum_expected = min(expected_values)

    # Cramer's V measures association strength.
    cramer_v = math.sqrt(
        statistic / (
            grand_total * min(len(table) - 1, column_count - 1)
        )
    )

    return TestResult(
        test_name=TestType.INDEPENDENCE.value,
        statistic=statistic,
        degrees_of_freedom=df,
        p_value=p_value,
        alpha=alpha,
        reject_null=p_value < alpha,
        interpretation=(
            "Evidence of an association between the variables."
            if p_value < alpha else
            "Insufficient evidence of an association between "
            "the variables."
        ) + (
            " Warning: at least one expected cell count is below 5."
            if minimum_expected < 5 else ""
        ),
        sample_size=grand_total,
        effect_size=cramer_v
    )


def normal_two_sided_p_value(z_score: float) -> float:
    return math.erfc(abs(z_score) / math.sqrt(2.0))


def one_sample_proportion_test(
    successes: int,
    trials: int,
    hypothesized_proportion: float,
    alpha: float = 0.05
) -> TestResult:
    """
    Large-sample one-proportion z-test.

    H0: p = p0
    H1: p != p0
    """
    validate_alpha(alpha)

    if (
        isinstance(successes, bool)
        or isinstance(trials, bool)
        or not isinstance(successes, int)
        or not isinstance(trials, int)
    ):
        raise StatisticalTestError("Counts must be integers.")

    if trials <= 0 or not 0 <= successes <= trials:
        raise StatisticalTestError("Invalid success or trial count.")

    if not 0 < hypothesized_proportion < 1:
        raise StatisticalTestError(
            "Hypothesized proportion must be strictly between 0 and 1."
        )

    p0 = hypothesized_proportion
    observed = successes / trials
    standard_error = math.sqrt(p0 * (1 - p0) / trials)

    if standard_error == 0:
        raise StatisticalTestError("Standard error is zero.")

    z = (observed - p0) / standard_error
    p_value = normal_two_sided_p_value(z)

    return TestResult(
        test_name=TestType.ONE_PROPORTION.value,
        statistic=z,
        degrees_of_freedom=0,
        p_value=p_value,
        alpha=alpha,
        reject_null=p_value < alpha,
        interpretation=(
            "Observed proportion significantly differs from "
            "the hypothesized proportion."
            if p_value < alpha else
            "Insufficient evidence of a difference from the "
            "hypothesized proportion."
        ),
        sample_size=trials,
        effect_size=observed - p0
    )


def two_sample_proportion_test(
    successes_a: int,
    trials_a: int,
    successes_b: int,
    trials_b: int,
    alpha: float = 0.05
) -> TestResult:
    """
    Two-sided pooled two-proportion z-test.

    H0: p1 = p2
    H1: p1 != p2
    """
    validate_alpha(alpha)

    values = (
        successes_a, trials_a,
        successes_b, trials_b
    )

    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in values
    ):
        raise StatisticalTestError("Counts must be integers.")

    if (
        trials_a <= 0 or trials_b <= 0
        or not 0 <= successes_a <= trials_a
        or not 0 <= successes_b <= trials_b
    ):
        raise StatisticalTestError("Invalid group counts.")

    pooled = (
        (successes_a + successes_b)
        / (trials_a + trials_b)
    )

    if pooled in (0, 1):
        raise StatisticalTestError(
            "Pooled variance is zero."
        )

    p_a = successes_a / trials_a
    p_b = successes_b / trials_b

    standard_error = math.sqrt(
        pooled * (1 - pooled)
        * (1 / trials_a + 1 / trials_b)
    )

    z = (p_a - p_b) / standard_error
    p_value = normal_two_sided_p_value(z)

    return TestResult(
        test_name=TestType.TWO_PROPORTION.value,
        statistic=z,
        degrees_of_freedom=0,
        p_value=p_value,
        alpha=alpha,
        reject_null=p_value < alpha,
        interpretation=(
            "The two population proportions significantly differ."
            if p_value < alpha else
            "Insufficient evidence of a difference between "
            "the two population proportions."
        ),
        sample_size=trials_a + trials_b,
        effect_size=p_a - p_b
    )


class StatisticalAnalysis:
    """Organizes tests and exports reproducible results."""

    def __init__(self, alpha: float = 0.05):
        validate_alpha(alpha)
        self.alpha = alpha
        self.results: list[TestResult] = []

    def run(self, test_function, *args, **kwargs) -> TestResult:
        kwargs.setdefault("alpha", self.alpha)
        result = test_function(*args, **kwargs)
        self.results.append(result)
        logger.info(
            "%s completed: statistic=%.6f, p=%.8f",
            result.test_name,
            result.statistic,
            result.p_value
        )
        return result

    def export_json(self, filename: str = "statistical_results.json"):
        path = Path(filename)

        # Prevent accidental writes through directory traversal.
        if path.name != str(path) or path.name in ("", ".", ".."):
            raise StatisticalTestError("Invalid export filename.")

        path.write_text(
            json.dumps(
                [result.to_dict() for result in self.results],
                indent=4
            ),
            encoding="utf-8"
        )

        logger.info("Results exported to %s", path.resolve())


def run_examples() -> None:
    analysis = StatisticalAnalysis(alpha=0.05)

    print("\n1. CHI-SQUARE GOODNESS-OF-FIT")

    goodness = analysis.run(
        chi_square_goodness_of_fit,
        observed=[48, 52, 45, 55],
        expected=[50, 50, 50, 50]
    )
    print(goodness)

    print("\n2. CHI-SQUARE TEST OF INDEPENDENCE")

    independence = analysis.run(
        chi_square_independence,
        table=[
            [40, 20],
            [15, 45]
        ]
    )
    print(independence)

    print("\n3. CHI-SQUARE TEST WITH YATES CORRECTION")

    corrected = analysis.run(
        chi_square_independence,
        table=[
            [40, 20],
            [15, 45]
        ],
        yates_correction=True
    )
    print(corrected)

    print("\n4. ONE-SAMPLE PROPORTION TEST")

    one_prop = analysis.run(
        one_sample_proportion_test,
        successes=120,
        trials=200,
        hypothesized_proportion=0.50
    )
    print(one_prop)

    print("\n5. TWO-SAMPLE PROPORTION TEST")

    two_prop = analysis.run(
        two_sample_proportion_test,
        successes_a=140,
        trials_a=200,
        successes_b=110,
        trials_b=200
    )
    print(two_prop)

    print("\n6. AUTOMATED STATISTICAL REPORT")

    for result in analysis.results:
        print(
            f"{result.test_name}: "
            f"statistic={result.statistic:.4f}, "
            f"p={result.p_value:.6f}, "
            f"reject={result.reject_null}"
        )

    analysis.export_json()


def run_tests() -> None:
    # Reference values and important edge cases.
    assert abs(
        chi_square_p_value(3.8414588207, 1) - 0.05
    ) < 1e-7

    result = chi_square_goodness_of_fit(
        [50, 50], [50, 50]
    )
    assert result.statistic == 0
    assert result.p_value == 1

    result = chi_square_independence(
        [[10, 10], [10, 10]]
    )
    assert result.statistic == 0

    result = one_sample_proportion_test(
        50, 100, 0.5
    )
    assert result.statistic == 0

    result = two_sample_proportion_test(
        50, 100, 50, 100
    )
    assert result.statistic == 0

    for invalid_operation in (
        lambda: chi_square_goodness_of_fit(
            [10, 20], [15, 15]
        ),
        lambda: chi_square_independence(
            [[10, 0], [0, 0]]
        ),
        lambda: one_sample_proportion_test(
            110, 100, 0.5
        ),
        lambda: two_sample_proportion_test(
            50, 100, 50, 0
        )
    ):
        try:
            invalid_operation()
        except StatisticalTestError:
            pass
        else:
            raise AssertionError("Invalid input was accepted.")

    print("All statistical tests passed.")


if __name__ == "__main__":
    run_tests()
    run_examples()
