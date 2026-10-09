#!/usr/bin/env python3
"""
Advanced Analytical SQL: Percentiles, Median, Conditional Aggregation,
Rolling Calculations, and Gaps and Islands.

The script implements a reproducible analytical dataset and demonstrates
the reasoning behind PostgreSQL analytical queries using Python's standard
library. It includes exact percentile calculations, rolling windows,
conditional aggregation, consecutive-date islands, missing-date gaps,
validation, and computational complexity considerations.

Run with:
    python advanced_analytical_sql.py
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DailyMetric:
    business_date: date
    department: str
    revenue: Decimal
    orders: int
    status: str

    def __post_init__(self) -> None:
        if self.revenue < 0:
            raise ValueError("Revenue cannot be negative.")
        if self.orders < 0:
            raise ValueError("Order count cannot be negative.")
        if self.status not in {"completed", "cancelled", "pending"}:
            raise ValueError(f"Unsupported status: {self.status}")


@dataclass(frozen=True)
class PercentileResult:
    percentile: Decimal
    continuous: Decimal
    discrete: Decimal


def decimal_average(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise ValueError("Cannot average an empty sequence.")
    return sum(values, Decimal("0")) / Decimal(len(values))


def percentile_cont(
    values: Iterable[Decimal], percentile: Decimal
) -> Decimal:
    """
    PostgreSQL PERCENTILE_CONT equivalent for a nonempty numeric sample.

    The zero-based interpolation position is p * (n - 1).
    This differs from selecting an actual sample value when interpolation
    is necessary.
    """
    if not Decimal("0") <= percentile <= Decimal("1"):
        raise ValueError("Percentile must be between 0 and 1.")

    ordered = sorted(Decimal(value) for value in values)
    if not ordered:
        raise ValueError("Cannot calculate a percentile of an empty sample.")

    position = percentile * Decimal(len(ordered) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - Decimal(lower_index)

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]

    return lower_value + fraction * (upper_value - lower_value)


def percentile_disc(
    values: Iterable[Decimal], percentile: Decimal
) -> Decimal:
    """
    PostgreSQL PERCENTILE_DISC equivalent for numeric values.

    Selects the first ordered value whose cumulative distribution is
    greater than or equal to p. The one-based array position is ceil(p*n),
    with a minimum position of one.
    """
    if not Decimal("0") <= percentile <= Decimal("1"):
        raise ValueError("Percentile must be between 0 and 1.")

    ordered = sorted(Decimal(value) for value in values)
    if not ordered:
        raise ValueError("Cannot calculate a percentile of an empty sample.")

    position = int(
        (percentile * Decimal(len(ordered))).to_integral_value(
            rounding="ROUND_CEILING"
        )
    )
    position = max(1, position)
    return ordered[position - 1]


def calculate_percentiles(
    values: Sequence[Decimal],
) -> list[PercentileResult]:
    results = []
    for p in map(Decimal, ("0.25", "0.50", "0.75", "0.90", "0.95")):
        results.append(
            PercentileResult(
                percentile=p,
                continuous=percentile_cont(values, p),
                discrete=percentile_disc(values, p),
            )
        )
    return results


def conditional_aggregation(
    records: Sequence[DailyMetric],
) -> dict[str, Decimal | int]:
    """
    Reproduce SUM(CASE WHEN ...), FILTER, and conditional COUNT patterns.
    Cancelled orders contribute to the cancellation count but not to
    completed revenue or completed-order averages.
    """
    completed = [r for r in records if r.status == "completed"]
    cancelled = [r for r in records if r.status == "cancelled"]
    pending = [r for r in records if r.status == "pending"]

    completed_revenue = sum(
        (r.revenue for r in completed), Decimal("0")
    )
    completed_orders = sum(r.orders for r in completed)
    cancelled_orders = sum(r.orders for r in cancelled)

    average_completed_daily_revenue = (
        decimal_average([r.revenue for r in completed])
        if completed
        else Decimal("0")
    )

    return {
        "record_count": len(records),
        "completed_days": len(completed),
        "cancelled_days": len(cancelled),
        "pending_days": len(pending),
        "completed_revenue": completed_revenue,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "average_completed_daily_revenue": average_completed_daily_revenue,
    }


def rolling_metrics(
    records: Sequence[DailyMetric], window_size: int = 3
) -> list[dict[str, object]]:
    """
    Compute a row-based trailing window after sorting by date.

    This is analogous to ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.
    It includes at most window_size rows, not necessarily every calendar
    day. Missing dates must be handled explicitly if calendar-day windows
    are required.
    """
    if window_size < 1:
        raise ValueError("Window size must be positive.")

    ordered = sorted(records, key=lambda r: r.business_date)
    output = []

    for index, current in enumerate(ordered):
        start = max(0, index - window_size + 1)
        window = ordered[start : index + 1]

        output.append(
            {
                "date": current.business_date,
                "daily_revenue": current.revenue,
                "rolling_revenue": sum(
                    (r.revenue for r in window), Decimal("0")
                ),
                "rolling_average": decimal_average(
                    [r.revenue for r in window]
                ),
                "rows_in_window": len(window),
            }
        )

    return output


def calendar_rolling_metrics(
    records: Sequence[DailyMetric], window_days: int = 7
) -> list[dict[str, object]]:
    """
    Calculate trailing calendar-day revenue, treating absent observations
    as zero. This assumes a missing row means no recorded revenue, not
    unknown revenue. That business decision must be explicit.
    """
    if window_days < 1:
        raise ValueError("Calendar window must be positive.")

    by_date: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    for record in records:
        by_date[record.business_date] += record.revenue

    if not by_date:
        return []

    first = min(by_date)
    last = max(by_date)
    result = []
    current = first

    while current <= last:
        start = current - timedelta(days=window_days - 1)
        days = [
            by_date.get(start + timedelta(days=offset), Decimal("0"))
            for offset in range(window_days)
        ]

        result.append(
            {
                "date": current,
                "rolling_calendar_revenue": sum(days, Decimal("0")),
                "window_days": window_days,
            }
        )
        current += timedelta(days=1)

    return result


def consecutive_date_islands(
    observed_dates: Iterable[date],
) -> list[dict[str, object]]:
    """
    Identify consecutive calendar-date islands.

    The SQL equivalent commonly uses:
        business_date - row_number() * INTERVAL '1 day'

    All dates are deduplicated before grouping, so duplicate observations
    cannot incorrectly split an island.
    """
    ordered = sorted(set(observed_dates))
    if not ordered:
        return []

    islands = []
    island_start = ordered[0]
    previous = ordered[0]

    for current in ordered[1:]:
        if current != previous + timedelta(days=1):
            islands.append(
                {
                    "start_date": island_start,
                    "end_date": previous,
                    "day_count": (previous - island_start).days + 1,
                }
            )
            island_start = current

        previous = current

    islands.append(
        {
            "start_date": island_start,
            "end_date": previous,
            "day_count": (previous - island_start).days + 1,
        }
    )
    return islands


def missing_date_gaps(
    observed_dates: Iterable[date],
    start_date: date,
    end_date: date,
) -> list[dict[str, object]]:
    """
    Find contiguous intervals of missing calendar dates inside an inclusive
    reporting period. The reporting boundaries are explicit, preventing
    leading and trailing gaps from being silently ignored.
    """
    if start_date > end_date:
        raise ValueError("Start date must not exceed end date.")

    observed = {
        d for d in observed_dates if start_date <= d <= end_date
    }
    gaps = []
    current = start_date
    gap_start: date | None = None

    while current <= end_date:
        if current not in observed and gap_start is None:
            gap_start = current
        elif current in observed and gap_start is not None:
            gaps.append(
                {
                    "start_date": gap_start,
                    "end_date": current - timedelta(days=1),
                    "missing_days": (current - gap_start).days,
                }
            )
            gap_start = None

        current += timedelta(days=1)

    if gap_start is not None:
        gaps.append(
            {
                "start_date": gap_start,
                "end_date": end_date,
                "missing_days": (end_date - gap_start).days + 1,
            }
        )

    return gaps


def consecutive_integer_islands(
    values: Iterable[int],
) -> list[dict[str, int]]:
    """
    Group consecutive integer identifiers into islands.
    For integer sequences, value - row_number is constant within an island.
    """
    ordered = sorted(set(values))
    if not ordered:
        return []

    result = []
    start = previous = ordered[0]

    for value in ordered[1:]:
        if value != previous + 1:
            result.append(
                {"start": start, "end": previous, "count": previous - start + 1}
            )
            start = value
        previous = value

    result.append(
        {"start": start, "end": previous, "count": previous - start + 1}
    )
    return result


def print_table(
    title: str,
    headers: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> None:
    print(f"\n{title}")
    print(" | ".join(headers))
    print("-" * 100)
    for row in rows:
        print(" | ".join(str(value) for value in row))


def build_sample_data() -> list[DailyMetric]:
    raw = [
        ("2026-09-01", "Operations", "1200.00", 24, "completed"),
        ("2026-09-02", "Operations", "1350.00", 27, "completed"),
        ("2026-09-03", "Operations", "0.00", 0, "cancelled"),
        ("2026-09-04", "Operations", "1820.00", 36, "completed"),
        ("2026-09-06", "Operations", "1600.00", 32, "completed"),
        ("2026-09-07", "Operations", "1750.00", 35, "completed"),
        ("2026-09-08", "Operations", "2100.00", 42, "completed"),
        ("2026-09-09", "Operations", "900.00", 18, "pending"),
        ("2026-09-10", "Operations", "2400.00", 48, "completed"),
        ("2026-09-11", "Operations", "1950.00", 39, "completed"),
        ("2026-09-12", "Operations", "2600.00", 52, "completed"),
        ("2026-09-13", "Operations", "800.00", 16, "cancelled"),
        ("2026-09-15", "Operations", "2850.00", 57, "completed"),
        ("2026-09-16", "Operations", "3000.00", 60, "completed"),
        ("2026-09-17", "Operations", "2750.00", 55, "completed"),
    ]
    return [
        DailyMetric(date.fromisoformat(d), dept, Decimal(revenue), orders, status)
        for d, dept, revenue, orders, status in raw
    ]


def run_self_tests() -> None:
    assert percentile_cont(
        [Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40")],
        Decimal("0.5"),
    ) == Decimal("25.0")

    assert percentile_disc(
        [Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40")],
        Decimal("0.5"),
    ) == Decimal("20")

    assert median([1, 3, 5, 7]) == 4.0

    islands = consecutive_date_islands(
        [
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 1, 4),
            date(2026, 1, 5),
        ]
    )
    assert [island["day_count"] for island in islands] == [2, 2]

    gaps = missing_date_gaps(
        [date(2026, 1, 2), date(2026, 1, 5)],
        date(2026, 1, 1),
        date(2026, 1, 6),
    )
    assert [gap["missing_days"] for gap in gaps] == [1, 2, 1]

    assert consecutive_integer_islands([1, 2, 4, 7, 8]) == [
        {"start": 1, "end": 2, "count": 2},
        {"start": 4, "end": 4, "count": 1},
        {"start": 7, "end": 8, "count": 2},
    ]

    try:
        percentile_cont([], Decimal("0.5"))
    except ValueError:
        pass
    else:
        raise AssertionError("Empty percentile input must fail.")

    print("All self-tests passed.")


def main() -> None:
    run_self_tests()
    records = build_sample_data()

    completed_revenues = [
        record.revenue for record in records if record.status == "completed"
    ]

    percentile_rows = []
    for result in calculate_percentiles(completed_revenues):
        percentile_rows.append(
            (
                f"{result.percentile:.0%}",
                result.continuous.quantize(Decimal("0.01")),
                result.discrete.quantize(Decimal("0.01")),
            )
        )

    print_table(
        "Continuous and discrete percentiles of completed daily revenue",
        ["Percentile", "PERCENTILE_CONT", "PERCENTILE_DISC"],
        percentile_rows,
    )

    summary = conditional_aggregation(records)
    print_table(
        "Conditional aggregation",
        ["Metric", "Value"],
        [(key, value) for key, value in summary.items()],
    )

    rolling_rows = [
        (
            item["date"],
            item["daily_revenue"],
            item["rolling_revenue"],
            item["rolling_average"].quantize(Decimal("0.01")),
            item["rows_in_window"],
        )
        for item in rolling_metrics(records, 3)
    ]
    print_table(
        "Three-row rolling calculations",
        ["Date", "Revenue", "Rolling sum", "Rolling average", "Rows"],
        rolling_rows,
    )

    calendar_rows = [
        (item["date"], item["rolling_calendar_revenue"])
        for item in calendar_rolling_metrics(records, 7)
    ]
    print_table(
        "Seven-calendar-day rolling revenue",
        ["Date", "Seven-day revenue"],
        calendar_rows,
    )

    observed_dates = [record.business_date for record in records]
    islands = consecutive_date_islands(observed_dates)
    print_table(
        "Consecutive date islands",
        ["Start", "End", "Calendar days"],
        [
            (item["start_date"], item["end_date"], item["day_count"])
            for item in islands
        ],
    )

    gaps = missing_date_gaps(
        observed_dates, date(2026, 9, 1), date(2026, 9, 17)
    )
    print_table(
        "Missing-date intervals within the reporting period",
        ["Start", "End", "Missing days"],
        [
            (item["start_date"], item["end_date"], item["missing_days"])
            for item in gaps
        ],
    )

    money = Decimal("1234.565").quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    print(f"\nExplicit financial rounding example: {money}")


if __name__ == "__main__":
    main()
