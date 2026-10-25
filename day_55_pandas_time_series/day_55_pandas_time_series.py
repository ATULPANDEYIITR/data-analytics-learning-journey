from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

import pandas as pd


class WindowMode(str, Enum):
    ROWS = "rows"
    TIME = "time"


@dataclass(frozen=True)
class TimeSeriesConfig:
    timezone_name: str = "UTC"
    frequency: str = "D"
    rolling_days: int = 7


def build_sensor_series() -> pd.DataFrame:
    """Create realistic irregular sensor observations."""
    timestamps = pd.to_datetime(
        [
            "2026-01-01 08:00",
            "2026-01-01 12:00",
            "2026-01-02 09:30",
            "2026-01-03 10:00",
            "2026-01-05 14:00",
            "2026-01-06 11:15",
            "2026-01-08 16:30",
            "2026-01-10 09:00",
            "2026-01-12 13:45",
            "2026-01-14 15:00",
        ],
        utc=True,
    )

    return pd.DataFrame(
        {
            "temperature": [21.2, 22.1, 20.8, 23.4, 24.0, 23.2, 25.1, 26.0, 24.7, 27.2],
            "pressure": [1008, 1007, 1009, 1006, 1005, 1007, 1004, 1003, 1005, 1002],
            "energy_kwh": [3.1, 2.4, 3.7, 4.0, 5.1, 4.4, 5.8, 6.2, 5.0, 6.7],
        },
        index=pd.DatetimeIndex(timestamps, name="timestamp"),
    )


def validate_datetime_index(frame: pd.DataFrame) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("A DatetimeIndex is required.")

    if not frame.index.is_monotonic_increasing:
        raise ValueError("DatetimeIndex must be sorted chronologically.")

    if frame.index.has_duplicates:
        raise ValueError("Duplicate timestamps are not allowed.")

    if frame.empty:
        raise ValueError("Time-series data cannot be empty.")


def normalize_timezone(frame: pd.DataFrame, timezone_name: str) -> pd.DataFrame:
    validate_datetime_index(frame)

    if frame.index.tz is None:
        result = frame.copy()
        result.index = result.index.tz_localize(timezone_name)
        return result

    result = frame.copy()
    result.index = result.index.tz_convert(timezone_name)
    return result


def daily_resampling(frame: pd.DataFrame) -> pd.DataFrame:
    validate_datetime_index(frame)

    return frame.resample("D").agg(
        {
            "temperature": "mean",
            "pressure": "mean",
            "energy_kwh": "sum",
        }
    )


def hourly_interpolation(frame: pd.DataFrame) -> pd.DataFrame:
    validate_datetime_index(frame)

    hourly = frame.resample("h").asfreq()

    numeric_columns = hourly.select_dtypes(include="number").columns
    hourly[numeric_columns] = hourly[numeric_columns].interpolate(
        method="time",
        limit=6,
        limit_direction="both",
    )

    return hourly


def calculate_time_based_rolling(frame: pd.DataFrame, days: int) -> pd.DataFrame:
    validate_datetime_index(frame)

    result = frame.copy()
    window = f"{days}D"

    result["temperature_rolling_mean"] = (
        result["temperature"].rolling(window=window, min_periods=2).mean()
    )

    result["temperature_rolling_std"] = (
        result["temperature"].rolling(window=window, min_periods=2).std()
    )

    result["energy_rolling_sum"] = (
        result["energy_kwh"].rolling(window=window, min_periods=1).sum()
    )

    return result


def calculate_shifts_and_changes(frame: pd.DataFrame) -> pd.DataFrame:
    validate_datetime_index(frame)

    result = frame.copy()

    result["temperature_previous"] = result["temperature"].shift(1)
    result["temperature_change"] = result["temperature"].diff()
    result["energy_growth_ratio"] = result["energy_kwh"].pct_change()

    return result


def group_by_calendar_period(frame: pd.DataFrame) -> pd.DataFrame:
    validate_datetime_index(frame)

    return (
        frame.groupby(frame.index.to_period("W"))
        .agg(
            temperature_mean=("temperature", "mean"),
            temperature_max=("temperature", "max"),
            energy_total=("energy_kwh", "sum"),
            observation_count=("temperature", "size"),
        )
        .reset_index(names="week")
    )


def group_by_month_and_hour(frame: pd.DataFrame) -> pd.DataFrame:
    validate_datetime_index(frame)

    return (
        frame.groupby(
            [
                frame.index.month.rename("month"),
                frame.index.hour.rename("hour"),
            ]
        )
        .agg(
            mean_temperature=("temperature", "mean"),
            total_energy=("energy_kwh", "sum"),
            samples=("temperature", "size"),
        )
        .reset_index()
        .sort_values(["month", "hour"])
    )


def detect_temperature_anomalies(
    frame: pd.DataFrame,
    threshold: float = 2.0,
) -> pd.DataFrame:
    if threshold <= 0:
        raise ValueError("Anomaly threshold must be positive.")

    enriched = calculate_time_based_rolling(frame, 7)

    deviation = (
        enriched["temperature"]
        - enriched["temperature_rolling_mean"]
    ).abs()

    enriched["temperature_anomaly"] = (
        deviation > threshold * enriched["temperature_rolling_std"].fillna(0)
    )

    return enriched


def demonstrate_file_round_trip(frame: pd.DataFrame) -> pd.DataFrame:
    """Demonstrate safe persistence without relying on external files."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "sensor_data.csv"

        frame.to_csv(path, index=True)

        restored = pd.read_csv(
            path,
            index_col="timestamp",
            parse_dates=["timestamp"],
        )

        restored.index = pd.DatetimeIndex(restored.index)

        return restored


def main() -> None:
    config = TimeSeriesConfig()

    raw = build_sensor_series()
    data = normalize_timezone(raw, config.timezone_name)

    validate_datetime_index(data)

    print("\n=== Original DatetimeIndex ===")
    print(data)

    print("\n=== Daily Resampling ===")
    print(daily_resampling(data))

    print("\n=== Hourly Resampling + Time Interpolation ===")
    print(hourly_interpolation(data).head(12))

    print("\n=== Time-Based Rolling Windows ===")
    rolling = calculate_time_based_rolling(data, config.rolling_days)
    print(
        rolling[
            [
                "temperature",
                "temperature_rolling_mean",
                "temperature_rolling_std",
                "energy_rolling_sum",
            ]
        ]
    )

    print("\n=== Shifting and Changes ===")
    print(calculate_shifts_and_changes(data))

    print("\n=== Weekly Calendar Grouping ===")
    print(group_by_calendar_period(data))

    print("\n=== Month/Hour Grouping ===")
    print(group_by_month_and_hour(data))

    print("\n=== Temperature Anomalies ===")
    print(
        detect_temperature_anomalies(data)[
            ["temperature", "temperature_rolling_mean", "temperature_anomaly"]
        ]
    )

    print("\n=== Persistence Round Trip ===")
    restored = demonstrate_file_round_trip(data)
    print(restored.head())

    assert isinstance(data.index, pd.DatetimeIndex)
    assert data.index.is_monotonic_increasing
    assert len(daily_resampling(data)) > 0
    assert "temperature_rolling_mean" in rolling.columns
    assert "temperature_previous" in calculate_shifts_and_changes(data).columns

    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
