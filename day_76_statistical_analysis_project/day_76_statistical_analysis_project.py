#!/usr/bin/env python3
"""
Statistical Analysis Project
Hypothesis testing, relationship analysis, permutation inference,
bootstrap confidence intervals, and statistical reporting.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence


@dataclass(frozen=True)
class Observation:
    participant_id: int
    study_hours: float
    exam_score: float

    def __post_init__(self):
        if self.participant_id <= 0:
            raise ValueError("Participant ID must be positive.")
        if not math.isfinite(self.study_hours) or self.study_hours < 0:
            raise ValueError("Study hours must be finite and non-negative.")
        if not math.isfinite(self.exam_score):
            raise ValueError("Exam score must be finite.")
        if not 0 <= self.exam_score <= 100:
            raise ValueError("Exam score must be between 0 and 100.")


@dataclass
class StatisticalResult:
    name: str
    estimate: float
    confidence_level: float
    confidence_interval: tuple[float, float]
    p_value: float
    hypothesis: str
    conclusion: str


class StatisticalAnalysisError(Exception):
    """Raised when a statistical operation cannot be performed."""


class StatisticalAnalyzer:
    ALPHA = 0.05

    def __init__(
        self,
        observations: Sequence[Observation],
        seed: int = 42
    ):
        if len(observations) < 4:
            raise ValueError("At least four observations are required.")

        ids = [item.participant_id for item in observations]
        if len(ids) != len(set(ids)):
            raise ValueError("Participant IDs must be unique.")

        self.data = tuple(observations)
        self.random = random.Random(seed)

        self.x = [item.study_hours for item in self.data]
        self.y = [item.exam_score for item in self.data]

        if len(set(self.x)) < 2 or len(set(self.y)) < 2:
            raise StatisticalAnalysisError(
                "Both variables must contain variation."
            )

    @staticmethod
    def mean(values):
        return statistics.fmean(values)

    @staticmethod
    def pearson(x, y):
        if len(x) != len(y) or len(x) < 3:
            raise ValueError("Equal samples with at least three values required.")

        mx = statistics.fmean(x)
        my = statistics.fmean(y)

        numerator = sum(
            (a - mx) * (b - my)
            for a, b in zip(x, y)
        )

        sx = sum((a - mx) ** 2 for a in x)
        sy = sum((b - my) ** 2 for b in y)

        denominator = math.sqrt(sx * sy)

        if denominator == 0:
            raise StatisticalAnalysisError("Correlation is undefined.")

        return numerator / denominator

    @staticmethod
    def regression_slope(x, y):
        mx = statistics.fmean(x)
        my = statistics.fmean(y)

        denominator = sum((value - mx) ** 2 for value in x)

        if denominator == 0:
            raise StatisticalAnalysisError("Regression slope is undefined.")

        return sum(
            (a - mx) * (b - my)
            for a, b in zip(x, y)
        ) / denominator

    @staticmethod
    def percentile(values, probability):
        if not values or not 0 <= probability <= 1:
            raise ValueError("Invalid percentile request.")

        ordered = sorted(values)
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

    def bootstrap_interval(
        self,
        statistic: Callable,
        iterations=5000,
        confidence=0.95
    ):
        if iterations < 1000:
            raise ValueError("Use at least 1000 bootstrap iterations.")

        if not 0 < confidence < 1:
            raise ValueError("Confidence level must be between 0 and 1.")

        estimates = []
        n = len(self.data)

        # Resample complete observations to preserve paired relationships.
        for _ in range(iterations):
            sample = [
                self.data[self.random.randrange(n)]
                for _ in range(n)
            ]

            sample_x = [item.study_hours for item in sample]
            sample_y = [item.exam_score for item in sample]

            try:
                estimates.append(statistic(sample_x, sample_y))
            except StatisticalAnalysisError:
                continue
            except ZeroDivisionError:
                continue

        if len(estimates) < iterations * 0.95:
            raise StatisticalAnalysisError(
                "Too many invalid bootstrap samples."
            )

        tail = (1 - confidence) / 2

        return (
            self.percentile(estimates, tail),
            self.percentile(estimates, 1 - tail)
        )

    def permutation_test(self, iterations=10000):
        """
        H0: Study hours and examination scores have no association.

        Randomly permutes the outcome variable while keeping
        study hours fixed.
        """
        if iterations < 1000:
            raise ValueError("At least 1000 permutations are required.")

        observed = abs(self.pearson(self.x, self.y))
        extreme = 0

        for _ in range(iterations):
            shuffled = self.y.copy()
            self.random.shuffle(shuffled)

            simulated = abs(self.pearson(self.x, shuffled))

            if simulated >= observed:
                extreme += 1

        # The plus-one correction prevents a zero Monte Carlo p-value.
        return (extreme + 1) / (iterations + 1)

    def descriptive_statistics(self):
        return {
            "sample_size": len(self.data),
            "study_hours": {
                "mean": self.mean(self.x),
                "median": statistics.median(self.x),
                "standard_deviation": statistics.stdev(self.x),
                "minimum": min(self.x),
                "maximum": max(self.x),
            },
            "exam_scores": {
                "mean": self.mean(self.y),
                "median": statistics.median(self.y),
                "standard_deviation": statistics.stdev(self.y),
                "minimum": min(self.y),
                "maximum": max(self.y),
            },
        }

    def analyze_relationship(self):
        correlation = self.pearson(self.x, self.y)
        slope = self.regression_slope(self.x, self.y)

        correlation_ci = self.bootstrap_interval(
            self.pearson
        )

        slope_ci = self.bootstrap_interval(
            self.regression_slope
        )

        p_value = self.permutation_test()

        conclusion = (
            "Statistically significant evidence of an association."
            if p_value < self.ALPHA
            else "Insufficient evidence of an association."
        )

        return StatisticalResult(
            name="Pearson correlation",
            estimate=correlation,
            confidence_level=0.95,
            confidence_interval=correlation_ci,
            p_value=p_value,
            hypothesis="H0: Population correlation equals zero.",
            conclusion=conclusion
        ), {
            "regression_slope": slope,
            "slope_confidence_interval": slope_ci,
            "intercept": (
                self.mean(self.y)
                - slope * self.mean(self.x)
            )
        }

    def evaluate_regression(self, slope, intercept):
        predictions = [
            intercept + slope * value
            for value in self.x
        ]

        residuals = [
            actual - predicted
            for actual, predicted in zip(self.y, predictions)
        ]

        ss_res = sum(value ** 2 for value in residuals)
        mean_y = self.mean(self.y)
        ss_tot = sum((value - mean_y) ** 2 for value in self.y)

        r_squared = 1 - ss_res / ss_tot

        return {
            "r_squared": r_squared,
            "root_mean_squared_error": math.sqrt(
                statistics.mean(value ** 2 for value in residuals)
            ),
            "mean_absolute_error": statistics.mean(
                abs(value) for value in residuals
            ),
        }

    def generate_report(self):
        result, regression = self.analyze_relationship()

        report = {
            "project": "Statistical Relationship Analysis",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "descriptive_statistics": self.descriptive_statistics(),
            "hypothesis_test": asdict(result),
            "regression": {
                **regression,
                **self.evaluate_regression(
                    regression["regression_slope"],
                    regression["intercept"]
                )
            },
            "interpretation": {
                "direction": (
                    "positive" if result.estimate > 0 else "negative"
                ),
                "strength": (
                    "strong" if abs(result.estimate) >= 0.7
                    else "moderate" if abs(result.estimate) >= 0.4
                    else "weak"
                ),
                "significance_threshold": self.ALPHA,
                "causality_warning": (
                    "Association does not establish causation."
                )
            }
        }

        return report


def create_sample_data():
    records = [
        (1, 1.0, 48),
        (2, 1.5, 52),
        (3, 2.0, 55),
        (4, 2.5, 58),
        (5, 3.0, 62),
        (6, 3.5, 65),
        (7, 4.0, 68),
        (8, 4.5, 70),
        (9, 5.0, 74),
        (10, 5.5, 77),
        (11, 6.0, 80),
        (12, 7.0, 86),
    ]

    return [Observation(*record) for record in records]


def run_validation_tests():
    assert abs(
        StatisticalAnalyzer.pearson(
            [1, 2, 3, 4],
            [2, 4, 6, 8]
        ) - 1.0
    ) < 1e-10

    assert abs(
        StatisticalAnalyzer.regression_slope(
            [1, 2, 3],
            [2, 4, 6]
        ) - 2.0
    ) < 1e-10

    assert StatisticalAnalyzer.percentile(
        [1, 2, 3, 4, 5], 0.5
    ) == 3

    try:
        Observation(0, 2, 50)
        raise AssertionError("Invalid participant ID was accepted.")
    except ValueError:
        pass

    try:
        StatisticalAnalyzer.pearson(
            [1, 1, 1],
            [2, 3, 4]
        )
        raise AssertionError("Undefined correlation was accepted.")
    except StatisticalAnalysisError:
        pass


def main():
    run_validation_tests()

    analyzer = StatisticalAnalyzer(
        create_sample_data(),
        seed=42
    )

    report = analyzer.generate_report()

    output_path = Path("statistical_analysis_report.json")

    # Write the report atomically to avoid leaving a partial JSON file.
    temporary_path = output_path.with_suffix(".json.tmp")

    try:
        temporary_path.write_text(
            json.dumps(report, indent=4, allow_nan=False),
            encoding="utf-8"
        )
        temporary_path.replace(output_path)
    except OSError:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    print("=" * 65)
    print("STATISTICAL ANALYSIS PROJECT")
    print("=" * 65)

    print(json.dumps(report, indent=4))

    print("\nReport saved:", output_path.resolve())


if __name__ == "__main__":
    main()
