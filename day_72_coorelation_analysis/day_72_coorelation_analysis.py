#!/usr/bin/env python3
"""
Correlation Analysis
Pearson, Spearman, Kendall, partial correlation, permutation testing,
confounding, spurious correlation, CSV analysis, and validation.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence


class CorrelationMethod(Enum):
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"


class AnalysisError(Exception):
    """Base exception for correlation analysis."""


class ValidationError(AnalysisError):
    """Raised when input data violates analysis requirements."""


class InsufficientDataError(AnalysisError):
    """Raised when insufficient valid observations are available."""


@dataclass(frozen=True)
class CorrelationResult:
    method: str
    coefficient: float
    sample_size: int
    interpretation: str
    assumptions_warning: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PermutationResult:
    observed_correlation: float
    p_value: float
    permutations: int
    significant_at_05: bool


def validate_data(
    x: Sequence[float],
    y: Sequence[float],
    minimum: int = 3
) -> tuple[list[float], list[float]]:
    """Validate paired observations and perform pairwise deletion."""

    if len(x) != len(y):
        raise ValidationError("Both variables must have equal lengths.")

    if minimum < 2:
        raise ValidationError("Minimum sample size must be at least 2.")

    clean_x, clean_y = [], []

    for a, b in zip(x, y):
        if a is None or b is None:
            continue

        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            raise ValidationError("Observations must be numeric.")

        if not math.isfinite(a) or not math.isfinite(b):
            raise ValidationError("Infinite and NaN values are invalid.")

        clean_x.append(a)
        clean_y.append(b)

    if len(clean_x) < minimum:
        raise InsufficientDataError(
            f"Need at least {minimum} valid paired observations; "
            f"received {len(clean_x)}."
        )

    return clean_x, clean_y


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    """Calculate Pearson's product-moment correlation."""

    x, y = validate_data(x, y)

    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)

    numerator = sum(
        (a - mean_x) * (b - mean_y)
        for a, b in zip(x, y)
    )

    sum_x = sum((a - mean_x) ** 2 for a in x)
    sum_y = sum((b - mean_y) ** 2 for b in y)

    denominator = math.sqrt(sum_x * sum_y)

    if denominator == 0:
        raise ValidationError(
            "Pearson correlation is undefined for constant variables."
        )

    return max(-1.0, min(1.0, numerator / denominator))


def average_ranks(values: Sequence[float]) -> list[float]:
    """
    Assign average ranks to tied observations.

    Example:
    [10, 20, 20, 40] -> [1, 2.5, 2.5, 4]
    """

    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)

    i = 0

    while i < len(indexed):
        j = i + 1

        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1

        average = (i + 1 + j) / 2.0

        for k in range(i, j):
            original_index = indexed[k][0]
            ranks[original_index] = average

        i = j

    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Calculate Spearman's rank correlation with tie handling."""

    x, y = validate_data(x, y)

    rank_x = average_ranks(x)
    rank_y = average_ranks(y)

    return pearson(rank_x, rank_y)


def kendall_tau_b(
    x: Sequence[float],
    y: Sequence[float]
) -> float:
    """
    Calculate Kendall's tau-b.

    Handles ties independently in both variables.
    Time complexity: O(n^2).
    """

    x, y = validate_data(x)

    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0

    n = len(x)

    for i in range(n):
        for j in range(i + 1, n):

            dx = (x[i] > x[j]) - (x[i] < x[j])
            dy = (y[i] > y[j]) - (y[i] < y[j])

            if dx == 0 and dy == 0:
                continue

            if dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif dx == dy:
                concordant += 1
            else:
                discordant += 1

    denominator = math.sqrt(
        (concordant + discordant + ties_x) *
        (concordant + discordant + ties_y)
    )

    if denominator == 0:
        raise ValidationError(
            "Kendall tau-b is undefined for constant variables."
        )

    return (concordant - discordant) / denominator


def interpret_correlation(value: float) -> str:
    """Provide a descriptive interpretation, not a significance claim."""

    magnitude = abs(value)

    if magnitude < 0.10:
        strength = "negligible"
    elif magnitude < 0.30:
        strength = "weak"
    elif magnitude < 0.50:
        strength = "moderate"
    elif magnitude < 0.70:
        strength = "strong"
    else:
        strength = "very strong"

    direction = (
        "positive" if value > 0
        else "negative" if value < 0
        else "neutral"
    )

    return f"{strength} {direction} association"


def analyze(
    x: Sequence[float],
    y: Sequence[float]
) -> list[CorrelationResult]:
    """Execute three complementary correlation analyses."""

    clean_x, clean_y = validate_data(x, y)

    methods = [
        (CorrelationMethod.PEARSON, pearson),
        (CorrelationMethod.SPEARMAN, spearman),
        (CorrelationMethod.KENDALL, kendall_tau_b),
    ]

    results = []

    warnings = {
        "pearson": (
            "Measures linear association; sensitive to outliers."
        ),
        "spearman": (
            "Measures monotonic rank association; does not establish causation."
        ),
        "kendall": (
            "Measures ordinal concordance; computationally quadratic here."
        ),
    }

    for method, function in methods:
        coefficient = function(clean_x, clean_y)

        results.append(
            CorrelationResult(
                method=method.value,
                coefficient=round(coefficient, 6),
                sample_size=len(clean_x),
                interpretation=interpret_correlation(coefficient),
                assumptions_warning=warnings[method.value],
            )
        )

    return results


def permutation_test(
    x: Sequence[float],
    y: Sequence[float],
    permutations: int = 2000,
    seed: int = 42
) -> PermutationResult:
    """
    Two-sided permutation test for Pearson correlation.

    The null hypothesis is exchangeability of y relative to x.
    The +1 correction prevents a zero estimated p-value.
    """

    x, y = validate_data(x, y)

    if permutations < 100:
        raise ValidationError("Use at least 100 permutations.")

    observed = pearson(x, y)
    rng = random.Random(seed)

    extreme = 0
    shuffled = list(y)

    for _ in range(permutations):
        rng.shuffle(shuffled)

        simulated = pearson(x, shuffled)

        if abs(simulated) >= abs(observed):
            extreme += 1

    p_value = (extreme + 1) / (permutations + 1)

    return PermutationResult(
        observed_correlation=observed,
        p_value=p_value,
        permutations=permutations,
        significant_at_05=p_value < 0.05,
    )


def residualize(
    values: Sequence[float],
    confounder: Sequence[float]
) -> list[float]:
    """Remove a fitted linear effect of one confounding variable."""

    if len(values) != len(confounder):
        raise ValidationError("Confounder length mismatch.")

    mean_v = statistics.fmean(values)
    mean_z = statistics.fmean(confounder)

    denominator = sum((z - mean_z) ** 2 for z in confounder)

    if denominator == 0:
        raise ValidationError("Confounder is constant.")

    slope = sum(
        (z - mean_z) * (v - mean_v)
        for z, v in zip(confounder, values)
    ) / denominator

    intercept = mean_v - slope * mean_z

    return [
        value - (intercept + slope * z)
        for value, z in zip(values, confounder)
    ]


def partial_correlation(
    x: Sequence[float],
    y: Sequence[float],
    z: Sequence[float]
) -> float:
    """
    First-order partial Pearson correlation.

    Measures the linear association between residualized x and y
    after removing their linear relationships with z.
    """

    x, y = validate_data(x, y)

    if len(z) != len(x):
        raise ValidationError("Confounder length mismatch.")

    clean_z = [float(value) for value in z]

    if not all(math.isfinite(value) for value in clean_z):
        raise ValidationError("Confounder contains invalid values.")

    rx = residualize(x, clean_z)
    ry = residualize(y, clean_z)

    return pearson(rx, ry)


def generate_confounded_data(
    size: int = 100,
    seed: int = 42
) -> tuple[list[float], list[float], list[float]]:
    """
    Generate two variables primarily driven by a shared confounder.
    Their apparent raw correlation can be much stronger than
    their adjusted partial correlation.
    """

    if size < 10:
        raise ValidationError("Use at least 10 observations.")

    rng = random.Random(seed)

    z = [float(i) for i in range(size)]

    x = [
        3.0 * value + rng.gauss(0, 8)
        for value in z
    ]

    y = [
        2.5 * value + rng.gauss(0, 8)
        for value in z
    ]

    return x, y, z


def generate_spurious_trends(
    size: int = 100,
    seed: int = 42
) -> tuple[list[float], list[float]]:
    """
    Generate unrelated noise series with a common time trend.

    The raw correlation may be high even though the independent
    noise components have no designed relationship.
    """

    if size < 10:
        raise ValidationError("Use at least 10 observations.")

    rng = random.Random(seed)

    trend = [i * 0.5 for i in range(size)]

    x = [
        t + rng.gauss(0, 5)
        for t in trend
    ]

    y = [
        t + rng.gauss(0, 5)
        for t in trend
    ]

    return x, y


def analyze_csv(
    path: Path,
    x_column: str,
    y_column: str
) -> list[CorrelationResult]:
    """Read numeric variables from a CSV file."""

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    x, y = [], []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValidationError("CSV requires a header row.")

        if x_column not in reader.fieldnames:
            raise ValidationError(f"Missing column: {x_column}")

        if y_column not in reader.fieldnames:
            raise ValidationError(f"Missing column: {y_column}")

        for row_number, row in enumerate(reader, start=2):
            a = row[x_column]
            b = row[y_column]

            if not a or not b:
                x.append(None)
                y.append(None)
                continue

            try:
                x.append(float(a))
                y.append(float(b))
            except ValueError as exc:
                raise ValidationError(
                    f"Invalid numeric value on CSV row {row_number}."
                ) from exc

    return analyze(x, y)


def run_demonstration() -> dict:
    """Execute deterministic educational scenarios."""

    linear_x = [1, 2, 3, 4, 5, 6]
    linear_y = [2, 4, 6, 8, 10, 12]

    nonlinear_x = [1, 2, 3, 4, 5, 6]
    nonlinear_y = [1, 4, 9, 16, 25, 36]

    tied_x = [1, 2, 2, 4, 5, 5]
    tied_y = [2, 1, 3, 4, 4, 6]

    x, y, z = generate_confounded_data()

    trend_x, trend_y = generate_spurious_trends()

    permutation = permutation_test(
        linear_x,
        linear_y,
        permutations=1000,
    )

    return {
        "perfect_linear_relationship": [
            result.to_dict()
            for result in analyze(linear_x, linear_y)
        ],
        "nonlinear_monotonic_relationship": [
            result.to_dict()
            for result in analyze(nonlinear_x, nonlinear_y)
        ],
        "tied_observations": [
            result.to_dict()
            for result in analyze(tied_x, tied_y)
        ],
        "permutation_test": asdict(permutation),
        "confounding_analysis": {
            "raw_pearson": round(pearson(x, y), 6),
            "partial_pearson": round(
                partial_correlation(x, y, z), 6
            ),
        },
        "spurious_trend_example": {
            "raw_pearson": round(pearson(trend_x, trend_y), 6),
            "warning": (
                "Common trends can produce misleading correlation. "
                "Examine detrended series and time-series properties."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Statistical correlation analysis"
    )

    parser.add_argument("--csv", type=Path)
    parser.add_argument("--x", default="x")
    parser.add_argument("--y", default="y")

    args = parser.parse_args()

    try:
        if args.csv:
            results = [
                result.to_dict()
                for result in analyze_csv(args.csv, args.x, args.y)
            ]
            print(json.dumps(results, indent=2))
        else:
            print(json.dumps(run_demonstration(), indent=2))

        # Fundamental correctness checks.
        assert math.isclose(
            pearson([1, 2, 3], [2, 4, 6]), 1.0
        )

        assert math.isclose(
            spearman([1, 2, 3], [1, 4, 9]), 1.0
        )

        assert math.isclose(
            kendall_tau_b([1, 2, 3], [1, 4, 9]), 1.0
        )

        assert average_ranks([1, 2, 2, 4]) == [
            1.0, 2.5, 2.5, 4.0
        ]

    except (AnalysisError, OSError, ValueError) as exc:
        print(
            json.dumps({
                "error": type(exc).__name__,
                "message": str(exc),
            }),
            flush=True,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
