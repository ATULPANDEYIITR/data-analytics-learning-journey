"""
SQL Window Functions II
=======================

A self-contained Python companion for learning and practicing:

- LAG and LEAD
- FIRST_VALUE and LAST_VALUE
- Running totals
- Moving averages
- Window partitioning and ordering
- Window frames
- Comparing current rows with previous and next rows
- Per-group analytics
- Time-series analysis
- Validation and edge cases
- SQL generation and execution with Python's sqlite3 standard library

The examples use realistic daily sales data. SQLite supports the window
functions demonstrated here, making the script executable without external
packages or a database server.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable


DATABASE = ":memory:"


@dataclass(frozen=True)
class Sale:
    sale_date: str
    region: str
    product: str
    revenue: float


def create_connection() -> sqlite3.Connection:
    """Create an in-memory SQLite database with row-name access."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """
    Create a compact sales table.

    sale_date is stored as ISO text because SQLite can compare ISO dates
    lexicographically in chronological order.
    """
    connection.execute(
        """
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            region TEXT NOT NULL,
            product TEXT NOT NULL,
            revenue REAL NOT NULL CHECK (revenue >= 0)
        )
        """
    )
    connection.commit()


def seed_data(connection: sqlite3.Connection) -> None:
    """
    Insert a realistic time series.

    Multiple regions and products make PARTITION BY meaningful. Several
    products intentionally have missing dates so that LAG/LEAD demonstrates
    row-relative behavior rather than pretending that every calendar day
    exists.
    """
    rows = [
        ("2026-09-01", "North", "Cloud", 1200),
        ("2026-09-02", "North", "Cloud", 1350),
        ("2026-09-03", "North", "Cloud", 1280),
        ("2026-09-04", "North", "Cloud", 1410),
        ("2026-09-05", "North", "Cloud", 1500),
        ("2026-09-06", "North", "Cloud", 1460),
        ("2026-09-07", "North", "Cloud", 1600),
        ("2026-09-01", "South", "Cloud", 900),
        ("2026-09-02", "South", "Cloud", 980),
        ("2026-09-03", "South", "Cloud", 1020),
        ("2026-09-04", "South", "Cloud", 1100),
        ("2026-09-05", "South", "Cloud", 1060),
        ("2026-09-06", "South", "Cloud", 1170),
        ("2026-09-07", "South", "Cloud", 1210),
        ("2026-09-01", "North", "Security", 800),
        ("2026-09-02", "North", "Security", 860),
        ("2026-09-03", "North", "Security", 920),
        ("2026-09-04", "North", "Security", 880),
        ("2026-09-05", "North", "Security", 990),
        ("2026-09-06", "North", "Security", 1040),
        ("2026-09-07", "North", "Security", 1120),
        ("2026-09-01", "South", "Security", 700),
        ("2026-09-02", "South", "Security", 760),
        ("2026-09-04", "South", "Security", 820),
        ("2026-09-05", "South", "Security", 850),
        ("2026-09-07", "South", "Security", 940),
    ]

    connection.executemany(
        """
        INSERT INTO sales (sale_date, region, product, revenue)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()


def print_rows(title: str, rows: Iterable[sqlite3.Row]) -> None:
    """Display query results without requiring a third-party table package."""
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")

    rows = list(rows)
    if not rows:
        print("(no rows)")
        return

    columns = rows[0].keys()
    print(" | ".join(columns))
    print("-" * 78)

    for row in rows:
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))
        print(" | ".join(values))


def demonstrate_lag(connection: sqlite3.Connection) -> None:
    """
    LAG reads a value from an earlier row in the window ordering.

    PARTITION BY keeps North and South histories independent. Without it,
    the final row of one region could be compared with the first row of
    another region, which would be analytically incorrect.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            LAG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS previous_revenue,
            revenue - LAG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS change_from_previous
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("LAG: compare each row with the previous observation",
               connection.execute(query))


def demonstrate_lead(connection: sqlite3.Connection) -> None:
    """
    LEAD reads a value from a later row.

    The final observation in each partition has no later row, so LEAD
    naturally returns NULL. COALESCE can be used when a business rule
    requires a replacement value.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            LEAD(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS next_revenue,
            LEAD(revenue, 1, 0) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS next_revenue_or_zero
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("LEAD: inspect the next observation",
               connection.execute(query))


def demonstrate_lag_lead_trend(connection: sqlite3.Connection) -> None:
    """
    Combining LAG and LEAD supports local trend analysis.

    A row is classified as rising when it is greater than the previous
    observation and the next observation is also greater than the current
    value. Missing neighbors are left as 'boundary' rather than incorrectly
    classified as a trend.
    """
    query = """
        WITH neighbors AS (
            SELECT
                sale_date,
                region,
                product,
                revenue,
                LAG(revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ) AS previous_revenue,
                LEAD(revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ) AS next_revenue
            FROM sales
        )
        SELECT
            sale_date,
            region,
            product,
            revenue,
            previous_revenue,
            next_revenue,
            CASE
                WHEN previous_revenue IS NULL
                  OR next_revenue IS NULL
                    THEN 'boundary'
                WHEN revenue > previous_revenue
                 AND next_revenue > revenue
                    THEN 'rising'
                WHEN revenue < previous_revenue
                 AND next_revenue < revenue
                    THEN 'falling'
                ELSE 'turning_or_flat'
            END AS local_trend
        FROM neighbors
        ORDER BY region, product, sale_date
    """
    print_rows("LAG + LEAD: local trend classification",
               connection.execute(query))


def demonstrate_first_value(connection: sqlite3.Connection) -> None:
    """
    FIRST_VALUE returns a value from the first row in the window frame.

    An explicit frame is used so the intended behavior is visible rather
    than relying on the database's default frame.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            FIRST_VALUE(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS first_revenue
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("FIRST_VALUE: first revenue in each region/product history",
               connection.execute(query))


def demonstrate_last_value(connection: sqlite3.Connection) -> None:
    """
    LAST_VALUE has an important frame-related trap.

    With a default frame ending at the current row, LAST_VALUE often means
    "the current row", not "the final row of the partition". Extending the
    frame to UNBOUNDED FOLLOWING makes the requested final observation
    available to every row.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            LAST_VALUE(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS last_value_in_current_frame,
            LAST_VALUE(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS final_revenue
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("LAST_VALUE: current-frame value versus final partition value",
               connection.execute(query))


def demonstrate_running_total(connection: sqlite3.Connection) -> None:
    """
    A running total accumulates values from the beginning of a partition
    through the current row.

    The explicit ROWS frame makes the intended cumulative behavior clear.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            SUM(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS running_revenue
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("Running total: cumulative revenue by region and product",
               connection.execute(query))


def demonstrate_moving_average(connection: sqlite3.Connection) -> None:
    """
    A three-row moving average smooths short-term fluctuations.

    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW means that the first rows use
    fewer observations because earlier rows do not exist. This is different
    from inventing zero-valued observations.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            AVG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS moving_average_3
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("Three-row moving average",
               connection.execute(query))


def demonstrate_centered_average(connection: sqlite3.Connection) -> None:
    """
    A centered window uses observations before and after the current row.

    It is useful for historical analysis but is generally unsuitable for
    real-time alerting because future observations are unavailable at the
    time the current event occurs.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            AVG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
            ) AS centered_average
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("Centered three-row average",
               connection.execute(query))


def demonstrate_change_percentage(connection: sqlite3.Connection) -> None:
    """
    LAG can feed a percentage-change calculation.

    NULLIF prevents division by zero. The CASE expression also handles the
    first observation, where no previous revenue exists.
    """
    query = """
        WITH history AS (
            SELECT
                sale_date,
                region,
                product,
                revenue,
                LAG(revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ) AS previous_revenue
            FROM sales
        )
        SELECT
            sale_date,
            region,
            product,
            revenue,
            previous_revenue,
            CASE
                WHEN previous_revenue IS NULL THEN NULL
                WHEN previous_revenue = 0 THEN NULL
                ELSE ROUND(
                    100.0 * (revenue - previous_revenue)
                    / NULLIF(previous_revenue, 0),
                    2
                )
            END AS percentage_change
        FROM history
        ORDER BY region, product, sale_date
    """
    print_rows("Percentage change using LAG",
               connection.execute(query))


def demonstrate_partition_level_summary(connection: sqlite3.Connection) -> None:
    """
    Window functions can enrich detailed rows with partition-level metrics.

    Unlike GROUP BY, the windowed SUM does not collapse the individual rows.
    """
    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            SUM(revenue) OVER (
                PARTITION BY region, product
            ) AS partition_total,
            ROUND(
                100.0 * revenue
                / NULLIF(
                    SUM(revenue) OVER (PARTITION BY region, product),
                    0
                ),
                2
            ) AS percentage_of_partition
        FROM sales
        ORDER BY region, product, sale_date
    """
    print_rows("Partition total retained alongside each detail row",
               connection.execute(query))


def demonstrate_missing_calendar_dates(connection: sqlite3.Connection) -> None:
    """
    LAG and LEAD operate on rows, not automatically on calendar intervals.

    South/Security has missing dates. The query therefore computes the actual
    number of calendar days between observations so that a consumer can tell
    whether a previous row represents yesterday or an older observation.
    """
    query = """
        WITH history AS (
            SELECT
                sale_date,
                region,
                product,
                revenue,
                LAG(sale_date) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ) AS previous_date,
                LAG(revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ) AS previous_revenue
            FROM sales
        )
        SELECT
            sale_date,
            region,
            product,
            revenue,
            previous_date,
            previous_revenue,
            CASE
                WHEN previous_date IS NULL THEN NULL
                ELSE CAST(
                    julianday(sale_date) - julianday(previous_date)
                    AS INTEGER
                )
            END AS calendar_days_since_previous
        FROM history
        ORDER BY region, product, sale_date
    """
    print_rows("LAG with explicit calendar-gap detection",
               connection.execute(query))


def demonstrate_nested_analytics(connection: sqlite3.Connection) -> None:
    """
    Window functions cannot simply be nested inside one another in the same
    SELECT expression when the second operation depends on the first.

    A CTE creates a logical intermediate result. Here the running total is
    calculated first, then LAG compares each running total with the previous
    running total.
    """
    query = """
        WITH cumulative AS (
            SELECT
                sale_date,
                region,
                product,
                revenue,
                SUM(revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS running_revenue
            FROM sales
        )
        SELECT
            sale_date,
            region,
            product,
            running_revenue,
            LAG(running_revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS previous_running_revenue,
            running_revenue
            - COALESCE(
                LAG(running_revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ),
                0
            ) AS daily_contribution
        FROM cumulative
        ORDER BY region, product, sale_date
    """
    print_rows("CTE + running total + LAG",
               connection.execute(query))


def validate_sql_environment(connection: sqlite3.Connection) -> None:
    """Verify that the runtime supports the required window-function syntax."""
    version = connection.execute("SELECT sqlite_version()").fetchone()[0]
    print(f"\nSQLite version: {version}")

    test = connection.execute(
        """
        SELECT value,
               LAG(value) OVER (ORDER BY value) AS previous_value
        FROM (VALUES (10), (20), (30)) AS sample(value)
        """
    ).fetchall()

    if len(test) != 3:
        raise RuntimeError("Window-function validation returned unexpected data.")

    print("Window-function capability check: passed")


def demonstrate_safe_query_parameterization(connection: sqlite3.Connection) -> None:
    """
    Values supplied by an application should be bound as parameters rather
    than concatenated into SQL.

    This protects the value predicate from SQL injection and also lets the
    database driver handle quoting correctly.
    """
    minimum_revenue = 1000.0

    query = """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            LAG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS previous_revenue
        FROM sales
        WHERE revenue >= ?
        ORDER BY region, product, sale_date
    """

    rows = connection.execute(query, (minimum_revenue,)).fetchall()
    print_rows("Parameterized SQL with LAG", rows)


def demonstrate_edge_case_empty_partition(connection: sqlite3.Connection) -> None:
    """
    Window functions naturally return no rows for an empty result set.

    This matters in reporting systems: an empty analytical result should not
    be interpreted as a zero-valued metric unless that is an explicit
    business rule.
    """
    rows = connection.execute(
        """
        SELECT
            sale_date,
            region,
            product,
            revenue,
            LAG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
            ) AS previous_revenue
        FROM sales
        WHERE region = ?
        ORDER BY sale_date
        """,
        ("West",),
    ).fetchall()

    print_rows("Empty partition/result-set behavior", rows)


def explain_query_plan(connection: sqlite3.Connection) -> None:
    """
    EXPLAIN QUERY PLAN helps investigate execution behavior.

    Window queries usually require ordering work. An index matching common
    partition/order columns can reduce sorting costs in suitable workloads,
    although the optimizer and data distribution determine the actual gain.
    """
    connection.execute(
        """
        CREATE INDEX idx_sales_region_product_date
        ON sales(region, product, sale_date)
        """
    )
    connection.commit()

    plan = connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT
            sale_date,
            region,
            product,
            revenue,
            AVG(revenue) OVER (
                PARTITION BY region, product
                ORDER BY sale_date
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS moving_average
        FROM sales
        """
    ).fetchall()

    print_rows("Execution-plan inspection for a window query", plan)


def demonstrate_business_rule_detection(connection: sqlite3.Connection) -> None:
    """
    A common analytical use case is detecting unusually large day-over-day
    changes.

    The threshold is deliberately explicit so the rule can be audited and
    changed without altering the window-function mechanics.
    """
    threshold_percent = 20.0

    query = """
        WITH changes AS (
            SELECT
                sale_date,
                region,
                product,
                revenue,
                LAG(revenue) OVER (
                    PARTITION BY region, product
                    ORDER BY sale_date
                ) AS previous_revenue
            FROM sales
        )
        SELECT
            sale_date,
            region,
            product,
            revenue,
            previous_revenue,
            ROUND(
                100.0 * (revenue - previous_revenue)
                / NULLIF(previous_revenue, 0),
                2
            ) AS change_percent,
            CASE
                WHEN previous_revenue IS NULL THEN 'insufficient_history'
                WHEN previous_revenue = 0 THEN 'undefined_baseline'
                WHEN ABS(
                    100.0 * (revenue - previous_revenue)
                    / NULLIF(previous_revenue, 0)
                ) >= ?
                    THEN 'review'
                ELSE 'normal'
            END AS monitoring_status
        FROM changes
        ORDER BY region, product, sale_date
    """

    print_rows(
        "Business-rule detection using LAG",
        connection.execute(query, (threshold_percent,)),
    )


def run_all_demos() -> None:
    """Build the complete example database and run every demonstration."""
    connection = create_connection()

    try:
        create_schema(connection)
        seed_data(connection)
        validate_sql_environment(connection)

        demonstrate_lag(connection)
        demonstrate_lead(connection)
        demonstrate_lag_lead_trend(connection)
        demonstrate_first_value(connection)
        demonstrate_last_value(connection)
        demonstrate_running_total(connection)
        demonstrate_moving_average(connection)
        demonstrate_centered_average(connection)
        demonstrate_change_percentage(connection)
        demonstrate_partition_level_summary(connection)
        demonstrate_missing_calendar_dates(connection)
        demonstrate_nested_analytics(connection)
        demonstrate_safe_query_parameterization(connection)
        demonstrate_edge_case_empty_partition(connection)
        demonstrate_business_rule_detection(connection)
        explain_query_plan(connection)

        print("\nAll SQL Window Functions II demonstrations completed successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    run_all_demos()
