#!/usr/bin/env python3
"""
Regression Fundamentals
Simple Linear Regression, Coefficients, Residuals, R-squared, and Assumptions.

Implements ordinary least squares without external dependencies.
"""

from __future__ import annotations

import csv
import math
import statistics
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence


class RegressionError(Exception):
    """Base exception for regression failures."""


class ValidationError(RegressionError):
    """Invalid input data."""


class ModelState(Enum):
    UNFITTED = "unfitted"
    FITTED = "fitted"


@dataclass(frozen=True)
class RegressionMetrics:
    mae: float
    mse: float
    rmse: float
    r_squared: float
    adjusted_r_squared: float
    residual_standard_error: float


@dataclass(frozen=True)
class AssumptionResult:
    name: str
    passed: bool
    statistic: float
    threshold: float
    interpretation: str


class SimpleLinearRegression:
    """
    Ordinary least squares model:

        y_hat = intercept + slope * x

    Time complexity:
        Fitting: O(n)
        Prediction: O(m)
        Residual calculation: O(n)
    """

    def __init__(self, *, variance_tolerance: float = 1e-12):
        self.variance_tolerance = variance_tolerance
        self.state = ModelState.UNFITTED
        self.slope: float | None = None
        self.intercept: float | None = None
        self.x_mean: float | None = None
        self.y_mean: float | None = None
        self.x_variance: float | None = None
        self.y_variance: float | None = None
        self.residuals: list[float] = []
        self.fitted_values: list[float] = []
        self.training_x: list[float] = []
        self.training_y: list[float] = []
        self.metrics: RegressionMetrics | None = None

    @staticmethod
    def _validate_data(
        x: Sequence[float],
        y: Sequence[float]
    ) -> tuple[list[float], list[float]]:

        if len(x) != len(y):
            raise ValidationError("X and Y must have equal lengths.")

        if len(x) < 3:
            raise ValidationError("At least three observations are required.")

        try:
            x_values = [float(value) for value in x]
            y_values = [float(value) for value in y]
        except (TypeError, ValueError) as exc:
            raise ValidationError("Observations must be numeric.") from exc

        if not all(math.isfinite(value) for value in x_values + y_values):
            raise ValidationError("NaN and infinite values are not permitted.")

        return x_values, y_values

    def fit(
        self,
        x: Sequence[float],
        y: Sequence[float]
    ) -> SimpleLinearRegression:

        x_values, y_values = self._validate_data(x, y)

        n = len(x_values)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        # Centering reduces numerical cancellation.
        sxx = sum((value - x_mean) ** 2 for value in x_values)
        syy = sum((value - y_mean) ** 2 for value in y_values)
        sxy = sum(
            (x_values[i] - x_mean) * (y_values[i] - y_mean)
            for i in range(n)
        )

        if sxx <= self.variance_tolerance:
            raise ValidationError(
                "Predictor has zero or near-zero variance."
            )

        slope = sxy / sxx
        intercept = y_mean - slope * x_mean

        fitted = [
            intercept + slope * value
            for value in x_values
        ]

        residuals = [
            y_values[i] - fitted[i]
            for i in range(n)
        ]

        sse = sum(error ** 2 for error in residuals)

        if syy <= self.variance_tolerance:
            r_squared = 1.0 if sse <= self.variance_tolerance else 0.0
        else:
            r_squared = 1.0 - sse / syy

        # One predictor and one estimated intercept.
        adjusted_r_squared = (
            1.0 - (1.0 - r_squared) * (n - 1) / (n - 2)
        )

        mse = sse / n
        mae = sum(abs(error) for error in residuals) / n

        residual_standard_error = math.sqrt(
            sse / (n - 2)
        )

        self.slope = slope
        self.intercept = intercept
        self.x_mean = x_mean
        self.y_mean = y_mean
        self.x_variance = sxx / (n - 1)
        self.y_variance = syy / (n - 1)
        self.training_x = x_values
        self.training_y = y_values
        self.fitted_values = fitted
        self.residuals = residuals

        self.metrics = RegressionMetrics(
            mae=mae,
            mse=mse,
            rmse=math.sqrt(mse),
            r_squared=r_squared,
            adjusted_r_squared=adjusted_r_squared,
            residual_standard_error=residual_standard_error
        )

        self.state = ModelState.FITTED
        return self

    def _ensure_fitted(self) -> None:
        if self.state != ModelState.FITTED:
            raise RegressionError("Fit the model before using it.")

    def predict(self, x: Sequence[float]) -> list[float]:
        self._ensure_fitted()

        values = [float(value) for value in x]

        if not all(math.isfinite(value) for value in values):
            raise ValidationError("Prediction inputs must be finite.")

        return [
            self.intercept + self.slope * value
            for value in values
        ]

    def predict_one(self, x: float) -> float:
        return self.predict([x])[0]

    def coefficient_of_determination(self) -> float:
        self._ensure_fitted()
        return self.metrics.r_squared

    def coefficient_standard_errors(self) -> tuple[float, float]:
        """Return standard errors of intercept and slope."""

        self._ensure_fitted()

        n = len(self.training_x)
        sse = sum(error ** 2 for error in self.residuals)
        sigma_squared = sse / (n - 2)

        sxx = sum(
            (value - self.x_mean) ** 2
            for value in self.training_x
        )

        slope_se = math.sqrt(sigma_squared / sxx)
        intercept_se = math.sqrt(
            sigma_squared * (
                1 / n + self.x_mean ** 2 / sxx
            )
        )

        return intercept_se, slope_se

    def confidence_interval_slope(
        self,
        critical_value: float = 1.96
    ) -> tuple[float, float]:
        """
        Approximate confidence interval.

        For small samples, replace 1.96 with an appropriate
        Student's t critical value.
        """

        self._ensure_fitted()

        if critical_value <= 0:
            raise ValidationError("Critical value must be positive.")

        _, slope_se = self.coefficient_standard_errors()

        return (
            self.slope - critical_value * slope_se,
            self.slope + critical_value * slope_se
        )

    def residual_diagnostics(self) -> dict:
        """Basic descriptive diagnostics, not formal hypothesis tests."""

        self._ensure_fitted()

        errors = self.residuals
        n = len(errors)

        mean_residual = statistics.mean(errors)

        variance = statistics.variance(errors)

        skewness = (
            sum((e - mean_residual) ** 3 for e in errors) / n
        ) / (variance ** 1.5) if variance > 0 else 0.0

        kurtosis = (
            sum((e - mean_residual) ** 4 for e in errors) / n
        ) / (variance ** 2) - 3 if variance > 0 else 0.0

        return {
            "mean_residual": mean_residual,
            "residual_variance": variance,
            "skewness": skewness,
            "excess_kurtosis": kurtosis,
            "maximum_absolute_residual": max(abs(e) for e in errors)
        }

    def assumption_checks(self) -> list[AssumptionResult]:
        """
        Basic diagnostic indicators.

        These indicators do not establish that assumptions
        are statistically satisfied.
        """

        self._ensure_fitted()

        errors = self.residuals
        n = len(errors)

        mean_error = abs(statistics.mean(errors))

        # Lag-one residual correlation is a descriptive indicator.
        numerator = sum(
            errors[i] * errors[i - 1]
            for i in range(1, n)
        )

        denominator = sum(error ** 2 for error in errors)

        lag_correlation = (
            numerator / denominator if denominator > 0 else 0.0
        )

        # Compare residual spread across lower and upper fitted values.
        ordered = sorted(
            zip(self.fitted_values, errors),
            key=lambda pair: pair[0]
        )

        split = n // 2

        lower = [error for _, error in ordered[:split]]
        upper = [error for _, error in ordered[split:]]

        lower_variance = (
            statistics.variance(lower) if len(lower) >= 2 else 0.0
        )

        upper_variance = (
            statistics.variance(upper) if len(upper) >= 2 else 0.0
        )

        variance_ratio = (
            max(lower_variance, upper_variance)
            / max(min(lower_variance, upper_variance), 1e-15)
        )

        diagnostics = self.residual_diagnostics()

        return [
            AssumptionResult(
                "Linearity",
                diagnostics["mean_residual"] < 1e-8,
                mean_error,
                1e-8,
                "OLS residuals average approximately zero when an intercept is fitted. "
                "Inspect residual plots to assess linearity."
            ),
            AssumptionResult(
                "Independence",
                abs(lag_correlation) < 0.3,
                abs(lag_correlation),
                0.3,
                "Lag-one residual correlation is descriptive, not a formal independence test."
            ),
            AssumptionResult(
                "Homoscedasticity",
                variance_ratio < 4.0,
                variance_ratio,
                4.0,
                "Compares residual variance across fitted-value groups."
            ),
            AssumptionResult(
                "Residual normality",
                abs(diagnostics["skewness"]) < 1.0,
                abs(diagnostics["skewness"]),
                1.0,
                "Uses absolute residual skewness as a rough indicator."
            )
        ]

    def summary(self) -> dict:
        self._ensure_fitted()

        intercept_se, slope_se = self.coefficient_standard_errors()

        return {
            "equation": (
                f"y = {self.intercept:.6f} "
                f"+ {self.slope:.6f} * x"
            ),
            "observations": len(self.training_x),
            "intercept": self.intercept,
            "slope": self.slope,
            "intercept_standard_error": intercept_se,
            "slope_standard_error": slope_se,
            "metrics": self.metrics,
            "diagnostics": self.residual_diagnostics()
        }


def load_csv(
    path: str,
    x_column: str,
    y_column: str
) -> tuple[list[float], list[float]]:

    x_values = []
    y_values = []

    with Path(path).open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValidationError("CSV file has no header.")

        if x_column not in reader.fieldnames:
            raise ValidationError(f"Missing column: {x_column}")

        if y_column not in reader.fieldnames:
            raise ValidationError(f"Missing column: {y_column}")

        for row_number, row in enumerate(reader, start=2):
            try:
                x_values.append(float(row[x_column]))
                y_values.append(float(row[y_column]))
            except (ValueError, TypeError) as exc:
                raise ValidationError(
                    f"Invalid numeric value at CSV row {row_number}."
                ) from exc

    return x_values, y_values


def print_report(model: SimpleLinearRegression) -> None:

    report = model.summary()

    print("\nREGRESSION REPORT")
    print("=" * 55)

    print("Equation:", report["equation"])
    print("Observations:", report["observations"])
    print(f"Intercept: {report['intercept']:.6f}")
    print(f"Slope: {report['slope']:.6f}")
    print(
        f"Intercept SE: {report['intercept_standard_error']:.6f}"
    )
    print(f"Slope SE: {report['slope_standard_error']:.6f}")

    metrics = report["metrics"]

    print("\nMODEL METRICS")
    print(f"MAE: {metrics.mae:.6f}")
    print(f"MSE: {metrics.mse:.6f}")
    print(f"RMSE: {metrics.rmse:.6f}")
    print(f"R-squared: {metrics.r_squared:.6f}")
    print(f"Adjusted R-squared: {metrics.adjusted_r_squared:.6f}")
    print(
        f"Residual standard error: "
        f"{metrics.residual_standard_error:.6f}"
    )

    print("\nASSUMPTION DIAGNOSTICS")

    for result in model.assumption_checks():
        status = "INDICATOR PASSED" if result.passed else "INVESTIGATE"
        print(
            f"{result.name}: {status} "
            f"(statistic={result.statistic:.6f})"
        )
        print(" ", result.interpretation)

    print("\nRESIDUAL DIAGNOSTICS")

    for key, value in model.residual_diagnostics().items():
        print(f"{key}: {value:.6f}")


def run_tests() -> None:
    # Perfect linear relationship.
    model = SimpleLinearRegression().fit(
        [1, 2, 3, 4, 5],
        [3, 5, 7, 9, 11]
    )

    assert abs(model.slope - 2.0) < 1e-10
    assert abs(model.intercept - 1.0) < 1e-10
    assert abs(model.metrics.r_squared - 1.0) < 1e-10
    assert abs(model.predict_one(6) - 13.0) < 1e-10

    # No relationship in a constant response.
    constant_model = SimpleLinearRegression().fit(
        [1, 2, 3],
        [5, 5, 5]
    )
    assert constant_model.metrics.r_squared == 1.0

    # Input validation.
    try:
        SimpleLinearRegression().fit([1, 1, 1], [2, 3, 4])
        raise AssertionError("Constant predictor was not rejected.")
    except ValidationError:
        pass

    try:
        SimpleLinearRegression().fit([1, 2], [3, 4])
        raise AssertionError("Insufficient observations were accepted.")
    except ValidationError:
        pass

    print("All regression tests passed.")


def main() -> None:

    # Study-hours and examination-score example.
    study_hours = [1, 2, 3, 4, 5, 6, 7, 8]
    examination_scores = [42, 46, 53, 57, 61, 68, 72, 79]

    model = SimpleLinearRegression()
    model.fit(study_hours, examination_scores)

    print_report(model)

    print("\nPREDICTIONS")

    for hours, prediction in zip(
        [2.5, 5.5, 9.0],
        model.predict([2.5, 5.5, 9.0])
    ):
        print(f"{hours:.1f} study hours -> {prediction:.2f} marks")

    lower, upper = model.confidence_interval_slope()
    print(f"\nApproximate slope confidence interval: ({lower:.4f}, {upper:.4f})")

    print("\nOBSERVED VS PREDICTED")

    for index, (actual, predicted, residual) in enumerate(
        zip(
            model.training_y,
            model.fitted_values,
            model.residuals
        ),
        start=1
    ):
        print(
            f"Observation {index}: actual={actual:.2f}, "
            f"predicted={predicted:.2f}, residual={residual:.2f}"
        )

    run_tests()


if __name__ == "__main__":
    main()
