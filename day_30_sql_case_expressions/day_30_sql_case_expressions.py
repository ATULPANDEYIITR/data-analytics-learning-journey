"""
SQL CASE Expressions
====================

A self-contained executable teaching model for SQL CASE expressions.

The program uses Python's standard library to simulate a small sales-analysis
workflow and generates real SQL queries containing:

- searched CASE WHEN conditions
- simple CASE expressions
- conditional transformations
- categorical bucketing
- business-rule classification
- NULL-aware handling
- aggregation with CASE
- conditional ordering
- validation of overlapping business rules
- parameterized SQL
- SQLite execution

The examples are deliberately implemented around SQL CASE semantics rather than
generic Python conditional programming.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable


SCHEMA_SQL = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region TEXT NOT NULL,
    customer_tier TEXT,
    annual_spend REAL NOT NULL,
    account_age_months INTEGER NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_amount REAL NOT NULL,
    order_status TEXT NOT NULL,
    discount_rate REAL,
    shipping_days INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
"""

CUSTOMERS = [
    (1, "Asha", "North", "Gold", 125000.0, 38),
    (2, "Ravi", "South", "Silver", 64000.0, 19),
    (3, "Meera", "West", None, 18000.0, 7),
    (4, "Kabir", "East", "Bronze", 42000.0, 14),
    (5, "Neha", "North", "Gold", 225000.0, 64),
    (6, "Vikram", "West", "Silver", 91000.0, 31),
    (7, "Isha", "South", None, 7000.0, 3),
]

ORDERS = [
    (101, 1, 18000.0, "completed", 0.10, 2),
    (102, 1, 42000.0, "completed", 0.05, 4),
    (103, 1, 9000.0, "cancelled", 0.00, None),
    (104, 2, 12000.0, "completed", 0.15, 3),
    (105, 2, 7600.0, "pending", 0.05, 6),
    (106, 3, 2500.0, "completed", None, 9),
    (107, 3, 14000.0, "completed", 0.20, 5),
    (108, 4, 48000.0, "completed", 0.05, 2),
    (109, 5, 65000.0, "completed", 0.12, 1),
    (110, 5, 11000.0, "completed", 0.08, 3),
    (111, 6, 27000.0, "completed", 0.10, 7),
    (112, 6, 52000.0, "completed", 0.03, 4),
    (113, 7, 1200.0, "pending", None, 12),
]


def create_database() -> sqlite3.Connection:
    """Create and populate an in-memory SQLite database."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_SQL)

    connection.executemany(
        """
        INSERT INTO customers (
            customer_id,
            customer_name,
            region,
            customer_tier,
            annual_spend,
            account_age_months
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        CUSTOMERS,
    )

    connection.executemany(
        """
        INSERT INTO orders (
            order_id,
            customer_id,
            order_amount,
            order_status,
            discount_rate,
            shipping_days
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ORDERS,
    )

    connection.commit()
    return connection


def print_rows(title: str, rows: Iterable[sqlite3.Row]) -> None:
    print(f"\n--- {title} ---")
    rows = list(rows)

    if not rows:
        print("(no rows)")
        return

    columns = rows[0].keys()
    print(" | ".join(columns))
    print("-" * 90)

    for row in rows:
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))
        print(" | ".join(values))


def demonstrate_searched_case(connection: sqlite3.Connection) -> None:
    """
    Searched CASE evaluates Boolean conditions from top to bottom.

    The first matching WHEN branch wins. This ordering matters when rules
    overlap.
    """
    query = """
    SELECT
        customer_id,
        customer_name,
        annual_spend,
        CASE
            WHEN annual_spend >= 200000 THEN 'Enterprise'
            WHEN annual_spend >= 100000 THEN 'Premium'
            WHEN annual_spend >= 50000 THEN 'Growth'
            ELSE 'Standard'
        END AS spend_segment
    FROM customers
    ORDER BY annual_spend DESC;
    """

    print_rows("Searched CASE: customer spend segmentation", connection.execute(query))


def demonstrate_simple_case(connection: sqlite3.Connection) -> None:
    """
    Simple CASE compares one expression against several values.

    It is useful when the classification is based on equality rather than
    independent Boolean predicates.
    """
    query = """
    SELECT
        customer_name,
        region,
        CASE region
            WHEN 'North' THEN 'Northern Territory'
            WHEN 'South' THEN 'Southern Territory'
            WHEN 'East' THEN 'Eastern Territory'
            WHEN 'West' THEN 'Western Territory'
            ELSE 'Unassigned Territory'
        END AS region_description
    FROM customers
    ORDER BY customer_id;
    """

    print_rows("Simple CASE: region transformation", connection.execute(query))


def demonstrate_conditional_transformation(connection: sqlite3.Connection) -> None:
    """
    CASE can transform a value according to a business condition.

    Here the discount is converted into a human-readable commercial policy.
    COALESCE is used because a missing discount is different from a zero
    discount in the source data.
    """
    query = """
    SELECT
        order_id,
        order_amount,
        discount_rate,
        CASE
            WHEN discount_rate IS NULL THEN 'Discount not recorded'
            WHEN discount_rate = 0 THEN 'No discount'
            WHEN discount_rate < 0.10 THEN 'Low discount'
            WHEN discount_rate < 0.20 THEN 'Standard discount'
            ELSE 'High discount'
        END AS discount_category,
        ROUND(
            order_amount * (1 - COALESCE(discount_rate, 0)),
            2
        ) AS estimated_net_amount
    FROM orders
    ORDER BY order_id;
    """

    print_rows(
        "CASE for conditional transformation and NULL handling",
        connection.execute(query),
    )


def demonstrate_bucketing(connection: sqlite3.Connection) -> None:
    """
    CASE is commonly used to turn continuous numeric values into business
    buckets. The thresholds must be ordered deliberately to avoid assigning
    a value to an unintended bucket.
    """
    query = """
    SELECT
        order_id,
        order_amount,
        CASE
            WHEN order_amount < 5000 THEN 'Small'
            WHEN order_amount < 15000 THEN 'Medium'
            WHEN order_amount < 50000 THEN 'Large'
            ELSE 'Enterprise'
        END AS order_bucket
    FROM orders
    ORDER BY order_amount;
    """

    print_rows("CASE bucketing: order size", connection.execute(query))


def demonstrate_business_rules(connection: sqlite3.Connection) -> None:
    """
    Multiple attributes can participate in a searched CASE.

    The rules model a simplified operational priority policy. Because CASE
    stops at the first matching WHEN, the highest-priority rule appears first.
    """
    query = """
    SELECT
        c.customer_name,
        c.customer_tier,
        c.annual_spend,
        o.order_id,
        o.order_amount,
        o.shipping_days,
        CASE
            WHEN o.order_status = 'cancelled' THEN 'Do not process'
            WHEN o.shipping_days IS NULL THEN 'Investigate shipping data'
            WHEN o.shipping_days > 7 AND o.order_amount >= 20000
                THEN 'Escalate delayed high-value order'
            WHEN o.order_amount >= 50000
                THEN 'Priority fulfillment'
            WHEN o.shipping_days > 7
                THEN 'Shipping review'
            ELSE 'Normal fulfillment'
        END AS operational_action
    FROM orders AS o
    JOIN customers AS c
      ON c.customer_id = o.customer_id
    ORDER BY o.order_id;
    """

    print_rows(
        "CASE business rules using multiple columns",
        connection.execute(query),
    )


def demonstrate_case_with_aggregation(connection: sqlite3.Connection) -> None:
    """
    CASE can appear inside aggregate functions.

    This produces conditional metrics without filtering the entire result set.
    SUM(CASE ...) is a common pattern for counting or totaling rows that meet
    a specific condition.
    """
    query = """
    SELECT
        c.region,
        COUNT(*) AS total_orders,
        SUM(
            CASE
                WHEN o.order_status = 'completed' THEN 1
                ELSE 0
            END
        ) AS completed_orders,
        SUM(
            CASE
                WHEN o.order_status = 'cancelled' THEN 1
                ELSE 0
            END
        ) AS cancelled_orders,
        ROUND(
            SUM(
                CASE
                    WHEN o.order_status = 'completed'
                    THEN o.order_amount
                    ELSE 0
                END
            ),
            2
        ) AS completed_revenue
    FROM customers AS c
    JOIN orders AS o
      ON o.customer_id = c.customer_id
    GROUP BY c.region
    ORDER BY completed_revenue DESC;
    """

    print_rows(
        "Conditional aggregation with SUM(CASE ...)",
        connection.execute(query),
    )


def demonstrate_case_in_having(connection: sqlite3.Connection) -> None:
    """
    CASE can calculate a business-specific aggregate and then HAVING can
    filter groups using that derived result.
    """
    query = """
    SELECT
        c.customer_name,
        ROUND(
            SUM(
                CASE
                    WHEN o.order_status = 'completed'
                    THEN o.order_amount
                    ELSE 0
                END
            ),
            2
        ) AS completed_revenue,
        CASE
            WHEN SUM(
                CASE
                    WHEN o.order_status = 'completed'
                    THEN o.order_amount
                    ELSE 0
                END
            ) >= 70000
            THEN 'High-value account'
            ELSE 'Standard account'
        END AS revenue_class
    FROM customers AS c
    JOIN orders AS o
      ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.customer_name
    HAVING SUM(
        CASE
            WHEN o.order_status = 'completed'
            THEN o.order_amount
            ELSE 0
        END
    ) > 10000
    ORDER BY completed_revenue DESC;
    """

    print_rows(
        "CASE inside grouped business logic with HAVING",
        connection.execute(query),
    )


def demonstrate_conditional_ordering(connection: sqlite3.Connection) -> None:
    """
    CASE in ORDER BY allows a business-defined ordering that is not naturally
    alphabetical or numerical.
    """
    query = """
    SELECT
        order_id,
        order_status,
        order_amount
    FROM orders
    ORDER BY
        CASE order_status
            WHEN 'cancelled' THEN 1
            WHEN 'pending' THEN 2
            WHEN 'completed' THEN 3
            ELSE 4
        END,
        order_amount DESC;
    """

    print_rows(
        "CASE in ORDER BY: operational priority",
        connection.execute(query),
    )


@dataclass(frozen=True)
class CaseRule:
    """Represents a threshold rule for validating bucket boundaries."""

    label: str
    minimum: float
    maximum: float | None


def validate_bucket_rules(rules: list[CaseRule]) -> None:
    """
    Validate numeric bucket definitions before converting them into SQL CASE.

    Adjacent boundaries are valid. Overlapping intervals are rejected because
    they make the CASE result dependent on WHEN ordering rather than on a
    clean partition of the input domain.
    """
    if not rules:
        raise ValueError("At least one CASE bucket is required.")

    ordered = sorted(rules, key=lambda rule: rule.minimum)

    previous_max: float | None = None

    for rule in ordered:
        if rule.maximum is not None and rule.maximum <= rule.minimum:
            raise ValueError(
                f"Invalid range for {rule.label!r}: maximum must exceed minimum."
            )

        if previous_max is not None and rule.minimum < previous_max:
            raise ValueError(
                f"Overlapping CASE bucket detected at {rule.label!r}."
            )

        previous_max = rule.maximum


def build_bucket_case(
    column_name: str,
    rules: list[CaseRule],
    default_label: str,
) -> str:
    """
    Generate a CASE expression from validated numeric rules.

    The function deliberately permits only a conservative SQL identifier so
    callers cannot accidentally inject arbitrary SQL through the column name.
    """
    if not column_name.replace("_", "").isalnum() or column_name[0].isdigit():
        raise ValueError("Unsafe SQL column identifier.")

    validate_bucket_rules(rules)

    branches = []

    for rule in sorted(rules, key=lambda item: item.minimum):
        if rule.maximum is None:
            branches.append(
                f"WHEN {column_name} >= {rule.minimum:g} "
                f"THEN '{rule.label.replace(\"'\", \"''\")}'"
            )
        else:
            branches.append(
                f"WHEN {column_name} >= {rule.minimum:g} "
                f"AND {column_name} < {rule.maximum:g} "
                f"THEN '{rule.label.replace(\"'\", \"''\")}'"
            )

    branches.append(f"ELSE '{default_label.replace(\"'\", \"''\")}'")

    return "CASE\n    " + "\n    ".join(branches) + "\nEND"


def demonstrate_generated_case(connection: sqlite3.Connection) -> None:
    """
    Generate a CASE expression from validated configuration.

    This models a common reporting system where business thresholds are stored
    as application configuration rather than being manually edited in every
    SQL query.
    """
    rules = [
        CaseRule("Micro", 0, 5000),
        CaseRule("Small", 5000, 15000),
        CaseRule("Medium", 15000, 50000),
        CaseRule("Large", 50000, None),
    ]

    case_expression = build_bucket_case(
        "order_amount",
        rules,
        "Unclassified",
    )

    query = f"""
    SELECT
        order_id,
        order_amount,
        {case_expression} AS configurable_bucket
    FROM orders
    ORDER BY order_id;
    """

    print_rows(
        "Configuration-driven CASE generation",
        connection.execute(query),
    )


def demonstrate_parameterized_case(connection: sqlite3.Connection) -> None:
    """
    CASE expressions can use parameters.

    Parameter binding keeps values separate from SQL syntax. This is safer than
    constructing SQL by concatenating user-provided threshold values.
    """
    query = """
    SELECT
        order_id,
        order_amount,
        CASE
            WHEN order_amount >= ? THEN 'Above threshold'
            ELSE 'Below threshold'
        END AS threshold_status
    FROM orders
    ORDER BY order_id;
    """

    threshold = 30000.0

    print_rows(
        "Parameterized CASE threshold",
        connection.execute(query, (threshold,)),
    )


def demonstrate_null_semantics(connection: sqlite3.Connection) -> None:
    """
    SQL NULL represents an unknown or missing value.

    A condition such as discount_rate = 0 does not match NULL. An explicit
    IS NULL branch is therefore needed when missing data has business meaning.
    """
    query = """
    SELECT
        order_id,
        discount_rate,
        CASE
            WHEN discount_rate IS NULL THEN 'Missing'
            WHEN discount_rate = 0 THEN 'Explicitly zero'
            ELSE 'Present and non-zero'
        END AS discount_data_quality
    FROM orders
    ORDER BY order_id;
    """

    print_rows(
        "NULL-aware CASE semantics",
        connection.execute(query),
    )


def demonstrate_rule_overlap() -> None:
    """
    Show why CASE branch ordering is part of business-rule design.

    The two expressions produce different results for the same value because
    both conditions match 120000. The first matching WHEN wins.
    """
    print("\n--- CASE rule ordering and overlap ---")

    value = 120000

    first_query = """
    SELECT CASE
        WHEN ? >= 100000 THEN 'Premium'
        WHEN ? >= 50000 THEN 'Growth'
        ELSE 'Standard'
    END AS classification;
    """

    second_query = """
    SELECT CASE
        WHEN ? >= 50000 THEN 'Growth'
        WHEN ? >= 100000 THEN 'Premium'
        ELSE 'Standard'
    END AS classification;
    """

    connection = sqlite3.connect(":memory:")

    first = connection.execute(first_query, (value, value)).fetchone()[0]
    second = connection.execute(second_query, (value, value)).fetchone()[0]

    print(f"Threshold value: {value}")
    print(f"Premium-first rules: {first}")
    print(f"Growth-first rules:  {second}")
    print(
        "Design implication: overlapping CASE predicates must be ordered "
        "deliberately or replaced with mutually exclusive ranges."
    )

    connection.close()


def demonstrate_case_edge_conditions(connection: sqlite3.Connection) -> None:
    """
    Demonstrate boundary values and explicit fallback behavior.

    Boundaries use >= for the lower bound and < for the upper bound so every
    non-negative amount belongs to exactly one configured interval.
    """
    query = """
    WITH amounts(amount) AS (
        VALUES
            (0.0),
            (4999.99),
            (5000.0),
            (14999.99),
            (15000.0),
            (49999.99),
            (50000.0),
            (NULL)
    )
    SELECT
        amount,
        CASE
            WHEN amount IS NULL THEN 'Missing amount'
            WHEN amount < 5000 THEN 'Small'
            WHEN amount < 15000 THEN 'Medium'
            WHEN amount < 50000 THEN 'Large'
            ELSE 'Enterprise'
        END AS boundary_classification
    FROM amounts;
    """

    print_rows(
        "CASE boundaries and fallback behavior",
        connection.execute(query),
    )


def run_all_demos() -> None:
    connection = create_database()

    try:
        demonstrate_searched_case(connection)
        demonstrate_simple_case(connection)
        demonstrate_conditional_transformation(connection)
        demonstrate_bucketing(connection)
        demonstrate_business_rules(connection)
        demonstrate_case_with_aggregation(connection)
        demonstrate_case_in_having(connection)
        demonstrate_conditional_ordering(connection)
        demonstrate_generated_case(connection)
        demonstrate_parameterized_case(connection)
        demonstrate_null_semantics(connection)
        demonstrate_case_rule_overlap()
        demonstrate_case_edge_conditions(connection)

        print("\n--- CASE implementation considerations ---")
        print(
            "CASE is an expression: it produces a value that can be used in "
            "SELECT, aggregation, ORDER BY, and other expression contexts."
        )
        print(
            "Searched CASE is appropriate for ranges and compound predicates; "
            "simple CASE is appropriate for equality-based mappings."
        )
        print(
            "WHEN clauses are evaluated in order and the first matching branch "
            "determines the result."
        )
        print(
            "For maintainable production SQL, keep business thresholds "
            "consistent across reports and validate configurable ranges."
        )
        print(
            "CASE can simplify reporting, but large rule sets may belong in "
            "reference tables or dedicated rule engines rather than enormous "
            "hard-coded expressions."
        )
    finally:
        connection.close()


if __name__ == "__main__":
    run_all_demos()
