"""
Data Analytics Lifecycle: A Comprehensive Python Study Script

This script demonstrates the major stages of a practical data analytics lifecycle:

1. Problem definition
2. Data acquisition
3. Data preparation
4. Data exploration
5. Analysis
6. Modeling
7. Visualization
8. Communication
9. Deployment
10. Monitoring

The examples use only the Python standard library so the file remains
self-contained and executable without third-party dependencies.

The simulated business scenario:
    An online retail company wants to understand customer purchasing behavior,
    predict whether customers are likely to become high-value customers, and
    monitor the analytical solution after deployment.

The script intentionally contains examples of:
- Structured problem definition
- Synthetic data acquisition
- Missing values and invalid values
- Duplicate detection
- Type conversion
- Feature engineering
- Descriptive statistics
- Correlation
- Segmentation
- Hypothesis-oriented analysis
- A simple logistic regression implementation
- Train/test evaluation
- Classification metrics
- Visualization using ASCII charts
- Communication artifacts
- Model deployment as reusable functions
- Monitoring for data quality and performance drift
- Error handling and validation
- Testing
- Performance considerations
- Production design considerations
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable, Optional


# =============================================================================
# 1. PROBLEM DEFINITION
# =============================================================================

@dataclass
class AnalyticsProblem:
    """
    Represents a structured analytics problem.

    A good analytics project begins with a business problem rather than a
    dataset. The analytical objective should be connected to a measurable
    business outcome.
    """

    business_problem: str
    analytical_question: str
    target_variable: str
    unit_of_analysis: str
    stakeholders: list[str]
    success_metric: str
    constraints: list[str]
    assumptions: list[str]


def define_problem() -> AnalyticsProblem:
    return AnalyticsProblem(
        business_problem=(
            "The retail company wants to identify customers with strong "
            "potential to become high-value customers."
        ),
        analytical_question=(
            "Which customer characteristics and purchasing behaviors are "
            "associated with becoming a high-value customer?"
        ),
        target_variable="is_high_value",
        unit_of_analysis="customer",
        stakeholders=[
            "Marketing team",
            "Sales team",
            "Business leadership",
            "Data analytics team",
        ],
        success_metric=(
            "Achieve useful classification performance while maintaining "
            "interpretable and actionable insights."
        ),
        constraints=[
            "Only historical transactional behavior is available.",
            "The analytical solution must be reproducible.",
            "Predictions must avoid invalid input values.",
        ],
        assumptions=[
            "Historical behavior contains useful predictive signals.",
            "Customer purchasing patterns remain reasonably stable.",
            "High-value status can be approximated using a business rule.",
        ],
    )


def print_problem_definition(problem: AnalyticsProblem) -> None:
    print("\n" + "=" * 80)
    print("1. PROBLEM DEFINITION")
    print("=" * 80)

    for field_name, value in asdict(problem).items():
        print(f"{field_name.replace('_', ' ').title()}: {value}")


# =============================================================================
# 2. DATA ACQUISITION
# =============================================================================

@dataclass
class CustomerRecord:
    customer_id: str
    age: Optional[int]
    region: str
    visits: Optional[int]
    purchases: Optional[int]
    total_spend: Optional[float]
    days_since_last_purchase: Optional[int]
    membership_years: Optional[float]
    is_high_value: Optional[int]


def generate_synthetic_customer_data(
    number_of_customers: int = 300,
    seed: int = 42,
) -> list[dict]:
    """
    Simulates acquisition from a source system.

    Real acquisition may involve:
    - Databases
    - CSV files
    - APIs
    - Event streams
    - Data warehouses
    - Sensors
    - Web logs

    Synthetic generation is used here so the script remains self-contained.
    """

    random.seed(seed)

    regions = ["North", "South", "East", "West"]
    records = []

    for index in range(1, number_of_customers + 1):
        age = random.randint(18, 75)
        visits = random.randint(1, 80)
        purchases = max(
            0,
            int(
                visits
                * random.uniform(0.05, 0.35)
                + random.gauss(0, 2)
            ),
        )

        average_order_value = random.uniform(20, 250)
        total_spend = round(
            max(
                0,
                purchases * average_order_value + random.gauss(0, 100),
            ),
            2,
        )

        days_since_last_purchase = random.randint(0, 365)
        membership_years = round(random.uniform(0, 10), 2)

        # Business-generated target relationship.
        # The relationship is intentionally probabilistic rather than perfect.
        score = (
            0.018 * total_spend
            + 0.04 * purchases
            + 0.02 * visits
            - 0.012 * days_since_last_purchase
            + 0.15 * membership_years
            + random.gauss(0, 2.5)
        )

        is_high_value = 1 if score > 6 else 0

        record = {
            "customer_id": f"C{index:04d}",
            "age": age,
            "region": random.choice(regions),
            "visits": visits,
            "purchases": purchases,
            "total_spend": total_spend,
            "days_since_last_purchase": days_since_last_purchase,
            "membership_years": membership_years,
            "is_high_value": is_high_value,
        }

        records.append(record)

    # Deliberately introduce realistic data quality problems.
    if len(records) >= 10:
        records[2]["age"] = None
        records[5]["total_spend"] = None
        records[8]["visits"] = -3
        records[9]["region"] = "UNKNOWN"

    # Duplicate record.
    if records:
        records.append(records[0].copy())

    return records


def save_records_to_csv(records: list[dict], path: Path) -> None:
    """
    Demonstrates persistence of acquired data.

    CSV is simple and widely supported but has limitations:
    - Weak type information
    - No schema enforcement
    - Difficult nested structures
    - Potential encoding and delimiter problems
    """

    if not records:
        raise ValueError("Cannot save an empty dataset.")

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def load_records_from_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Data source does not exist: {path}")

    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


# =============================================================================
# 3. DATA PREPARATION
# =============================================================================

def convert_to_optional_int(value: object) -> Optional[int]:
    """
    Safely converts a value to int.

    Empty strings and None are treated as missing values.
    """

    if value is None or value == "":
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def convert_to_optional_float(value: object) -> Optional[float]:
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def missing_value_count(records: list[dict], column: str) -> int:
    return sum(
        1
        for record in records
        if record.get(column) is None or record.get(column) == ""
    )


def median(values: Iterable[float]) -> float:
    values = list(values)

    if not values:
        raise ValueError("Median cannot be calculated for an empty sequence.")

    return statistics.median(values)


def remove_duplicate_records(
    records: list[dict],
    key: str,
) -> tuple[list[dict], int]:
    """
    Removes duplicate records using a business key.

    Important production consideration:
    A duplicate definition depends on business semantics. Two records with the
    same customer ID might represent an update, repeated event, or actual
    duplication depending on the source system.
    """

    seen = set()
    unique_records = []
    duplicates_removed = 0

    for record in records:
        value = record.get(key)

        if value in seen:
            duplicates_removed += 1
            continue

        seen.add(value)
        unique_records.append(record)

    return unique_records, duplicates_removed


def validate_record(record: dict) -> list[str]:
    """
    Returns validation errors without immediately stopping the pipeline.

    Production pipelines often separate:
    - Rejectable records
    - Repairable records
    - Warning-only records
    """

    errors = []

    if not record.get("customer_id"):
        errors.append("Missing customer_id")

    age = record.get("age")
    if age is not None and not (0 < age < 120):
        errors.append("Age is outside the valid range")

    visits = record.get("visits")
    if visits is not None and visits < 0:
        errors.append("Visits cannot be negative")

    purchases = record.get("purchases")
    if purchases is not None and purchases < 0:
        errors.append("Purchases cannot be negative")

    total_spend = record.get("total_spend")
    if total_spend is not None and total_spend < 0:
        errors.append("Total spend cannot be negative")

    return errors


def prepare_data(raw_records: list[dict]) -> tuple[list[dict], dict]:
    """
    Performs a simplified ETL/ELT-style preparation process.

    Typical preparation activities include:
    - Schema normalization
    - Missing value handling
    - Duplicate removal
    - Outlier investigation
    - Invalid value correction
    - Feature engineering
    """

    normalized_records = []

    for raw in raw_records:
        normalized_records.append(
            {
                "customer_id": str(raw.get("customer_id", "")).strip(),
                "age": convert_to_optional_int(raw.get("age")),
                "region": str(raw.get("region", "")).strip().title(),
                "visits": convert_to_optional_int(raw.get("visits")),
                "purchases": convert_to_optional_int(raw.get("purchases")),
                "total_spend": convert_to_optional_float(
                    raw.get("total_spend")
                ),
                "days_since_last_purchase": convert_to_optional_int(
                    raw.get("days_since_last_purchase")
                ),
                "membership_years": convert_to_optional_float(
                    raw.get("membership_years")
                ),
                "is_high_value": convert_to_optional_int(
                    raw.get("is_high_value")
                ),
            }
        )

    unique_records, duplicates_removed = remove_duplicate_records(
        normalized_records,
        key="customer_id",
    )

    validation_errors = defaultdict(list)

    for record in unique_records:
        errors = validate_record(record)

        if errors:
            validation_errors[record["customer_id"]].extend(errors)

    # Correct negative visits by treating them as invalid/missing.
    for record in unique_records:
        if record["visits"] is not None and record["visits"] < 0:
            record["visits"] = None

    # Standardize unknown categories.
    allowed_regions = {"North", "South", "East", "West"}

    for record in unique_records:
        if record["region"] not in allowed_regions:
            record["region"] = "Unknown"

    numeric_columns = [
        "age",
        "visits",
        "purchases",
        "total_spend",
        "days_since_last_purchase",
        "membership_years",
    ]

    # Median imputation is more robust than mean imputation when distributions
    # contain strong outliers.
    imputation_values = {}

    for column in numeric_columns:
        valid_values = [
            record[column]
            for record in unique_records
            if record[column] is not None
        ]

        imputation_values[column] = median(valid_values)

        for record in unique_records:
            if record[column] is None:
                record[column] = imputation_values[column]

    # Feature engineering.
    for record in unique_records:
        visits = record["visits"]
        purchases = record["purchases"]
        total_spend = record["total_spend"]

        record["conversion_rate"] = (
            purchases / visits if visits > 0 else 0.0
        )

        record["average_order_value"] = (
            total_spend / purchases if purchases > 0 else 0.0
        )

        record["recent_customer"] = (
            1 if record["days_since_last_purchase"] <= 30 else 0
        )

        record["engagement_score"] = (
            0.5 * visits
            + 2.0 * purchases
            - 0.05 * record["days_since_last_purchase"]
        )

    metadata = {
        "input_records": len(raw_records),
        "prepared_records": len(unique_records),
        "duplicates_removed": duplicates_removed,
        "imputation_values": imputation_values,
        "validation_errors": dict(validation_errors),
    }

    return unique_records, metadata


# =============================================================================
# 4. DATA EXPLORATION
# =============================================================================

def mean(values: Iterable[float]) -> float:
    values = list(values)

    if not values:
        raise ValueError("Mean cannot be calculated for an empty sequence.")

    return sum(values) / len(values)


def sample_standard_deviation(values: Iterable[float]) -> float:
    values = list(values)

    if len(values) < 2:
        return 0.0

    return statistics.stdev(values)


def percentile(values: Iterable[float], percentile_value: float) -> float:
    """
    Calculates a percentile using linear interpolation.
    """

    values = sorted(values)

    if not values:
        raise ValueError("Percentile cannot be calculated for empty data.")

    if not 0 <= percentile_value <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    position = (len(values) - 1) * percentile_value / 100
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))

    if lower_index == upper_index:
        return values[lower_index]

    lower_weight = upper_index - position
    upper_weight = position - lower_index

    return (
        values[lower_index] * lower_weight
        + values[upper_index] * upper_weight
    )


def describe_numeric_column(
    records: list[dict],
    column: str,
) -> dict[str, float]:
    values = [float(record[column]) for record in records]

    return {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "std_dev": sample_standard_deviation(values),
        "minimum": min(values),
        "p25": percentile(values, 25),
        "p75": percentile(values, 75),
        "maximum": max(values),
    }


def detect_iqr_outliers(
    records: list[dict],
    column: str,
) -> list[dict]:
    """
    Detects potential outliers using the Interquartile Range rule.

    Lower bound = Q1 - 1.5 * IQR
    Upper bound = Q3 + 1.5 * IQR

    An outlier is not automatically an error. It may represent:
    - A valid extreme customer
    - A data-entry problem
    - A changed business process
    - Fraud
    """

    values = [float(record[column]) for record in records]

    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return [
        record
        for record in records
        if float(record[column]) < lower_bound
        or float(record[column]) > upper_bound
    ]


def pearson_correlation(
    x_values: list[float],
    y_values: list[float],
) -> float:
    """
    Calculates Pearson correlation.

    Correlation measures linear association, not causation.
    """

    if len(x_values) != len(y_values):
        raise ValueError("Sequences must have the same length.")

    if len(x_values) < 2:
        return 0.0

    x_mean = mean(x_values)
    y_mean = mean(y_values)

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    )

    x_denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in x_values)
    )

    y_denominator = math.sqrt(
        sum((y - y_mean) ** 2 for y in y_values)
    )

    denominator = x_denominator * y_denominator

    if denominator == 0:
        return 0.0

    return numerator / denominator


def explore_data(records: list[dict]) -> dict:
    print("\n" + "=" * 80)
    print("4. DATA EXPLORATION")
    print("=" * 80)

    numeric_columns = [
        "age",
        "visits",
        "purchases",
        "total_spend",
        "days_since_last_purchase",
        "membership_years",
        "conversion_rate",
        "average_order_value",
        "engagement_score",
    ]

    descriptive_statistics = {}

    for column in numeric_columns:
        description = describe_numeric_column(records, column)
        descriptive_statistics[column] = description
        print(f"\n{column.upper()}")
        for metric, value in description.items():
            print(f"  {metric:10}: {value:.3f}")

    region_distribution = Counter(
        record["region"] for record in records
    )

    print("\nREGION DISTRIBUTION")
    for region, count in region_distribution.items():
        print(f"  {region:10}: {count}")

    target_distribution = Counter(
        record["is_high_value"] for record in records
    )

    print("\nTARGET DISTRIBUTION")
    for target, count in sorted(target_distribution.items()):
        label = "High value" if target == 1 else "Not high value"
        print(f"  {label:15}: {count}")

    correlations = {}

    for column in numeric_columns:
        x_values = [
            float(record[column])
            for record in records
        ]

        y_values = [
            float(record["is_high_value"])
            for record in records
        ]

        correlations[column] = pearson_correlation(
            x_values,
            y_values,
        )

    print("\nCORRELATION WITH TARGET")
    for column, value in sorted(
        correlations.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    ):
        print(f"  {column:25}: {value:.4f}")

    outliers = detect_iqr_outliers(records, "total_spend")

    print(
        f"\nPotential total_spend outliers detected: {len(outliers)}"
    )

    return {
        "descriptive_statistics": descriptive_statistics,
        "region_distribution": dict(region_distribution),
        "target_distribution": dict(target_distribution),
        "correlations": correlations,
        "total_spend_outliers": outliers,
    }


# =============================================================================
# 5. ANALYSIS
# =============================================================================

def group_mean(
    records: list[dict],
    group_column: str,
    value_column: str,
) -> dict[str, float]:
    groups = defaultdict(list)

    for record in records:
        groups[str(record[group_column])].append(
            float(record[value_column])
        )

    return {
        group: mean(values)
        for group, values in groups.items()
    }


def customer_segmentation(records: list[dict]) -> list[dict]:
    """
    Creates simple rule-based customer segments.

    Rule-based segmentation is highly interpretable but can be less flexible
    than clustering or learned segmentation.
    """

    segmented_records = []

    for record in records:
        segmented = record.copy()

        if (
            record["total_spend"] >= 2000
            and record["purchases"] >= 10
        ):
            segment = "High Engagement"
        elif record["days_since_last_purchase"] > 180:
            segment = "At Risk"
        elif record["visits"] >= 40:
            segment = "High Interest"
        else:
            segment = "Developing"

        segmented["segment"] = segment
        segmented_records.append(segmented)

    return segmented_records


def analyze_data(records: list[dict]) -> dict:
    print("\n" + "=" * 80)
    print("5. ANALYSIS")
    print("=" * 80)

    spend_by_region = group_mean(
        records,
        "region",
        "total_spend",
    )

    print("\nAVERAGE SPEND BY REGION")
    for region, average_spend in sorted(
        spend_by_region.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"  {region:10}: {average_spend:.2f}")

    high_value_records = [
        record for record in records
        if record["is_high_value"] == 1
    ]

    non_high_value_records = [
        record for record in records
        if record["is_high_value"] == 0
    ]

    high_value_average_spend = mean(
        record["total_spend"]
        for record in high_value_records
    )

    non_high_value_average_spend = mean(
        record["total_spend"]
        for record in non_high_value_records
    )

    print("\nGROUP COMPARISON")
    print(
        f"  High-value average spend: "
        f"{high_value_average_spend:.2f}"
    )
    print(
        f"  Other customer average spend: "
        f"{non_high_value_average_spend:.2f}"
    )

    segmented_records = customer_segmentation(records)

    segment_counts = Counter(
        record["segment"]
        for record in segmented_records
    )

    print("\nCUSTOMER SEGMENTS")
    for segment, count in segment_counts.items():
        print(f"  {segment:20}: {count}")

    return {
        "spend_by_region": spend_by_region,
        "high_value_average_spend": high_value_average_spend,
        "non_high_value_average_spend": non_high_value_average_spend,
        "segment_counts": dict(segment_counts),
        "segmented_records": segmented_records,
    }


# =============================================================================
# 6. MODELING
# =============================================================================

class StandardScaler:
    """
    Standardizes numeric features.

    z = (x - mean) / standard_deviation

    Scaling helps gradient-based optimization when features have very
    different numeric ranges.
    """

    def __init__(self) -> None:
        self.means: list[float] = []
        self.standard_deviations: list[float] = []

    def fit(self, features: list[list[float]]) -> "StandardScaler":
        if not features:
            raise ValueError("Cannot fit scaler on empty features.")

        number_of_columns = len(features[0])

        self.means = []
        self.standard_deviations = []

        for column_index in range(number_of_columns):
            values = [
                row[column_index]
                for row in features
            ]

            column_mean = mean(values)
            column_std = sample_standard_deviation(values)

            # Avoid division by zero for constant features.
            if column_std == 0:
                column_std = 1.0

            self.means.append(column_mean)
            self.standard_deviations.append(column_std)

        return self

    def transform(
        self,
        features: list[list[float]],
    ) -> list[list[float]]:
        if not self.means:
            raise RuntimeError(
                "Scaler must be fitted before transformation."
            )

        return [
            [
                (
                    value - self.means[column_index]
                )
                / self.standard_deviations[column_index]
                for column_index, value in enumerate(row)
            ]
            for row in features
        ]

    def fit_transform(
        self,
        features: list[list[float]],
    ) -> list[list[float]]:
        return self.fit(features).transform(features)


class LogisticRegression:
    """
    Educational implementation of binary logistic regression.

    Logistic regression estimates:

        P(y = 1 | x) = sigmoid(w0 + w1*x1 + ... + wn*xn)

    It is a linear classifier in feature space and produces probabilities.

    This implementation uses batch gradient descent.
    """

    def __init__(
        self,
        learning_rate: float = 0.05,
        iterations: int = 1000,
        l2_penalty: float = 0.01,
    ) -> None:
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")

        if iterations <= 0:
            raise ValueError("iterations must be positive.")

        if l2_penalty < 0:
            raise ValueError("l2_penalty cannot be negative.")

        self.learning_rate = learning_rate
        self.iterations = iterations
        self.l2_penalty = l2_penalty

        self.weights: list[float] = []
        self.bias: float = 0.0
        self.loss_history: list[float] = []

    @staticmethod
    def sigmoid(value: float) -> float:
        """
        Numerically stable sigmoid implementation.
        """

        if value >= 0:
            exponent = math.exp(-value)
            return 1 / (1 + exponent)

        exponent = math.exp(value)
        return exponent / (1 + exponent)

    def predict_proba(
        self,
        features: list[list[float]],
    ) -> list[float]:
        if not self.weights:
            raise RuntimeError("Model must be fitted before prediction.")

        probabilities = []

        for row in features:
            linear_score = self.bias + sum(
                weight * value
                for weight, value in zip(
                    self.weights,
                    row,
                )
            )

            probabilities.append(
                self.sigmoid(linear_score)
            )

        return probabilities

    def predict(
        self,
        features: list[list[float]],
        threshold: float = 0.5,
    ) -> list[int]:
        if not 0 < threshold < 1:
            raise ValueError(
                "Classification threshold must be between 0 and 1."
            )

        probabilities = self.predict_proba(features)

        return [
            1 if probability >= threshold else 0
            for probability in probabilities
        ]

    def binary_cross_entropy(
        self,
        probabilities: list[float],
        targets: list[int],
    ) -> float:
        epsilon = 1e-15

        total_loss = 0.0

        for probability, target in zip(
            probabilities,
            targets,
        ):
            probability = min(
                max(probability, epsilon),
                1 - epsilon,
            )

            total_loss += (
                -target * math.log(probability)
                - (1 - target)
                * math.log(1 - probability)
            )

        data_loss = total_loss / len(targets)

        regularization = (
            self.l2_penalty
            * sum(weight ** 2 for weight in self.weights)
            / (2 * len(targets))
        )

        return data_loss + regularization

    def fit(
        self,
        features: list[list[float]],
        targets: list[int],
    ) -> "LogisticRegression":
        if not features:
            raise ValueError("Training features cannot be empty.")

        if len(features) != len(targets):
            raise ValueError(
                "Features and targets must have equal length."
            )

        number_of_samples = len(features)
        number_of_features = len(features[0])

        if any(
            len(row) != number_of_features
            for row in features
        ):
            raise ValueError(
                "All feature rows must have equal length."
            )

        if any(target not in (0, 1) for target in targets):
            raise ValueError(
                "Binary logistic regression requires targets of 0 or 1."
            )

        self.weights = [0.0] * number_of_features
        self.bias = 0.0
        self.loss_history = []

        for iteration in range(self.iterations):
            probabilities = self.predict_proba(
                features
            ) if self.weights else [0.5] * number_of_samples

            weight_gradients = [0.0] * number_of_features
            bias_gradient = 0.0

            for row, target, probability in zip(
                features,
                targets,
                probabilities,
            ):
                error = probability - target

                for feature_index, value in enumerate(row):
                    weight_gradients[feature_index] += (
                        error * value
                    )

                bias_gradient += error

            for feature_index in range(number_of_features):
                weight_gradient = (
                    weight_gradients[feature_index]
                    / number_of_samples
                    + (
                        self.l2_penalty
                        * self.weights[feature_index]
                        / number_of_samples
                    )
                )

                self.weights[feature_index] -= (
                    self.learning_rate
                    * weight_gradient
                )

            self.bias -= (
                self.learning_rate
                * bias_gradient
                / number_of_samples
            )

            probabilities = self.predict_proba(features)

            loss = self.binary_cross_entropy(
                probabilities,
                targets,
            )

            self.loss_history.append(loss)

            # Simple convergence check.
            if iteration > 20:
                recent_change = abs(
                    self.loss_history[-1]
                    - self.loss_history[-2]
                )

                if recent_change < 1e-9:
                    break

        return self


def train_test_split(
    records: list[dict],
    test_fraction: float = 0.25,
    seed: int = 42,
) -> tuple[list[dict], list[dict]]:
    """
    Splits records into training and testing partitions.

    Important principle:
    Test data must not influence training decisions.

    In time-dependent problems, random splitting may be inappropriate.
    A chronological split can be required to avoid future information leakage.
    """

    if not 0 < test_fraction < 1:
        raise ValueError(
            "test_fraction must be greater than 0 and less than 1."
        )

    shuffled_records = records.copy()
    random.Random(seed).shuffle(shuffled_records)

    split_index = int(
        len(shuffled_records)
        * (1 - test_fraction)
    )

    return (
        shuffled_records[:split_index],
        shuffled_records[split_index:],
    )


def records_to_features(
    records: list[dict],
    feature_names: list[str],
) -> tuple[list[list[float]], list[int]]:
    features = []
    targets = []

    for record in records:
        row = []

        for feature_name in feature_names:
            value = record[feature_name]

            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Feature {feature_name} must be numeric."
                )

            row.append(float(value))

        features.append(row)
        targets.append(int(record["is_high_value"]))

    return features, targets


def classification_metrics(
    actual: list[int],
    predicted: list[int],
) -> dict[str, float | int]:
    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted values must have equal length."
        )

    true_positive = sum(
        1
        for a, p in zip(actual, predicted)
        if a == 1 and p == 1
    )

    true_negative = sum(
        1
        for a, p in zip(actual, predicted)
        if a == 0 and p == 0
    )

    false_positive = sum(
        1
        for a, p in zip(actual, predicted)
        if a == 0 and p == 1
    )

    false_negative = sum(
        1
        for a, p in zip(actual, predicted)
        if a == 1 and p == 0
    )

    total = len(actual)

    accuracy = (
        (true_positive + true_negative) / total
        if total > 0
        else 0.0
    )

    precision = (
        true_positive
        / (true_positive + false_positive)
        if true_positive + false_positive > 0
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if true_positive + false_negative > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return {
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }


@dataclass
class ModelPipeline:
    feature_names: list[str]
    scaler: StandardScaler
    model: LogisticRegression

    def predict_customer(
        self,
        customer: dict,
        threshold: float = 0.5,
    ) -> dict:
        """
        Deployment-style prediction interface.

        Production systems should validate input before prediction.
        """

        row = []

        for feature_name in self.feature_names:
            value = customer.get(feature_name)

            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"Invalid value for feature: {feature_name}"
                )

            row.append(float(value))

        scaled_row = self.scaler.transform([row])

        probability = self.model.predict_proba(
            scaled_row
        )[0]

        prediction = (
            1 if probability >= threshold else 0
        )

        return {
            "probability_high_value": probability,
            "prediction": prediction,
            "threshold": threshold,
        }


def build_and_evaluate_model(
    records: list[dict],
) -> tuple[ModelPipeline, dict]:
    print("\n" + "=" * 80)
    print("6. MODELING")
    print("=" * 80)

    feature_names = [
        "age",
        "visits",
        "purchases",
        "total_spend",
        "days_since_last_purchase",
        "membership_years",
        "conversion_rate",
        "average_order_value",
        "engagement_score",
    ]

    train_records, test_records = train_test_split(
        records,
        test_fraction=0.25,
    )

    train_features, train_targets = (
        records_to_features(
            train_records,
            feature_names,
        )
    )

    test_features, test_targets = (
        records_to_features(
            test_records,
            feature_names,
        )
    )

    scaler = StandardScaler()

    scaled_train_features = scaler.fit_transform(
        train_features
    )

    scaled_test_features = scaler.transform(
        test_features
    )

    model = LogisticRegression(
        learning_rate=0.05,
        iterations=2000,
        l2_penalty=0.01,
    )

    model.fit(
        scaled_train_features,
        train_targets,
    )

    predictions = model.predict(
        scaled_test_features
    )

    metrics = classification_metrics(
        test_targets,
        predictions,
    )

    print("\nMODEL PERFORMANCE")
    for metric, value in metrics.items():
        if isinstance(value, float):
            print(f"  {metric:20}: {value:.4f}")
        else:
            print(f"  {metric:20}: {value}")

    print("\nFEATURE COEFFICIENTS")
    for feature_name, weight in sorted(
        zip(feature_names, model.weights),
        key=lambda item: abs(item[1]),
        reverse=True,
    ):
        print(f"  {feature_name:30}: {weight:.4f}")

    print(
        f"\nTraining iterations completed: "
        f"{len(model.loss_history)}"
    )

    if model.loss_history:
        print(
            f"Initial loss: {model.loss_history[0]:.6f}"
        )
        print(
            f"Final loss:   {model.loss_history[-1]:.6f}"
        )

    pipeline = ModelPipeline(
        feature_names=feature_names,
        scaler=scaler,
        model=model,
    )

    evaluation = {
        "metrics": metrics,
        "train_size": len(train_records),
        "test_size": len(test_records),
        "feature_names": feature_names,
        "loss_history": model.loss_history,
    }

    return pipeline, evaluation


# =============================================================================
# 7. VISUALIZATION
# =============================================================================

def ascii_bar_chart(
    values: dict[str, float],
    title: str,
    width: int = 40,
) -> None:
    """
    Creates a dependency-free text visualization.

    Production analytics often uses graphical libraries and dashboards.
    ASCII visualization is useful for self-contained examples and terminals.
    """

    print("\n" + title)

    if not values:
        print("No data available.")
        return

    maximum = max(values.values())

    if maximum == 0:
        maximum = 1

    for label, value in sorted(
        values.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        bar_length = int(
            abs(value) / maximum * width
        )

        bar = "#" * bar_length

        print(
            f"{label:20} | "
            f"{bar:<{width}} "
            f"{value:.2f}"
        )


def visualize_results(
    exploration: dict,
    analysis: dict,
) -> None:
    print("\n" + "=" * 80)
    print("7. VISUALIZATION")
    print("=" * 80)

    ascii_bar_chart(
        {
            key: float(value)
            for key, value in analysis[
                "spend_by_region"
            ].items()
        },
        "Average Spend by Region",
    )

    ascii_bar_chart(
        {
            key: float(value)
            for key, value in analysis[
                "segment_counts"
            ].items()
        },
        "Customer Segment Counts",
    )

    absolute_correlations = {
        feature: abs(value)
        for feature, value in exploration[
            "correlations"
        ].items()
    }

    ascii_bar_chart(
        absolute_correlations,
        "Absolute Correlation with High-Value Status",
    )


# =============================================================================
# 8. COMMUNICATION
# =============================================================================

def create_business_report(
    problem: AnalyticsProblem,
    exploration: dict,
    analysis: dict,
    evaluation: dict,
) -> str:
    """
    Converts technical analysis into stakeholder-oriented communication.

    Effective communication distinguishes:
    - Observation: what the data shows
    - Interpretation: what the observation may mean
    - Recommendation: what action should be considered
    - Limitation: what the analysis cannot establish
    """

    strongest_feature = max(
        exploration["correlations"].items(),
        key=lambda item: abs(item[1]),
    )

    best_region = max(
        analysis["spend_by_region"].items(),
        key=lambda item: item[1],
    )

    metrics = evaluation["metrics"]

    lines = [
        "DATA ANALYTICS BUSINESS REPORT",
        "",
        "Business Problem",
        problem.business_problem,
        "",
        "Analytical Question",
        problem.analytical_question,
        "",
        "Key Observations",
        (
            f"The strongest linear relationship with high-value status "
            f"in this dataset is {strongest_feature[0]} "
            f"with correlation {strongest_feature[1]:.3f}."
        ),
        (
            f"The region with the highest average spend in this analysis "
            f"is {best_region[0]} at {best_region[1]:.2f}."
        ),
        (
            f"The predictive model achieved accuracy of "
            f"{metrics['accuracy']:.3f} and F1 score of "
            f"{metrics['f1_score']:.3f} on the held-out test set."
        ),
        "",
        "Interpretation",
        (
            "Purchasing activity, engagement, recency, and spending behavior "
            "can provide useful signals for customer prioritization."
        ),
        "",
        "Limitations",
        (
            "Correlation does not establish causation. The synthetic dataset "
            "does not represent every real-world source of bias, seasonality, "
            "data drift, operational change, or customer behavior."
        ),
        (
            "Model performance can decline after deployment if incoming data "
            "differs from training data."
        ),
    ]

    return "\n".join(lines)


def communicate_results(report: str) -> None:
    print("\n" + "=" * 80)
    print("8. COMMUNICATION")
    print("=" * 80)
    print(report)


# =============================================================================
# 9. DEPLOYMENT
# =============================================================================

def serialize_pipeline(
    pipeline: ModelPipeline,
    path: Path,
) -> None:
    """
    Stores a simplified model artifact as JSON.

    Real production systems may require:
    - Versioned artifacts
    - Schema contracts
    - Encryption
    - Access control
    - Reproducible environments
    - Model registries
    """

    artifact = {
        "feature_names": pipeline.feature_names,
        "scaler_means": pipeline.scaler.means,
        "scaler_standard_deviations": (
            pipeline.scaler.standard_deviations
        ),
        "model_weights": pipeline.model.weights,
        "model_bias": pipeline.model.bias,
        "learning_rate": pipeline.model.learning_rate,
        "iterations": pipeline.model.iterations,
        "l2_penalty": pipeline.model.l2_penalty,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            artifact,
            file,
            indent=2,
        )


def load_pipeline(
    path: Path,
) -> ModelPipeline:
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        artifact = json.load(file)

    scaler = StandardScaler()
    scaler.means = artifact["scaler_means"]
    scaler.standard_deviations = (
        artifact["scaler_standard_deviations"]
    )

    model = LogisticRegression(
        learning_rate=artifact["learning_rate"],
        iterations=artifact["iterations"],
        l2_penalty=artifact["l2_penalty"],
    )

    model.weights = artifact["model_weights"]
    model.bias = artifact["model_bias"]

    return ModelPipeline(
        feature_names=artifact["feature_names"],
        scaler=scaler,
        model=model,
    )


def deploy_model_demo(
    pipeline: ModelPipeline,
    sample_customer: dict,
    artifact_path: Path,
) -> None:
    print("\n" + "=" * 80)
    print("9. DEPLOYMENT")
    print("=" * 80)

    serialize_pipeline(
        pipeline,
        artifact_path,
    )

    deployed_pipeline = load_pipeline(
        artifact_path
    )

    prediction = deployed_pipeline.predict_customer(
        sample_customer
    )

    print("Sample deployed prediction:")
    print(
        json.dumps(
            prediction,
            indent=2,
        )
    )


# =============================================================================
# 10. MONITORING
# =============================================================================

def calculate_population_stability_index(
    reference_values: list[float],
    current_values: list[float],
    bins: int = 10,
) -> float:
    """
    Simplified Population Stability Index.

    PSI compares distribution proportions between reference and current data.

    Important limitation:
    PSI thresholds depend on organizational policy and context.
    """

    if not reference_values or not current_values:
        return 0.0

    minimum = min(
        min(reference_values),
        min(current_values),
    )

    maximum = max(
        max(reference_values),
        max(current_values),
    )

    if minimum == maximum:
        return 0.0

    bin_width = (
        maximum - minimum
    ) / bins

    def bin_index(value: float) -> int:
        index = int(
            (value - minimum)
            / bin_width
        )

        return min(
            max(index, 0),
            bins - 1,
        )

    reference_counts = [0] * bins
    current_counts = [0] * bins

    for value in reference_values:
        reference_counts[
            bin_index(value)
        ] += 1

    for value in current_values:
        current_counts[
            bin_index(value)
        ] += 1

    epsilon = 1e-6
    psi = 0.0

    for reference_count, current_count in zip(
        reference_counts,
        current_counts,
    ):
        reference_fraction = max(
            reference_count
            / len(reference_values),
            epsilon,
        )

        current_fraction = max(
            current_count
            / len(current_values),
            epsilon,
        )

        psi += (
            current_fraction
            - reference_fraction
        ) * math.log(
            current_fraction
            / reference_fraction
        )

    return psi


def monitor_pipeline(
    pipeline: ModelPipeline,
    reference_records: list[dict],
    incoming_records: list[dict],
) -> dict:
    print("\n" + "=" * 80)
    print("10. MONITORING")
    print("=" * 80)

    quality_results = {}

    for feature_name in pipeline.feature_names:
        missing_count = sum(
            1
            for record in incoming_records
            if record.get(feature_name) is None
        )

        quality_results[feature_name] = {
            "missing_count": missing_count,
            "missing_rate": (
                missing_count / len(incoming_records)
                if incoming_records
                else 0.0
            ),
        }

    drift_results = {}

    for feature_name in pipeline.feature_names:
        reference_values = [
            float(record[feature_name])
            for record in reference_records
        ]

        current_values = [
            float(record[feature_name])
            for record in incoming_records
            if record.get(feature_name) is not None
        ]

        drift_results[feature_name] = (
            calculate_population_stability_index(
                reference_values,
                current_values,
            )
        )

    print("\nDATA QUALITY")
    for feature_name, result in quality_results.items():
        print(
            f"  {feature_name:30} "
            f"missing_rate={result['missing_rate']:.3f}"
        )

    print("\nDISTRIBUTION DRIFT (PSI)")
    for feature_name, psi in sorted(
        drift_results.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(
            f"  {feature_name:30} PSI={psi:.4f}"
        )

    return {
        "quality": quality_results,
        "drift": drift_results,
        "monitoring_timestamp": (
            datetime.now().isoformat()
        ),
    }


# =============================================================================
# TESTING AND DEBUGGING
# =============================================================================

def run_basic_tests() -> None:
    """
    Small unit-style tests for important assumptions.

    Production systems typically use a dedicated test framework, but Python
    assertions demonstrate the underlying testing principle.
    """

    assert convert_to_optional_int("10") == 10
    assert convert_to_optional_int("") is None
    assert convert_to_optional_float("2.5") == 2.5

    assert median([1, 2, 3]) == 2
    assert median([1, 2, 3, 4]) == 2.5

    assert pearson_correlation(
        [1, 2, 3],
        [1, 2, 3],
    ) > 0.99

    metrics = classification_metrics(
        [1, 0, 1, 0],
        [1, 0, 0, 0],
    )

    assert metrics["true_positive"] == 1
    assert metrics["true_negative"] == 2
    assert metrics["false_negative"] == 1

    scaler = StandardScaler()

    scaled = scaler.fit_transform(
        [[1.0, 10.0], [2.0, 20.0]]
    )

    assert len(scaled) == 2
    assert len(scaled[0]) == 2


# =============================================================================
# PRODUCTION AND PERFORMANCE CONSIDERATIONS
# =============================================================================

def demonstrate_streaming_processing(
    records: Iterable[dict],
) -> dict[str, float]:
    """
    Demonstrates memory-efficient aggregation.

    Loading a very large dataset entirely into memory can be expensive.
    Streaming aggregation processes one record at a time.
    """

    total_spend = 0.0
    count = 0

    for record in records:
        value = record.get("total_spend")

        if isinstance(value, (int, float)):
            total_spend += float(value)
            count += 1

    return {
        "count": count,
        "average_total_spend": (
            total_spend / count
            if count > 0
            else 0.0
        ),
    }


def explain_production_considerations() -> None:
    print("\n" + "=" * 80)
    print("PRODUCTION CONSIDERATIONS")
    print("=" * 80)

    considerations = [
        "Version datasets, code, transformations, and model artifacts.",
        "Validate schemas before processing.",
        "Prevent data leakage between training and evaluation.",
        "Monitor missing values, drift, failures, latency, and prediction quality.",
        "Restrict access to customer data using appropriate authorization.",
        "Avoid logging unnecessary sensitive information.",
        "Define rollback procedures for failed deployments.",
        "Use reproducible random seeds where deterministic experiments are required.",
        "Investigate business impact, not only statistical model metrics.",
    ]

    for number, consideration in enumerate(
        considerations,
        start=1,
    ):
        print(f"{number}. {consideration}")


# =============================================================================
# COMPLETE LIFECYCLE EXECUTION
# =============================================================================

def main() -> None:
    start_time = time.perf_counter()

    print("=" * 80)
    print("COMPREHENSIVE DATA ANALYTICS LIFECYCLE")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # Stage 1: Define the business and analytical problem.
    # -------------------------------------------------------------------------
    problem = define_problem()
    print_problem_definition(problem)

    # -------------------------------------------------------------------------
    # Stage 2: Acquire raw data.
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. DATA ACQUISITION")
    print("=" * 80)

    raw_records = generate_synthetic_customer_data(
        number_of_customers=300,
        seed=42,
    )

    raw_data_path = Path(
        "customer_raw_data.csv"
    )

    save_records_to_csv(
        raw_records,
        raw_data_path,
    )

    acquired_records = load_records_from_csv(
        raw_data_path
    )

    print(
        f"Raw records acquired: "
        f"{len(acquired_records)}"
    )

    # -------------------------------------------------------------------------
    # Stage 3: Prepare and validate data.
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. DATA PREPARATION")
    print("=" * 80)

    prepared_records, preparation_metadata = (
        prepare_data(
            acquired_records
        )
    )

    print(
        f"Prepared records: "
        f"{preparation_metadata['prepared_records']}"
    )

    print(
        f"Duplicates removed: "
        f"{preparation_metadata['duplicates_removed']}"
    )

    print("Imputation values:")
    for column, value in (
        preparation_metadata[
            "imputation_values"
        ].items()
    ):
        print(
            f"  {column:30}: {value:.3f}"
        )

    if preparation_metadata[
        "validation_errors"
    ]:
        print("\nValidation issues detected before correction:")
        for customer_id, errors in (
            preparation_metadata[
                "validation_errors"
            ].items()
        ):
            print(
                f"  {customer_id}: "
                f"{'; '.join(errors)}"
            )

    # -------------------------------------------------------------------------
    # Stage 4: Explore data.
    # -------------------------------------------------------------------------
    exploration = explore_data(
        prepared_records
    )

    # -------------------------------------------------------------------------
    # Stage 5: Perform analytical comparisons and segmentation.
    # -------------------------------------------------------------------------
    analysis = analyze_data(
        prepared_records
    )

    # -------------------------------------------------------------------------
    # Stage 6: Build and evaluate a predictive model.
    # -------------------------------------------------------------------------
    pipeline, evaluation = (
        build_and_evaluate_model(
            prepared_records
        )
    )

    # -------------------------------------------------------------------------
    # Stage 7: Visualize findings.
    # -------------------------------------------------------------------------
    visualize_results(
        exploration,
        analysis,
    )

    # -------------------------------------------------------------------------
    # Stage 8: Communicate findings.
    # -------------------------------------------------------------------------
    report = create_business_report(
        problem,
        exploration,
        analysis,
        evaluation,
    )

    communicate_results(report)

    report_path = Path(
        "analytics_business_report.txt"
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    # -------------------------------------------------------------------------
    # Stage 9: Serialize and deploy the analytical pipeline.
    # -------------------------------------------------------------------------
    sample_customer = prepared_records[0]

    model_artifact_path = Path(
        "customer_value_model.json"
    )

    deploy_model_demo(
        pipeline,
        sample_customer,
        model_artifact_path,
    )

    # -------------------------------------------------------------------------
    # Stage 10: Monitor incoming data.
    # -------------------------------------------------------------------------
    incoming_records = generate_synthetic_customer_data(
        number_of_customers=100,
        seed=999,
    )

    prepared_incoming_records, _ = (
        prepare_data(
            incoming_records
        )
    )

    monitoring_results = monitor_pipeline(
        pipeline,
        prepared_records,
        prepared_incoming_records,
    )

    monitoring_path = Path(
        "monitoring_results.json"
    )

    with monitoring_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            monitoring_results,
            file,
            indent=2,
        )

    # -------------------------------------------------------------------------
    # Testing and performance.
    # -------------------------------------------------------------------------
    run_basic_tests()

    streaming_result = (
        demonstrate_streaming_processing(
            iter(prepared_records)
        )
    )

    print("\nSTREAMING AGGREGATION")
    print(
        json.dumps(
            streaming_result,
            indent=2,
        )
    )

    explain_production_considerations()

    elapsed_time = (
        time.perf_counter()
        - start_time
    )

    print("\n" + "=" * 80)
    print(
        f"Lifecycle execution completed in "
        f"{elapsed_time:.4f} seconds."
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
