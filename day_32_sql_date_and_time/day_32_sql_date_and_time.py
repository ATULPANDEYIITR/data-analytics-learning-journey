#!/usr/bin/env python3
"""
SQL Date & Time Learning Simulator

This executable Python program models the concepts commonly used when working
with SQL date and time values:

- DATE
- TIMESTAMP
- INTERVAL
- DATE_PART
- DATE_TRUNC
- Time zones
- Date arithmetic
- Boundary and precision issues
- Reporting windows and scheduling logic

The implementation intentionally uses Python's standard library so that the
SQL concepts can be explored without requiring a database driver.

The examples use ISO-8601 values and timezone-aware datetime objects, closely
matching the data representation encountered in PostgreSQL and similar SQL
systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import calendar
import csv
import io
import re
import unittest


UTC = timezone.utc


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Event:
    """A business event with a timezone-aware timestamp."""

    event_id: int
    name: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("Event timestamps must be timezone-aware")


@dataclass(frozen=True)
class DateRange:
    """A half-open time range: [start, end)."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("DateRange endpoints must be timezone-aware")
        if self.start >= self.end:
            raise ValueError("Range start must be earlier than range end")

    def contains(self, value: datetime) -> bool:
        return self.start <= value < self.end


@dataclass(frozen=True)
class SQLInterval:
    """
    A simplified SQL-style interval.

    SQL intervals can represent calendar-aware months as well as fixed
    durations. A Python timedelta cannot represent "one month" because the
    number of days in a month varies, so months are retained separately.
    """

    months: int = 0
    days: int = 0
    seconds: int = 0
    microseconds: int = 0

    def normalized(self) -> "SQLInterval":
        extra_days, remaining_seconds = divmod(self.seconds, 86400)
        return SQLInterval(
            months=self.months,
            days=self.days + extra_days,
            seconds=remaining_seconds,
            microseconds=self.microseconds,
        )

    def as_timedelta(self) -> timedelta:
        if self.months != 0:
            raise ValueError(
                "Month-bearing intervals cannot be converted to a fixed "
                "timedelta without a reference date"
            )
        return timedelta(
            days=self.days,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )

    def __str__(self) -> str:
        parts: list[str] = []
        if self.months:
            parts.append(f"{self.months} month(s)")
        if self.days:
            parts.append(f"{self.days} day(s)")
        if self.seconds:
            parts.append(f"{self.seconds} second(s)")
        if self.microseconds:
            parts.append(f"{self.microseconds} microsecond(s)")
        return " + ".join(parts) if parts else "0"


# ---------------------------------------------------------------------------
# DATE fundamentals
# ---------------------------------------------------------------------------

def demonstrate_date_type() -> None:
    print("\n=== DATE: calendar values without a time of day ===")

    order_date = date(2026, 10, 2)
    print("Order date:", order_date)
    print("Year:", order_date.year)
    print("Month:", order_date.month)
    print("Day:", order_date.day)
    print("ISO representation:", order_date.isoformat())

    # DATE arithmetic is calendar-oriented. A date plus seven days is another
    # date; there is no clock time involved.
    delivery_date = order_date + timedelta(days=7)
    print("Seven days later:", delivery_date)

    # Python date.weekday() follows Monday=0 through Sunday=6.
    print("Weekday index:", order_date.weekday())
    print("ISO week:", order_date.isocalendar().week)

    # A common SQL reporting pattern is to derive a month boundary from a date.
    first_of_month = order_date.replace(day=1)
    next_month = (
        date(order_date.year + (order_date.month == 12),
             1 if order_date.month == 12 else order_date.month + 1,
             1)
    )
    print("First day of month:", first_of_month)
    print("First day of next month:", next_month)


# ---------------------------------------------------------------------------
# TIMESTAMP fundamentals
# ---------------------------------------------------------------------------

def demonstrate_timestamp_type() -> None:
    print("\n=== TIMESTAMP: date and time precision ===")

    timestamp_value = datetime(2026, 10, 2, 6, 48, 23, 456789)
    print("Timestamp:", timestamp_value)
    print("Microseconds:", timestamp_value.microsecond)

    # SQL TIMESTAMP without time zone should not be silently treated as a
    # globally comparable instant. It is a calendar clock reading.
    naive_timestamp = datetime(2026, 10, 2, 9, 30)
    print("Naive timestamp:", naive_timestamp)
    print("Naive timestamp has tzinfo:", naive_timestamp.tzinfo is not None)

    aware_timestamp = naive_timestamp.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    print("Interpreted in Asia/Kolkata:", aware_timestamp.isoformat())
    print("Equivalent UTC instant:", aware_timestamp.astimezone(UTC).isoformat())

    # The distinction matters when a timestamp crosses a timezone boundary.
    same_instant = aware_timestamp.astimezone(ZoneInfo("America/New_York"))
    print("Same instant in New York:", same_instant.isoformat())


# ---------------------------------------------------------------------------
# SQL-style DATE_PART
# ---------------------------------------------------------------------------

def date_part(part: str, value: date | datetime | timedelta) -> int | float:
    """
    Approximate common DATE_PART fields.

    PostgreSQL DATE_PART returns a numeric value. This implementation focuses
    on fields that have a direct and useful standard-library representation.
    """

    normalized = part.strip().lower()

    if isinstance(value, datetime):
        if normalized in {"year", "y"}:
            return value.year
        if normalized in {"month", "mon"}:
            return value.month
        if normalized in {"day", "d"}:
            return value.day
        if normalized in {"hour", "h"}:
            return value.hour
        if normalized in {"minute", "min"}:
            return value.minute
        if normalized in {"second", "s"}:
            return value.second + value.microsecond / 1_000_000
        if normalized == "microseconds":
            return value.microsecond
        if normalized == "dow":
            # PostgreSQL-style Sunday=0 through Saturday=6.
            return (value.weekday() + 1) % 7
        if normalized == "isodow":
            return value.isoweekday()
        if normalized == "doy":
            return value.timetuple().tm_yday
        if normalized == "epoch":
            if value.tzinfo is None:
                raise ValueError("epoch extraction requires an aware datetime")
            return value.timestamp()

    if isinstance(value, date) and not isinstance(value, datetime):
        if normalized == "year":
            return value.year
        if normalized == "month":
            return value.month
        if normalized == "day":
            return value.day
        if normalized == "dow":
            return (value.weekday() + 1) % 7
        if normalized == "isodow":
            return value.isoweekday()
        if normalized == "doy":
            return value.timetuple().tm_yday

    if isinstance(value, timedelta):
        total_seconds = value.total_seconds()
        if normalized == "epoch":
            return total_seconds
        if normalized == "day":
            return value.days
        if normalized == "hour":
            return int(total_seconds // 3600)
        if normalized == "minute":
            return int(total_seconds // 60)
        if normalized == "second":
            return total_seconds

    raise ValueError(f"Unsupported DATE_PART field: {part!r}")


def demonstrate_date_part() -> None:
    print("\n=== DATE_PART: extracting components ===")

    value = datetime(
        2026, 10, 2, 6, 48, 23, 456789, tzinfo=ZoneInfo("Asia/Kolkata")
    )

    for field in ("year", "month", "day", "hour", "minute", "second",
                  "dow", "isodow", "doy", "epoch"):
        print(f"{field:>12}: {date_part(field, value)}")

    # DATE_PART is useful for grouping or filtering by components, but
    # DATE_TRUNC is generally better when the intended result is a boundary.
    print("Extracted quarter:", (date_part("month", value) - 1) // 3 + 1)


# ---------------------------------------------------------------------------
# SQL-style DATE_TRUNC
# ---------------------------------------------------------------------------

def date_trunc(part: str, value: datetime | date) -> datetime | date:
    """
    Truncate a date/time to a calendar boundary.

    For timezone-aware datetime values, the original timezone is retained.
    """

    normalized = part.strip().lower()

    if isinstance(value, date) and not isinstance(value, datetime):
        if normalized in {"day", "date"}:
            return value
        if normalized == "month":
            return value.replace(day=1)
        if normalized == "year":
            return value.replace(month=1, day=1)
        raise ValueError(f"Unsupported DATE_TRUNC field for DATE: {part}")

    assert isinstance(value, datetime)

    if normalized == "year":
        return value.replace(month=1, day=1, hour=0, minute=0, second=0,
                             microsecond=0)
    if normalized == "quarter":
        first_month = ((value.month - 1) // 3) * 3 + 1
        return value.replace(month=first_month, day=1, hour=0, minute=0,
                             second=0, microsecond=0)
    if normalized == "month":
        return value.replace(day=1, hour=0, minute=0, second=0,
                             microsecond=0)
    if normalized == "week":
        start = value - timedelta(days=value.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if normalized == "day":
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    if normalized == "hour":
        return value.replace(minute=0, second=0, microsecond=0)
    if normalized == "minute":
        return value.replace(second=0, microsecond=0)
    if normalized == "second":
        return value.replace(microsecond=0)

    raise ValueError(f"Unsupported DATE_TRUNC field: {part}")


def demonstrate_date_trunc() -> None:
    print("\n=== DATE_TRUNC: creating calendar boundaries ===")

    value = datetime(
        2026, 10, 2, 6, 48, 23, 456789, tzinfo=ZoneInfo("Asia/Kolkata")
    )

    for unit in ("year", "quarter", "month", "week", "day", "hour",
                 "minute", "second"):
        print(f"{unit:>8}: {date_trunc(unit, value).isoformat()}")

    month_start = date_trunc("month", value)
    next_month_start = add_months(month_start, 1)
    print("Half-open monthly reporting range:")
    print("  start:", month_start.isoformat())
    print("  end:  ", next_month_start.isoformat())


# ---------------------------------------------------------------------------
# Calendar-aware month arithmetic
# ---------------------------------------------------------------------------

def add_months(value: date | datetime, months: int) -> date | datetime:
    """
    Add calendar months while preserving a valid calendar date.

    SQL interval arithmetic involving months is calendar-sensitive. For
    example, January 31 + one month cannot remain February 31, so this
    function clamps to the last day of February.
    """

    original_day = value.day
    zero_based_month = value.month - 1 + months
    new_year = value.year + zero_based_month // 12
    new_month = zero_based_month % 12 + 1

    last_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(original_day, last_day)

    return value.replace(year=new_year, month=new_month, day=new_day)


def add_sql_interval(
    value: date | datetime,
    interval: SQLInterval,
) -> date | datetime:
    """Apply months first, then fixed calendar days and clock duration."""

    result = add_months(value, interval.months)

    if isinstance(result, datetime):
        return result + timedelta(
            days=interval.days,
            seconds=interval.seconds,
            microseconds=interval.microseconds,
        )

    if interval.seconds or interval.microseconds:
        raise ValueError("Clock components cannot be applied to a DATE")

    return result + timedelta(days=interval.days)


def demonstrate_intervals_and_arithmetic() -> None:
    print("\n=== INTERVAL and date arithmetic ===")

    base = date(2026, 1, 31)
    print("Base date:", base)
    print("One calendar month later:", add_months(base, 1))
    print("Two calendar months later:", add_months(base, 2))

    interval = SQLInterval(months=1, days=3, seconds=90)
    result = add_sql_interval(
        datetime(2026, 1, 31, 22, 30, tzinfo=ZoneInfo("Asia/Kolkata")),
        interval,
    )
    print("Complex interval:", interval)
    print("Result:", result.isoformat())

    duration = timedelta(days=4, hours=5, minutes=30)
    print("Fixed duration:", duration)
    print("Duration in seconds:", duration.total_seconds())


# ---------------------------------------------------------------------------
# Time-zone handling
# ---------------------------------------------------------------------------

def parse_timezone(name: str) -> ZoneInfo:
    """Load an IANA timezone and produce a useful validation error."""

    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"Unknown IANA timezone {name!r}; use a name such as "
            "'Asia/Kolkata' or 'America/New_York'"
        ) from exc


def localize_wall_clock(
    local_value: datetime,
    timezone_name: str,
) -> datetime:
    """
    Interpret a timezone-naive clock reading in an explicit IANA timezone.

    This operation is intentionally separate from conversion. Attaching a
    timezone means "this wall-clock time belongs to this zone"; converting an
    aware datetime means "show the same instant in another zone."
    """

    if local_value.tzinfo is not None:
        raise ValueError("localize_wall_clock expects a naive datetime")

    return local_value.replace(tzinfo=parse_timezone(timezone_name))


def convert_timezone(value: datetime, timezone_name: str) -> datetime:
    """Convert an aware timestamp to another timezone."""

    if value.tzinfo is None:
        raise ValueError("Timezone conversion requires an aware datetime")

    return value.astimezone(parse_timezone(timezone_name))


def demonstrate_time_zones() -> None:
    print("\n=== Time zones: interpretation versus conversion ===")

    meeting_wall_clock = datetime(2026, 10, 2, 9, 30)
    meeting_kolkata = localize_wall_clock(meeting_wall_clock, "Asia/Kolkata")
    meeting_london = convert_timezone(meeting_kolkata, "Europe/London")
    meeting_new_york = convert_timezone(
        meeting_kolkata, "America/New_York"
    )

    print("Original wall clock:", meeting_wall_clock)
    print("Asia/Kolkata:", meeting_kolkata.isoformat())
    print("Europe/London:", meeting_london.isoformat())
    print("America/New_York:", meeting_new_york.isoformat())

    # A timezone-aware instant can be compared safely after normalization to
    # UTC. The local representations differ while the instant is identical.
    print(
        "Same instant:",
        meeting_kolkata.astimezone(UTC) == meeting_london.astimezone(UTC)
        == meeting_new_york.astimezone(UTC),
    )

    # DST creates days that are not always exactly 24 elapsed hours in local
    # wall-clock terms. Fixed durations and calendar arithmetic therefore
    # deserve different treatment.
    before_dst = datetime(
        2026, 3, 8, 1, 30, tzinfo=ZoneInfo("America/New_York")
    )
    after_one_hour = before_dst + timedelta(hours=1)
    print("DST boundary example:", before_dst.isoformat())
    print("After fixed one-hour timedelta:", after_one_hour.isoformat())


# ---------------------------------------------------------------------------
# Reporting windows
# ---------------------------------------------------------------------------

def month_range(year: int, month: int, zone: ZoneInfo) -> DateRange:
    """Create a timezone-aware half-open monthly reporting range."""

    start_date = date(year, month, 1)
    end_date = add_months(start_date, 1)

    start = datetime.combine(start_date, time.min, tzinfo=zone)
    end = datetime.combine(end_date, time.min, tzinfo=zone)
    return DateRange(start=start, end=end)


def day_range(value: date, zone: ZoneInfo) -> DateRange:
    """Create [midnight, next midnight) for a local calendar day."""

    start = datetime.combine(value, time.min, tzinfo=zone)
    end = start + timedelta(days=1)
    return DateRange(start=start, end=end)


def filter_events(events: list[Event], window: DateRange) -> list[Event]:
    """Return events whose instants fall inside a half-open range."""

    return [event for event in events if window.contains(event.occurred_at)]


def demonstrate_reporting_windows() -> None:
    print("\n=== Reporting windows and DATE_TRUNC ===")

    zone = ZoneInfo("Asia/Kolkata")
    events = [
        Event(
            1,
            "Invoice created",
            datetime(2026, 10, 1, 0, 0, tzinfo=zone),
        ),
        Event(
            2,
            "Payment received",
            datetime(2026, 10, 2, 11, 15, tzinfo=zone),
        ),
        Event(
            3,
            "Month-end adjustment",
            datetime(2026, 10, 31, 23, 59, 59, 999999, tzinfo=zone),
        ),
        Event(
            4,
            "November event",
            datetime(2026, 11, 1, 0, 0, tzinfo=zone),
        ),
    ]

    october = month_range(2026, 10, zone)
    october_events = filter_events(events, october)

    print("October start:", october.start.isoformat())
    print("November boundary:", october.end.isoformat())

    for event in october_events:
        print(f"{event.event_id}: {event.name} -> {event.occurred_at.isoformat()}")

    # The half-open [start, end) design avoids fragile "23:59:59.999999"
    # boundary calculations and works naturally with timestamp precision.
    print("November 1 excluded:", not october.contains(events[-1].occurred_at))


# ---------------------------------------------------------------------------
# Business age and elapsed-time calculations
# ---------------------------------------------------------------------------

def completed_years(start: date, end: date) -> int:
    """Calculate completed calendar years rather than dividing days by 365."""

    if end < start:
        raise ValueError("End date cannot precede start date")

    years = end.year - start.year
    anniversary = start.replace(year=start.year + years)

    # February 29 requires an explicit anniversary policy in non-leap years.
    if start.month == 2 and start.day == 29 and not calendar.isleap(end.year):
        anniversary = date(end.year, 2, 28)

    if anniversary > end:
        years -= 1

    return years


def demonstrate_date_difference() -> None:
    print("\n=== Date differences: elapsed duration versus calendar difference ===")

    created = date(2020, 2, 29)
    as_of = date(2026, 2, 28)

    print("Created:", created)
    print("As of:", as_of)
    print("Completed calendar years:", completed_years(created, as_of))
    print("Elapsed days:", (as_of - created).days)

    # These two measurements answer different questions. SQL applications
    # should choose an operation according to business semantics.
    started_at = datetime(2026, 10, 2, 9, 0, tzinfo=UTC)
    finished_at = datetime(2026, 10, 2, 17, 45, tzinfo=UTC)
    elapsed = finished_at - started_at
    print("Elapsed processing time:", elapsed)
    print("Elapsed seconds:", elapsed.total_seconds())


# ---------------------------------------------------------------------------
# Parsing and validation
# ---------------------------------------------------------------------------

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_sql_date(value: str) -> date:
    """Parse a strict ISO calendar date."""

    if not ISO_DATE_PATTERN.fullmatch(value):
        raise ValueError("DATE must use YYYY-MM-DD format")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid calendar date: {value}") from exc


def parse_timestamp(value: str) -> datetime:
    """
    Parse an ISO timestamp and require an explicit UTC offset.

    Production systems should avoid silently guessing a timezone when an
    event represents a global instant.
    """

    normalized = value.strip().replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO timestamp: {value}") from exc

    if parsed.tzinfo is None:
        raise ValueError(
            "Timestamp must contain a timezone offset, such as +05:30"
        )

    return parsed


def demonstrate_validation() -> None:
    print("\n=== Validation and failure conditions ===")

    valid_dates = ["2026-10-02", "2024-02-29"]
    invalid_dates = ["2026-02-29", "2026/10/02", "October 2 2026"]

    for value in valid_dates:
        print("Parsed DATE:", parse_sql_date(value))

    for value in invalid_dates:
        try:
            parse_sql_date(value)
        except ValueError as exc:
            print("Rejected DATE:", value, "|", exc)

    valid_timestamp = "2026-10-02T06:48:23+05:30"
    print("Parsed timestamp:", parse_timestamp(valid_timestamp).isoformat())

    try:
        parse_timestamp("2026-10-02 06:48:23")
    except ValueError as exc:
        print("Rejected timezone-less timestamp:", exc)


# ---------------------------------------------------------------------------
# Time-zone aware event aggregation
# ---------------------------------------------------------------------------

def group_events_by_local_day(
    events: list[Event],
    timezone_name: str,
) -> dict[date, list[Event]]:
    """
    Group global instants according to the calendar day in a requested zone.

    This demonstrates why grouping by UTC date can produce a different answer
    from grouping by the user's local business date.
    """

    zone = parse_timezone(timezone_name)
    grouped: dict[date, list[Event]] = {}

    for event in events:
        local_date = event.occurred_at.astimezone(zone).date()
        grouped.setdefault(local_date, []).append(event)

    return grouped


def demonstrate_local_reporting() -> None:
    print("\n=== Time-zone aware local reporting ===")

    events = [
        Event(
            101,
            "Checkout",
            datetime(2026, 10, 1, 23, 30, tzinfo=UTC),
        ),
        Event(
            102,
            "Checkout",
            datetime(2026, 10, 2, 00, 30, tzinfo=UTC),
        ),
        Event(
            103,
            "Checkout",
            datetime(2026, 10, 2, 18, 45, tzinfo=UTC),
        ),
    ]

    for zone_name in ("UTC", "Asia/Kolkata", "America/New_York"):
        grouped = group_events_by_local_day(events, zone_name)
        print(f"\nBusiness-day grouping in {zone_name}:")
        for local_day, day_events in sorted(grouped.items()):
            ids = [event.event_id for event in day_events]
            print(local_day, "->", ids)


# ---------------------------------------------------------------------------
# SQL-like query result preparation
# ---------------------------------------------------------------------------

def sql_style_projection(event: Event, reporting_zone: str) -> dict[str, object]:
    """
    Produce fields commonly selected in an analytics query.

    The output mirrors the conceptual role of DATE_PART, DATE_TRUNC and
    timezone conversion in a SQL SELECT statement.
    """

    local = convert_timezone(event.occurred_at, reporting_zone)

    return {
        "event_id": event.event_id,
        "event_name": event.name,
        "utc_timestamp": event.occurred_at.astimezone(UTC).isoformat(),
        "local_timestamp": local.isoformat(),
        "local_date": local.date().isoformat(),
        "month_start": date_trunc("month", local).isoformat(),
        "hour": date_part("hour", local),
        "weekday": date_part("isodow", local),
    }


def demonstrate_projection() -> None:
    print("\n=== Analytical timestamp projection ===")

    event = Event(
        200,
        "Subscription renewed",
        datetime(2026, 10, 2, 3, 45, 12, tzinfo=UTC),
    )

    row = sql_style_projection(event, "Asia/Kolkata")
    for key, value in row.items():
        print(f"{key}: {value}")


# ---------------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------------

def export_events_csv(events: list[Event]) -> str:
    """Serialize normalized timestamps for downstream reporting."""

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["event_id", "name", "occurred_at_utc"],
    )
    writer.writeheader()

    for event in events:
        writer.writerow(
            {
                "event_id": event.event_id,
                "name": event.name,
                "occurred_at_utc": event.occurred_at.astimezone(UTC).isoformat(),
            }
        )

    return output.getvalue()


def demonstrate_export() -> None:
    print("\n=== Exporting normalized temporal data ===")

    events = [
        Event(
            301,
            "Order placed",
            datetime(2026, 10, 2, 4, 10, tzinfo=UTC),
        ),
        Event(
            302,
            "Order shipped",
            datetime(2026, 10, 2, 8, 40, tzinfo=UTC),
        ),
    ]

    print(export_events_csv(events))


# ---------------------------------------------------------------------------
# Precision and financial-style reporting
# ---------------------------------------------------------------------------

def round_duration_seconds(seconds: float, decimals: int = 3) -> Decimal:
    """
    Round elapsed time only for presentation.

    Internal calculations retain the original datetime precision instead of
    repeatedly rounding timestamps.
    """

    quantizer = Decimal("1." + ("0" * decimals))
    return Decimal(str(seconds)).quantize(
        quantizer,
        rounding=ROUND_HALF_UP,
    )


def demonstrate_precision() -> None:
    print("\n=== Precision management ===")

    start = datetime(
        2026, 10, 2, 6, 48, 0, 123456, tzinfo=UTC
    )
    end = datetime(
        2026, 10, 2, 6, 48, 3, 987654, tzinfo=UTC
    )

    seconds = (end - start).total_seconds()
    print("Exact elapsed seconds:", seconds)
    print("Presentation value:", round_duration_seconds(seconds, 3))


# ---------------------------------------------------------------------------
# Advanced scheduling logic
# ---------------------------------------------------------------------------

def next_business_day(value: date) -> date:
    """Return the next Monday-Friday date."""

    candidate = value + timedelta(days=1)

    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)

    return candidate


def add_business_days(value: date, number_of_days: int) -> date:
    """Add business days without counting Saturday or Sunday."""

    if number_of_days < 0:
        raise ValueError("number_of_days must be non-negative")

    result = value
    for _ in range(number_of_days):
        result = next_business_day(result)

    return result


def demonstrate_business_calendar() -> None:
    print("\n=== Calendar-aware business scheduling ===")

    submitted = date(2026, 10, 2)  # Friday
    deadline = add_business_days(submitted, 3)
    print("Submitted:", submitted)
    print("Three business days later:", deadline)


# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

class DateTimeConceptTests(unittest.TestCase):
    def test_date_part_year(self) -> None:
        value = datetime(2026, 10, 2, 6, 48, tzinfo=UTC)
        self.assertEqual(date_part("year", value), 2026)

    def test_date_part_second_includes_fraction(self) -> None:
        value = datetime(2026, 10, 2, 6, 48, 23, 500000, tzinfo=UTC)
        self.assertEqual(date_part("second", value), 23.5)

    def test_date_trunc_month(self) -> None:
        value = datetime(2026, 10, 17, 14, 25, 12, tzinfo=UTC)
        expected = datetime(2026, 10, 1, tzinfo=UTC)
        self.assertEqual(date_trunc("month", value), expected)

    def test_month_end_clamps(self) -> None:
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))

    def test_leap_year_month_end(self) -> None:
        self.assertEqual(add_months(date(2024, 1, 31), 1), date(2024, 2, 29))

    def test_timezone_conversion_preserves_instant(self) -> None:
        kolkata = datetime(
            2026, 10, 2, 9, 30, tzinfo=ZoneInfo("Asia/Kolkata")
        )
        new_york = convert_timezone(kolkata, "America/New_York")
        self.assertEqual(kolkata.astimezone(UTC), new_york.astimezone(UTC))

    def test_range_is_half_open(self) -> None:
        zone = ZoneInfo("Asia/Kolkata")
        window = month_range(2026, 10, zone)
        self.assertTrue(
            window.contains(datetime(2026, 10, 31, 23, 59, tzinfo=zone))
        )
        self.assertFalse(
            window.contains(datetime(2026, 11, 1, 0, 0, tzinfo=zone))
        )

    def test_timestamp_requires_timezone(self) -> None:
        with self.assertRaises(ValueError):
            parse_timestamp("2026-10-02T06:48:23")

    def test_completed_years(self) -> None:
        self.assertEqual(
            completed_years(date(2020, 2, 29), date(2026, 2, 28)),
            6,
        )


def run_tests() -> None:
    print("\n=== Automated tests ===")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        DateTimeConceptTests
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Main executable learning workflow
# ---------------------------------------------------------------------------

def main() -> None:
    print("SQL DATE & TIME CONCEPTS")
    print("========================")
    print("The examples model SQL temporal operations using Python's standard library.")

    demonstrate_date_type()
    demonstrate_timestamp_type()
    demonstrate_date_part()
    demonstrate_date_trunc()
    demonstrate_intervals_and_arithmetic()
    demonstrate_time_zones()
    demonstrate_reporting_windows()
    demonstrate_date_difference()
    demonstrate_validation()
    demonstrate_local_reporting()
    demonstrate_projection()
    demonstrate_export()
    demonstrate_precision()
    demonstrate_business_calendar()
    run_tests()

    print("\nExecution completed successfully.")


if __name__ == "__main__":
    main()
