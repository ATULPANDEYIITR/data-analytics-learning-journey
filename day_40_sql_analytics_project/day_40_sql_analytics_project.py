"""
SQL Analytics Project
End-to-end business analytics database implemented with Python's standard library.

The program creates a realistic retail analytics database in SQLite, loads normalized
business data, validates the data, executes more than 40 analytical questions, and
exports selected results. The SQL patterns are intentionally close to PostgreSQL
analytics even though the executable demonstration uses SQLite for zero dependencies.
"""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


DB_PATH = Path("business_analytics.db")
REPORT_PATH = Path("analytics_report.csv")


SCHEMA = """
PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS monthly_sales;
DROP VIEW IF EXISTS customer_lifetime_value;
DROP VIEW IF EXISTS product_performance;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS sales_reps;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS categories;


CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE sales_reps (
    sales_rep_id INTEGER PRIMARY KEY,
    rep_name TEXT NOT NULL,
    region_id INTEGER NOT NULL REFERENCES regions(region_id)
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('Consumer', 'Corporate', 'Small Business')),
    region_id INTEGER NOT NULL REFERENCES regions(region_id),
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0 AND unit_cost <= unit_price)
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    sales_rep_id INTEGER NOT NULL REFERENCES sales_reps(sales_rep_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('Completed', 'Cancelled', 'Returned', 'Pending')
    ),
    discount_rate REAL NOT NULL DEFAULT 0
        CHECK (discount_rate >= 0 AND discount_rate <= 1)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0 AND unit_cost <= unit_price),
    UNIQUE(order_id, product_id)
);

CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_rep ON orders(sales_rep_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_customers_region ON customers(region_id);

CREATE VIEW monthly_sales AS
SELECT
    substr(o.order_date, 1, 7) AS sales_month,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) AS revenue,
    SUM(oi.quantity) AS units
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY substr(o.order_date, 1, 7);

CREATE VIEW product_performance AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    SUM(CASE WHEN o.status = 'Completed'
        THEN oi.quantity ELSE 0 END) AS units_sold,
    ROUND(SUM(CASE WHEN o.status = 'Completed'
        THEN oi.quantity * oi.unit_price * (1 - o.discount_rate)
        ELSE 0 END), 2) AS revenue,
    ROUND(SUM(CASE WHEN o.status = 'Completed'
        THEN oi.quantity * (oi.unit_price * (1 - o.discount_rate) - oi.unit_cost)
        ELSE 0 END), 2) AS gross_profit
FROM products p
JOIN categories c ON c.category_id = p.category_id
LEFT JOIN order_items oi ON oi.product_id = p.product_id
LEFT JOIN orders o ON o.order_id = oi.order_id
GROUP BY p.product_id, p.product_name, c.category_name;

CREATE VIEW customer_lifetime_value AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    COUNT(DISTINCT CASE WHEN o.status = 'Completed' THEN o.order_id END) AS orders_count,
    ROUND(COALESCE(SUM(
        CASE WHEN o.status = 'Completed'
        THEN oi.quantity * oi.unit_price * (1 - o.discount_rate)
        ELSE 0 END
    ), 0), 2) AS lifetime_revenue
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, c.customer_name, c.segment;
"""


@dataclass(frozen=True)
class Query:
    name: str
    sql: str


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def seed_database(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)

    categories = [
        (1, "Electronics"),
        (2, "Office Equipment"),
        (3, "Furniture"),
        (4, "Software"),
    ]
    regions = [
        (1, "North"),
        (2, "South"),
        (3, "East"),
        (4, "West"),
    ]
    reps = [
        (1, "Aarav Mehta", 1),
        (2, "Priya Sharma", 2),
        (3, "Rohan Singh", 3),
        (4, "Neha Verma", 4),
    ]
    customers = [
        (1, "Atlas Consulting", "Corporate", 1, "2025-01-12"),
        (2, "BluePeak Retail", "Small Business", 2, "2025-02-18"),
        (3, "Cedar Finance", "Corporate", 3, "2025-03-07"),
        (4, "Delta Health", "Corporate", 4, "2025-04-21"),
        (5, "Evergreen Traders", "Small Business", 1, "2025-05-15"),
        (6, "Falcon Services", "Consumer", 2, "2025-06-09"),
        (7, "Granite Labs", "Corporate", 3, "2025-07-14"),
        (8, "Horizon Media", "Small Business", 4, "2025-08-20"),
        (9, "Indigo Works", "Consumer", 1, "2025-09-11"),
        (10, "Jupiter Systems", "Corporate", 2, "2025-10-02"),
    ]
    products = [
        (1, "Business Laptop", 1, 1200, 820),
        (2, "Network Router", 1, 420, 260),
        (3, "Laser Printer", 2, 550, 340),
        (4, "Conference Desk", 3, 780, 470),
        (5, "Ergonomic Chair", 3, 360, 210),
        (6, "Analytics Suite", 4, 900, 180),
        (7, "Security Monitor", 1, 650, 390),
        (8, "Document Scanner", 2, 310, 180),
    ]

    connection.executemany(
        "INSERT INTO categories VALUES (?, ?)", categories
    )
    connection.executemany(
        "INSERT INTO regions VALUES (?, ?)", regions
    )
    connection.executemany(
        "INSERT INTO sales_reps VALUES (?, ?, ?)", reps
    )
    connection.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers
    )
    connection.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?)", products
    )

    order_rows = []
    item_rows = []
    start = date(2026, 1, 5)
    order_id = 1
    item_id = 1

    # The deterministic generator makes the dataset reproducible while still
    # creating different months, segments, products, discounts, and outcomes.
    for index in range(48):
        order_date = start + timedelta(days=index * 6)
        customer_id = (index % 10) + 1
        rep_id = ((index + 1) % 4) + 1

        if index in {11, 27, 43}:
            status = "Cancelled"
        elif index in {17, 36}:
            status = "Returned"
        elif index in {7, 25, 41}:
            status = "Pending"
        else:
            status = "Completed"

        discount = [0, 0.05, 0.10, 0.15][index % 4]

        order_rows.append(
            (
                order_id,
                customer_id,
                rep_id,
                order_date.isoformat(),
                status,
                discount,
            )
        )

        first_product = (index % len(products)) + 1
        second_product = ((index * 3) % len(products)) + 1

        for product_id in {first_product, second_product}:
            product = products[product_id - 1]
            quantity = (index % 4) + 1
            item_rows.append(
                (
                    item_id,
                    order_id,
                    product_id,
                    quantity,
                    product[3],
                    product[4],
                )
            )
            item_id += 1

        order_id += 1

    connection.executemany(
        """
        INSERT INTO orders
        (order_id, customer_id, sales_rep_id, order_date, status, discount_rate)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        order_rows,
    )
    connection.executemany(
        """
        INSERT INTO order_items
        (order_item_id, order_id, product_id, quantity, unit_price, unit_cost)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        item_rows,
    )
    connection.commit()


QUERIES = [
    Query("Revenue by month", """
        SELECT sales_month, revenue
        FROM monthly_sales
        ORDER BY sales_month
    """),
    Query("Units by month", """
        SELECT sales_month, units
        FROM monthly_sales
        ORDER BY sales_month
    """),
    Query("Total completed revenue", """
        SELECT ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) AS revenue
        FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
    """),
    Query("Total gross profit", """
        SELECT ROUND(SUM(
            oi.quantity * (oi.unit_price * (1 - o.discount_rate) - oi.unit_cost)
        ), 2) AS gross_profit
        FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
    """),
    Query("Average completed order value", """
        SELECT ROUND(AVG(order_value), 2) AS average_order_value
        FROM (
            SELECT o.order_id,
                   SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)) AS order_value
            FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'Completed'
            GROUP BY o.order_id
        )
    """),
    Query("Revenue by region", """
        SELECT r.region_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM regions r
        JOIN customers c ON c.region_id = r.region_id
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY r.region_id, r.region_name
        ORDER BY revenue DESC
    """),
    Query("Revenue by customer segment", """
        SELECT c.segment,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY c.segment
        ORDER BY revenue DESC
    """),
    Query("Revenue by category", """
        SELECT cat.category_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM categories cat
        JOIN products p ON p.category_id = cat.category_id
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'Completed'
        GROUP BY cat.category_id, cat.category_name
        ORDER BY revenue DESC
    """),
    Query("Units by category", """
        SELECT cat.category_name, SUM(oi.quantity) units
        FROM categories cat
        JOIN products p ON p.category_id = cat.category_id
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'Completed'
        GROUP BY cat.category_id, cat.category_name
        ORDER BY units DESC
    """),
    Query("Top products by revenue", """
        SELECT product_name, category_name, revenue
        FROM product_performance
        ORDER BY revenue DESC
        LIMIT 5
    """),
    Query("Top products by units", """
        SELECT product_name, units_sold
        FROM product_performance
        ORDER BY units_sold DESC
        LIMIT 5
    """),
    Query("Top products by gross profit", """
        SELECT product_name, gross_profit
        FROM product_performance
        ORDER BY gross_profit DESC
        LIMIT 5
    """),
    Query("Product margin percentage", """
        SELECT product_name,
               ROUND(100.0 * gross_profit / NULLIF(revenue, 0), 2) margin_pct
        FROM product_performance
        WHERE revenue > 0
        ORDER BY margin_pct DESC
    """),
    Query("Customer lifetime value ranking", """
        SELECT customer_name, segment, orders_count, lifetime_revenue
        FROM customer_lifetime_value
        ORDER BY lifetime_revenue DESC
    """),
    Query("Customers with no completed revenue", """
        SELECT customer_name, segment
        FROM customer_lifetime_value
        WHERE lifetime_revenue = 0
    """),
    Query("Orders by status", """
        SELECT status, COUNT(*) order_count
        FROM orders
        GROUP BY status
        ORDER BY order_count DESC
    """),
    Query("Cancellation rate", """
        SELECT ROUND(
            100.0 * SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) cancellation_rate_pct
        FROM orders
    """),
    Query("Return rate", """
        SELECT ROUND(
            100.0 * SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) return_rate_pct
        FROM orders
    """),
    Query("Pending orders", """
        SELECT o.order_id, c.customer_name, o.order_date
        FROM orders o JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.status = 'Pending'
        ORDER BY o.order_date
    """),
    Query("Sales representative revenue", """
        SELECT sr.rep_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM sales_reps sr
        JOIN orders o ON o.sales_rep_id = sr.sales_rep_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY sr.sales_rep_id, sr.rep_name
        ORDER BY revenue DESC
    """),
    Query("Sales representative order count", """
        SELECT sr.rep_name, COUNT(DISTINCT o.order_id) orders_count
        FROM sales_reps sr
        JOIN orders o ON o.sales_rep_id = sr.sales_rep_id
        WHERE o.status = 'Completed'
        GROUP BY sr.sales_rep_id, sr.rep_name
        ORDER BY orders_count DESC
    """),
    Query("Discount impact by rate", """
        SELECT discount_rate,
               COUNT(*) order_count,
               ROUND(SUM(
                   oi.quantity * oi.unit_price * (1 - o.discount_rate)
               ), 2) net_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY discount_rate
        ORDER BY discount_rate
    """),
    Query("High-value orders", """
        SELECT o.order_id, c.customer_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) order_value
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY o.order_id, c.customer_name
        HAVING order_value >= 2500
        ORDER BY order_value DESC
    """),
    Query("Customer order frequency", """
        SELECT c.customer_name, COUNT(DISTINCT o.order_id) completed_orders
        FROM customers c
        LEFT JOIN orders o
          ON o.customer_id = c.customer_id AND o.status = 'Completed'
        GROUP BY c.customer_id, c.customer_name
        ORDER BY completed_orders DESC
    """),
    Query("Average units per order", """
        SELECT ROUND(
            CAST(SUM(oi.quantity) AS REAL) / COUNT(DISTINCT o.order_id), 2
        ) avg_units_per_order
        FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
    """),
    Query("Revenue concentration by customer", """
        WITH totals AS (
            SELECT SUM(lifetime_revenue) total_revenue
            FROM customer_lifetime_value
        )
        SELECT customer_name,
               lifetime_revenue,
               ROUND(100.0 * lifetime_revenue / NULLIF(t.total_revenue, 0), 2) revenue_share_pct
        FROM customer_lifetime_value, totals t
        WHERE lifetime_revenue > 0
        ORDER BY lifetime_revenue DESC
    """),
    Query("Revenue by customer and category", """
        SELECT c.customer_name, cat.category_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE o.status = 'Completed'
        GROUP BY c.customer_id, c.customer_name, cat.category_id, cat.category_name
        ORDER BY revenue DESC
    """),
    Query("Regional category performance", """
        SELECT r.region_name, cat.category_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM regions r
        JOIN customers c ON c.region_id = r.region_id
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE o.status = 'Completed'
        GROUP BY r.region_id, r.region_name, cat.category_id, cat.category_name
        ORDER BY r.region_name, revenue DESC
    """),
    Query("Best category per region", """
        WITH regional_category AS (
            SELECT r.region_name, cat.category_name,
                   SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)) revenue
            FROM regions r
            JOIN customers c ON c.region_id = r.region_id
            JOIN orders o ON o.customer_id = c.customer_id
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            JOIN categories cat ON cat.category_id = p.category_id
            WHERE o.status = 'Completed'
            GROUP BY r.region_id, r.region_name, cat.category_id, cat.category_name
        ),
        ranked AS (
            SELECT *,
                   RANK() OVER (
                       PARTITION BY region_name ORDER BY revenue DESC
                   ) category_rank
            FROM regional_category
        )
        SELECT region_name, category_name, ROUND(revenue, 2) revenue
        FROM ranked
        WHERE category_rank = 1
    """),
    Query("Monthly revenue change", """
        WITH months AS (
            SELECT sales_month, revenue,
                   LAG(revenue) OVER (ORDER BY sales_month) previous_revenue
            FROM monthly_sales
        )
        SELECT sales_month, revenue,
               ROUND(revenue - previous_revenue, 2) absolute_change,
               ROUND(100.0 * (revenue - previous_revenue)
                     / NULLIF(previous_revenue, 0), 2) pct_change
        FROM months
    """),
    Query("Running revenue total", """
        SELECT sales_month, revenue,
               ROUND(SUM(revenue) OVER (
                   ORDER BY sales_month
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ), 2) running_revenue
        FROM monthly_sales
    """),
    Query("Three-month moving average", """
        SELECT sales_month, revenue,
               ROUND(AVG(revenue) OVER (
                   ORDER BY sales_month
                   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
               ), 2) moving_average
        FROM monthly_sales
    """),
    Query("Category revenue ranking", """
        SELECT category_name, revenue,
               RANK() OVER (ORDER BY revenue DESC) revenue_rank
        FROM (
            SELECT cat.category_name,
                   SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)) revenue
            FROM categories cat
            JOIN products p ON p.category_id = cat.category_id
            JOIN order_items oi ON oi.product_id = p.product_id
            JOIN orders o ON o.order_id = oi.order_id
            WHERE o.status = 'Completed'
            GROUP BY cat.category_id, cat.category_name
        )
    """),
    Query("Customer segment ranking", """
        SELECT segment, lifetime_revenue,
               DENSE_RANK() OVER (ORDER BY lifetime_revenue DESC) segment_rank
        FROM (
            SELECT segment, SUM(lifetime_revenue) lifetime_revenue
            FROM customer_lifetime_value
            GROUP BY segment
        )
    """),
    Query("Customers above segment average", """
        WITH customer_values AS (
            SELECT customer_id, customer_name, segment, lifetime_revenue
            FROM customer_lifetime_value
        ),
        segment_avg AS (
            SELECT segment, AVG(lifetime_revenue) avg_value
            FROM customer_values
            GROUP BY segment
        )
        SELECT cv.customer_name, cv.segment, cv.lifetime_revenue,
               ROUND(sa.avg_value, 2) segment_average
        FROM customer_values cv
        JOIN segment_avg sa ON sa.segment = cv.segment
        WHERE cv.lifetime_revenue > sa.avg_value
        ORDER BY cv.lifetime_revenue DESC
    """),
    Query("Repeat customers", """
        SELECT customer_name, orders_count
        FROM customer_lifetime_value
        WHERE orders_count >= 2
        ORDER BY orders_count DESC, customer_name
    """),
    Query("Single-order customers", """
        SELECT customer_name
        FROM customer_lifetime_value
        WHERE orders_count = 1
        ORDER BY customer_name
    """),
    Query("Product revenue contribution", """
        WITH product_totals AS (
            SELECT SUM(revenue) total_revenue
            FROM product_performance
        )
        SELECT product_name, revenue,
               ROUND(100.0 * revenue / NULLIF(total_revenue, 0), 2) contribution_pct
        FROM product_performance, product_totals
        WHERE revenue > 0
        ORDER BY contribution_pct DESC
    """),
    Query("Low-margin products", """
        SELECT product_name, revenue, gross_profit,
               ROUND(100.0 * gross_profit / NULLIF(revenue, 0), 2) margin_pct
        FROM product_performance
        WHERE revenue > 0
          AND 100.0 * gross_profit / revenue < 35
        ORDER BY margin_pct
    """),
    Query("Cancelled order value", """
        SELECT ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) cancelled_value
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Cancelled'
    """),
    Query("Returned order value", """
        SELECT ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) returned_value
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Returned'
    """),
    Query("Revenue by sales representative region", """
        SELECT r.region_name, sr.rep_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)), 2) revenue
        FROM sales_reps sr
        JOIN regions r ON r.region_id = sr.region_id
        JOIN orders o ON o.sales_rep_id = sr.sales_rep_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY r.region_id, r.region_name, sr.sales_rep_id, sr.rep_name
        ORDER BY revenue DESC
    """),
    Query("Average discount by segment", """
        SELECT c.segment, ROUND(AVG(o.discount_rate) * 100, 2) avg_discount_pct
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        WHERE o.status = 'Completed'
        GROUP BY c.segment
        ORDER BY avg_discount_pct DESC
    """),
    Query("Order value distribution", """
        WITH order_values AS (
            SELECT o.order_id,
                   SUM(oi.quantity * oi.unit_price * (1 - o.discount_rate)) value
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'Completed'
            GROUP BY o.order_id
        )
        SELECT
            CASE
                WHEN value < 1000 THEN 'Under 1000'
                WHEN value < 2500 THEN '1000-2499'
                ELSE '2500+'
            END AS order_band,
            COUNT(*) order_count,
            ROUND(SUM(value), 2) revenue
        FROM order_values
        GROUP BY order_band
        ORDER BY revenue DESC
    """),
    Query("Data quality: orphan order items", """
        SELECT COUNT(*) orphan_items
        FROM order_items oi
        LEFT JOIN orders o ON o.order_id = oi.order_id
        WHERE o.order_id IS NULL
    """),
    Query("Data quality: invalid product economics", """
        SELECT COUNT(*) invalid_products
        FROM products
        WHERE unit_price <= 0 OR unit_cost < 0 OR unit_cost > unit_price
    """),
    Query("Data quality: customers without orders", """
        SELECT c.customer_name
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id
        WHERE o.order_id IS NULL
    """),
    Query("Data quality: products never sold", """
        SELECT p.product_name
        FROM products p
        LEFT JOIN order_items oi ON oi.product_id = p.product_id
        WHERE oi.order_item_id IS NULL
    """),
]


def run_query(connection: sqlite3.Connection, query: Query) -> list[sqlite3.Row]:
    return connection.execute(query.sql).fetchall()


def print_result(query: Query, rows: Iterable[sqlite3.Row]) -> None:
    rows = list(rows)
    print(f"\n=== {query.name} ===")
    if not rows:
        print("(no rows)")
        return

    columns = rows[0].keys()
    print(" | ".join(columns))
    print("-" * 90)
    for row in rows[:12]:
        print(" | ".join(str(row[column]) for column in columns))

    if len(rows) > 12:
        print(f"... {len(rows) - 12} additional rows")


def validate_database(connection: sqlite3.Connection) -> None:
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise RuntimeError(f"Foreign-key validation failed: {foreign_key_errors}")

    invalid_economics = connection.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE unit_price <= 0 OR unit_cost < 0 OR unit_cost > unit_price
    """).fetchone()[0]

    if invalid_economics:
        raise RuntimeError("Product economic constraints are violated.")

    print("\nDatabase validation passed.")
    print(f"Analytical questions configured: {len(QUERIES)}")


def export_report(connection: sqlite3.Connection) -> None:
    query = """
        SELECT
            c.customer_name,
            c.segment,
            r.region_name,
            COUNT(DISTINCT o.order_id) completed_orders,
            ROUND(SUM(
                oi.quantity * oi.unit_price * (1 - o.discount_rate)
            ), 2) revenue
        FROM customers c
        JOIN regions r ON r.region_id = c.region_id
        LEFT JOIN orders o
          ON o.customer_id = c.customer_id
         AND o.status = 'Completed'
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY c.customer_id, c.customer_name, c.segment, r.region_name
        ORDER BY revenue DESC
    """

    rows = connection.execute(query).fetchall()

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(rows[0].keys() if rows else [
            "customer_name", "segment", "region_name",
            "completed_orders", "revenue"
        ])
        for row in rows:
            writer.writerow(tuple(row))

    print(f"\nExported customer analytics to {REPORT_PATH.resolve()}")


def explain_query_plan(connection: sqlite3.Connection) -> None:
    plan = connection.execute("""
        EXPLAIN QUERY PLAN
        SELECT c.customer_name,
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY c.customer_id, c.customer_name
    """).fetchall()

    print("\n=== Query plan for customer revenue analysis ===")
    for row in plan:
        print(tuple(row))


def main() -> None:
    connection = connect()
    try:
        seed_database(connection)
        validate_database(connection)

        for query in QUERIES:
            print_result(query, run_query(connection, query))

        explain_query_plan(connection)
        export_report(connection)

        print("\nAnalytics run completed successfully.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
