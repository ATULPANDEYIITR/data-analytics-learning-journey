from __future__ import annotations

import json
import math
import random
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Any, Iterable


# ============================================================
# POWER BI ADVANCED ANALYTICS
# Decomposition Trees, Key Influencers, Forecasting,
# and Anomaly Detection
#
# Dependencies: Python 3.10+
# Uses only the Python standard library.
# ============================================================


class AnalyticsError(Exception):
    """Base exception for analytics operations."""


class ValidationError(AnalyticsError):
    """Raised when analytical input is invalid."""


class InsufficientDataError(AnalyticsError):
    """Raised when an analysis has insufficient observations."""


class AnalysisType(Enum):
    DECOMPOSITION = "decomposition"
    KEY_INFLUENCERS = "key_influencers"
    FORECAST = "forecast"
    ANOMALY = "anomaly"


@dataclass(frozen=True)
class SalesRecord:
    transaction_id: int
    transaction_date: date
    region: str
    product: str
    segment: str
    channel: str
    revenue: float
    units: int
    marketing_spend: float
    discount: float
    customer_satisfaction: float

    def validate(self) -> None:
        if self.transaction_id <= 0:
            raise ValidationError("Transaction ID must be positive.")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.region, self.product, self.segment, self.channel)
        ):
            raise ValidationError("Categorical fields cannot be empty.")

        numeric_values = (
            self.revenue,
            self.marketing_spend,
            self.discount,
            self.customer_satisfaction,
        )

        if not all(math.isfinite(value) for value in numeric_values):
            raise ValidationError("Numeric values must be finite.")

        if self.revenue < 0 or self.marketing_spend < 0:
            raise ValidationError("Revenue and marketing spend cannot be negative.")

        if self.units < 0:
            raise ValidationError("Units cannot be negative.")

        if not 0 <= self.discount <= 100:
            raise ValidationError("Discount must be between 0 and 100.")

        if not 0 <= self.customer_satisfaction <= 10:
            raise ValidationError("Satisfaction must be between 0 and 10.")


@dataclass
class DecompositionNode:
    dimension: str
    value: str
    revenue: float
    record_count: int
    contribution: float
    children: list["DecompositionNode"]


@dataclass
class InfluencerResult:
    dimension: str
    value: str
    sample_size: int
    comparison_size: int
    target_average: float
    comparison_average: float
    difference: float
    relative_change_percent: float


@dataclass
class ForecastPoint:
    period: str
    actual: float | None
    predicted: float
    lower_bound: float
    upper_bound: float


@dataclass
class AnomalyResult:
    transaction_id: int
    actual: float
    expected: float
    deviation: float
    anomaly_score: float
    severity: str


# ============================================================
# DATA GENERATION
# ============================================================

def generate_sales_data(
    number_of_records: int = 600,
    seed: int = 42,
) -> list[SalesRecord]:

    if number_of_records < 30:
        raise ValidationError("At least 30 records are required.")

    rng = random.Random(seed)

    regions = ["North", "South", "East", "West"]
    products = ["Laptop", "Mobile", "Tablet", "Monitor"]
    segments = ["Consumer", "Corporate", "Small Business"]
    channels = ["Online", "Retail", "Partner"]

    records = []
    start_date = date(2025, 1, 1)

    for index in range(number_of_records):

        transaction_date = start_date + timedelta(days=index % 365)

        region = rng.choice(regions)
        product = rng.choice(products)
        segment = rng.choice(segments)
        channel = rng.choice(channels)

        units = rng.randint(1, 12)

        base_prices = {
            "Laptop": 850,
            "Mobile": 420,
            "Tablet": 300,
            "Monitor": 260,
        }

        regional_factor = {
            "North": 1.15,
            "South": 1.05,
            "East": 0.90,
            "West": 1.10,
        }

        segment_factor = {
            "Consumer": 1.0,
            "Corporate": 1.30,
            "Small Business": 1.10,
        }

        discount = rng.uniform(0, 20)

        revenue = (
            base_prices[product]
            * units
            * regional_factor[region]
            * segment_factor[segment]
            * (1 - discount / 100)
        )

        revenue += rng.gauss(0, 90)
        revenue = max(0, revenue)

        marketing_spend = rng.uniform(50, 600)
        satisfaction = min(10, max(0, rng.gauss(7.5, 1.1)))

        # Inject occasional unusual transactions for anomaly analysis.
        if index in (75, 190, 330, 470):
            revenue *= 3.5

        records.append(
            SalesRecord(
                transaction_id=index + 1,
                transaction_date=transaction_date,
                region=region,
                product=product,
                segment=segment,
                channel=channel,
                revenue=round(revenue, 2),
                units=units,
                marketing_spend=round(marketing_spend, 2),
                discount=round(discount, 2),
                customer_satisfaction=round(satisfaction, 2),
            )
        )

    for record in records:
        record.validate()

    return records


# ============================================================
# DATA VALIDATION AND MEASURES
# ============================================================

class SalesAnalytics:

    DIMENSIONS = {
        "region",
        "product",
        "segment",
        "channel",
    }

    def __init__(self, records: Iterable[SalesRecord]):
        self.records = list(records)

        if not self.records:
            raise InsufficientDataError("Dataset cannot be empty.")

        seen_ids = set()

        for record in self.records:
            record.validate()

            if record.transaction_id in seen_ids:
                raise ValidationError("Duplicate transaction ID.")

            seen_ids.add(record.transaction_id)

        self.total_revenue = sum(r.revenue for r in self.records)

    def measure(self) -> dict[str, float]:
        total_revenue = sum(r.revenue for r in self.records)
        total_units = sum(r.units for r in self.records)
        total_marketing = sum(r.marketing_spend for r in self.records)

        return {
            "transaction_count": len(self.records),
            "total_revenue": round(total_revenue, 2),
            "total_units": total_units,
            "average_revenue": round(total_revenue / len(self.records), 2),
            "average_order_value": round(
                total_revenue / max(1, len(self.records)), 2
            ),
            "marketing_spend": round(total_marketing, 2),
            "marketing_roi": round(
                (total_revenue - total_marketing) / max(total_marketing, 1),
                3,
            ),
            "average_satisfaction": round(
                statistics.mean(r.customer_satisfaction for r in self.records),
                2,
            ),
        }

    # ========================================================
    # 1. DECOMPOSITION TREE
    # ========================================================

    def decomposition_tree(
        self,
        dimensions: list[str],
        top_n: int = 5,
    ) -> list[DecompositionNode]:

        if not dimensions:
            raise ValidationError("At least one dimension is required.")

        if len(set(dimensions)) != len(dimensions):
            raise ValidationError("Duplicate dimensions are not allowed.")

        if any(dimension not in self.DIMENSIONS for dimension in dimensions):
            raise ValidationError("Unsupported decomposition dimension.")

        if top_n < 1:
            raise ValidationError("top_n must be positive.")

        def build_node(
            records: list[SalesRecord],
            dimension_index: int,
        ) -> list[DecompositionNode]:

            if dimension_index >= len(dimensions):
                return []

            dimension = dimensions[dimension_index]
            grouped = defaultdict(list)

            for record in records:
                grouped[getattr(record, dimension)].append(record)

            parent_total = sum(r.revenue for r in records)

            ordered = sorted(
                grouped.items(),
                key=lambda item: sum(r.revenue for r in item[1]),
                reverse=True,
            )[:top_n]

            nodes = []

            for value, group_records in ordered:

                revenue = sum(r.revenue for r in group_records)

                contribution = (
                    revenue / parent_total * 100
                    if parent_total > 0
                    else 0
                )

                nodes.append(
                    DecompositionNode(
                        dimension=dimension,
                        value=str(value),
                        revenue=round(revenue, 2),
                        record_count=len(group_records),
                        contribution=round(contribution, 2),
                        children=build_node(
                            group_records,
                            dimension_index + 1,
                        ),
                    )
                )

            return nodes

        return build_node(self.records, 0)

    # ========================================================
    # 2. KEY INFLUENCERS
    # ========================================================

    def key_influencers(
        self,
        target: str,
        dimensions: list[str] | None = None,
        minimum_group_size: int = 10,
    ) -> list[InfluencerResult]:

        if target not in {
            "high_revenue",
            "high_satisfaction",
            "high_discount",
        }:
            raise ValidationError("Unsupported target.")

        if minimum_group_size < 2:
            raise ValidationError("Minimum group size must be at least 2.")

        dimensions = dimensions or [
            "region",
            "product",
            "segment",
            "channel",
        ]

        if any(d not in self.DIMENSIONS for d in dimensions):
            raise ValidationError("Unsupported influencer dimension.")

        if target == "high_revenue":
            values = [r.revenue for r in self.records]

        elif target == "high_satisfaction":
            values = [r.customer_satisfaction for r in self.records]

        else:
            values = [r.discount for r in self.records]

        threshold = statistics.median(values)

        def matches(record: SalesRecord) -> bool:
            value = getattr(record, {
                "high_revenue": "revenue",
                "high_satisfaction": "customer_satisfaction",
                "high_discount": "discount",
            }[target])

            return value > threshold

        results = []

        for dimension in dimensions:

            groups = defaultdict(list)

            for record in self.records:
                groups[getattr(record, dimension)].append(record)

            for value, group in groups.items():

                if len(group) < minimum_group_size:
                    continue

                target_group = [r for r in group if matches(r)]

                comparison_group = [
                    r for r in self.records
                    if getattr(r, dimension) != value
                ]

                if not comparison_group:
                    continue

                target_rate = len(target_group) / len(group)

                comparison_rate = (
                    sum(matches(r) for r in comparison_group)
                    / len(comparison_group)
                )

                difference = target_rate - comparison_rate

                if difference <= 0:
                    continue

                relative_change = (
                    difference / comparison_rate * 100
                    if comparison_rate > 0
                    else 100.0
                )

                results.append(
                    InfluencerResult(
                        dimension=dimension,
                        value=str(value),
                        sample_size=len(group),
                        comparison_size=len(comparison_group),
                        target_average=round(target_rate, 4),
                        comparison_average=round(comparison_rate, 4),
                        difference=round(difference, 4),
                        relative_change_percent=round(
                            relative_change, 2
                        ),
                    )
                )

        return sorted(
            results,
            key=lambda result: (
                result.difference,
                result.sample_size,
            ),
            reverse=True,
        )

    # ========================================================
    # 3. TIME-SERIES FORECASTING
    # ========================================================

    def monthly_revenue(self) -> list[tuple[str, float]]:

        grouped = defaultdict(float)

        for record in self.records:
            month = record.transaction_date.strftime("%Y-%m")
            grouped[month] += record.revenue

        return sorted(grouped.items())

    @staticmethod
    def linear_regression(
        values: list[float],
    ) -> tuple[float, float]:

        if len(values) < 3:
            raise InsufficientDataError(
                "At least three observations are required."
            )

        x_values = list(range(len(values)))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        denominator = sum(
            (x - x_mean) ** 2 for x in x_values
        )

        if denominator == 0:
            raise InsufficientDataError("Regression denominator is zero.")

        slope = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(x_values, values)
        ) / denominator

        intercept = y_mean - slope * x_mean

        return intercept, slope

    def forecast(
        self,
        periods: int = 3,
        seasonal_period: int = 0,
    ) -> list[ForecastPoint]:

        if periods < 1 or periods > 36:
            raise ValidationError("Forecast periods must be between 1 and 36.")

        monthly = self.monthly_revenue()

        if len(monthly) < 6:
            raise InsufficientDataError(
                "At least six monthly observations are required."
            )

        values = [value for _, value in monthly]

        if seasonal_period < 0:
            raise ValidationError("Seasonal period cannot be negative.")

        if seasonal_period and len(values) < seasonal_period * 2:
            raise InsufficientDataError(
                "Two complete seasonal cycles are required."
            )

        intercept, slope = self.linear_regression(values)

        residuals = [
            actual - (intercept + slope * index)
            for index, actual in enumerate(values)
        ]

        residual_std = (
            statistics.stdev(residuals)
            if len(residuals) > 1
            else 0
        )

        last_month = date.fromisoformat(monthly[-1][0] + "-01")

        results = []

        for step in range(1, periods + 1):

            index = len(values) - 1 + step

            predicted = intercept + slope * index

            # Seasonal adjustment uses the observed average trend
            # within the same seasonal position.
            if seasonal_period:
                seasonal_indices = [
                    i for i in range(len(values))
                    if i % seasonal_period == index % seasonal_period
                ]

                if seasonal_indices:
                    seasonal_component = statistics.mean(
                        residuals[i] for i in seasonal_indices
                    )

                    predicted += seasonal_component

            predicted = max(0, predicted)

            month_number = last_month.month - 1 + step
            year = last_month.year + month_number // 12
            month = month_number % 12 + 1

            period = f"{year:04d}-{month:02d}"

            uncertainty = 1.96 * residual_std * math.sqrt(
                1 + step / len(values)
            )

            results.append(
                ForecastPoint(
                    period=period,
                    actual=None,
                    predicted=round(predicted, 2),
                    lower_bound=round(max(0, predicted - uncertainty), 2),
                    upper_bound=round(predicted + uncertainty, 2),
                )
            )

        return results

    # ========================================================
    # 4. ANOMALY DETECTION
    # ========================================================

    @staticmethod
    def median_absolute_deviation(values: list[float]) -> tuple[float, float]:

        median = statistics.median(values)

        deviations = [
            abs(value - median)
            for value in values
        ]

        mad = statistics.median(deviations)

        return median, mad

    def detect_anomalies(
        self,
        threshold: float = 3.5,
    ) -> list[AnomalyResult]:

        if not math.isfinite(threshold) or threshold <= 0:
            raise ValidationError("Threshold must be positive and finite.")

        values = [r.revenue for r in self.records]

        median, mad = self.median_absolute_deviation(values)

        if mad == 0:
            raise InsufficientDataError(
                "MAD is zero; the dataset cannot support this detector."
            )

        results = []

        for record in self.records:

            score = (
                0.6745 * (record.revenue - median) / mad
            )

            if abs(score) >= threshold:

                severity = (
                    "CRITICAL"
                    if abs(score) >= 7
                    else "HIGH"
                )

                results.append(
                    AnomalyResult(
                        transaction_id=record.transaction_id,
                        actual=record.revenue,
                        expected=round(median, 2),
                        deviation=round(record.revenue - median, 2),
                        anomaly_score=round(score, 3),
                        severity=severity,
                    )
                )

        return sorted(
            results,
            key=lambda item: abs(item.anomaly_score),
            reverse=True,
        )

    # ========================================================
    # 5. EXPORT AND REPORTING
    # ========================================================

    def export_report(self, output_file: str) -> None:

        report = {
            "metrics": self.measure(),
            "decomposition": [
                asdict(node)
                for node in self.decomposition_tree(
                    ["region", "product", "channel"]
                )
            ],
            "key_influencers": [
                asdict(item)
                for item in self.key_influencers("high_revenue")
            ],
            "forecast": [
                asdict(item)
                for item in self.forecast(3)
            ],
            "anomalies": [
                asdict(item)
                for item in self.detect_anomalies()
            ],
        }

        # Write atomically to avoid leaving a partially written report.
        import os
        import tempfile

        destination = os.path.abspath(output_file)
        directory = os.path.dirname(destination)

        os.makedirs(directory, exist_ok=True)

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = file.name

                json.dump(
                    report,
                    file,
                    indent=2,
                    default=str,
                    allow_nan=False,
                )

            os.replace(temporary_path, destination)

        except OSError:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)
            raise


# ============================================================
# APPLICATION EXECUTION
# ============================================================

def main() -> None:

    print("=" * 65)
    print("POWER BI ADVANCED ANALYTICS ENGINE")
    print("=" * 65)

    records = generate_sales_data()

    analytics = SalesAnalytics(records)

    print("\n1. BUSINESS MEASURES")

    for name, value in analytics.measure().items():
        print(f"{name:25}: {value}")

    print("\n2. DECOMPOSITION TREE")

    tree = analytics.decomposition_tree(
        ["region", "product", "channel"],
        top_n=3,
    )

    def display_tree(nodes, level=0):
        for node in nodes:
            indentation = "  " * level

            print(
                f"{indentation}{node.dimension}: {node.value} | "
                f"Revenue={node.revenue:.2f} | "
                f"Contribution={node.contribution:.2f}%"
            )

            display_tree(node.children, level + 1)

    display_tree(tree)

    print("\n3. KEY INFLUENCERS")

    influencers = analytics.key_influencers(
        "high_revenue",
        minimum_group_size=10,
    )

    for result in influencers[:8]:
        print(
            f"{result.dimension}={result.value} | "
            f"Target rate={result.target_average:.2%} | "
            f"Comparison={result.comparison_average:.2%} | "
            f"Difference={result.difference:.2%}"
        )

    print("\n4. MONTHLY REVENUE FORECAST")

    for point in analytics.forecast(
        periods=3,
        seasonal_period=0,
    ):
        print(
            f"{point.period}: "
            f"Prediction={point.predicted:.2f}, "
            f"Interval=[{point.lower_bound:.2f}, "
            f"{point.upper_bound:.2f}]"
        )

    print("\n5. ANOMALY DETECTION")

    anomalies = analytics.detect_anomalies(threshold=3.5)

    for anomaly in anomalies[:10]:
        print(
            f"Transaction={anomaly.transaction_id} | "
            f"Revenue={anomaly.actual:.2f} | "
            f"Score={anomaly.anomaly_score} | "
            f"Severity={anomaly.severity}"
        )

    print(f"\nDetected anomalies: {len(anomalies)}")

    print("\n6. REPORT EXPORT")

    analytics.export_report("powerbi_advanced_analytics_report.json")

    print("Report exported successfully.")

    # Basic executable validation.
    assert analytics.measure()["transaction_count"] == 600
    assert len(tree) > 0
    assert len(analytics.forecast(2)) == 2
    assert all(
        item.anomaly_score >= 3.5 or item.anomaly_score <= -3.5
        for item in anomalies
    )

    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
