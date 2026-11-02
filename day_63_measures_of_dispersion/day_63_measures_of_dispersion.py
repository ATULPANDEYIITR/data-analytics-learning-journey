from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from statistics import median
from pathlib import Path
import json
import tempfile


class DispersionMethod(Enum):
    RANGE = "range"
    VARIANCE = "variance"
    STANDARD_DEVIATION = "standard_deviation"
    IQR = "iqr"
    MAD = "mad"
    COEFFICIENT_OF_VARIATION = "coefficient_of_variation"


@dataclass(frozen=True)
class DispersionReport:
    count: int
    minimum: float
    maximum: float
    range_value: float
    mean: float
    population_variance: float
    sample_variance: float
    population_standard_deviation: float
    sample_standard_deviation: float
    q1: float
    q3: float
    iqr: float
    median_absolute_deviation: float
    coefficient_of_variation_percent: float


class DispersionError(ValueError):
    pass


def validate_data(values: list[float]) -> list[float]:
    if not values:
        raise DispersionError("At least one numeric observation is required.")

    cleaned = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise DispersionError(f"Non-numeric observation: {value!r}")
        if not float("-inf") < float(value) < float("inf"):
            raise DispersionError("Infinite or NaN values are not allowed.")
        cleaned.append(float(value))

    return cleaned


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def calculate_report(values: list[float]) -> DispersionReport:
    values = validate_data(values)
    n = len(values)
    avg = mean(values)

    squared_deviations = [(x - avg) ** 2 for x in values]
    population_variance = sum(squared_deviations) / n
    sample_variance = (
        sum(squared_deviations) / (n - 1) if n > 1 else float("nan")
    )

    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    med = median(values)
    mad = median([abs(x - med) for x in values])

    cv = (
        sqrt(population_variance) / abs(avg) * 100
        if avg != 0
        else float("inf")
    )

    return DispersionReport(
        count=n,
        minimum=min(values),
        maximum=max(values),
        range_value=max(values) - min(values),
        mean=avg,
        population_variance=population_variance,
        sample_variance=sample_variance,
        population_standard_deviation=sqrt(population_variance),
        sample_standard_deviation=(
            sqrt(sample_variance) if n > 1 else float("nan")
        ),
        q1=q1,
        q3=q3,
        iqr=q3 - q1,
        median_absolute_deviation=mad,
        coefficient_of_variation_percent=cv,
    )


def interpret_cv(cv_percent: float) -> str:
    if cv_percent == float("inf"):
        return "Undefined for a zero mean."
    if cv_percent < 10:
        return "Low relative dispersion."
    if cv_percent < 20:
        return "Moderate relative dispersion."
    return "High relative dispersion."


def report_to_dict(report: DispersionReport) -> dict:
    return {
        key: (
            None if isinstance(value, float) and value != value else value
        )
        for key, value in report.__dict__.items()
    }


def save_report(report: DispersionReport, path: Path) -> None:
    path.write_text(
        json.dumps(report_to_dict(report), indent=2),
        encoding="utf-8",
    )


def run_tests() -> None:
    data = [12, 15, 14, 10, 18, 20, 13, 16, 15, 11]

    report = calculate_report(data)

    assert report.count == 10
    assert report.minimum == 10
    assert report.maximum == 20
    assert report.range_value == 10
    assert round(report.mean, 6) == 14.4
    assert report.population_variance > 0
    assert report.population_standard_deviation > 0
    assert report.iqr > 0
    assert report.median_absolute_deviation > 0

    single = calculate_report([5])
    assert single.range_value == 0
    assert single.population_variance == 0
    assert single.iqr == 0
    assert single.median_absolute_deviation == 0

    try:
        calculate_report([])
        raise AssertionError("Empty input should fail.")
    except DispersionError:
        pass

    try:
        calculate_report([1, float("nan")])
        raise AssertionError("NaN input should fail.")
    except DispersionError:
        pass


def main() -> None:
    observations = [12, 15, 14, 10, 18, 20, 13, 16, 15, 11]

    report = calculate_report(observations)

    print("Measures of Dispersion")
    print("======================")
    print(f"Observations:              {report.count}")
    print(f"Minimum:                   {report.minimum:.2f}")
    print(f"Maximum:                   {report.maximum:.2f}")
    print(f"Range:                     {report.range_value:.2f}")
    print(f"Mean:                      {report.mean:.2f}")
    print(f"Population variance:       {report.population_variance:.4f}")
    print(f"Sample variance:            {report.sample_variance:.4f}")
    print(
        f"Population standard deviation: "
        f"{report.population_standard_deviation:.4f}"
    )
    print(
        f"Sample standard deviation: "
        f"{report.sample_standard_deviation:.4f}"
    )
    print(f"Q1:                        {report.q1:.2f}")
    print(f"Q3:                        {report.q3:.2f}")
    print(f"IQR:                       {report.iqr:.2f}")
    print(
        f"Median absolute deviation: "
        f"{report.median_absolute_deviation:.2f}"
    )
    print(
        f"Coefficient of variation: "
        f"{report.coefficient_of_variation_percent:.2f}%"
    )
    print(
        f"CV interpretation: "
        f"{interpret_cv(report.coefficient_of_variation_percent)}"
    )

    with tempfile.TemporaryDirectory() as directory:
        output_path = Path(directory) / "dispersion_report.json"
        save_report(report, output_path)
        print(f"JSON report written to: {output_path}")

    run_tests()
    print("Validation tests: passed")


if __name__ == "__main__":
    main()
