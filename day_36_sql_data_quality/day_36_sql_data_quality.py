#!/usr/bin/env python3
"""
SQL Data Quality Engineering
============================

A self-contained executable demonstration of four closely related data-quality
problems in relational data:

- Duplicate detection
- Missing-value detection and profiling
- Referential-integrity validation
- Anomaly detection using SQL-oriented statistical techniques

The program uses SQLite from Python's standard library so it runs without
third-party packages. The SQL statements intentionally resemble patterns that
can be transferred to PostgreSQL with small dialect-specific changes.

The implementation treats data quality as a measurable property of a dataset,
not merely as a collection of ad-hoc cleanup statements.
"""

from __future__ import annotations

import csv
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median
from typing import Iterable, Sequence


DB_PATH = Path("sql_data_quality_demo.db")


@dataclass(frozen=True)
class QualityIssue:
    rule: str
    table_name: str
    record_key: str
    detail: str
    severity: str


class DataQualityEngine:
    """Runs SQL-based data-quality checks against a relational dataset."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def execute(self, sql: str, parameters: Sequence = ()) -> list[sqlite3.Row]:
        cursor = self.connection.execute(sql, parameters)
        return cursor.fetchall()

    def scalar(self, sql: str, parameters: Sequence = ()) -> object:
        row = self.connection.execute(sql, parameters).fetchone()
        return None if row is None else row[0]

    def profile_customers(self) -> None:
        print("\n=== CUSTOMER COMPLETENESS PROFILE ===")

        rows = self.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS missing_id,
                SUM(CASE WHEN full_name IS NULL OR TRIM(full_name) = '' THEN 1 ELSE 0 END)
                    AS missing_name,
                SUM(CASE WHEN email IS NULL OR TRIM(email) = '' THEN 1 ELSE 0 END)
                    AS missing_email,
                SUM(CASE WHEN phone IS NULL OR TRIM(phone) = '' THEN 1 ELSE 0 END)
                    AS missing_phone
            FROM customers;
            """
        )

        row = rows[0]
        for key in row.keys():
            print(f"{key:15}: {row[key]}")

    def find_exact_duplicates(self) -> list[QualityIssue]:
        """
        Exact duplicate detection groups records by business attributes.

        customer_id is deliberately excluded because duplicate records may have
        different surrogate identifiers while representing the same customer.
        """
        rows = self.execute(
            """
            SELECT
                LOWER(TRIM(email)) AS normalized_email,
                LOWER(TRIM(full_name)) AS normalized_name,
                COUNT(*) AS duplicate_count,
                GROUP_CONCAT(customer_id) AS customer_ids
            FROM customers
            WHERE email IS NOT NULL
              AND TRIM(email) <> ''
            GROUP BY LOWER(TRIM(email)), LOWER(TRIM(full_name))
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC;
            """
        )

        issues: list[QualityIssue] = []
        for row in rows:
            issues.append(
                QualityIssue(
                    rule="duplicate_customer",
                    table_name="customers",
                    record_key=str(row["customer_ids"]),
                    detail=(
                        f"email/name combination occurs {row['duplicate_count']} "
                        f"times"
                    ),
                    severity="HIGH",
                )
            )
        return issues

    def find_missing_values(self) -> list[QualityIssue]:
        """Find field-level completeness violations."""
        rows = self.execute(
            """
            SELECT customer_id, 'full_name' AS column_name
            FROM customers
            WHERE full_name IS NULL OR TRIM(full_name) = ''

            UNION ALL

            SELECT customer_id, 'email'
            FROM customers
            WHERE email IS NULL OR TRIM(email) = ''

            UNION ALL

            SELECT customer_id, 'phone'
            FROM customers
            WHERE phone IS NULL OR TRIM(phone) = ''

            ORDER BY customer_id, column_name;
            """
        )

        return [
            QualityIssue(
                rule="missing_value",
                table_name="customers",
                record_key=str(row["customer_id"]),
                detail=f"{row['column_name']} is missing",
                severity="MEDIUM",
            )
            for row in rows
        ]

    def check_referential_integrity(self) -> list[QualityIssue]:
        """
        Detect orphaned child rows.

        SQLite foreign-key enforcement is enabled below, but this explicit query
        is still useful when auditing imported legacy data or systems where
        constraints were temporarily disabled.
        """
        rows = self.execute(
            """
            SELECT
                o.order_id,
                o.customer_id
            FROM orders AS o
            LEFT JOIN customers AS c
                ON c.customer_id = o.customer_id
            WHERE c.customer_id IS NULL
            ORDER BY o.order_id;
            """
        )

        return [
            QualityIssue(
                rule="orphan_order",
                table_name="orders",
                record_key=str(row["order_id"]),
                detail=f"customer_id {row['customer_id']} does not exist",
                severity="CRITICAL",
            )
            for row in rows
        ]

    def check_domain_rules(self) -> list[QualityIssue]:
        """Detect values that violate business-level domain expectations."""
        rows = self.execute(
            """
            SELECT order_id, 'amount' AS field, amount AS value
            FROM orders
            WHERE amount IS NULL OR amount <= 0

            UNION ALL

            SELECT order_id, 'order_date', order_date
            FROM orders
            WHERE order_date IS NULL OR TRIM(order_date) = ''

            UNION ALL

            SELECT order_id, 'status', status
            FROM orders
            WHERE status NOT IN ('pending', 'paid', 'cancelled', 'refunded')

            ORDER BY order_id;
            """
        )

        return [
            QualityIssue(
                rule="domain_violation",
                table_name="orders",
                record_key=str(row["order_id"]),
                detail=f"{row['field']} has invalid value {row['value']!r}",
                severity="HIGH",
            )
            for row in rows
        ]

    def detect_amount_anomalies(self) -> list[QualityIssue]:
        """
        Detect unusually large order amounts using a robust IQR rule.

        IQR is useful when monetary data contains legitimate skew and a few
        extreme observations. The rule flags values above Q3 + 1.5 * IQR.
        """
        rows = self.execute(
            """
            SELECT amount
            FROM orders
            WHERE amount IS NOT NULL
              AND amount > 0
            ORDER BY amount;
            """
        )

        values = [float(row["amount"]) for row in rows]
        if len(values) < 4:
            return []

        q1 = percentile(values, 25)
        q3 = percentile(values, 75)
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr

        anomalies = self.execute(
            """
            SELECT order_id, customer_id, amount
            FROM orders
            WHERE amount > ?
            ORDER BY amount DESC;
            """,
            (upper_bound,),
        )

        return [
            QualityIssue(
                rule="amount_anomaly",
                table_name="orders",
                record_key=str(row["order_id"]),
                detail=(
                    f"amount={row['amount']:.2f} exceeds IQR upper bound "
                    f"{upper_bound:.2f}"
                ),
                severity="HIGH",
            )
            for row in anomalies
        ]

    def detect_customer_velocity_anomalies(self) -> list[QualityIssue]:
        """
        Detect customers placing an unusually high number of orders on one day.

        This uses a window-function query to calculate customer/day activity,
        followed by a threshold derived from the distribution of daily counts.
        """
        rows = self.execute(
            """
            WITH daily_activity AS (
                SELECT
                    customer_id,
                    DATE(order_date) AS order_day,
                    COUNT(*) AS daily_orders
                FROM orders
                WHERE customer_id IS NOT NULL
                GROUP BY customer_id, DATE(order_date)
            ),
            statistics AS (
                SELECT
                    AVG(daily_orders) AS average_orders,
                    AVG(daily_orders * daily_orders) AS average_squared
                FROM daily_activity
            )
            SELECT
                d.customer_id,
                d.order_day,
                d.daily_orders,
                s.average_orders,
                SQRT(
                    CASE
                        WHEN s.average_squared - s.average_orders * s.average_orders < 0
                        THEN 0
                        ELSE s.average_squared - s.average_orders * s.average_orders
                    END
                ) AS population_stddev
            FROM daily_activity AS d
            CROSS JOIN statistics AS s
            WHERE d.daily_orders >
                  s.average_orders +
                  3 * SQRT(
                      CASE
                          WHEN s.average_squared - s.average_orders * s.average_orders < 0
                          THEN 0
                          ELSE s.average_squared - s.average_orders * s.average_orders
                      END
                  )
            ORDER BY d.daily_orders DESC;
            """
        )

        return [
            QualityIssue(
                rule="order_velocity_anomaly",
                table_name="orders",
                record_key=f"{row['customer_id']}:{row['order_day']}",
                detail=(
                    f"{row['daily_orders']} orders on {row['order_day']} "
                    f"exceeds the 3-sigma activity threshold"
                ),
                severity="HIGH",
            )
            for row in rows
        ]

    def calculate_quality_score(self) -> float:
        """
        Produce a simple weighted quality score.

        The score is intentionally transparent rather than pretending that
        every data-quality rule has identical business impact.
        """
        total = int(self.scalar("SELECT COUNT(*) FROM customers") or 0)
        if total == 0:
            return 100.0

        duplicate_groups = int(
            self.scalar(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT LOWER(TRIM(email)), LOWER(TRIM(full_name))
                    FROM customers
                    WHERE email IS NOT NULL AND TRIM(email) <> ''
                    GROUP BY LOWER(TRIM(email)), LOWER(TRIM(full_name))
                    HAVING COUNT(*) > 1
                );
                """
            )
            or 0
        )

        missing_cells = int(
            self.scalar(
                """
                SELECT
                    SUM(
                        CASE WHEN full_name IS NULL OR TRIM(full_name) = ''
                        THEN 1 ELSE 0 END
                    )
                    +
                    SUM(
                        CASE WHEN email IS NULL OR TRIM(email) = ''
                        THEN 1 ELSE 0 END
                    )
                    +
                    SUM(
                        CASE WHEN phone IS NULL OR TRIM(phone) = ''
                        THEN 1 ELSE 0 END
                    )
                FROM customers;
                """
            )
            or 0
        )

        orphan_count = len(self.check_referential_integrity())
        domain_count = len(self.check_domain_rules())

        duplicate_penalty = min(35.0, duplicate_groups / total * 100 * 20)
        missing_penalty = min(35.0, missing_cells / (total * 3) * 100 * 30)
        orphan_penalty = min(25.0, orphan_count / max(total, 1) * 100 * 25)
        domain_penalty = min(25.0, domain_count / max(total, 1) * 100 * 25)

        return max(
            0.0,
            100.0
            - duplicate_penalty
            - missing_penalty
            - orphan_penalty
            - domain_penalty,
        )

    def print_quality_report(self) -> None:
        checks = [
            ("Duplicate detection", self.find_exact_duplicates()),
            ("Missing-value detection", self.find_missing_values()),
            ("Referential integrity", self.check_referential_integrity()),
            ("Domain validation", self.check_domain_rules()),
            ("Amount anomaly detection", self.detect_amount_anomalies()),
            ("Velocity anomaly detection", self.detect_customer_velocity_anomalies()),
        ]

        print("\n=== DATA QUALITY REPORT ===")
        for name, issues in checks:
            print(f"\n{name}: {len(issues)} issue(s)")
            for issue in issues:
                print(
                    f"  [{issue.severity}] {issue.table_name}:{issue.record_key} "
                    f"- {issue.detail}"
                )

        print(f"\nQuality score: {self.calculate_quality_score():.2f}/100")


def percentile(values: Sequence[float], percentile_value: float) -> float:
    """Calculate a linearly interpolated percentile without NumPy."""
    if not values:
        raise ValueError("Cannot calculate a percentile for an empty sequence.")
    if not 0 <= percentile_value <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def create_database(connection: sqlite3.Connection) -> None:
    """
    Create a relational model with database-level integrity rules.

    The foreign key from orders.customer_id to customers.customer_id prevents
    new orphan records when enforcement is enabled.
    """
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript(
        """
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT,
            CHECK (amount > 0),
            CHECK (status IN ('pending', 'paid', 'cancelled', 'refunded'))
        );

        CREATE INDEX idx_customers_email
            ON customers (LOWER(TRIM(email)));

        CREATE INDEX idx_orders_customer_date
            ON orders (customer_id, order_date);

        CREATE INDEX idx_orders_amount
            ON orders (amount);
        """
    )


def seed_data(connection: sqlite3.Connection) -> None:
    """
    Insert intentionally imperfect records.

    Real data-quality testing requires both valid records and records that
    expose the rules being tested.
    """
    customers = [
        (1, "Asha Verma", "asha@example.com", "9876500001", "2026-09-01"),
        (2, "Ravi Kumar", "ravi@example.com", "9876500002", "2026-09-02"),
        (3, "Ravi Kumar", "ravi@example.com", "9876500002", "2026-09-03"),
        (4, "Meera Shah", None, "9876500004", "2026-09-04"),
        (5, "", "meera2@example.com", None, "2026-09-05"),
        (6, "Kabir Singh", "kabir@example.com", "9876500006", "2026-09-06"),
        (7, "Nisha Rao", "nisha@example.com", "9876500007", "2026-09-07"),
        (8, "Omar Khan", "omarkhan@example.com", "9876500008", "2026-09-08"),
    ]

    connection.executemany(
        """
        INSERT INTO customers
            (customer_id, full_name, email, phone, created_at)
        VALUES (?, ?, ?, ?, ?);
        """,
        customers,
    )

    orders = [
        (101, 1, 120.50, "2026-10-01", "paid"),
        (102, 2, 80.00, "2026-10-01", "paid"),
        (103, 2, 75.00, "2026-10-01", "paid"),
        (104, 2, 70.00, "2026-10-01", "paid"),
        (105, 2, 65.00, "2026-10-01", "paid"),
        (106, 2, 55.00, "2026-10-01", "paid"),
        (107, 6, 150.00, "2026-10-02", "pending"),
        (108, 7, 210.00, "2026-10-02", "paid"),
        (109, 8, 9999.00, "2026-10-02", "paid"),
        (110, 1, 95.00, "2026-10-03", "cancelled"),
    ]

    connection.executemany(
        """
        INSERT INTO orders
            (order_id, customer_id, amount, order_date, status)
        VALUES (?, ?, ?, ?, ?);
        """,
        orders,
    )

    connection.commit()


def demonstrate_constraint_enforcement(connection: sqlite3.Connection) -> None:
    print("\n=== DATABASE CONSTRAINT ENFORCEMENT ===")

    try:
        connection.execute(
            """
            INSERT INTO orders
                (order_id, customer_id, amount, order_date, status)
            VALUES (?, ?, ?, ?, ?);
            """,
            (999, 99999, 100.0, "2026-10-05", "paid"),
        )
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.rollback()
        print("Foreign-key violation correctly rejected:", exc)

    try:
        connection.execute(
            """
            INSERT INTO orders
                (order_id, customer_id, amount, order_date, status)
            VALUES (?, ?, ?, ?, ?);
            """,
            (1000, 1, -50.0, "2026-10-05", "paid"),
        )
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.rollback()
        print("CHECK constraint correctly rejected:", exc)


def export_issue_report(
    issues: Iterable[QualityIssue], output_path: Path
) -> None:
    """Persist detected issues as a CSV audit artifact."""
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["rule", "table", "record_key", "severity", "detail"]
        )
        for issue in issues:
            writer.writerow(
                [
                    issue.rule,
                    issue.table_name,
                    issue.record_key,
                    issue.severity,
                    issue.detail,
                ]
            )


def demonstrate_transactional_repair(connection: sqlite3.Connection) -> None:
    """
    Demonstrate safe remediation.

    A production cleanup should not blindly overwrite data. The example creates
    a savepoint, changes one known duplicate, validates the result, and commits
    only when the duplicate condition is removed.
    """
    print("\n=== TRANSACTIONAL DATA REPAIR ===")

    connection.execute("SAVEPOINT duplicate_repair")

    try:
        connection.execute(
            """
            UPDATE customers
            SET email = 'ravi.kumar.duplicate@example.com'
            WHERE customer_id = 3;
            """
        )

        duplicate_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT LOWER(TRIM(email)), LOWER(TRIM(full_name))
                    FROM customers
                    GROUP BY LOWER(TRIM(email)), LOWER(TRIM(full_name))
                    HAVING COUNT(*) > 1
                );
                """
            ).fetchone()[0]
        )

        if duplicate_count != 0:
            raise RuntimeError("Duplicate validation failed after repair.")

        connection.execute("RELEASE SAVEPOINT duplicate_repair")
        connection.commit()
        print("Repair committed after validation.")
    except Exception as exc:
        connection.execute("ROLLBACK TO SAVEPOINT duplicate_repair")
        connection.execute("RELEASE SAVEPOINT duplicate_repair")
        connection.rollback()
        print("Repair rolled back:", exc)


def demonstrate_window_analysis(connection: sqlite3.Connection) -> None:
    """
    Use SQL window functions to identify records that differ substantially
    from a customer's own historical spending level.
    """
    print("\n=== CUSTOMER-LEVEL SPENDING ANALYSIS ===")

    rows = connection.execute(
        """
        WITH customer_orders AS (
            SELECT
                customer_id,
                order_id,
                amount,
                AVG(amount) OVER (
                    PARTITION BY customer_id
                ) AS customer_average,
                ROW_NUMBER() OVER (
                    PARTITION BY customer_id
                    ORDER BY amount DESC
                ) AS amount_rank
            FROM orders
            WHERE status <> 'cancelled'
        )
        SELECT
            customer_id,
            order_id,
            amount,
            ROUND(customer_average, 2) AS customer_average,
            amount_rank
        FROM customer_orders
        WHERE amount > customer_average * 2
        ORDER BY customer_id, amount DESC;
        """
    ).fetchall()

    for row in rows:
        print(
            f"customer={row['customer_id']} "
            f"order={row['order_id']} "
            f"amount={row['amount']:.2f} "
            f"customer_avg={row['customer_average']:.2f} "
            f"rank={row['amount_rank']}"
        )


def print_summary_statistics(connection: sqlite3.Connection) -> None:
    amounts = [
        float(row[0])
        for row in connection.execute(
            "SELECT amount FROM orders WHERE amount > 0;"
        )
    ]

    if not amounts:
        return

    print("\n=== BASIC DISTRIBUTION STATISTICS ===")
    print(f"count : {len(amounts)}")
    print(f"mean  : {mean(amounts):.2f}")
    print(f"median: {median(amounts):.2f}")
    print(f"p25   : {percentile(amounts, 25):.2f}")
    print(f"p75   : {percentile(amounts, 75):.2f}")
    print(f"max   : {max(amounts):.2f}")


def main() -> None:
    connection = sqlite3.connect(":memory:")

    try:
        create_database(connection)
        seed_data(connection)

        engine = DataQualityEngine(connection)

        engine.profile_customers()
        engine.print_quality_report()
        print_summary_statistics(connection)
        demonstrate_window_analysis(connection)
        demonstrate_constraint_enforcement(connection)

        all_issues = (
            engine.find_exact_duplicates()
            + engine.find_missing_values()
            + engine.check_referential_integrity()
            + engine.check_domain_rules()
            + engine.detect_amount_anomalies()
            + engine.detect_customer_velocity_anomalies()
        )

        report_path = Path("data_quality_issues.csv")
        export_issue_report(all_issues, report_path)
        print(f"\nIssue report written to {report_path.resolve()}")

        demonstrate_transactional_repair(connection)

        print("\n=== POST-REPAIR DUPLICATE CHECK ===")
        remaining_duplicates = engine.find_exact_duplicates()
        print(f"Remaining duplicate groups: {len(remaining_duplicates)}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
