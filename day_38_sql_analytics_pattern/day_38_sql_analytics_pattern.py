"""
SQL Analytics Patterns: Top-N, Cohort Preparation, Retention, Funnels, Segmentation

A self-contained Python companion that builds realistic event data and demonstrates
the analytical logic behind common SQL analytics patterns. The implementation uses
only the Python standard library so the file can run without external packages.

The examples mirror operations commonly expressed with PostgreSQL window functions,
CTEs, conditional aggregation, date arithmetic, and segmentation logic.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import ceil
from typing import Iterable


@dataclass(frozen=True)
class Event:
    user_id: int
    event_time: datetime
    event_name: str
    properties: dict[str, str | float | int]


@dataclass(frozen=True)
class User:
    user_id: int
    signup_date: date
    country: str
    acquisition_channel: str


@dataclass(frozen=True)
class ProductSale:
    product_id: str
    product_name: str
    category: str
    revenue: float


def print_title(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def print_rows(rows: Iterable[dict], limit: int | None = None) -> None:
    rows = list(rows)
    if limit is not None:
        rows = rows[:limit]

    if not rows:
        print("(no rows)")
        return

    columns = list(rows[0])
    widths = {
        column: max(len(column), max(len(str(row.get(column, ""))) for row in rows))
        for column in columns
    }

    print(" | ".join(column.ljust(widths[column]) for column in columns))
    print("-+-".join("-" * widths[column] for column in columns))

    for row in rows:
        print(" | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))


def build_users() -> list[User]:
    return [
        User(1, date(2026, 1, 2), "IN", "organic"),
        User(2, date(2026, 1, 3), "IN", "paid"),
        User(3, date(2026, 1, 8), "US", "organic"),
        User(4, date(2026, 1, 15), "IN", "referral"),
        User(5, date(2026, 2, 2), "DE", "paid"),
        User(6, date(2026, 2, 5), "IN", "organic"),
        User(7, date(2026, 2, 9), "US", "paid"),
        User(8, date(2026, 2, 20), "IN", "referral"),
        User(9, date(2026, 3, 1), "IN", "organic"),
        User(10, date(2026, 3, 4), "DE", "paid"),
        User(11, date(2026, 3, 11), "US", "referral"),
        User(12, date(2026, 3, 20), "IN", "organic"),
    ]


def build_events(users: list[User]) -> list[Event]:
    events: list[Event] = []

    def add(
        user_id: int,
        day_offset: int,
        event_name: str,
        hour: int = 10,
        properties: dict[str, str | float | int] | None = None,
    ) -> None:
        signup = next(user.signup_date for user in users if user.user_id == user_id)
        events.append(
            Event(
                user_id=user_id,
                event_time=datetime.combine(
                    signup + timedelta(days=day_offset),
                    datetime.min.time(),
                ).replace(hour=hour),
                event_name=event_name,
                properties=properties or {},
            )
        )

    # Users 1-4 form a January cohort with different levels of activity.
    for user_id in (1, 2, 3, 4):
        add(user_id, 0, "signup")
        add(user_id, 0, "view_product")
        add(user_id, 0, "add_to_cart")
        if user_id in (1, 2, 4):
            add(user_id, 0, "checkout_started")
        if user_id in (1, 2):
            add(user_id, 0, "purchase", properties={"amount": 120 + user_id * 20})
        if user_id in (1, 2, 3):
            add(user_id, 7, "login")
        if user_id == 1:
            add(user_id, 30, "login")

    # February cohort.
    for user_id in (5, 6, 7, 8):
        add(user_id, 0, "signup")
        add(user_id, 0, "view_product")
        if user_id in (5, 6, 8):
            add(user_id, 0, "add_to_cart")
        if user_id in (5, 6):
            add(user_id, 0, "checkout_started")
            add(user_id, 0, "purchase", properties={"amount": 180 + user_id * 10})
        if user_id in (5, 6, 7):
            add(user_id, 7, "login")
        if user_id in (5, 6):
            add(user_id, 30, "login")

    # March cohort.
    for user_id in (9, 10, 11, 12):
        add(user_id, 0, "signup")
        add(user_id, 0, "view_product")
        if user_id in (9, 10, 12):
            add(user_id, 0, "add_to_cart")
        if user_id in (9, 10):
            add(user_id, 0, "checkout_started")
            add(user_id, 0, "purchase", properties={"amount": 200 + user_id * 5})
        if user_id in (9, 10, 11):
            add(user_id, 7, "login")

    return sorted(events, key=lambda event: (event.event_time, event.user_id))


def top_n_products(
    sales: list[ProductSale],
    n: int,
) -> list[dict[str, str | float | int]]:
    """
    Equivalent analytical idea to:
        ROW_NUMBER() OVER (ORDER BY revenue DESC)
    or
        RANK() OVER (...) / DENSE_RANK()

    The tie policy matters. Here we use dense-rank semantics so tied products
    receive the same rank.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    ordered = sorted(sales, key=lambda sale: (-sale.revenue, sale.product_id))
    rows: list[dict[str, str | float | int]] = []
    current_rank = 0
    previous_revenue: float | None = None

    for position, sale in enumerate(ordered, start=1):
        if previous_revenue != sale.revenue:
            current_rank += 1
        previous_revenue = sale.revenue

        if current_rank <= n:
            rows.append(
                {
                    "rank": current_rank,
                    "product_id": sale.product_id,
                    "product_name": sale.product_name,
                    "revenue": round(sale.revenue, 2),
                }
            )

    return rows


def monthly_cohort_key(signup_date: date) -> str:
    return f"{signup_date.year:04d}-{signup_date.month:02d}"


def prepare_cohort_rows(users: list[User]) -> list[dict[str, str | int]]:
    """
    Creates the dimensional attributes normally produced by a SQL CTE before
    retention analysis. Keeping cohort preparation separate from retention
    measurement prevents signup dates from being recalculated inconsistently.
    """
    rows = []
    for user in users:
        rows.append(
            {
                "user_id": user.user_id,
                "signup_date": user.signup_date.isoformat(),
                "cohort_month": monthly_cohort_key(user.signup_date),
                "country": user.country,
                "acquisition_channel": user.acquisition_channel,
            }
        )
    return rows


def month_difference(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def retention_by_month(
    users: list[User],
    events: list[Event],
) -> list[dict[str, str | int | float]]:
    """
    Calculates classic cohort retention.

    A user is retained in month N when at least one qualifying activity event
    occurs in that month. The denominator is the number of users in the
    original signup cohort, not the previous month's active users.
    """
    qualifying_events = {"login", "view_product", "add_to_cart", "purchase"}

    user_lookup = {user.user_id: user for user in users}
    active_periods: set[tuple[int, int]] = set()

    for event in events:
        if event.event_name not in qualifying_events:
            continue
        user = user_lookup[event.user_id]
        active_periods.add(
            (
                event.user_id,
                month_difference(user.signup_date, event.event_time.date()),
            )
        )

    cohort_sizes = Counter(
        monthly_cohort_key(user.signup_date)
        for user in users
    )

    cohort_activity: dict[tuple[str, int], set[int]] = defaultdict(set)

    for user_id, period in active_periods:
        user = user_lookup[user_id]
        cohort_activity[(monthly_cohort_key(user.signup_date), period)].add(user_id)

    result = []

    for cohort, size in sorted(cohort_sizes.items()):
        for period in range(0, 2):
            retained = len(cohort_activity.get((cohort, period), set()))
            result.append(
                {
                    "cohort_month": cohort,
                    "period_month": period,
                    "cohort_size": size,
                    "retained_users": retained,
                    "retention_pct": round(100 * retained / size, 1) if size else 0.0,
                }
            )

    return result


def funnel_analysis(
    users: list[User],
    events: list[Event],
) -> list[dict[str, int | float]]:
    """
    Counts unique users at each funnel stage.

    A user's presence at a stage means at least one event of that type occurred.
    The conversion percentage uses the immediately preceding stage.
    """
    stages = [
        ("signup", "signup"),
        ("product_view", "view_product"),
        ("cart", "add_to_cart"),
        ("checkout", "checkout_started"),
        ("purchase", "purchase"),
    ]

    user_events: dict[int, set[str]] = defaultdict(set)
    for event in events:
        user_events[event.user_id].add(event.event_name)

    rows = []
    previous_count: int | None = None

    for stage_name, event_name in stages:
        count = sum(
            event_name in user_events[user.user_id]
            for user in users
        )

        rows.append(
            {
                "stage": stage_name,
                "users": count,
                "conversion_from_previous_pct": (
                    100.0
                    if previous_count is None and count
                    else round(100 * count / previous_count, 1)
                    if previous_count
                    else 0.0
                ),
            }
        )
        previous_count = count

    return rows


def segment_users(
    users: list[User],
    events: list[Event],
) -> list[dict[str, str | int | float]]:
    """
    Builds behavior-based segments from observable activity.

    The thresholds are intentionally explicit because segmentation becomes
    difficult to audit when business rules are hidden inside arbitrary scoring.
    """
    activity_counts = Counter()
    purchase_counts = Counter()
    revenue = Counter()

    for event in events:
        if event.event_name in {"login", "view_product", "add_to_cart"}:
            activity_counts[event.user_id] += 1

        if event.event_name == "purchase":
            purchase_counts[event.user_id] += 1
            revenue[event.user_id] += float(event.properties.get("amount", 0))

    rows = []
    for user in users:
        activity = activity_counts[user.user_id]
        purchases = purchase_counts[user.user_id]
        spend = revenue[user.user_id]

        if purchases >= 2 or spend >= 300:
            segment = "high_value"
        elif purchases >= 1:
            segment = "buyer"
        elif activity >= 3:
            segment = "engaged_non_buyer"
        else:
            segment = "low_activity"

        rows.append(
            {
                "user_id": user.user_id,
                "country": user.country,
                "channel": user.acquisition_channel,
                "activity_events": activity,
                "purchases": purchases,
                "revenue": round(spend, 2),
                "segment": segment,
            }
        )

    return rows


def compare_segment_performance(
    segmented_users: list[dict[str, str | int | float]],
) -> list[dict[str, str | int | float]]:
    grouped: dict[str, list[dict]] = defaultdict(list)

    for row in segmented_users:
        grouped[str(row["segment"])].append(row)

    result = []
    for segment, members in sorted(grouped.items()):
        revenue = sum(float(member["revenue"]) for member in members)
        buyers = sum(int(member["purchases"]) > 0 for member in members)

        result.append(
            {
                "segment": segment,
                "users": len(members),
                "buyers": buyers,
                "buyer_rate_pct": round(100 * buyers / len(members), 1),
                "total_revenue": round(revenue, 2),
                "avg_revenue_per_user": round(revenue / len(members), 2),
            }
        )

    return result


def demonstrate_edge_cases() -> None:
    print_title("Edge Cases and Analytical Rules")

    empty_sales: list[ProductSale] = []
    print("Empty Top-N result:", top_n_products(empty_sales, 3))

    try:
        top_n_products([], 0)
    except ValueError as exc:
        print("Invalid Top-N parameter rejected:", exc)

    zero_denominator = 0
    conversion = 0.0 if zero_denominator == 0 else 100 / zero_denominator
    print("Zero-denominator conversion safely handled:", conversion)

    print(
        "Month difference across year boundary:",
        month_difference(date(2025, 12, 15), date(2026, 2, 10)),
    )


def main() -> None:
    users = build_users()
    events = build_events(users)

    print_title("Dataset")
    print(f"Users: {len(users)}")
    print(f"Events: {len(events)}")

    print_title("Top-N Analytics")
    sales = [
        ProductSale("P100", "Analytics Platform", "software", 18200),
        ProductSale("P200", "Operations Suite", "software", 15700),
        ProductSale("P300", "Data Connector", "integration", 15700),
        ProductSale("P400", "Audit Module", "governance", 11900),
        ProductSale("P500", "Forecasting Module", "analytics", 9400),
    ]
    print_rows(top_n_products(sales, 3))

    print_title("Cohort Preparation")
    print_rows(prepare_cohort_rows(users), limit=8)

    print_title("Monthly Retention")
    print_rows(retention_by_month(users, events))

    print_title("Funnel Analysis")
    print_rows(funnel_analysis(users, events))

    print_title("Behavioral Segmentation")
    segmented = segment_users(users, events)
    print_rows(segmented)

    print_title("Segment Performance")
    print_rows(compare_segment_performance(segmented))

    demonstrate_edge_cases()

    print_title("Analytical Design Notes")
    print(
        "Top-N requires an explicit tie policy. Cohorts require a stable "
        "cohort assignment. Retention requires a clearly defined activity event. "
        "Funnels require ordered stages and unique-user counting. Segmentation "
        "requires auditable business rules and mutually understandable thresholds."
    )


if __name__ == "__main__":
    main()
