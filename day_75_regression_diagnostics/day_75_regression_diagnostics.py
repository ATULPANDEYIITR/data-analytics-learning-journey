#!/usr/bin/env python3
"""
Regression Diagnostics
======================

Implements:
1. Ordinary Least Squares (OLS)
2. Multicollinearity diagnostics: correlation matrix and VIF
3. Heteroscedasticity: Breusch-Pagan test
4. Residual analysis: normality indicators and residual patterns
5. Influence diagnostics: leverage, studentized residuals, Cook's distance
6. HC3 heteroscedasticity-consistent covariance estimation
7. Diagnostic warnings and automated model assessment

Dependencies: Python 3.10+
External dependencies: None
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class DiagnosticStatus(Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class RegressionError(Exception):
    pass


@dataclass
class Observation:
    identifier: str
    features: list[float]
    target: float


@dataclass
class DiagnosticThresholds:
    vif_warning: float = 5.0
    vif_critical: float = 10.0
    cook_warning: float = 4.0
    leverage_multiplier: float = 2.0
    studentized_limit: float = 3.0
    bp_significance: float = 0.05


@dataclass
class DiagnosticResult:
    name: str
    statistic: float
    threshold: float
    status: DiagnosticStatus
    explanation: str


def validate_observations(
    observations: list[Observation],
    feature_count: int
) -> None:
    if not observations:
        raise RegressionError("Dataset cannot be empty.")

    if feature_count < 1:
        raise RegressionError("At least one predictor is required.")

    if len(observations) <= feature_count + 1:
        raise RegressionError(
            "Insufficient observations for regression diagnostics."
        )

    identifiers = set()

    for observation in observations:
        if observation.identifier in identifiers:
            raise RegressionError("Duplicate observation identifier.")

        identifiers.add(observation.identifier)

        if len(observation.features) != feature_count:
            raise RegressionError("Inconsistent feature dimensions.")

        values = observation.features + [observation.target]

        if not all(math.isfinite(value) for value in values):
            raise RegressionError("Dataset contains non-finite values.")


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def solve_linear_system(
    matrix: list[list[float]],
    vector: list[float]
) -> list[float]:
    """Gaussian elimination with partial pivoting."""

    n = len(vector)

    if n == 0 or len(matrix) != n:
        raise RegressionError("Invalid linear system.")

    augmented = [
        list(matrix[i]) + [vector[i]]
        for i in range(n)
    ]

    for col in range(n):
        pivot = max(
            range(col, n),
            key=lambda row: abs(augmented[row][col])
        )

        if abs(augmented[pivot][col]) < 1e-12:
            raise RegressionError(
                "Singular matrix. Check for perfect multicollinearity."
            )

        augmented[col], augmented[pivot] = (
            augmented[pivot],
            augmented[col]
        )

        pivot_value = augmented[col][col]

        for j in range(col, n + 1):
            augmented[col][j] /= pivot_value

        for row in range(n):
            if row == col:
                continue

            factor = augmented[row][col]

            for j in range(col, n + 1):
                augmented[row][j] -= (
                    factor * augmented[col][j]
                )

    return [augmented[i][n] for i in range(n)]


def matrix_inverse(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)

    columns = []

    for col in range(n):
        unit = [0.0] * n
        unit[col] = 1.0
        columns.append(
            solve_linear_system(matrix, unit)
        )

    return [
        [columns[j][i] for j in range(n)]
        for i in range(n)
    ]


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in zip(*matrix)]


def matrix_multiply(
    a: list[list[float]],
    b: list[list[float]]
) -> list[list[float]]:
    bt = transpose(b)

    return [
        [dot(row, column) for column in bt]
        for row in a
    ]


def mean(values: list[float]) -> float:
    return statistics.fmean(values)


def variance(values: list[float]) -> float:
    center = mean(values)

    return sum(
        (value - center) ** 2 for value in values
    ) / len(values)


def correlation(a: list[float], b: list[float]) -> float:
    mean_a = mean(a)
    mean_b = mean(b)

    numerator = sum(
        (x - mean_a) * (y - mean_b)
        for x, y in zip(a, b)
    )

    denominator = math.sqrt(
        sum((x - mean_a) ** 2 for x in a)
        * sum((y - mean_b) ** 2 for y in b)
    )

    if denominator < 1e-15:
        raise RegressionError("Constant variable detected.")

    return numerator / denominator


class RegressionModel:

    def __init__(self, observations: list[Observation]):
        self.observations = observations
        self.n = len(observations)
        self.p = len(observations[0].features) + 1

        validate_observations(
            observations,
            self.p - 1
        )

        self.design = [
            [1.0] + observation.features
            for observation in observations
        ]

        self.y = [
            observation.target
            for observation in observations
        ]

        self.coefficients: list[float] = []
        self.fitted: list[float] = []
        self.residuals: list[float] = []
        self.xtx_inverse: list[list[float]] = []
        self.sse = 0.0
        self.mse = 0.0
        self.r_squared = 0.0

    def fit(self) -> None:
        xt = transpose(self.design)
        xtx = matrix_multiply(xt, self.design)
        xty = [
            dot(column, self.y)
            for column in xt
        ]

        self.xtx_inverse = matrix_inverse(xtx)

        self.coefficients = [
            dot(row, xty)
            for row in self.xtx_inverse
        ]

        self.fitted = [
            dot(row, self.coefficients)
            for row in self.design
        ]

        self.residuals = [
            actual - predicted
            for actual, predicted in zip(
                self.y, self.fitted
            )
        ]

        self.sse = sum(
            residual ** 2
            for residual in self.residuals
        )

        degrees_of_freedom = self.n - self.p

        if degrees_of_freedom <= 0:
            raise RegressionError("No residual degrees of freedom.")

        self.mse = self.sse / degrees_of_freedom

        total_sum_squares = sum(
            (value - mean(self.y)) ** 2
            for value in self.y
        )

        if total_sum_squares <= 1e-15:
            raise RegressionError(
                "Target variable has zero variance."
            )

        self.r_squared = 1.0 - (
            self.sse / total_sum_squares
        )

    def leverage(self) -> list[float]:
        if not self.coefficients:
            raise RegressionError("Fit the model first.")

        hat_matrix = matrix_multiply(
            matrix_multiply(
                self.design,
                self.xtx_inverse
            ),
            transpose(self.design)
        )

        return [
            hat_matrix[i][i]
            for i in range(self.n)
        ]

    def studentized_residuals(self) -> list[float]:
        if self.mse <= 0:
            raise RegressionError(
                "Studentized residuals undefined for zero error variance."
            )

        leverage = self.leverage()
        result = []

        for residual, h in zip(
            self.residuals, leverage
        ):
            denominator = math.sqrt(
                self.mse * max(1e-15, 1.0 - h)
            )

            result.append(residual / denominator)

        return result

    def cooks_distance(self) -> list[float]:
        leverage = self.leverage()
        studentized = self.studentized_residuals()

        result = []

        for r, h in zip(studentized, leverage):
            denominator = self.p * max(
                1e-15, 1.0 - h
            )

            result.append(
                (r ** 2 * h) / denominator
            )

        return result

    def correlation_matrix(self) -> list[list[float]]:
        columns = transpose(self.design)[1:]

        return [
            [
                correlation(a, b)
                for b in columns
            ]
            for a in columns
        ]

    def vif(self) -> dict[str, float]:
        """Calculate VIF using auxiliary regressions."""

        predictors = transpose(self.design)[1:]
        result = {}

        for i, target in enumerate(predictors):
            other_columns = [
                column
                for j, column in enumerate(predictors)
                if i != j
            ]

            if not other_columns:
                result[f"X{i + 1}"] = 1.0
                continue

            auxiliary_design = [
                [1.0] + [
                    other_columns[j][row]
                    for j in range(len(other_columns))
                ]
                for row in range(self.n)
            ]

            xt = transpose(auxiliary_design)

            inverse = matrix_inverse(
                matrix_multiply(xt, auxiliary_design)
            )

            xty = [
                dot(column, target)
                for column in xt
            ]

            beta = [
                dot(row, xty)
                for row in inverse
            ]

            predicted = [
                dot(row, beta)
                for row in auxiliary_design
            ]

            sse = sum(
                (actual - fitted) ** 2
                for actual, fitted in zip(target, predicted)
            )

            sst = sum(
                (value - mean(target)) ** 2
                for value in target
            )

            if sst <= 1e-15:
                raise RegressionError(
                    "Cannot calculate VIF for constant predictor."
                )

            r_squared = 1.0 - sse / sst

            if 1.0 - r_squared <= 1e-12:
                result[f"X{i + 1}"] = float("inf")
            else:
                result[f"X{i + 1}"] = (
                    1.0 / (1.0 - r_squared)
                )

        return result

    def breusch_pagan(self) -> tuple[float, float]:
        """
        Breusch-Pagan LM statistic.

        The p-value uses the chi-square survival function.
        """

        squared_residuals = [
            residual ** 2
            for residual in self.residuals
        ]

        auxiliary_design = self.design
        xt = transpose(auxiliary_design)

        inverse = matrix_inverse(
            matrix_multiply(xt, auxiliary_design)
        )

        xty = [
            dot(column, squared_residuals)
            for column in xt
        ]

        beta = [
            dot(row, xty)
            for row in inverse
        ]

        predicted = [
            dot(row, beta)
            for row in auxiliary_design
        ]

        auxiliary_mean = mean(squared_residuals)

        sse = sum(
            (actual - fitted) ** 2
            for actual, fitted in zip(
                squared_residuals, predicted
            )
        )

        sst = sum(
            (value - auxiliary_mean) ** 2
            for value in squared_residuals
        )

        if sst <= 1e-15:
            return 0.0, 1.0

        auxiliary_r_squared = max(
            0.0, min(1.0, 1.0 - sse / sst)
        )

        lm = self.n * auxiliary_r_squared
        degrees = self.p - 1

        return lm, chi_square_survival(lm, degrees)

    def hc3_standard_errors(self) -> list[float]:
        """
        HC3 sandwich covariance estimator.

        Cov(beta) = (X'X)^-1 X' diag(e_i^2/(1-h_i)^2)
                    X (X'X)^-1
        """

        leverage = self.leverage()

        weighted_design = []

        for row, residual, h in zip(
            self.design,
            self.residuals,
            leverage
        ):
            weight = (
                residual / max(1e-12, 1.0 - h)
            ) ** 2

            weighted_design.append(
                [value * weight for value in row]
            )

        middle = matrix_multiply(
            transpose(self.design),
            weighted_design
        )

        covariance = matrix_multiply(
            matrix_multiply(
                self.xtx_inverse,
                middle
            ),
            self.xtx_inverse
        )

        return [
            math.sqrt(max(0.0, covariance[i][i]))
            for i in range(self.p)
        ]


def chi_square_survival(
    statistic: float,
    degrees: int
) -> float:
    """
    Chi-square survival probability.

    Uses the regularized upper incomplete gamma function.
    """

    if degrees <= 0 or statistic < 0:
        raise ValueError("Invalid chi-square parameters.")

    a = degrees / 2.0
    x = statistic / 2.0

    if x == 0:
        return 1.0

    if x < a + 1.0:
        ap = a
        term = 1.0 / a
        total = term

        for _ in range(1000):
            ap += 1.0
            term *= x / ap
            total += term

            if abs(term) < abs(total) * 1e-14:
                break

        lower = total * math.exp(
            -x + a * math.log(x) - math.lgamma(a)
        )

        return max(0.0, min(1.0, 1.0 - lower))

    b = x + 1.0 - a
    c = 1e300
    d = 1.0 / max(1e-300, b)
    h = d

    for i in range(1, 1000):
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

    return max(
        0.0,
        min(
            1.0,
            math.exp(
                -x + a * math.log(x) - math.lgamma(a)
            ) * h
        )
    )


def jarque_bera(
    residuals: list[float]
) -> tuple[float, float]:
    """Jarque-Bera normality diagnostic."""

    center = mean(residuals)
    population_variance = variance(residuals)

    if population_variance <= 1e-15:
        return 0.0, 1.0

    skewness = (
        sum((x - center) ** 3 for x in residuals)
        / len(residuals)
        / population_variance ** 1.5
    )

    kurtosis = (
        sum((x - center) ** 4 for x in residuals)
        / len(residuals)
        / population_variance ** 2
    )

    n = len(residuals)

    jb = n / 6.0 * (
        skewness ** 2
        + (kurtosis - 3.0) ** 2 / 4.0
    )

    return jb, chi_square_survival(jb, 2)


def run_diagnostics(
    model: RegressionModel,
    thresholds: Optional[DiagnosticThresholds] = None
) -> dict:
    thresholds = thresholds or DiagnosticThresholds()

    vif_values = model.vif()
    bp_statistic, bp_pvalue = model.breusch_pagan()
    jb_statistic, jb_pvalue = jarque_bera(
        model.residuals
    )

    leverage = model.leverage()
    studentized = model.studentized_residuals()
    cooks = model.cooks_distance()

    results = []

    for name, value in vif_values.items():
        status = (
            DiagnosticStatus.FAIL
            if value >= thresholds.vif_critical
            else DiagnosticStatus.WARNING
            if value >= thresholds.vif_warning
            else DiagnosticStatus.PASS
        )

        results.append(
            DiagnosticResult(
                f"Multicollinearity: {name}",
                value,
                thresholds.vif_warning,
                status,
                "Variance inflation factor."
            )
        )

    results.append(
        DiagnosticResult(
            "Breusch-Pagan",
            bp_pvalue,
            thresholds.bp_significance,
            (
                DiagnosticStatus.WARNING
                if bp_pvalue < thresholds.bp_significance
                else DiagnosticStatus.PASS
            ),
            "Low p-value indicates evidence of heteroscedasticity."
        )
    )

    results.append(
        DiagnosticResult(
            "Jarque-Bera",
            jb_pvalue,
            0.05,
            (
                DiagnosticStatus.WARNING
                if jb_pvalue < 0.05
                else DiagnosticStatus.PASS
            ),
            "Low p-value indicates departure from normality."
        )
    )

    cooks_threshold = thresholds.cook_warning / model.n

    for i, distance in enumerate(cooks):
        if distance > cooks_threshold:
            results.append(
                DiagnosticResult(
                    f"Influence: {model.observations[i].identifier}",
                    distance,
                    cooks_threshold,
                    DiagnosticStatus.WARNING,
                    "Observation exceeds Cook's distance screening threshold."
                )
            )

    leverage_threshold = (
        thresholds.leverage_multiplier
        * model.p
        / model.n
    )

    for i, value in enumerate(leverage):
        if value > leverage_threshold:
            results.append(
                DiagnosticResult(
                    f"High leverage: {model.observations[i].identifier}",
                    value,
                    leverage_threshold,
                    DiagnosticStatus.WARNING,
                    "Observation has unusually high predictor-space leverage."
                )
            )

    for i, value in enumerate(studentized):
        if abs(value) > thresholds.studentized_limit:
            results.append(
                DiagnosticResult(
                    f"Large studentized residual: {model.observations[i].identifier}",
                    value,
                    thresholds.studentized_limit,
                    DiagnosticStatus.WARNING,
                    "Observation has an unusually large residual."
                )
            )

    return {
        "sample_size": model.n,
        "parameter_count": model.p,
        "coefficients": model.coefficients,
        "r_squared": model.r_squared,
        "adjusted_r_squared": (
            1.0
            - (1.0 - model.r_squared)
            * (model.n - 1)
            / (model.n - model.p)
        ),
        "residual_standard_error": math.sqrt(model.mse),
        "vif": vif_values,
        "breusch_pagan": {
            "statistic": bp_statistic,
            "p_value": bp_pvalue
        },
        "jarque_bera": {
            "statistic": jb_statistic,
            "p_value": jb_pvalue
        },
        "hc3_standard_errors": model.hc3_standard_errors(),
        "diagnostics": [
            {
                **asdict(result),
                "status": result.status.value
            }
            for result in results
        ]
    }


def create_sample_data() -> list[Observation]:
    """Generate deterministic data with correlated predictors."""

    observations = []

    for i in range(1, 81):
        x1 = float(i)
        x2 = 0.92 * x1 + (i % 7) * 0.8

        # Error variance increases with x1.
        error = (
            ((i % 9) - 4)
            * (0.4 + 0.025 * x1)
        )

        if i == 72:
            error += 35.0

        y = 12.0 + 2.5 * x1 + 1.3 * x2 + error

        observations.append(
            Observation(
                identifier=f"OBS-{i:03d}",
                features=[x1, x2],
                target=y
            )
        )

    return observations


def export_report(report: dict, filename: str) -> None:
    """Write reports atomically to avoid partial output files."""

    destination = Path(filename)
    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(report, indent=2, allow_nan=False),
        encoding="utf-8"
    )

    temporary.replace(destination)


def run_tests() -> None:
    data = create_sample_data()
    model = RegressionModel(data)
    model.fit()

    assert len(model.coefficients) == 3
    assert len(model.residuals) == len(data)
    assert abs(mean(model.residuals)) < 1e-7
    assert 0.0 <= model.r_squared <= 1.0
    assert len(model.leverage()) == len(data)
    assert len(model.cooks_distance()) == len(data)
    assert all(
        value >= 1.0
        for value in model.vif().values()
    )

    assert abs(
        chi_square_survival(5.9914645, 2) - 0.05
    ) < 1e-5

    print("All regression diagnostic tests passed.")


def main() -> None:
    run_tests()

    observations = create_sample_data()
    model = RegressionModel(observations)
    model.fit()

    report = run_diagnostics(model)

    print("\nREGRESSION DIAGNOSTICS")
    print("=" * 65)
    print(f"Observations: {report['sample_size']}")
    print(f"Parameters: {report['parameter_count']}")
    print(f"R-squared: {report['r_squared']:.5f}")
    print(
        f"Adjusted R-squared: "
        f"{report['adjusted_r_squared']:.5f}"
    )
    print(
        f"Residual standard error: "
        f"{report['residual_standard_error']:.5f}"
    )

    print("\nCoefficients:")
    for index, coefficient in enumerate(
        report["coefficients"]
    ):
        print(f"  Beta {index}: {coefficient:.6f}")

    print("\nVIF:")
    for name, value in report["vif"].items():
        print(f"  {name}: {value:.4f}")

    print("\nBreusch-Pagan:")
    print(report["breusch_pagan"])

    print("\nJarque-Bera:")
    print(report["jarque_bera"])

    print("\nHC3 standard errors:")
    print(report["hc3_standard_errors"])

    print("\nDiagnostic findings:")
    for diagnostic in report["diagnostics"]:
        print(
            f"  [{diagnostic['status']}] "
            f"{diagnostic['name']}: "
            f"{diagnostic['statistic']:.5f}"
        )

    export_report(report, "regression_diagnostics.json")

    print("\nReport saved to regression_diagnostics.json")


if __name__ == "__main__":
    try:
        main()
    except (RegressionError, ValueError, OSError) as error:
        print(f"Execution failed: {error}")
        raise SystemExit(1)
