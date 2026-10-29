from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite, log, sqrt
from pathlib import Path
from statistics import mean, median, pstdev
import csv
import json
import random
import tempfile


class Transform(str, Enum):
    NONE = "none"
    LOG1P = "log1p"
    SQRT = "sqrt"
    ZSCORE = "zscore"
    ROBUST = "robust"


@dataclass(frozen=True)
class Observation:
    customer_id: int
    income: float
    spending: float
    visits: float
    tenure_months: float
    complaints: float


@dataclass
class FeatureSummary:
    name: str
    count: int
    mean: float
    median: float
    stddev: float
    skewness: float
    lower_fence: float
    upper_fence: float
    outliers: list[float]


def validate_numeric(values: list[float], name: str) -> None:
    if not values:
        raise ValueError(f"{name} cannot be empty")
    if any(not isfinite(v) for v in values):
        raise ValueError(f"{name} contains non-finite values")


def quantile(values: list[float], q: float) -> float:
    validate_numeric(values, "values")
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")

    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered))
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def pearson(x: list[float], y: list[float]) -> float:
    validate_numeric(x, "x")
    validate_numeric(y, "y")
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Pearson correlation requires equal non-empty samples")

    mx, my = mean(x), mean(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = sqrt(sum((a - mx) ** 2 for a in x))
    dy = sqrt(sum((b - my) ** 2 for b in y))
    if dx == 0 or dy == 0:
        return 0.0
    return numerator / (dx * dy)


def covariance(x: list[float], y: list[float]) -> float:
    validate_numeric(x, "x")
    validate_numeric(y, "y")
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Covariance requires equal samples with at least two values")
    mx, my = mean(x), mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (len(x) - 1)


def sample_skewness(values: list[float]) -> float:
    validate_numeric(values, "values")
    n = len(values)
    if n < 3:
        return 0.0

    m = mean(values)
    s = sqrt(sum((v - m) ** 2 for v in values) / (n - 1))
    if s == 0:
        return 0.0

    return n / ((n - 1) * (n - 2)) * sum(
        ((v - m) / s) ** 3 for v in values
    )


def iqr_outliers(values: list[float]) -> tuple[float, float, list[float]]:
    q1, q3 = quantile(values, 0.25), quantile(values, 0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return lower, upper, [v for v in values if v < lower or v > upper]


def summarize(values: list[float], name: str) -> FeatureSummary:
    validate_numeric(values, name)
    lower, upper, outliers = iqr_outliers(values)
    return FeatureSummary(
        name=name,
        count=len(values),
        mean=mean(values),
        median=median(values),
        stddev=pstdev(values),
        skewness=sample_skewness(values),
        lower_fence=lower,
        upper_fence=upper,
        outliers=outliers,
    )


def transform(values: list[float], operation: Transform) -> list[float]:
    validate_numeric(values, "values")

    if operation == Transform.NONE:
        return values.copy()

    if operation == Transform.LOG1P:
        if any(v <= -1 for v in values):
            raise ValueError("log1p requires every value to be greater than -1")
        return [log1p(v) for v in values]

    if operation == Transform.SQRT:
        if any(v < 0 for v in values):
            raise ValueError("sqrt requires non-negative values")
        return [sqrt(v) for v in values]

    if operation == Transform.ZSCORE:
        m = mean(values)
        s = pstdev(values)
        return [0.0 if s == 0 else (v - m) / s for v in values]

    if operation == Transform.ROBUST:
        med = median(values)
        q1, q3 = quantile(values, 0.25), quantile(values, 0.75)
        scale = q3 - q1
        return [0.0 if scale == 0 else (v - med) / scale for v in values]

    raise ValueError(f"Unsupported transformation: {operation}")


def rank_correlation(x: list[float], y: list[float]) -> float:
    def ranks(values: list[float]) -> list[float]:
        indexed = sorted(enumerate(values), key=lambda item: item[1])
        result = [0.0] * len(values)
        i = 0
        while i < len(indexed):
            j = i
            while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
                j += 1
            rank = (i + j + 2) / 2
            for k in range(i, j + 1):
                result[indexed[k][0]] = rank
            i = j + 1
        return result

    return pearson(ranks(x), ranks(y))


def relationship_matrix(data: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    names = list(data)
    return {
        a: {b: round(pearson(data[a], data[b]), 4) for b in names}
        for a in names
    }


def load_csv(path: Path) -> list[Observation]:
    records: list[Observation] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "customer_id", "income", "spending", "visits",
            "tenure_months", "complaints"
        }
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("CSV is missing required columns")

        for row in reader:
            records.append(
                Observation(
                    customer_id=int(row["customer_id"]),
                    income=float(row["income"]),
                    spending=float(row["spending"]),
                    visits=float(row["visits"]),
                    tenure_months=float(row["tenure_months"]),
                    complaints=float(row["complaints"]),
                )
            )
    return records


def create_sample_csv(path: Path) -> None:
    random.seed(42)
    base = [
        (1, 42000, 1100, 3, 8, 2),
        (2, 48000, 1350, 4, 14, 1),
        (3, 51000, 1500, 5, 18, 1),
        (4, 56000, 1720, 6, 25, 0),
        (5, 62000, 1900, 7, 30, 0),
        (6, 68000, 2150, 8, 36, 1),
        (7, 72000, 2450, 9, 42, 0),
        (8, 79000, 2600, 10, 48, 0),
        (9, 85000, 3000, 11, 52, 1),
        (10, 91000, 3200, 12, 60, 0),
        (11, 47000, 1250, 4, 12, 3),
        (12, 53000, 1550, 5, 21, 2),
        (13, 60000, 1820, 7, 28, 1),
        (14, 74000, 2300, 9, 45, 0),
        (15, 1500000, 3500, 3, 10, 5),
        (16, 45000, 1050, 2, 5, 7),
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "customer_id", "income", "spending", "visits",
            "tenure_months", "complaints"
        ])
        writer.writerows(base)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        csv_path = Path(directory) / "customers.csv"
        create_sample_csv(csv_path)
        observations = load_csv(csv_path)

        features = {
            "income": [o.income for o in observations],
            "spending": [o.spending for o in observations],
            "visits": [o.visits for o in observations],
            "tenure_months": [o.tenure_months for o in observations],
            "complaints": [o.complaints for o in observations],
        }

        print("ADVANCED EXPLORATORY DATA ANALYSIS")
        print("=" * 60)

        summaries = {
            name: summarize(values, name)
            for name, values in features.items()
        }

        for summary in summaries.values():
            print(f"\n{summary.name}")
            print(f"  count       : {summary.count}")
            print(f"  mean        : {summary.mean:.3f}")
            print(f"  median      : {summary.median:.3f}")
            print(f"  stddev      : {summary.stddev:.3f}")
            print(f"  skewness    : {summary.skewness:.3f}")
            print(f"  IQR fences  : [{summary.lower_fence:.3f}, "
                  f"{summary.upper_fence:.3f}]")
            print(f"  outliers    : {summary.outliers}")

        print("\nCORRELATION MATRIX")
        matrix = relationship_matrix(features)
        for name, row in matrix.items():
            print(name.ljust(14), " ".join(f"{v:7.3f}" for v in row.values()))

        print("\nCOVARIANCE AND RANK CORRELATION")
        for a, b in [
            ("income", "spending"),
            ("visits", "spending"),
            ("complaints", "spending"),
        ]:
            print(
                f"{a} vs {b}: covariance={covariance(features[a], features[b]):.3f}, "
                f"Spearman={rank_correlation(features[a], features[b]):.3f}"
            )

        income_log = transform(features["income"], Transform.LOG1P)
        print("\nTRANSFORMATION DIAGNOSTIC")
        print(
            f"income skewness before={sample_skewness(features['income']):.3f}, "
            f"after log1p={sample_skewness(income_log):.3f}"
        )

        robust_spending = transform(features["spending"], Transform.ROBUST)
        print(
            f"robust spending range: "
            f"{min(robust_spending):.3f} to {max(robust_spending):.3f}"
        )

        print("\nHIGH-CORRELATION RELATIONSHIPS")
        names = list(features)
        for i, left in enumerate(names):
            for right in names[i + 1:]:
                r = pearson(features[left], features[right])
                if abs(r) >= 0.70:
                    print(f"  {left} <-> {right}: r={r:.3f}")

        print("\nEDGE-CASE VALIDATION")
        try:
            transform([-2, 3], Transform.SQRT)
        except ValueError as exc:
            print(f"  rejected invalid sqrt input: {exc}")

        try:
            pearson([1, 1, 1], [2, 3, 4])
        except Exception as exc:
            print(f"  unexpected failure: {exc}")

        print("\nPRODUCTION NOTES")
        print("  - Validate schema and finite numeric values before analysis.")
        print("  - Inspect outliers rather than deleting them automatically.")
        print("  - Use rank correlation when monotonic relationships are non-linear.")
        print("  - Transformation choices must preserve domain meaning.")
        print("  - Correlation is not evidence of causation.")
        print("  - Keep preprocessing parameters derived from training data only.")

        report = {
            "features": {
                name: {
                    "mean": summary.mean,
                    "median": summary.median,
                    "skewness": summary.skewness,
                    "outliers": summary.outliers,
                }
                for name, summary in summaries.items()
            },
            "correlation": matrix,
        }
        print("\nREPORT JSON")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
