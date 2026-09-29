"""
SQL Subqueries: Scalar Subqueries, Correlated Subqueries, Nested Queries,
EXISTS, and NOT EXISTS

This standalone study program teaches SQL subqueries from beginner through
advanced level using Python's standard library sqlite3 module.

The examples are executable. SQLite is used because it is included with
Python and supports scalar subqueries, correlated subqueries, nested queries,
EXISTS, NOT EXISTS, aggregation, CTEs, window functions, indexes, and query
plans.

The program builds a small sales database and progressively demonstrates:

1. What a subquery is
2. Scalar subqueries
3. Single-row and multi-row subqueries
4. IN and NOT IN
5. EXISTS and NOT EXISTS
6. Correlated subqueries
7. Nested subqueries
8. Subqueries in SELECT, FROM, and WHERE
9. Aggregate subqueries
10. Comparison operators with scalar subqueries
11. Derived tables
12. Relational division using NOT EXISTS
13. Anti-joins and NULL-related pitfalls
14. Correlated-subquery performance
15. Query-plan inspection
16. Transaction-safe data manipulation involving subqueries
17. Validation and edge cases
18. Practical reporting patterns

Run with:

    python sql_subqueries.py
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


DATABASE_SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('Retail', 'Business', 'Enterprise'))
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')
    ),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category);
"""


CUSTOMERS = [
    (1, "Aarav Retail", "Lucknow", "Retail"),
    (2, "Bharat Foods", "Delhi", "Business"),
    (3, "Crescent Labs", "Bengaluru", "Enterprise"),
    (4, "Delta Stores", "Mumbai", "Retail"),
    (5, "Evergreen Systems", "Pune", "Enterprise"),
    (6, "Future Office", "Hyderabad", "Business"),
    (7, "Galaxy Traders", "Jaipur", "Business"),
    (8, "Horizon Retail", "Kolkata", "Retail"),
]

PRODUCTS = [
    (1, "Laptop Pro", "Computers", 90000.00, 1),
    (2, "Office Laptop", "Computers", 60000.00, 1),
    (3, "Mechanical Keyboard", "Accessories", 7000.00, 1),
    (4, "Wireless Mouse", "Accessories", 2500.00, 1),
    (5, "4K Monitor", "Displays", 30000.00, 1),
    (6, "USB-C Dock", "Accessories", 12000.00, 1),
    (7, "Server Rack", "Infrastructure", 50000.00, 1),
    (8, "Network Switch", "Infrastructure", 18000.00, 1),
    (9, "Legacy Monitor", "Displays", 10000.00, 0),
]

ORDERS = [
    (101, 1, "2026-01-05", "Delivered"),
    (102, 1, "2026-02-10", "Delivered"),
    (103, 2, "2026-01-15", "Shipped"),
    (104, 2, "2026-03-01", "Delivered"),
    (105, 3, "2026-01-20", "Delivered"),
    (106, 3, "2026-02-21", "Delivered"),
    (107, 4, "2026-02-05", "Cancelled"),
    (108, 4, "2026-03-11", "Delivered"),
    (109, 5, "2026-01-25", "Delivered"),
    (110, 5, "2026-03-14", "Delivered"),
    (111, 6, "2026-02-18", "Pending"),
    (112, 7, "2026-03-15", "Delivered"),
]

ORDER_ITEMS = [
    (101, 1, 1, 90000),
    (101, 3, 2, 7000),
    (102, 5, 2, 30000),
    (102, 4, 2, 2500),
    (103, 2, 3, 60000),
    (103, 4, 3, 2500),
    (104, 7, 1, 50000),
    (104, 8, 2, 18000),
    (105, 1, 2, 90000),
    (105, 6, 2, 12000),
    (106, 5, 3, 30000),
    (106, 3, 5, 7000),
    (107, 9, 2, 10000),
    (108, 2, 2, 60000),
    (108, 4, 4, 2500),
    (109, 7, 2, 50000),
    (109, 8, 2, 18000),
    (110, 1, 1, 90000),
    (110, 6, 1, 12000),
    (111, 3, 3, 7000),
    (112, 8, 5, 18000),
]


@dataclass(frozen=True)
class QueryExample:
    title: str
    purpose: str
    sql: str
    parameters: tuple[Any, ...] = ()


def create_connection() -> sqlite3.Connection:
    """Create an in-memory database with foreign-key enforcement."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(DATABASE_SCHEMA)

    connection.executemany(
        """
        INSERT INTO customers(customer_id, customer_name, city, segment)
        VALUES (?, ?, ?, ?)
        """,
        CUSTOMERS,
    )

    connection.executemany(
        """
        INSERT INTO products(product_id, product_name, category, price, active)
        VALUES (?, ?, ?, ?, ?)
        """,
        PRODUCTS,
    )

    connection.executemany(
        """
        INSERT INTO orders(order_id, customer_id, order_date, status)
        VALUES (?, ?, ?, ?)
        """,
        ORDERS,
    )

    connection.executemany(
        """
        INSERT INTO order_items(order_id, product_id, quantity, unit_price)
        VALUES (?, ?, ?, ?)
        """,
        ORDER_ITEMS,
    )

    connection.commit()
    return connection


def print_rows(rows: Sequence[sqlite3.Row], max_rows: int = 20) -> None:
    """Print query results in a compact table-like representation."""
    if not rows:
        print("(no rows)")
        return

    rows_to_show = list(rows[:max_rows])
    columns = rows_to_show[0].keys()

    widths = {
        column: max(
            len(column),
            *(len(str(row[column])) for row in rows_to_show),
        )
        for column in columns
    }

    header = " | ".join(f"{column:<{widths[column]}}" for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in rows_to_show:
        print(
            " | ".join(
                f"{str(row[column]):<{widths[column]}}"
                for column in columns
            )
        )

    if len(rows) > max_rows:
        print(f"... {len(rows) - max_rows} additional row(s) omitted")


def run_query(
    connection: sqlite3.Connection,
    title: str,
    sql: str,
    parameters: Iterable[Any] = (),
) -> list[sqlite3.Row]:
    """Execute a SELECT query and display the result."""
    print(f"\n{'=' * 78}")
    print(title)
    print("=" * 78)
    print(sql.strip())

    rows = connection.execute(sql, tuple(parameters)).fetchall()
    print_rows(rows)
    return rows


def explain_query(
    connection: sqlite3.Connection,
    title: str,
    sql: str,
    parameters: Iterable[Any] = (),
) -> None:
    """Display SQLite's query plan for performance analysis."""
    print(f"\n--- Query plan: {title} ---")
    plan = connection.execute(
        f"EXPLAIN QUERY PLAN {sql}",
        tuple(parameters),
    ).fetchall()

    for row in plan:
        print(" | ".join(str(value) for value in row))


def scalar_subquery_examples(connection: sqlite3.Connection) -> None:
    """
    A scalar subquery returns one value.

    A scalar subquery can appear where a single value is expected. If a
    scalar subquery produces no row, SQLite represents the result as NULL.
    If it produces multiple rows, SQLite's scalar-subquery behavior differs
    across database systems, so production SQL should guarantee one row.
    """

    run_query(
        connection,
        "1. Scalar subquery: compare each product with the overall average price",
        """
        SELECT
            product_name,
            category,
            price,
            ROUND(
                price - (SELECT AVG(price) FROM products),
                2
            ) AS difference_from_average
        FROM products
        WHERE active = 1
        ORDER BY price DESC;
        """,
    )

    run_query(
        connection,
        "2. Scalar subquery: find products priced above the global average",
        """
        SELECT product_name, price
        FROM products
        WHERE price > (
            SELECT AVG(price)
            FROM products
        )
        ORDER BY price DESC;
        """,
    )

    run_query(
        connection,
        "3. Scalar subquery in SELECT: display the global average beside every product",
        """
        SELECT
            product_name,
            price,
            ROUND((SELECT AVG(price) FROM products), 2) AS average_price
        FROM products
        WHERE active = 1
        ORDER BY product_id;
        """,
    )

    run_query(
        connection,
        "4. Scalar subquery with MAX: identify the most expensive product(s)",
        """
        SELECT product_name, price
        FROM products
        WHERE price = (
            SELECT MAX(price)
            FROM products
        );
        """,
    )

    run_query(
        connection,
        "5. Scalar subquery with MIN: identify the least expensive active product",
        """
        SELECT product_name, price
        FROM products
        WHERE price = (
            SELECT MIN(price)
            FROM products
            WHERE active = 1
        );
        """,
    )


def multirow_subquery_examples(connection: sqlite3.Connection) -> None:
    """
    A multi-row subquery returns a set of values.

    IN is useful when the outer query should match any value returned by an
    inner query. NOT IN requires special care when the subquery can return
    NULL because SQL uses three-valued logic.
    """

    run_query(
        connection,
        "6. Multi-row subquery with IN: customers who have placed delivered orders",
        """
        SELECT customer_id, customer_name, segment
        FROM customers
        WHERE customer_id IN (
            SELECT customer_id
            FROM orders
            WHERE status = 'Delivered'
        )
        ORDER BY customer_id;
        """,
    )

    run_query(
        connection,
        "7. Multi-row subquery with IN: products appearing in delivered orders",
        """
        SELECT product_id, product_name, category
        FROM products
        WHERE product_id IN (
            SELECT product_id
            FROM order_items
            WHERE order_id IN (
                SELECT order_id
                FROM orders
                WHERE status = 'Delivered'
            )
        )
        ORDER BY product_id;
        """,
    )

    run_query(
        connection,
        "8. Nested subqueries: customers whose delivered order value exceeds 100,000",
        """
        SELECT customer_id, customer_name
        FROM customers
        WHERE customer_id IN (
            SELECT customer_id
            FROM orders
            WHERE order_id IN (
                SELECT order_id
                FROM (
                    SELECT
                        oi.order_id,
                        SUM(oi.quantity * oi.unit_price) AS order_value
                    FROM order_items AS oi
                    GROUP BY oi.order_id
                    HAVING SUM(oi.quantity * oi.unit_price) > 100000
                ) AS high_value_orders
            )
            AND status = 'Delivered'
        )
        ORDER BY customer_id;
        """,
    )

    run_query(
        connection,
        "9. Subquery returning values for NOT IN",
        """
        SELECT customer_id, customer_name
        FROM customers
        WHERE customer_id NOT IN (
            SELECT customer_id
            FROM orders
            WHERE status = 'Delivered'
        )
        ORDER BY customer_id;
        """,
    )


def exists_examples(connection: sqlite3.Connection) -> None:
    """
    EXISTS tests whether at least one related row exists.

    EXISTS is logically a Boolean existence test. The database can often stop
    searching once it finds the first matching row, making EXISTS natural for
    relationship tests.
    """

    run_query(
        connection,
        "10. EXISTS: customers with at least one delivered order",
        """
        SELECT c.customer_id, c.customer_name
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Delivered'
        )
        ORDER BY c.customer_id;
        """,
    )

    run_query(
        connection,
        "11. EXISTS: products that have ever been ordered",
        """
        SELECT p.product_id, p.product_name
        FROM products AS p
        WHERE EXISTS (
            SELECT 1
            FROM order_items AS oi
            WHERE oi.product_id = p.product_id
        )
        ORDER BY p.product_id;
        """,
    )

    run_query(
        connection,
        "12. EXISTS: customers with at least one order above 100,000",
        """
        SELECT c.customer_name
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND EXISTS (
                  SELECT 1
                  FROM order_items AS oi
                  WHERE oi.order_id = o.order_id
                  GROUP BY oi.order_id
                  HAVING SUM(oi.quantity * oi.unit_price) > 100000
              )
        )
        ORDER BY c.customer_name;
        """,
    )


def not_exists_examples(connection: sqlite3.Connection) -> None:
    """
    NOT EXISTS is the standard anti-existence pattern.

    It asks whether there is no related row satisfying the inner condition.
    Unlike NOT IN, NOT EXISTS is not exposed to the same NULL poisoning
    behavior when written correctly.
    """

    run_query(
        connection,
        "13. NOT EXISTS: customers with no delivered order",
        """
        SELECT c.customer_id, c.customer_name
        FROM customers AS c
        WHERE NOT EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Delivered'
        )
        ORDER BY c.customer_id;
        """,
    )

    run_query(
        connection,
        "14. NOT EXISTS: products that have never been ordered",
        """
        SELECT p.product_id, p.product_name
        FROM products AS p
        WHERE NOT EXISTS (
            SELECT 1
            FROM order_items AS oi
            WHERE oi.product_id = p.product_id
        )
        ORDER BY p.product_id;
        """,
    )

    run_query(
        connection,
        "15. NOT EXISTS: customers with no cancelled orders",
        """
        SELECT c.customer_id, c.customer_name
        FROM customers AS c
        WHERE NOT EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Cancelled'
        )
        ORDER BY c.customer_id;
        """,
    )


def correlated_subquery_examples(connection: sqlite3.Connection) -> None:
    """
    A correlated subquery references a column from the current outer row.

    Conceptually, the inner query is evaluated in the context of each outer
    row. Modern optimizers can transform correlated queries, but the logical
    dependency remains important.
    """

    run_query(
        connection,
        "16. Correlated subquery: customers with their latest order date",
        """
        SELECT
            c.customer_id,
            c.customer_name,
            (
                SELECT MAX(o.order_date)
                FROM orders AS o
                WHERE o.customer_id = c.customer_id
            ) AS latest_order_date
        FROM customers AS c
        ORDER BY c.customer_id;
        """,
    )

    run_query(
        connection,
        "17. Correlated scalar subquery: count orders for every customer",
        """
        SELECT
            c.customer_name,
            (
                SELECT COUNT(*)
                FROM orders AS o
                WHERE o.customer_id = c.customer_id
            ) AS order_count
        FROM customers AS c
        ORDER BY order_count DESC, c.customer_name;
        """,
    )

    run_query(
        connection,
        "18. Correlated subquery: products priced above their category average",
        """
        SELECT
            p.product_name,
            p.category,
            p.price
        FROM products AS p
        WHERE p.active = 1
          AND p.price > (
              SELECT AVG(p2.price)
              FROM products AS p2
              WHERE p2.category = p.category
                AND p2.active = 1
          )
        ORDER BY p.category, p.price DESC;
        """,
    )

    run_query(
        connection,
        "19. Correlated NOT EXISTS: customers with no pending orders",
        """
        SELECT c.customer_id, c.customer_name
        FROM customers AS c
        WHERE NOT EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Pending'
        )
        ORDER BY c.customer_id;
        """,
    )


def from_subquery_examples(connection: sqlite3.Connection) -> None:
    """
    A subquery in FROM creates a derived table.

    A derived table behaves like a temporary result relation for the duration
    of the query. It is useful when an intermediate aggregate must be queried
    again.
    """

    run_query(
        connection,
        "20. Derived table: calculate order totals before filtering",
        """
        SELECT
            order_id,
            order_value
        FROM (
            SELECT
                order_id,
                SUM(quantity * unit_price) AS order_value
            FROM order_items
            GROUP BY order_id
        ) AS order_totals
        WHERE order_value > 100000
        ORDER BY order_value DESC;
        """,
    )

    run_query(
        connection,
        "21. Derived table: calculate customer revenue and classify customers",
        """
        SELECT
            customer_id,
            customer_name,
            revenue,
            CASE
                WHEN revenue >= 200000 THEN 'High Value'
                WHEN revenue >= 100000 THEN 'Medium Value'
                ELSE 'Standard'
            END AS customer_class
        FROM (
            SELECT
                c.customer_id,
                c.customer_name,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
            FROM customers AS c
            LEFT JOIN orders AS o
                ON o.customer_id = c.customer_id
               AND o.status <> 'Cancelled'
            LEFT JOIN order_items AS oi
                ON oi.order_id = o.order_id
            GROUP BY c.customer_id, c.customer_name
        ) AS customer_revenue
        ORDER BY revenue DESC;
        """,
    )


def comparison_subqueries(connection: sqlite3.Connection) -> None:
    """Demonstrate comparison operators and aggregate subqueries."""

    run_query(
        connection,
        "22. Compare every order with the average order value",
        """
        SELECT
            order_id,
            order_value
        FROM (
            SELECT
                order_id,
                SUM(quantity * unit_price) AS order_value
            FROM order_items
            GROUP BY order_id
        ) AS totals
        WHERE order_value > (
            SELECT AVG(order_value)
            FROM (
                SELECT
                    order_id,
                    SUM(quantity * unit_price) AS order_value
                FROM order_items
                GROUP BY order_id
            ) AS all_totals
        )
        ORDER BY order_value DESC;
        """,
    )

    run_query(
        connection,
        "23. Use ALL-like logic through MAX: product more expensive than every active accessory",
        """
        SELECT product_name, price
        FROM products
        WHERE price > (
            SELECT MAX(price)
            FROM products
            WHERE category = 'Accessories'
              AND active = 1
        )
        ORDER BY price DESC;
        """,
    )

    run_query(
        connection,
        "24. Use MIN-based logic: product cheaper than at least one active computer",
        """
        SELECT product_name, price
        FROM products
        WHERE price < (
            SELECT MAX(price)
            FROM products
            WHERE category = 'Computers'
              AND active = 1
        )
        ORDER BY price;
        """,
    )


def relational_division_example(connection: sqlite3.Connection) -> None:
    """
    Relational division asks questions such as:

        Which customers have purchased every required product?

    Nested NOT EXISTS is a powerful SQL pattern for this type of requirement.
    """

    required_products = (3, 4, 6)

    placeholders = ", ".join("?" for _ in required_products)

    sql = f"""
    SELECT c.customer_id, c.customer_name
    FROM customers AS c
    WHERE NOT EXISTS (
        SELECT 1
        FROM products AS required
        WHERE required.product_id IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1
              FROM orders AS o
              JOIN order_items AS oi
                ON oi.order_id = o.order_id
              WHERE o.customer_id = c.customer_id
                AND o.status = 'Delivered'
                AND oi.product_id = required.product_id
          )
    )
    ORDER BY c.customer_id;
    """

    run_query(
        connection,
        "25. Double NOT EXISTS: customers who purchased every required product",
        sql,
        required_products,
    )


def null_and_not_in_demo(connection: sqlite3.Connection) -> None:
    """
    SQL uses three-valued logic: TRUE, FALSE, and UNKNOWN.

    The classic NOT IN problem occurs when the subquery contains NULL.
    To make the issue visible, a small independent table is created.
    """

    connection.execute("CREATE TABLE nullable_values (value INTEGER)")
    connection.executemany(
        "INSERT INTO nullable_values(value) VALUES (?)",
        [(1,), (2,), (None,)],
    )

    run_query(
        connection,
        "26. NULL demonstration: inspect values returned by a subquery",
        """
        SELECT value
        FROM nullable_values
        ORDER BY value IS NOT NULL, value;
        """,
    )

    run_query(
        connection,
        "27. Safer anti-existence pattern with NOT EXISTS",
        """
        SELECT candidate.value
        FROM (
            SELECT 1 AS value
            UNION ALL SELECT 2
            UNION ALL SELECT 3
        ) AS candidate
        WHERE NOT EXISTS (
            SELECT 1
            FROM nullable_values AS n
            WHERE n.value = candidate.value
        )
        ORDER BY candidate.value;
        """,
    )

    print(
        "\nImportant rule: NOT IN can produce UNKNOWN when its subquery contains "
        "NULL. NOT EXISTS is usually safer for anti-join logic."
    )


def window_function_comparison(connection: sqlite3.Connection) -> None:
    """
    Some problems that can be solved by correlated subqueries can also be
    solved by window functions. The comparison illustrates query-design
    alternatives rather than declaring one universally superior.
    """

    run_query(
        connection,
        "28. Correlated subquery: highest-priced product in each category",
        """
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.price
        FROM products AS p
        WHERE p.price = (
            SELECT MAX(p2.price)
            FROM products AS p2
            WHERE p2.category = p.category
        )
        ORDER BY p.category, p.product_id;
        """,
    )

    run_query(
        connection,
        "29. Window-function alternative: highest-priced product in each category",
        """
        SELECT product_id, product_name, category, price
        FROM (
            SELECT
                product_id,
                product_name,
                category,
                price,
                RANK() OVER (
                    PARTITION BY category
                    ORDER BY price DESC
                ) AS category_rank
            FROM products
        ) AS ranked_products
        WHERE category_rank = 1
        ORDER BY category, product_id;
        """,
    )


def update_with_subquery(connection: sqlite3.Connection) -> None:
    """
    Subqueries are not limited to SELECT statements.

    This example updates product prices using an aggregate value from another
    query. The operation is wrapped in a transaction and rolled back so the
    demonstration does not permanently modify the study dataset.
    """

    print("\n" + "=" * 78)
    print("30. UPDATE using a scalar subquery")
    print("=" * 78)

    before = connection.execute(
        "SELECT product_id, product_name, price FROM products WHERE active = 1"
    ).fetchall()

    connection.execute("BEGIN")

    connection.execute(
        """
        UPDATE products
        SET price = price * 1.05
        WHERE category = 'Accessories'
          AND price < (
              SELECT AVG(price)
              FROM products
              WHERE category = 'Accessories'
          );
        """
    )

    after = connection.execute(
        "SELECT product_id, product_name, price FROM products WHERE active = 1"
    ).fetchall()

    print("Rows before temporary update:")
    print_rows(before)

    print("\nRows after temporary update:")
    print_rows(after)

    connection.rollback()
    print("\nTransaction rolled back; original prices restored.")


def delete_with_subquery(connection: sqlite3.Connection) -> None:
    """
    DELETE can also use EXISTS or NOT EXISTS.

    This demonstration runs inside a savepoint and rolls back.
    """

    print("\n" + "=" * 78)
    print("31. DELETE using NOT EXISTS")
    print("=" * 78)

    connection.execute("SAVEPOINT delete_demo")

    before_count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    connection.execute(
        """
        DELETE FROM products AS p
        WHERE NOT EXISTS (
            SELECT 1
            FROM order_items AS oi
            WHERE oi.product_id = p.product_id
        );
        """
    )

    after_count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    print(f"Product rows before temporary DELETE: {before_count}")
    print(f"Product rows after temporary DELETE:  {after_count}")

    connection.execute("ROLLBACK TO delete_demo")
    connection.execute("RELEASE delete_demo")
    print("Savepoint rolled back; original rows restored.")


def query_plan_examples(connection: sqlite3.Connection) -> None:
    """
    Performance depends on data size, indexes, optimizer behavior, selectivity,
    and query shape. EXPLAIN QUERY PLAN helps inspect how SQLite intends to
    execute a statement.
    """

    explain_query(
        connection,
        "Correlated EXISTS with indexed customer relationship",
        """
        SELECT c.customer_name
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Delivered'
        );
        """,
    )

    explain_query(
        connection,
        "IN subquery",
        """
        SELECT customer_name
        FROM customers
        WHERE customer_id IN (
            SELECT customer_id
            FROM orders
            WHERE status = 'Delivered'
        );
        """,
    )

    print(
        "\nPerformance principle: do not assume a correlated subquery is slow "
        "or that a JOIN is always faster. Measure realistic workloads and "
        "inspect the execution plan."
    )


def validation_examples(connection: sqlite3.Connection) -> None:
    """Run small assertions that verify important query semantics."""

    delivered_customers = connection.execute(
        """
        SELECT COUNT(*)
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Delivered'
        );
        """
    ).fetchone()[0]

    products_never_ordered = connection.execute(
        """
        SELECT COUNT(*)
        FROM products AS p
        WHERE NOT EXISTS (
            SELECT 1
            FROM order_items AS oi
            WHERE oi.product_id = p.product_id
        );
        """
    ).fetchone()[0]

    average_price = connection.execute(
        "SELECT AVG(price) FROM products"
    ).fetchone()[0]

    assert delivered_customers > 0
    assert products_never_ordered >= 0
    assert average_price > 0

    print("\n" + "=" * 78)
    print("32. Validation checks")
    print("=" * 78)
    print(f"Customers with delivered orders: {delivered_customers}")
    print(f"Products never ordered: {products_never_ordered}")
    print(f"Average product price: {average_price:.2f}")
    print("All semantic assertions passed.")


def best_practice_examples(connection: sqlite3.Connection) -> None:
    """Show readable query patterns suitable for practical systems."""

    examples = [
        QueryExample(
            "EXISTS for relationship testing",
            "Tests whether at least one related row exists.",
            """
            SELECT c.customer_name
            FROM customers AS c
            WHERE EXISTS (
                SELECT 1
                FROM orders AS o
                WHERE o.customer_id = c.customer_id
            )
            ORDER BY c.customer_name;
            """,
        ),
        QueryExample(
            "NOT EXISTS for anti-existence",
            "Finds outer rows with no qualifying related row.",
            """
            SELECT p.product_name
            FROM products AS p
            WHERE NOT EXISTS (
                SELECT 1
                FROM order_items AS oi
                WHERE oi.product_id = p.product_id
            )
            ORDER BY p.product_name;
            """,
        ),
        QueryExample(
            "Scalar aggregate",
            "Compares a row against one global aggregate value.",
            """
            SELECT product_name, price
            FROM products
            WHERE price > (SELECT AVG(price) FROM products)
            ORDER BY price DESC;
            """,
        ),
    ]

    for example in examples:
        print(f"\n--- {example.title} ---")
        print(example.purpose)
        print(example.sql.strip())


def main() -> None:
    print("=" * 78)
    print("SQL SUBQUERIES: COMPLETE PYTHON STUDY PROGRAM")
    print("=" * 78)
    print(
        "Database: SQLite in memory\n"
        "Focus: scalar subqueries, correlated subqueries, nested queries, "
        "EXISTS, and NOT EXISTS"
    )

    with closing(create_connection()) as connection:
        scalar_subquery_examples(connection)
        multirow_subquery_examples(connection)
        exists_examples(connection)
        not_exists_examples(connection)
        correlated_subquery_examples(connection)
        from_subquery_examples(connection)
        comparison_subqueries(connection)
        relational_division_example(connection)
        null_and_not_in_demo(connection)
        window_function_comparison(connection)
        update_with_subquery(connection)
        delete_with_subquery(connection)
        query_plan_examples(connection)
        validation_examples(connection)
        best_practice_examples(connection)

        print("\n" + "=" * 78)
        print("Study program completed successfully.")
        print("=" * 78)


if __name__ == "__main__":
    main()
