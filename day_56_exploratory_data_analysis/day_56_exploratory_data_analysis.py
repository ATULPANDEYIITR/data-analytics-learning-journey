from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from statistics import mean, median, pstdev
from typing import Any, Iterable
import json
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


class AnalysisType(Enum):
    UNIVARIATE = "univariate"
    BIVARIATE = "bivariate"
    MULTIVARIATE = "multivariate"
    ANOMALY = "anomaly"


@dataclass(frozen=True)
class Observation:
    customer_id: int
    age: float
    income: float
    monthly_spend: float
    visits: int
    satisfaction: float


class EDAError(Exception):
    """Raised when the dataset violates an analytical precondition."""


class EDAEngine:
    """
    Dependency-free exploratory data analysis engine.

    The implementation intentionally uses explicit calculations so that
    statistical assumptions and edge cases remain visible.
    """

    REQUIRED_FIELDS = {
        "customer_id",
        "age",
        "income",
        "monthly_spend",
        "visits",
        "satisfaction",
    }

    def __init__(self, observations: list[Observation]) -> None:
        if not observations:
            raise EDAError("Dataset must contain at least one observation.")

        ids = [row.customer_id for row in observations]
        if len(ids) != len(set(ids)):
            raise EDAError("customer_id values must be unique.")

        for row in observations:
            self._validate_observation(row)

        self.rows = observations

    @staticmethod
    def _validate_observation(row: Observation) -> None:
        numeric_values = (
            row.age,
            row.income,
            row.monthly_spend,
            row.visits,
            row.satisfaction,
        )
        if any(not isinstance(value, (int, float)) for value in numeric_values):
            raise EDAError(f"Non-numeric value found for customer {row.customer_id}.")

        if not all(map(lambda value: value == value, numeric_values)):
            raise EDAError(f"NaN value found for customer {row.customer_id}.")

        if row.age < 0 or row.age > 120:
            raise EDAError(f"Invalid age: {row.age}.")
        if row.income < 0 or row.monthly_spend < 0:
            raise EDAError("Income and monthly_spend cannot be negative.")
        if row.visits < 0:
            raise EDAError("Visits cannot be negative.")
        if not 0 <= row.satisfaction <= 10:
            raise EDAError("Satisfaction must be between 0 and 10.")

    def column(self, name: str) -> list[float]:
        if name not in self.REQUIRED_FIELDS:
            raise KeyError(f"Unknown column: {name}")

        return [float(getattr(row, name)) for row in self.rows]

    def descriptive_statistics(self, name: str) -> dict[str, float]:
        values = self.column(name)

        if not values:
            raise EDAError("Cannot analyze an empty column.")

        result = {
            "count": float(len(values)),
            "mean": mean(values),
            "median": median(values),
            "minimum": min(values),
            "maximum": max(values),
            "std_population": pstdev(values) if len(values) > 1 else 0.0,
        }

        return result

    @staticmethod
    def quantile(values: list[float], q: float) -> float:
        if not values:
            raise EDAError("Cannot calculate a quantile for empty data.")
        if not 0 <= q <= 1:
            raise ValueError("Quantile must be between 0 and 1.")

        ordered = sorted(values)
        position = (len(ordered) - 1) * q
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower

        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    def five_number_summary(self, name: str) -> dict[str, float]:
        values = self.column(name)
        return {
            "min": min(values),
            "q1": self.quantile(values, 0.25),
            "median": self.quantile(values, 0.50),
            "q3": self.quantile(values, 0.75),
            "max": max(values),
        }

    def histogram(self, name: str, bins: int = 5) -> list[dict[str, Any]]:
        if bins <= 0:
            raise ValueError("bins must be positive.")

        values = self.column(name)
        minimum = min(values)
        maximum = max(values)

        if minimum == maximum:
            return [{
                "lower": minimum,
                "upper": maximum,
                "count": len(values),
            }]

        width = (maximum - minimum) / bins
        counts = [0] * bins

        for value in values:
            index = int((value - minimum) / width)
            index = min(index, bins - 1)
            counts[index] += 1

        result = []
        for index, count in enumerate(counts):
            lower = minimum + index * width
            upper = maximum if index == bins - 1 else lower + width
            result.append({
                "lower": round(lower, 4),
                "upper": round(upper, 4),
                "count": count,
            })

        return result

    @staticmethod
    def pearson_correlation(x: list[float], y: list[float]) -> float:
        if len(x) != len(y) or not x:
            raise EDAError("Correlation requires equally sized non-empty vectors.")

        x_mean = mean(x)
        y_mean = mean(y)

        numerator = sum(
            (a - x_mean) * (b - y_mean)
            for a, b in zip(x, y)
        )
        denominator_x = sqrt(sum((a - x_mean) ** 2 for a in x))
        denominator_y = sqrt(sum((b - y_mean) ** 2 for b in y))

        denominator = denominator_x * denominator_y

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def bivariate_analysis(self, x_name: str, y_name: str) -> dict[str, Any]:
        x = self.column(x_name)
        y = self.column(y_name)

        correlation = self.pearson_correlation(x, y)

        x_mean = mean(x)
        y_mean = mean(y)
        covariance = sum(
            (a - x_mean) * (b - y_mean)
            for a, b in zip(x, y)
        ) / len(x)

        return {
            "x": x_name,
            "y": y_name,
            "pearson_correlation": round(correlation, 6),
            "population_covariance": round(covariance, 6),
        }

    def z_score_anomalies(
        self,
        name: str,
        threshold: float = 2.0,
    ) -> list[dict[str, Any]]:
        if threshold <= 0:
            raise ValueError("threshold must be positive.")

        values = self.column(name)
        center = mean(values)
        standard_deviation = pstdev(values)

        if standard_deviation == 0:
            return []

        anomalies = []
        for row, value in zip(self.rows, values):
            z = (value - center) / standard_deviation
            if abs(z) >= threshold:
                anomalies.append({
                    "customer_id": row.customer_id,
                    "column": name,
                    "value": value,
                    "z_score": round(z, 4),
                })

        return anomalies

    def iqr_anomalies(self, name: str) -> list[dict[str, Any]]:
        values = self.column(name)
        q1 = self.quantile(values, 0.25)
        q3 = self.quantile(values, 0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        return [
            {
                "customer_id": row.customer_id,
                "column": name,
                "value": value,
                "lower_fence": round(lower, 4),
                "upper_fence": round(upper, 4),
            }
            for row, value in zip(self.rows, values)
            if value < lower or value > upper
        ]

    def covariance_matrix(self, columns: list[str]) -> list[list[float]]:
        if len(columns) < 2:
            raise EDAError("At least two columns are required.")

        matrix = []
        values = {column: self.column(column) for column in columns}

        for column_a in columns:
            row = []
            a = values[column_a]
            a_mean = mean(a)

            for column_b in columns:
                b = values[column_b]
                b_mean = mean(b)
                covariance = sum(
                    (x - a_mean) * (y - b_mean)
                    for x, y in zip(a, b)
                ) / len(a)
                row.append(round(covariance, 6))

            matrix.append(row)

        return matrix

    def multivariate_profile(self, columns: list[str]) -> dict[str, Any]:
        return {
            "columns": columns,
            "rows": len(self.rows),
            "statistics": {
                column: self.descriptive_statistics(column)
                for column in columns
            },
            "covariance_matrix": self.covariance_matrix(columns),
        }

    def segment_by_spend(self) -> dict[str, int]:
        """
        A simple derived categorical variable for multivariate exploration.
        Thresholds are domain rules, not statistical significance claims.
        """
        segments = {"low": 0, "medium": 0, "high": 0}

        for row in self.rows:
            if row.monthly_spend < 300:
                segments["low"] += 1
            elif row.monthly_spend <= 700:
                segments["medium"] += 1
            else:
                segments["high"] += 1

        return segments

    def report(self) -> dict[str, Any]:
        numeric_columns = [
            "age",
            "income",
            "monthly_spend",
            "visits",
            "satisfaction",
        ]

        return {
            "row_count": len(self.rows),
            "univariate": {
                column: self.descriptive_statistics(column)
                for column in numeric_columns
            },
            "distributions": {
                "monthly_spend": self.histogram("monthly_spend", bins=5),
                "satisfaction": self.histogram("satisfaction", bins=5),
            },
            "bivariate": [
                self.bivariate_analysis("income", "monthly_spend"),
                self.bivariate_analysis("visits", "monthly_spend"),
                self.bivariate_analysis("age", "satisfaction"),
            ],
            "multivariate": self.multivariate_profile([
                "age",
                "income",
                "monthly_spend",
                "visits",
                "satisfaction",
            ]),
            "anomalies": {
                "monthly_spend_z_score": self.z_score_anomalies(
                    "monthly_spend",
                    threshold=1.5,
                ),
                "income_iqr": self.iqr_anomalies("income"),
            },
            "derived_segments": self.segment_by_spend(),
        }


def load_observations(records: Iterable[dict[str, Any]]) -> list[Observation]:
    observations = []

    for record in records:
        try:
            observations.append(
                Observation(
                    customer_id=int(record["customer_id"]),
                    age=float(record["age"]),
                    income=float(record["income"]),
                    monthly_spend=float(record["monthly_spend"]),
                    visits=int(record["visits"]),
                    satisfaction=float(record["satisfaction"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EDAError(f"Invalid record: {record}") from exc

    return observations


def main() -> None:
    records = [
        {
            "customer_id": 101,
            "age": 24,
            "income": 42000,
            "monthly_spend": 280,
            "visits": 4,
            "satisfaction": 7.5,
        },
        {
            "customer_id": 102,
            "age": 31,
            "income": 58000,
            "monthly_spend": 450,
            "visits": 6,
            "satisfaction": 8.2,
        },
        {
            "customer_id": 103,
            "age": 45,
            "income": 76000,
            "monthly_spend": 680,
            "visits": 8,
            "satisfaction": 8.7,
        },
        {
            "customer_id": 104,
            "age": 52,
            "income": 91000,
            "monthly_spend": 820,
            "visits": 10,
            "satisfaction": 9.1,
        },
        {
            "customer_id": 105,
            "age": 29,
            "income": 51000,
            "monthly_spend": 390,
            "visits": 5,
            "satisfaction": 7.9,
        },
        {
            "customer_id": 106,
            "age": 38,
            "income": 67000,
            "monthly_spend": 540,
            "visits": 7,
            "satisfaction": 8.4,
        },
        {
            "customer_id": 107,
            "age": 63,
            "income": 125000,
            "monthly_spend": 1450,
            "visits": 18,
            "satisfaction": 6.1,
        },
        {
            "customer_id": 108,
            "age": 41,
            "income": 72000,
            "monthly_spend": 610,
            "visits": 9,
            "satisfaction": 8.8,
        },
        {
            "customer_id": 109,
            "age": 34,
            "income": 47000,
            "monthly_spend": 330,
            "visits": 4,
            "satisfaction": 7.1,
        },
        {
            "customer_id": 110,
            "age": 57,
            "income": 84000,
            "monthly_spend": 760,
            "visits": 11,
            "satisfaction": 8.9,
        },
    ]

    engine = EDAEngine(load_observations(records))

    report = engine.report()

    print(json.dumps(report, indent=2))

    # Assertions act as lightweight executable validation.
    assert report["row_count"] == 10
    assert report["univariate"]["income"]["minimum"] == 42000
    assert len(report["bivariate"]) == 3

    logging.info(
        "EDA completed: %d observations, %d monthly-spend anomalies.",
        report["row_count"],
        len(report["anomalies"]["monthly_spend_z_score"]),
    )


if __name__ == "__main__":
    main()
