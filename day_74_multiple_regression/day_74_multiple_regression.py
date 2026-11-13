#!/usr/bin/env python3
"""
MULTIPLE REGRESSION
Multiple predictors, categorical variables, interactions, and interpretation.

Standard-library implementation of ordinary least squares (OLS).
Supports:
- Multiple numerical predictors
- Categorical predictors using reference-category dummy encoding
- Two-way interaction terms
- Coefficient interpretation
- R-squared and adjusted R-squared
- Residuals, RMSE, MAE
- Multicollinearity diagnostics through VIF
- Prediction and input validation

Run:
    python multiple_regression.py
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Optional


class RegressionError(Exception):
    """Base exception for regression errors."""


class ValidationError(RegressionError):
    """Invalid data or model specification."""


class SingularMatrixError(RegressionError):
    """Model cannot be estimated because of singularity."""


@dataclass(frozen=True)
class Interaction:
    first: str
    second: str


@dataclass
class RegressionResult:
    feature_names: list[str]
    coefficients: list[float]
    predictions: list[float]
    residuals: list[float]
    r_squared: float
    adjusted_r_squared: float
    rmse: float
    mae: float
    degrees_of_freedom: int
    standard_errors: list[Optional[float]]

    def coefficient_table(self) -> list[dict[str, Any]]:
        rows = []
        for name, coefficient, standard_error in zip(
            self.feature_names,
            self.coefficients,
            self.standard_errors
        ):
            t_value = (
                coefficient / standard_error
                if standard_error is not None and standard_error > 0
                else None
            )
            rows.append({
                "term": name,
                "coefficient": round(coefficient, 5),
                "standard_error": (
                    round(standard_error, 5)
                    if standard_error is not None else None
                ),
                "t_statistic": (
                    round(t_value, 5) if t_value is not None else None
                )
            })
        return rows


def solve_linear_system(
    matrix: list[list[float]],
    vector: list[float]
) -> list[float]:
    """Solve Ax=b using Gaussian elimination with partial pivoting."""

    n = len(vector)
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
            raise SingularMatrixError(
                "Singular design matrix. Check redundant predictors "
                "and perfect multicollinearity."
            )

        augmented[col], augmented[pivot] = (
            augmented[pivot],
            augmented[col]
        )

        divisor = augmented[col][col]

        for j in range(col, n + 1):
            augmented[col][j] /= divisor

        for row in range(n):
            if row == col:
                continue

            factor = augmented[row][col]

            for j in range(col, n + 1):
                augmented[row][j] -= (
                    factor * augmented[col][j]
                )

    return [augmented[i][n] for i in range(n)]


def invert_matrix(matrix: list[list[float]]) -> list[list[float]]:
    """Calculate a matrix inverse using Gauss-Jordan elimination."""

    n = len(matrix)
    augmented = [
        list(matrix[i]) +
        [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        pivot = max(
            range(col, n),
            key=lambda row: abs(augmented[row][col])
        )

        if abs(augmented[pivot][col]) < 1e-12:
            raise SingularMatrixError("Matrix is not invertible.")

        augmented[col], augmented[pivot] = (
            augmented[pivot],
            augmented[col]
        )

        divisor = augmented[col][col]
        augmented[col] = [
            value / divisor for value in augmented[col]
        ]

        for row in range(n):
            if row == col:
                continue

            factor = augmented[row][col]

            augmented[row] = [
                augmented[row][j] -
                factor * augmented[col][j]
                for j in range(2 * n)
            ]

    return [
        augmented[i][n:]
        for i in range(n)
    ]


class MultipleRegression:
    def __init__(
        self,
        target: str,
        numerical: list[str],
        categorical: Optional[list[str]] = None,
        interactions: Optional[list[Interaction]] = None
    ):
        self.target = target
        self.numerical = numerical
        self.categorical = categorical or []
        self.interactions = interactions or []

        all_predictors = numerical + self.categorical

        if not target or not numerical:
            raise ValidationError(
                "Target and at least one numerical predictor are required."
            )

        if len(set(all_predictors)) != len(all_predictors):
            raise ValidationError("Duplicate predictor names.")

        if target in all_predictors:
            raise ValidationError(
                "Target cannot also be a predictor."
            )

        for interaction in self.interactions:
            if (
                interaction.first not in all_predictors
                or interaction.second not in all_predictors
            ):
                raise ValidationError(
                    "Interaction references an unknown predictor."
                )

        self.category_levels: dict[str, list[str]] = {}
        self.feature_names: list[str] = []
        self.coefficients: Optional[list[float]] = None
        self.result: Optional[RegressionResult] = None

    def _validate_data(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            raise ValidationError("Dataset cannot be empty.")

        required = (
            [self.target] +
            self.numerical +
            self.categorical
        )

        for index, row in enumerate(rows):
            missing = [key for key in required if key not in row]

            if missing:
                raise ValidationError(
                    f"Row {index} is missing columns: {missing}"
                )

            for column in [self.target] + self.numerical:
                value = row[column]

                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                ):
                    raise ValidationError(
                        f"Invalid numeric value in row {index}: {column}"
                    )

            for column in self.categorical:
                if row[column] is None or str(row[column]) == "":
                    raise ValidationError(
                        f"Missing category in row {index}: {column}"
                    )

    def _fit_encoder(self, rows: list[dict[str, Any]]) -> None:
        for column in self.categorical:
            levels = sorted({
                str(row[column]) for row in rows
            })

            if len(levels) < 2:
                raise ValidationError(
                    f"Categorical variable {column} needs two levels."
                )

            self.category_levels[column] = levels

    def _design_row(self, row: dict[str, Any]) -> list[float]:
        values = [1.0]

        values.extend(
            float(row[column])
            for column in self.numerical
        )

        for column in self.categorical:
            value = str(row[column])
            levels = self.category_levels[column]

            if value not in levels:
                raise ValidationError(
                    f"Unknown category '{value}' for {column}."
                )

            # First category is the reference category.
            for level in levels[1:]:
                values.append(
                    1.0 if value == level else 0.0
                )

        lookup: dict[str, float] = {}

        for index, column in enumerate(self.numerical):
            lookup[column] = float(row[column])

        for column in self.categorical:
            levels = self.category_levels[column]

            # Reference category is represented by zero.
            for level in levels[1:]:
                lookup[f"{column}[{level}]"] = (
                    1.0 if str(row[column]) == level else 0.0
                )

        for interaction in self.interactions:
            first = interaction.first
            second = interaction.second

            if first in lookup and second in lookup:
                values.append(lookup[first] * lookup[second])
            else:
                raise ValidationError(
                    "Interactions must use numerical variables or "
                    "explicit dummy-coded category terms."
                )

        return values

    def _build_feature_names(self) -> list[str]:
        names = ["Intercept"]
        names.extend(self.numerical)

        for column in self.categorical:
            for level in self.category_levels[column][1:]:
                names.append(f"{column}[{level}]")

        for interaction in self.interactions:
            names.append(
                f"{interaction.first}:{interaction.second}"
            )

        return names

    def fit(self, rows: list[dict[str, Any]]) -> RegressionResult:
        self._validate_data(rows)
        self._fit_encoder(rows)

        design = [
            self._design_row(row)
            for row in rows
        ]

        y = [float(row[self.target]) for row in rows]

        n = len(y)
        p = len(design[0])

        if n <= p:
            raise ValidationError(
                f"Need more than {p} observations; received {n}."
            )

        self.feature_names = self._build_feature_names()

        # Construct X'X and X'y.
        xtx = [
            [
                sum(
                    design[k][i] * design[k][j]
                    for k in range(n)
                )
                for j in range(p)
            ]
            for i in range(p)
        ]

        xty = [
            sum(
                design[k][i] * y[k]
                for k in range(n)
            )
            for i in range(p)
        ]

        coefficients = solve_linear_system(xtx, xty)

        predictions = [
            sum(
                design[i][j] * coefficients[j]
                for j in range(p)
            )
            for i in range(n)
        ]

        residuals = [
            y[i] - predictions[i]
            for i in range(n)
        ]

        mean_y = statistics.mean(y)

        sse = sum(r * r for r in residuals)
        sst = sum((value - mean_y) ** 2 for value in y)

        if sst <= 1e-12:
            raise ValidationError(
                "Target variance is zero; R-squared is undefined."
            )

        r_squared = 1.0 - sse / sst
        adjusted_r_squared = (
            1.0 - (1.0 - r_squared) * (n - 1) / (n - p)
        )

        rmse = math.sqrt(sse / n)
        mae = sum(abs(r) for r in residuals) / n

        degrees_of_freedom = n - p
        mse = sse / degrees_of_freedom

        inverse = invert_matrix(xtx)

        standard_errors = [
            math.sqrt(max(0.0, mse * inverse[i][i]))
            for i in range(p)
        ]

        self.coefficients = coefficients

        self.result = RegressionResult(
            feature_names=self.feature_names,
            coefficients=coefficients,
            predictions=predictions,
            residuals=residuals,
            r_squared=r_squared,
            adjusted_r_squared=adjusted_r_squared,
            rmse=rmse,
            mae=mae,
            degrees_of_freedom=degrees_of_freedom,
            standard_errors=standard_errors
        )

        return self.result

    def predict(self, row: dict[str, Any]) -> float:
        if self.coefficients is None:
            raise RegressionError("Fit the model before prediction.")

        required = (
            self.numerical + self.categorical
        )

        for column in required:
            if column not in row:
                raise ValidationError(
                    f"Prediction input missing: {column}"
                )

        for column in self.numerical:
            if (
                isinstance(row[column], bool)
                or not isinstance(row[column], (int, float))
                or not math.isfinite(float(row[column]))
            ):
                raise ValidationError(
                    f"Invalid prediction value: {column}"
                )

        design = self._design_row(row)

        return sum(
            design[i] * self.coefficients[i]
            for i in range(len(design))
        )

    def interpret(self) -> list[str]:
        if self.result is None:
            raise RegressionError("Model has not been fitted.")

        interpretations = []

        for name, coefficient in zip(
            self.result.feature_names,
            self.result.coefficients
        ):
            if name == "Intercept":
                description = (
                    "Expected target value when numerical predictors "
                    "are zero and categories are at reference levels."
                )
            elif ":" in name:
                description = (
                    "Change in the relevant predictor's marginal effect "
                    "associated with a one-unit increase in the other "
                    "interaction variable."
                )
            else:
                description = (
                    "Expected target change for a one-unit increase "
                    "or category contrast, holding other terms constant."
                )

            interpretations.append(
                f"{name}: coefficient={coefficient:.4f}. {description}"
            )

        return interpretations


def calculate_vif(
    rows: list[dict[str, Any]],
    columns: list[str]
) -> dict[str, float]:
    """
    Calculate numerical-predictor VIF values.

    Each predictor is regressed against the remaining predictors.
    """
    if len(columns) < 2:
        return {column: 1.0 for column in columns}

    if len(rows) <= len(columns):
        raise ValidationError("Insufficient rows for VIF calculation.")

    result = {}

    for target in columns:
        others = [column for column in columns if column != target]

        regression = MultipleRegression(
            target=target,
            numerical=others
        )

        fitted = regression.fit(rows)
        r2 = fitted.r_squared

        result[target] = (
            float("inf")
            if r2 >= 1.0 - 1e-12
            else 1.0 / (1.0 - r2)
        )

    return result


def main() -> None:
    # Example: explain employee compensation using several predictors.
    data = [
        {"salary": 45000, "experience": 1, "education": "Bachelor",
         "performance": 3, "department": "Sales"},
        {"salary": 49000, "experience": 2, "education": "Bachelor",
         "performance": 4, "department": "Sales"},
        {"salary": 53000, "experience": 3, "education": "Master",
         "performance": 3, "department": "Sales"},
        {"salary": 57000, "experience": 4, "education": "Master",
         "performance": 4, "department": "Technology"},
        {"salary": 65000, "experience": 5, "education": "Master",
         "performance": 5, "department": "Technology"},
        {"salary": 61000, "experience": 4, "education": "Bachelor",
         "performance": 5, "department": "Technology"},
        {"salary": 72000, "experience": 6, "education": "PhD",
         "performance": 4, "department": "Technology"},
        {"salary": 76000, "experience": 7, "education": "PhD",
         "performance": 5, "department": "Technology"},
        {"salary": 50000, "experience": 2, "education": "Bachelor",
         "performance": 3, "department": "Operations"},
        {"salary": 55000, "experience": 3, "education": "Master",
         "performance": 4, "department": "Operations"},
        {"salary": 59000, "experience": 4, "education": "Bachelor",
         "performance": 4, "department": "Operations"},
        {"salary": 68000, "experience": 6, "education": "PhD",
         "performance": 5, "department": "Operations"},
        {"salary": 48000, "experience": 2, "education": "Bachelor",
         "performance": 2, "department": "Sales"},
        {"salary": 62000, "experience": 5, "education": "Master",
         "performance": 4, "department": "Sales"},
        {"salary": 70000, "experience": 6, "education": "PhD",
         "performance": 5, "department": "Technology"},
        {"salary": 54000, "experience": 3, "education": "Bachelor",
         "performance": 3, "department": "Operations"},
        {"salary": 74000, "experience": 7, "education": "Master",
         "performance": 5, "department": "Technology"},
        {"salary": 58000, "experience": 4, "education": "Master",
         "performance": 3, "department": "Sales"},
        {"salary": 64000, "experience": 5, "education": "Bachelor",
         "performance": 5, "department": "Operations"},
        {"salary": 79000, "experience": 8, "education": "PhD",
         "performance": 5, "department": "Technology"}
    ]

    model = MultipleRegression(
        target="salary",
        numerical=["experience", "performance"],
        categorical=["education", "department"],
        interactions=[
            Interaction("experience", "performance")
        ]
    )

    result = model.fit(data)

    print("\nMULTIPLE REGRESSION RESULTS")
    print("=" * 65)

    for row in result.coefficient_table():
        print(row)

    print("\nMODEL PERFORMANCE")
    print(f"R-squared:          {result.r_squared:.4f}")
    print(f"Adjusted R-squared: {result.adjusted_r_squared:.4f}")
    print(f"RMSE:               {result.rmse:.2f}")
    print(f"MAE:                {result.mae:.2f}")
    print(f"Degrees of freedom: {result.degrees_of_freedom}")

    print("\nCOEFFICIENT INTERPRETATION")

    for interpretation in model.interpret():
        print(interpretation)

    employee = {
        "experience": 5,
        "performance": 4,
        "education": "Master",
        "department": "Technology"
    }

    print("\nNEW EMPLOYEE PREDICTION")
    print(f"Predicted salary: {model.predict(employee):,.2f}")

    print("\nNUMERICAL PREDICTOR VIF")
    print(calculate_vif(
        data,
        ["experience", "performance"]
    ))

    # Fundamental correctness checks.
    assert len(result.coefficients) == len(result.feature_names)
    assert len(result.predictions) == len(data)
    assert math.isfinite(result.r_squared)

    try:
        model.predict({
            "experience": 5,
            "performance": 4,
            "education": "Unknown",
            "department": "Technology"
        })
    except ValidationError as error:
        print("\nEXPECTED VALIDATION ERROR:", error)

    print("\nExecution completed successfully.")


if __name__ == "__main__":
    main()
