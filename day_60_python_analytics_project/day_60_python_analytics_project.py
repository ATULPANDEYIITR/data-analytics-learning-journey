#!/usr/bin/env python3
"""
Comprehensive Exploratory Data Analysis of the Iris Dataset.

Dataset: UCI Machine Learning Repository, Iris (150 observations).
DOI: https://doi.org/10.24432/C56C76
License: Creative Commons Attribution 4.0 International.

Features:
- Reproducible dataset acquisition and CSV loading
- Data validation and cleaning
- Missing-value and duplicate detection
- Descriptive statistics and percentile analysis
- Species distribution and group comparisons
- IQR-based outlier detection
- Pearson correlation analysis
- Automated analytical report generation
- Cleaned dataset export
- Offline fallback dataset
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import statistics
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DATASET_URL = (
    "https://archive.ics.uci.edu/ml/"
    "machine-learning-databases/iris/iris.data"
)

FEATURES = (
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
)

SPECIES = {"setosa", "versicolor", "virginica"}

SAMPLE_DATA = """sepal_length,sepal_width,petal_length,petal_width,species
5.1,3.5,1.4,0.2,setosa
4.9,3.0,1.4,0.2,setosa
4.7,3.2,1.3,0.2,setosa
4.6,3.1,1.5,0.2,setosa
5.0,3.6,1.4,0.2,setosa
7.0,3.2,4.7,1.4,versicolor
6.4,3.2,4.5,1.5,versicolor
6.9,3.1,4.9,1.5,versicolor
5.5,2.3,4.0,1.3,versicolor
6.5,2.8,4.6,1.5,versicolor
6.3,3.3,6.0,2.5,virginica
5.8,2.7,5.1,1.9,virginica
7.1,3.0,5.9,2.1,virginica
6.3,2.9,5.6,1.8,virginica
6.5,3.0,5.8,2.2,virginica
"""


class DataValidationError(Exception):
    """Raised when a dataset cannot be analyzed."""


@dataclass(frozen=True)
class Flower:
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    def values(self) -> tuple[float, ...]:
        return (
            self.sepal_length,
            self.sepal_width,
            self.petal_length,
            self.petal_width,
        )


@dataclass
class Dataset:
    observations: list[Flower]
    rejected_rows: list[str]
    source: str

    @property
    def row_count(self) -> int:
        return len(self.observations)


@dataclass(frozen=True)
class StatisticsResult:
    minimum: float
    q1: float
    median: float
    mean: float
    q3: float
    maximum: float
    standard_deviation: float
    outlier_count: int


def normalize_species(value: str) -> str:
    normalized = value.strip().lower().replace("iris-", "")
    normalized = normalized.replace(" ", "")

    if normalized == "versicolour":
        normalized = "versicolor"

    if normalized not in SPECIES:
        raise DataValidationError(
            f"Unknown species category: {value!r}"
        )

    return normalized


def parse_observation(row: list[str]) -> Flower:
    if len(row) != 5:
        raise DataValidationError(
            f"Expected five columns, received {len(row)}."
        )

    try:
        values = tuple(float(value.strip()) for value in row[:4])
    except (ValueError, TypeError) as exc:
        raise DataValidationError(
            "A measurement is not numeric."
        ) from exc

    if not all(math.isfinite(value) for value in values):
        raise DataValidationError(
            "Non-finite measurements are not permitted."
        )

    if any(value <= 0 or value >= 10 for value in values):
        raise DataValidationError(
            "Measurements must be greater than zero and below ten."
        )

    species = normalize_species(row[4])

    return Flower(*values, species)


def download_dataset(destination: Path) -> bool:
    """Download the original UCI CSV without external dependencies."""
    request = urllib.request.Request(
        DATASET_URL,
        headers={"User-Agent": "Python-Iris-EDA/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            content = response.read()

        if not content:
            return False

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return True

    except Exception as exc:
        print(f"Dataset download unavailable: {exc}")
        return False


def load_dataset(
    input_path: Path,
    offline: bool = False,
) -> Dataset:

    source = str(input_path)

    if input_path.exists():
        content = input_path.read_text(encoding="utf-8-sig")
        source = f"Local CSV: {input_path}"

    elif not offline and download_dataset(input_path):
        content = input_path.read_text(encoding="utf-8-sig")
        source = f"UCI dataset downloaded to {input_path}"

    else:
        content = SAMPLE_DATA
        source = "Embedded genuine Iris observation subset"

    reader = csv.reader(io.StringIO(content))

    observations: list[Flower] = []
    rejected_rows: list[str] = []
    seen: set[tuple] = set()

    for line_number, row in enumerate(reader, start=1):

        if not row or all(not value.strip() for value in row):
            continue

        if row[0].strip().lower() in {
            "sepal_length",
            "sepallengthcm",
            "sepal length",
        }:
            continue

        try:
            flower = parse_observation(row)
            observations.append(flower)

            key = (
                flower.values(),
                flower.species,
            )

            if key in seen:
                rejected_rows.append(
                    f"Line {line_number}: duplicate observation detected."
                )
            else:
                seen.add(key)

        except DataValidationError as exc:
            rejected_rows.append(
                f"Line {line_number}: {exc}"
            )

    if not observations:
        raise DataValidationError(
            "No valid observations were available for analysis."
        )

    return Dataset(observations, rejected_rows, source)


def quantile(values: list[float], probability: float) -> float:
    """Calculate an interpolated percentile using linear interpolation."""
    ordered = sorted(values)

    if not ordered:
        raise ValueError("Cannot calculate a quantile of an empty list.")

    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
        ordered[lower] * (1 - fraction)
        + ordered[upper] * fraction
    )


def calculate_statistics(
    values: list[float],
) -> StatisticsResult:

    if not values:
        raise ValueError("Statistics require at least one observation.")

    q1 = quantile(values, 0.25)
    q3 = quantile(values, 0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = sum(
        value < lower_bound or value > upper_bound
        for value in values
    )

    return StatisticsResult(
        minimum=min(values),
        q1=q1,
        median=statistics.median(values),
        mean=statistics.mean(values),
        q3=q3,
        maximum=max(values),
        standard_deviation=(
            statistics.stdev(values)
            if len(values) > 1
            else 0.0
        ),
        outlier_count=outliers,
    )


def pearson_correlation(
    first: list[float],
    second: list[float],
) -> Optional[float]:

    if len(first) != len(second) or len(first) < 2:
        return None

    mean_first = statistics.mean(first)
    mean_second = statistics.mean(second)

    numerator = sum(
        (x - mean_first) * (y - mean_second)
        for x, y in zip(first, second)
    )

    denominator_first = math.sqrt(
        sum((x - mean_first) ** 2 for x in first)
    )

    denominator_second = math.sqrt(
        sum((y - mean_second) ** 2 for y in second)
    )

    denominator = denominator_first * denominator_second

    if denominator == 0:
        return None

    return numerator / denominator


def feature_values(
    observations: list[Flower],
    feature_index: int,
) -> list[float]:

    return [flower.values()[feature_index] for flower in observations]


def class_distribution(
    observations: list[Flower],
) -> dict[str, int]:

    counts = Counter(
        flower.species for flower in observations
    )

    return {
        species: counts.get(species, 0)
        for species in sorted(SPECIES)
    }


def analyze_by_species(
    observations: list[Flower],
) -> dict[str, dict[str, float]]:

    groups: dict[str, list[Flower]] = defaultdict(list)

    for flower in observations:
        groups[flower.species].append(flower)

    results = {}

    for species, flowers in sorted(groups.items()):
        results[species] = {}

        for index, feature in enumerate(FEATURES):
            values = feature_values(flowers, index)
            results[species][feature] = statistics.mean(values)

    return results


def build_correlation_matrix(
    observations: list[Flower],
) -> list[list[Optional[float]]]:

    matrix = []

    for first_index in range(len(FEATURES)):
        row = []

        for second_index in range(len(FEATURES)):
            correlation = pearson_correlation(
                feature_values(observations, first_index),
                feature_values(observations, second_index),
            )

            row.append(correlation)

        matrix.append(row)

    return matrix


def assess_data_quality(dataset: Dataset) -> dict:
    observations = dataset.observations

    duplicate_count = len(
        observations
    ) - len({
        (flower.values(), flower.species)
        for flower in observations
    })

    return {
        "valid_rows": len(observations),
        "rejected_rows": len(dataset.rejected_rows),
        "missing_cells": 0,
        "duplicate_observations": duplicate_count,
        "species_count": len({
            flower.species for flower in observations
        }),
    }


def format_number(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def create_report(dataset: Dataset) -> str:

    observations = dataset.observations
    distribution = class_distribution(observations)
    species_means = analyze_by_species(observations)
    correlations = build_correlation_matrix(observations)
    quality = assess_data_quality(dataset)

    lines = [
        "# Exploratory Data Analysis: Iris Dataset",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Dataset Overview",
        "",
        f"- Source: {dataset.source}",
        "- Original dataset: UCI Iris, Fisher (1936).",
        f"- Valid observations: {len(observations)}",
        "- Numerical features: 4",
        "- Target variable: species",
        "- Measurement unit: centimetres",
        "",
        "## 2. Data Quality Assessment",
        "",
        "| Metric | Result |",
        "|---|---:|",
    ]

    for key, value in quality.items():
        lines.append(f"| {key.replace('_', ' ').title()} | {value} |")

    lines.extend([
        "",
        "## 3. Species Distribution",
        "",
        "| Species | Observations | Percentage |",
        "|---|---:|---:|",
    ])

    for species, count in distribution.items():
        percentage = count / len(observations) * 100
        lines.append(
            f"| {species.title()} | {count} | {percentage:.2f}% |"
        )

    lines.extend([
        "",
        "## 4. Descriptive Statistics",
        "",
        "| Feature | Min | Q1 | Median | Mean | Q3 | Max | Sample SD | Outliers |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for index, feature in enumerate(FEATURES):
        result = calculate_statistics(
            feature_values(observations, index)
        )

        lines.append(
            f"| {feature} | "
            f"{result.minimum:.3f} | "
            f"{result.q1:.3f} | "
            f"{result.median:.3f} | "
            f"{result.mean:.3f} | "
            f"{result.q3:.3f} | "
            f"{result.maximum:.3f} | "
            f"{result.standard_deviation:.3f} | "
            f"{result.outlier_count} |"
        )

    lines.extend([
        "",
        "## 5. Feature Means by Species",
        "",
        "| Species | Sepal Length | Sepal Width | Petal Length | Petal Width |",
        "|---|---:|---:|---:|---:|",
    ])

    for species, means in species_means.items():
        lines.append(
            f"| {species.title()} | "
            + " | ".join(
                f"{means[feature]:.3f}"
                for feature in FEATURES
            )
            + " |"
        )

    lines.extend([
        "",
        "## 6. Pearson Correlation Matrix",
        "",
        "| Feature | " + " | ".join(FEATURES) + " |",
        "|" + "---|" * (len(FEATURES) + 1),
    ])

    for index, feature in enumerate(FEATURES):
        cells = [
            format_number(value)
            for value in correlations[index]
        ]

        lines.append(
            f"| {feature} | " + " | ".join(cells) + " |"
        )

    lines.extend([
        "",
        "## 7. Analytical Findings",
        "",
    ])

    petal_length_index = FEATURES.index("petal_length")
    petal_width_index = FEATURES.index("petal_width")

    petal_correlation = correlations[
        petal_length_index
    ][petal_width_index]

    lines.append(
        f"- Petal length and petal width Pearson correlation: "
        f"{format_number(petal_correlation)}."
    )

    largest_mean_species = max(
        species_means,
        key=lambda species: species_means[species]["petal_length"],
    )

    smallest_mean_species = min(
        species_means,
        key=lambda species: species_means[species]["petal_length"],
    )

    lines.append(
        f"- Highest mean petal length: {largest_mean_species} "
        f"({species_means[largest_mean_species]['petal_length']:.3f} cm)."
    )

    lines.append(
        f"- Lowest mean petal length: {smallest_mean_species} "
        f"({species_means[smallest_mean_species]['petal_length']:.3f} cm)."
    )

    lines.extend([
        "- Outliers are identified with the 1.5 × IQR rule. "
        "They are flagged, not automatically removed.",
        "- Correlation measures linear association and does not establish causation.",
        "- Results describe the observations actually loaded; a fallback subset "
        "must not be interpreted as the complete 150-observation dataset.",
        "",
        "## 8. Methodological Limitations",
        "",
        "- The Iris dataset is small and balanced by design.",
        "- It contains only four continuous measurements and one categorical label.",
        "- The dataset is not representative of all plant species.",
        "- Pearson correlation captures linear relationships only.",
        "- Outlier flags require domain interpretation before removal.",
        "",
        "## 9. Data Provenance",
        "",
        "Fisher, R. A. (1936). The Use of Multiple Measurements in "
        "Taxonomic Problems.",
        "",
        "UCI Machine Learning Repository: Iris Dataset.",
        "",
        "https://doi.org/10.24432/C56C76",
        "",
        "License: CC BY 4.0.",
        "",
        "---",
        "",
        "End of analytical report.",
    ])

    return "\n".join(lines)


def export_cleaned_data(
    observations: list[Flower],
    destination: Path,
) -> None:

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            *FEATURES,
            "species",
        ])

        for flower in observations:
            writer.writerow([
                *flower.values(),
                flower.species,
            ])


def print_console_report(dataset: Dataset) -> None:

    print("\n" + "=" * 65)
    print("IRIS DATASET: EXPLORATORY DATA ANALYSIS")
    print("=" * 65)

    print(f"Source: {dataset.source}")
    print(f"Valid observations: {dataset.row_count}")
    print(f"Rejected rows: {len(dataset.rejected_rows)}")

    print("\nSpecies distribution:")

    for species, count in class_distribution(
        dataset.observations
    ).items():
        print(f"  {species:12s} {count:4d}")

    print("\nFeature statistics:")

    for index, feature in enumerate(FEATURES):
        result = calculate_statistics(
            feature_values(dataset.observations, index)
        )

        print(
            f"{feature:15s} "
            f"mean={result.mean:.3f} "
            f"median={result.median:.3f} "
            f"std={result.standard_deviation:.3f} "
            f"outliers={result.outlier_count}"
        )

    print("\nCorrelation matrix:")

    print(" " * 17 + " ".join(
        f"{feature[:8]:>10s}" for feature in FEATURES
    ))

    for index, feature in enumerate(FEATURES):
        values = build_correlation_matrix(
            dataset.observations
        )[index]

        print(
            f"{feature:15s} "
            + " ".join(
                f"{value:10.4f}" if value is not None
                else f"{'N/A':>10s}"
                for value in values
            )
        )


def main() -> int:

    parser = argparse.ArgumentParser(
        description="Complete exploratory analysis of the Iris dataset."
    )

    parser.add_argument(
        "--input",
        default="iris.csv",
        help="Path to the input CSV file.",
    )

    parser.add_argument(
        "--output-dir",
        default="iris_eda_output",
        help="Directory for generated files.",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use an existing CSV or the embedded sample without downloading.",
    )

    arguments = parser.parse_args()

    try:
        input_path = Path(arguments.input)
        output_dir = Path(arguments.output_dir)

        dataset = load_dataset(
            input_path,
            arguments.offline,
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path = output_dir / "analytical_report.md"
        cleaned_path = output_dir / "iris_cleaned.csv"

        report = create_report(dataset)

        report_path.write_text(
            report,
            encoding="utf-8",
        )

        export_cleaned_data(
            dataset.observations,
            cleaned_path,
        )

        print_console_report(dataset)

        print("\nGenerated files:")
        print(f"  Report:  {report_path}")
        print(f"  Cleaned: {cleaned_path}")

        if dataset.rejected_rows:
            rejection_path = output_dir / "rejected_rows.txt"

            rejection_path.write_text(
                "\n".join(dataset.rejected_rows),
                encoding="utf-8",
            )

            print(f"  Rejections: {rejection_path}")

        print("\nAnalysis completed successfully.")
        return 0

    except (
        DataValidationError,
        OSError,
        ValueError,
    ) as exc:

        print(f"Analysis failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
