"""
SQL Introduction: Databases, Relational Databases, Tables, Rows, Columns,
Primary Keys, Foreign Keys, Schemas, and the SQL Execution Model

This standalone study program teaches SQL database fundamentals through executable
Python examples. It uses Python's built-in sqlite3 module, so no external package
is required.

The examples progress from:
    1. Database fundamentals
    2. Relational database structure
    3. Tables, rows, and columns
    4. Primary keys
    5. Foreign keys
    6. Schemas and database metadata
    7. SQL statements and execution
    8. INSERT, SELECT, UPDATE, DELETE
    9. Filtering, sorting, grouping, and joins
   10. Constraints and validation
   11. Transactions and rollback
   12. Parameterized queries and SQL injection prevention
   13. Query plans and indexes
   14. Normalization concepts
   15. Realistic relational design
   16. Edge cases and common mistakes
   17. A complete mini database case study

Run with:
    python sql_introduction.py

The program creates an in-memory SQLite database, so it does not modify files.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Iterator, Sequence


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def print_title(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subtitle(title: str) -> None:
    """Print a smaller subsection heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def print_rows(rows: Sequence[sqlite3.Row]) -> None:
    """Display SQLite rows in a readable form."""
    if not rows:
        print("(no rows)")
        return

    column_names = rows[0].keys()
    print(" | ".join(column_names))
    print("-" * max(20, len(" | ".join(column_names)) + 10))

    for row in rows:
        print(" | ".join(str(row[column]) for column in column_names))


def execute_and_print(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Sequence[object] = (),
) -> list[sqlite3.Row]:
    """
    Execute a SQL query and print its result.

    Parameterized SQL is used whenever values come from program variables.
    """
    print(f"SQL> {sql}")
    if parameters:
        print(f"Parameters: {parameters}")

    cursor = connection.execute(sql, parameters)

    if cursor.description is None:
        print(f"Rows affected: {cursor.rowcount}")
        return []

    rows = cursor.fetchall()
    print_rows(rows)
    return rows


def explain_sql(sql: str, parameters: Sequence[object] = ()) -> None:
    """
    Explain the conceptual lifecycle of a SQL statement.

    SQLite internally performs considerably more work than this simplified
    teaching model. The stages shown here are useful for understanding why
    SQL is declarative.
    """
    print(f"\nStatement: {sql}")
    if parameters:
        print(f"Bound values: {parameters}")

    print("Conceptual execution model:")
    print("  1. The application sends SQL to the database engine.")
    print("  2. The engine parses the SQL syntax.")
    print("  3. Names are resolved against tables, columns, and schema metadata.")
    print("  4. The engine checks whether the operation is valid.")
    print("  5. The optimizer determines an efficient execution strategy.")
    print("  6. The execution engine reads or modifies database structures.")
    print("  7. The engine returns rows, affected-row information, or an error.")
    print()
    print("Important distinction:")
    print("  SQL describes what result or operation is required.")
    print("  The database engine determines how to perform it.")


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def create_connection() -> sqlite3.Connection:
    """
    Create an in-memory SQLite database.

    SQLite is a relational database management system embedded directly into
    the application process. It supports SQL, tables, keys, constraints,
    transactions, indexes, and query planning.
    """
    connection = sqlite3.connect(":memory:")

    # Returning sqlite3.Row objects makes column access clearer:
    # row["customer_id"] instead of row[0].
    connection.row_factory = sqlite3.Row

    # SQLite does not enforce foreign keys unless this setting is enabled
    # for the connection. This is an important SQLite-specific behavior.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ---------------------------------------------------------------------------
# Fundamental concepts
# ---------------------------------------------------------------------------

def demonstrate_database_fundamentals() -> None:
    print_title("1. Database fundamentals")

    print(
        """
A database is an organized collection of data managed so that applications
can store, retrieve, modify, and protect information.

A database management system (DBMS) provides mechanisms for:
  - storing data
  - querying data
  - enforcing rules
  - controlling transactions
  - handling concurrent access
  - managing indexes
  - recovering from failures
  - protecting data

A relational DBMS represents information using relations, commonly visualized
as tables. A table contains rows and columns.

Example conceptual table:

Customers
    customer_id | name          | email
    ------------+---------------+-------------------
    1           | Priya Sharma  | priya@example.com
    2           | Rahul Verma   | rahul@example.com

A row represents one record.
A column represents one attribute or field.
A primary key identifies a row.
A foreign key connects related rows between tables.
A schema describes database objects and their structure.

SQL is a declarative language. A query normally states the desired operation
or result rather than giving the database a step-by-step algorithm for how
to scan storage.
"""
    )


# ---------------------------------------------------------------------------
# Creating a relational schema
# ---------------------------------------------------------------------------

def create_schema(connection: sqlite3.Connection) -> None:
    print_title("2. Creating a relational schema")

    schema_sql = """
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        price NUMERIC NOT NULL CHECK (price >= 0),
        stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0)
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'PENDING',
        FOREIGN KEY (customer_id)
            REFERENCES customers(customer_id)
    );

    CREATE TABLE order_items (
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price NUMERIC NOT NULL CHECK (unit_price >= 0),

        PRIMARY KEY (order_id, product_id),

        FOREIGN KEY (order_id)
            REFERENCES orders(order_id)
            ON DELETE CASCADE,

        FOREIGN KEY (product_id)
            REFERENCES products(product_id)
    );
    """

    connection.executescript(schema_sql)

    print(
        """
The schema contains four related tables:

customers
    One row per customer.

products
    One row per product.

orders
    One row per order. Each order belongs to one customer.

order_items
    One row per product appearing in an order. It connects orders and
    products and therefore represents a many-to-many relationship.

The order_items primary key is composite:
    (order_id, product_id)

This prevents the same product from appearing twice in the same order.
"""
    )


# ---------------------------------------------------------------------------
# Schema inspection
# ---------------------------------------------------------------------------

def inspect_schema(connection: sqlite3.Connection) -> None:
    print_title("3. Inspecting tables and schema metadata")

    rows = execute_and_print(
        connection,
        """
        SELECT name, type
        FROM sqlite_master
        WHERE type IN ('table', 'index')
        ORDER BY type, name
        """,
    )

    print("\nObjects returned:", len(rows))

    print_subtitle("Customers table columns")

    columns = connection.execute("PRAGMA table_info(customers)").fetchall()
    print_rows(columns)

    print(
        """
The metadata reveals properties such as:
  - column position
  - column name
  - declared type
  - whether NOT NULL is required
  - default value
  - whether the column participates in a primary key

Different DBMS products expose schema metadata through different mechanisms.
For example, PostgreSQL uses information_schema and system catalogs, while
SQLite provides PRAGMA commands and sqlite_master.
"""
    )

    print_subtitle("Foreign keys in orders")

    foreign_keys = connection.execute("PRAGMA foreign_key_list(orders)").fetchall()
    print_rows(foreign_keys)


# ---------------------------------------------------------------------------
# Inserting data
# ---------------------------------------------------------------------------

def seed_data(connection: sqlite3.Connection) -> None:
    print_title("4. INSERT: adding rows")

    customers = [
        (1, "Asha Mehta", "asha@example.com"),
        (2, "Rohan Singh", "rohan@example.com"),
        (3, "Neha Kapoor", "neha@example.com"),
        (4, "Vikram Rao", "vikram@example.com"),
    ]

    products = [
        (1, "Laptop", 75000, 10),
        (2, "Mechanical Keyboard", 5500, 25),
        (3, "Monitor", 18000, 15),
        (4, "USB-C Hub", 3200, 40),
        (5, "Webcam", 4500, 20),
    ]

    connection.executemany(
        """
        INSERT INTO customers (customer_id, full_name, email)
        VALUES (?, ?, ?)
        """,
        customers,
    )

    connection.executemany(
        """
        INSERT INTO products
            (product_id, product_name, price, stock_quantity)
        VALUES (?, ?, ?, ?)
        """,
        products,
    )

    print("Customers inserted:", len(customers))
    print("Products inserted:", len(products))

    print_subtitle("Selecting inserted rows")

    execute_and_print(
        connection,
        """
        SELECT customer_id, full_name, email
        FROM customers
        ORDER BY customer_id
        """,
    )

    execute_and_print(
        connection,
        """
        SELECT product_id, product_name, price, stock_quantity
        FROM products
        ORDER BY price DESC
        """,
    )


# ---------------------------------------------------------------------------
# Basic SELECT concepts
# ---------------------------------------------------------------------------

def demonstrate_select(connection: sqlite3.Connection) -> None:
    print_title("5. SELECT: retrieving data")

    print_subtitle("Selecting specific columns")

    execute_and_print(
        connection,
        """
        SELECT full_name, email
        FROM customers
        """,
    )

    print_subtitle("Selecting all columns")

    execute_and_print(
        connection,
        """
        SELECT *
        FROM products
        """,
    )

    print(
        """
SELECT * is convenient during exploration, but explicit columns are usually
preferable in application code because they make the expected result clear
and avoid accidentally retrieving newly added columns.
"""
    )

    print_subtitle("Expressions and aliases")

    execute_and_print(
        connection,
        """
        SELECT
            product_name,
            price,
            price * 1.18 AS price_with_tax
        FROM products
        ORDER BY price
        """,
    )


# ---------------------------------------------------------------------------
# Filtering and NULL
# ---------------------------------------------------------------------------

def demonstrate_filtering(connection: sqlite3.Connection) -> None:
    print_title("6. WHERE, comparisons, logical operators, and NULL")

    print_subtitle("Equality")

    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE product_name = 'Monitor'
        """,
    )

    print_subtitle("Range filtering")

    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE price >= 5000
          AND price <= 20000
        ORDER BY price
        """,
    )

    print_subtitle("IN")

    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE product_name IN ('Laptop', 'Monitor', 'Webcam')
        """,
    )

    print_subtitle("LIKE")

    execute_and_print(
        connection,
        """
        SELECT product_name
        FROM products
        WHERE product_name LIKE '%USB%'
        """,
    )

    print(
        """
SQL uses three-valued logic for expressions involving NULL:
    TRUE
    FALSE
    UNKNOWN

NULL means an absent or unknown value. It is not equivalent to zero and is
not an empty string.

Therefore this is incorrect:
    WHERE email = NULL

The correct test is:
    WHERE email IS NULL

Likewise:
    WHERE email IS NOT NULL
"""
    )

    connection.execute(
        """
        CREATE TABLE nullable_demo (
            id INTEGER PRIMARY KEY,
            note TEXT
        )
        """
    )

    connection.executemany(
        "INSERT INTO nullable_demo (id, note) VALUES (?, ?)",
        [(1, "present"), (2, None), (3, "")],
    )

    execute_and_print(
        connection,
        """
        SELECT id, note
        FROM nullable_demo
        WHERE note IS NULL
        """,
    )


# ---------------------------------------------------------------------------
# UPDATE and DELETE
# ---------------------------------------------------------------------------

def demonstrate_update_delete(connection: sqlite3.Connection) -> None:
    print_title("7. UPDATE and DELETE")

    print_subtitle("UPDATE")

    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE product_id = ?
        """,
        (4,),
    )

    connection.execute(
        """
        UPDATE products
        SET price = price * ?
        WHERE product_id = ?
        """,
        (1.10, 4),
    )

    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE product_id = ?
        """,
        (4,),
    )

    print(
        """
A missing WHERE clause in UPDATE can modify every row.

For example:
    UPDATE products SET price = 0;

That is syntactically valid SQL but may be disastrous if it was not intended.
Always verify the WHERE condition before executing a broad modification.
"""
    )

    print_subtitle("DELETE")

    connection.execute(
        """
        INSERT INTO customers (customer_id, full_name, email)
        VALUES (?, ?, ?)
        """,
        (99, "Temporary Customer", "temporary@example.com"),
    )

    execute_and_print(
        connection,
        """
        SELECT customer_id, full_name
        FROM customers
        WHERE customer_id = 99
        """,
    )

    connection.execute(
        "DELETE FROM customers WHERE customer_id = ?",
        (99,),
    )

    execute_and_print(
        connection,
        """
        SELECT customer_id, full_name
        FROM customers
        WHERE customer_id = 99
        """,
    )


# ---------------------------------------------------------------------------
# Orders and relationships
# ---------------------------------------------------------------------------

def create_orders(connection: sqlite3.Connection) -> None:
    print_title("8. Foreign keys and relationships")

    connection.execute(
        """
        INSERT INTO orders (order_id, customer_id, status)
        VALUES (?, ?, ?)
        """,
        (1001, 1, "PAID"),
    )

    connection.execute(
        """
        INSERT INTO orders (order_id, customer_id, status)
        VALUES (?, ?, ?)
        """,
        (1002, 2, "PENDING"),
    )

    connection.executemany(
        """
        INSERT INTO order_items
            (order_id, product_id, quantity, unit_price)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1001, 1, 1, 75000),
            (1001, 2, 2, 5500),
            (1001, 4, 1, 3520),
            (1002, 3, 2, 18000),
            (1002, 5, 1, 4500),
        ],
    )

    print_subtitle("Foreign-key relationship")

    execute_and_print(
        connection,
        """
        SELECT
            orders.order_id,
            customers.full_name,
            orders.status
        FROM orders
        INNER JOIN customers
            ON orders.customer_id = customers.customer_id
        ORDER BY orders.order_id
        """,
    )

    print(
        """
The foreign key in orders.customer_id references customers.customer_id.

This creates a relationship:

customers
    1
    |
    | customer_id
    |
    many
orders

A customer may have many orders, while each order belongs to one customer.
"""
    )


# ---------------------------------------------------------------------------
# JOINs
# ---------------------------------------------------------------------------

def demonstrate_joins(connection: sqlite3.Connection) -> None:
    print_title("9. JOINs: combining related tables")

    print_subtitle("INNER JOIN")

    execute_and_print(
        connection,
        """
        SELECT
            o.order_id,
            c.full_name,
            o.status
        FROM orders AS o
        INNER JOIN customers AS c
            ON o.customer_id = c.customer_id
        ORDER BY o.order_id
        """,
    )

    print_subtitle("Joining four tables")

    execute_and_print(
        connection,
        """
        SELECT
            o.order_id,
            c.full_name,
            p.product_name,
            oi.quantity,
            oi.unit_price,
            oi.quantity * oi.unit_price AS line_total
        FROM orders AS o
        JOIN customers AS c
            ON c.customer_id = o.customer_id
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        JOIN products AS p
            ON p.product_id = oi.product_id
        ORDER BY o.order_id, p.product_name
        """,
    )

    print_subtitle("LEFT JOIN")

    execute_and_print(
        connection,
        """
        SELECT
            c.customer_id,
            c.full_name,
            o.order_id
        FROM customers AS c
        LEFT JOIN orders AS o
            ON o.customer_id = c.customer_id
        ORDER BY c.customer_id, o.order_id
        """,
    )

    print(
        """
INNER JOIN returns matching rows from both sides.

LEFT JOIN preserves every row from the left table and supplies NULL values
when there is no matching row on the right.

Other important join types include:
  - RIGHT JOIN: preserves rows from the right side in systems that support it.
  - FULL OUTER JOIN: preserves unmatched rows from both sides in systems that
    support it.
  - CROSS JOIN: produces combinations of every row from both inputs.
  - SELF JOIN: joins a table to itself.

Join support and syntax vary slightly among database products.
"""
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def demonstrate_aggregation(connection: sqlite3.Connection) -> None:
    print_title("10. Aggregate functions, GROUP BY, and HAVING")

    print_subtitle("COUNT")

    execute_and_print(
        connection,
        """
        SELECT COUNT(*) AS order_count
        FROM orders
        """,
    )

    print_subtitle("GROUP BY")

    execute_and_print(
        connection,
        """
        SELECT
            customer_id,
            COUNT(*) AS number_of_orders
        FROM orders
        GROUP BY customer_id
        ORDER BY number_of_orders DESC
        """,
    )

    print_subtitle("SUM and grouping by customer")

    execute_and_print(
        connection,
        """
        SELECT
            c.customer_id,
            c.full_name,
            SUM(oi.quantity * oi.unit_price) AS total_spending
        FROM customers AS c
        JOIN orders AS o
            ON o.customer_id = c.customer_id
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        GROUP BY c.customer_id, c.full_name
        ORDER BY total_spending DESC
        """,
    )

    print_subtitle("HAVING")

    execute_and_print(
        connection,
        """
        SELECT
            o.customer_id,
            SUM(oi.quantity * oi.unit_price) AS total_spending
        FROM orders AS o
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        GROUP BY o.customer_id
        HAVING SUM(oi.quantity * oi.unit_price) > ?
        """,
        (20000,),
    )

    print(
        """
WHERE filters rows before grouping.
HAVING filters groups after aggregation.

Common aggregate functions include:
    COUNT
    SUM
    AVG
    MIN
    MAX

The exact behavior around NULL values differs by function and must be
understood when designing analytical queries.
"""
    )


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------

def demonstrate_constraints(connection: sqlite3.Connection) -> None:
    print_title("11. Constraints: enforcing data rules")

    print(
        """
Important relational constraints include:

PRIMARY KEY
    Identifies a row uniquely.

FOREIGN KEY
    Requires a value to correspond to a referenced row, subject to the
    database's foreign-key rules.

NOT NULL
    Prevents a column from containing NULL.

UNIQUE
    Prevents duplicate values according to the database's uniqueness rules.

CHECK
    Requires a Boolean condition to be satisfied.

DEFAULT
    Supplies a value when an INSERT does not explicitly provide one.
"""
    )

    print_subtitle("NOT NULL violation")

    try:
        connection.execute(
            """
            INSERT INTO products
                (product_id, product_name, price, stock_quantity)
            VALUES (?, ?, ?, ?)
            """,
            (50, None, 100, 5),
        )
    except sqlite3.IntegrityError as error:
        print("Expected integrity error:", error)

    print_subtitle("CHECK violation")

    try:
        connection.execute(
            """
            INSERT INTO products
                (product_id, product_name, price, stock_quantity)
            VALUES (?, ?, ?, ?)
            """,
            (51, "Invalid Product", -100, 5),
        )
    except sqlite3.IntegrityError as error:
        print("Expected integrity error:", error)

    print_subtitle("Foreign-key violation")

    try:
        connection.execute(
            """
            INSERT INTO orders (order_id, customer_id, status)
            VALUES (?, ?, ?)
            """,
            (9999, 123456, "PENDING"),
        )
    except sqlite3.IntegrityError as error:
        print("Expected integrity error:", error)

    print_subtitle("UNIQUE violation")

    try:
        connection.execute(
            """
            INSERT INTO customers (customer_id, full_name, email)
            VALUES (?, ?, ?)
            """,
            (55, "Duplicate Email", "asha@example.com"),
        )
    except sqlite3.IntegrityError as error:
        print("Expected integrity error:", error)


# ---------------------------------------------------------------------------
# Composite keys
# ---------------------------------------------------------------------------

def demonstrate_composite_key(connection: sqlite3.Connection) -> None:
    print_title("12. Composite primary keys")

    print(
        """
A primary key does not always have to consist of one column.

order_items uses:
    PRIMARY KEY (order_id, product_id)

The combination identifies a line item.

This means:
    (1001, 1) is unique
    (1001, 2) is unique
    (1002, 1) would also be unique

But:
    (1001, 1) again

would violate the primary-key constraint.
"""
    )

    try:
        connection.execute(
            """
            INSERT INTO order_items
                (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """,
            (1001, 1, 3, 75000),
        )
    except sqlite3.IntegrityError as error:
        print("Expected composite-key violation:", error)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def demonstrate_transactions(connection: sqlite3.Connection) -> None:
    print_title("13. Transactions and atomic changes")

    print(
        """
A transaction groups operations into one logical unit of work.

The common ACID properties are:

Atomicity
    The transaction is treated as a unit. A failure can cause the transaction
    to be rolled back.

Consistency
    Database rules and constraints should remain satisfied after a successful
    transaction.

Isolation
    Concurrent transactions should not improperly interfere with one another.
    The exact isolation behavior depends on the DBMS.

Durability
    After a committed transaction, the DBMS provides persistence guarantees
    appropriate to its storage and configuration.
"""
    )

    print_subtitle("Successful transaction")

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO customers (customer_id, full_name, email)
                VALUES (?, ?, ?)
                """,
                (10, "Transaction Customer", "transaction@example.com"),
            )

            connection.execute(
                """
                INSERT INTO orders (order_id, customer_id, status)
                VALUES (?, ?, ?)
                """,
                (1010, 10, "PENDING"),
            )

        print("Transaction committed.")

    except sqlite3.Error as error:
        print("Transaction failed:", error)

    print_subtitle("Failed transaction")

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO customers (customer_id, full_name, email)
                VALUES (?, ?, ?)
                """,
                (11, "Rollback Customer", "rollback@example.com"),
            )

            # This violates the foreign-key constraint.
            connection.execute(
                """
                INSERT INTO orders (order_id, customer_id, status)
                VALUES (?, ?, ?)
                """,
                (1011, 987654, "PENDING"),
            )
    except sqlite3.IntegrityError as error:
        print("Transaction rolled back because:", error)

    rows = connection.execute(
        """
        SELECT customer_id, full_name
        FROM customers
        WHERE customer_id = 11
        """
    ).fetchall()

    print("Customer 11 exists after rollback:", bool(rows))


# ---------------------------------------------------------------------------
# Parameterized queries and security
# ---------------------------------------------------------------------------

def demonstrate_sql_injection_prevention(connection: sqlite3.Connection) -> None:
    print_title("14. Parameterized SQL and SQL injection")

    print(
        """
Never construct SQL by concatenating untrusted input.

Unsafe conceptual pattern:
    sql = "SELECT ... WHERE email = '" + user_input + "'"

An attacker may provide input containing SQL syntax and alter the meaning
of the statement.

The safe pattern is parameterized SQL:
    SQL template + separately bound values

The database driver treats the supplied value as data rather than allowing
it to become SQL syntax.
"""
    )

    user_supplied_email = "asha@example.com"

    execute_and_print(
        connection,
        """
        SELECT customer_id, full_name, email
        FROM customers
        WHERE email = ?
        """,
        (user_supplied_email,),
    )

    malicious_input = "' OR 1=1 --"

    print_subtitle("Malicious-looking input remains data")

    execute_and_print(
        connection,
        """
        SELECT customer_id, full_name, email
        FROM customers
        WHERE email = ?
        """,
        (malicious_input,),
    )

    print(
        """
Parameterized queries are important for security and also help prevent
quoting and escaping mistakes.

Identifiers such as table names cannot normally be passed as ordinary value
parameters. Dynamic identifiers require a carefully designed allowlist or
database-driver-specific identifier handling.
"""
    )


# ---------------------------------------------------------------------------
# Indexes and query planning
# ---------------------------------------------------------------------------

def demonstrate_indexes(connection: sqlite3.Connection) -> None:
    print_title("15. Indexes and query planning")

    print(
        """
An index is an additional data structure that helps a database find rows
without scanning every row in a table for every query.

Indexes can improve read performance but have costs:
  - additional storage
  - additional work when INSERT, UPDATE, and DELETE occur
  - maintenance overhead
  - possible memory/cache usage

Indexes should support real query patterns rather than being created on
every column automatically.
"""
    )

    connection.execute(
        """
        CREATE INDEX idx_orders_customer_id
        ON orders(customer_id)
        """
    )

    print_subtitle("Query plan")

    plan = connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT order_id, status
        FROM orders
        WHERE customer_id = 1
        """
    ).fetchall()

    print_rows(plan)

    print(
        """
EXPLAIN QUERY PLAN is SQLite-specific. Other DBMS products provide their
own query-plan commands, often with substantially more information.

A useful production workflow is:
    1. Identify a slow query.
    2. Measure it with realistic data.
    3. Inspect the execution plan.
    4. Consider indexes or query changes.
    5. Re-measure.
"""
    )


# ---------------------------------------------------------------------------
# SQL execution model
# ---------------------------------------------------------------------------

def demonstrate_execution_model(connection: sqlite3.Connection) -> None:
    print_title("16. SQL execution model")

    query = """
    SELECT
        c.full_name,
        SUM(oi.quantity * oi.unit_price) AS total_spending
    FROM customers AS c
    JOIN orders AS o
        ON o.customer_id = c.customer_id
    JOIN order_items AS oi
        ON oi.order_id = o.order_id
    WHERE o.status = ?
    GROUP BY c.customer_id, c.full_name
    HAVING SUM(oi.quantity * oi.unit_price) > ?
    ORDER BY total_spending DESC
    """

    explain_sql(query, ("PAID", 10000))

    print_subtitle("Actual query")

    execute_and_print(
        connection,
        query,
        ("PAID", 10000),
    )

    print(
        """
A simplified logical processing order for a SELECT statement is commonly
described as:

    FROM / JOIN
    WHERE
    GROUP BY
    HAVING
    SELECT
    DISTINCT
    ORDER BY
    LIMIT / OFFSET

This is a logical model, not a literal description of every physical step
performed by a database engine.

For example, SELECT aliases are generally unavailable in WHERE because the
logical WHERE phase precedes SELECT in this model.

The optimizer may physically execute operations in a different order when
that is safe and improves performance.
"""
    )


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def demonstrate_normalization() -> None:
    print_title("17. Relational design and normalization")

    print(
        """
Normalization is a family of design principles used to reduce inappropriate
duplication and dependency problems in relational databases.

Consider an unnormalized order record:

    order_id
    customer_name
    customer_email
    product_1
    product_1_price
    product_1_quantity
    product_2
    product_2_price
    product_2_quantity

This structure has several problems:
  - a fixed number of product columns
  - duplicated customer information
  - update anomalies
  - insertion anomalies
  - deletion anomalies

A more relational design separates concepts:

    customers
        customer_id
        full_name
        email

    products
        product_id
        product_name
        price

    orders
        order_id
        customer_id

    order_items
        order_id
        product_id
        quantity
        unit_price

The exact level of normalization depends on the application. Highly
normalized designs reduce duplication and improve consistency, while
carefully chosen denormalization can improve read performance in some systems.

Denormalization should be a deliberate engineering decision based on access
patterns, consistency requirements, and measured performance.
"""
    )


# ---------------------------------------------------------------------------
# Data type considerations
# ---------------------------------------------------------------------------

def demonstrate_data_types(connection: sqlite3.Connection) -> None:
    print_title("18. Data types and portability")

    print(
        """
Relational databases support typed values, but SQL type systems differ
between products.

Typical conceptual categories include:
    INTEGER
    DECIMAL / NUMERIC
    FLOAT / REAL
    CHARACTER / VARCHAR / TEXT
    DATE
    TIME
    TIMESTAMP
    BOOLEAN
    BINARY

SQLite uses dynamic typing with type affinity, which makes it flexible but
also means that behavior differs from strongly typed systems such as
PostgreSQL or many enterprise database configurations.

For financial values, fixed-precision DECIMAL/NUMERIC types are commonly
preferred over binary floating-point types when the target DBMS supports them.

Dates and timestamps also deserve deliberate design because time zones,
precision, storage format, and application conventions can affect correctness.
"""
    )

    connection.execute(
        """
        CREATE TABLE type_demo (
            id INTEGER PRIMARY KEY,
            integer_value INTEGER,
            text_value TEXT,
            numeric_value NUMERIC
        )
        """
    )

    connection.execute(
        """
        INSERT INTO type_demo
            (id, integer_value, text_value, numeric_value)
        VALUES (?, ?, ?, ?)
        """,
        (1, 42, "database", Decimal("123.45")),
    )

    execute_and_print(
        connection,
        "SELECT id, integer_value, text_value, numeric_value FROM type_demo",
    )


# ---------------------------------------------------------------------------
# Application-level validation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProductInput:
    """Application-level representation of a product to be inserted."""

    product_id: int
    product_name: str
    price: Decimal
    stock_quantity: int


def validate_product_input(product: ProductInput) -> None:
    """
    Validate input before sending it to the database.

    Database constraints remain necessary. Application validation improves
    error messages and reduces avoidable database requests, but it must not
    be considered a replacement for database constraints.
    """
    if product.product_id <= 0:
        raise ValueError("product_id must be positive")

    if not product.product_name.strip():
        raise ValueError("product_name cannot be empty")

    if product.price < 0:
        raise ValueError("price cannot be negative")

    if product.stock_quantity < 0:
        raise ValueError("stock_quantity cannot be negative")


def demonstrate_validation(connection: sqlite3.Connection) -> None:
    print_title("19. Application validation plus database constraints")

    valid_product = ProductInput(
        product_id=20,
        product_name="Desk Microphone",
        price=Decimal("8500.00"),
        stock_quantity=8,
    )

    validate_product_input(valid_product)

    connection.execute(
        """
        INSERT INTO products
            (product_id, product_name, price, stock_quantity)
        VALUES (?, ?, ?, ?)
        """,
        (
            valid_product.product_id,
            valid_product.product_name,
            valid_product.price,
            valid_product.stock_quantity,
        ),
    )

    print("Valid product inserted.")

    invalid_product = ProductInput(
        product_id=21,
        product_name="",
        price=Decimal("-1"),
        stock_quantity=-3,
    )

    try:
        validate_product_input(invalid_product)
    except ValueError as error:
        print("Application validation rejected input:", error)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def demonstrate_pagination(connection: sqlite3.Connection) -> None:
    print_title("20. ORDER BY, LIMIT, and pagination")

    execute_and_print(
        connection,
        """
        SELECT product_id, product_name, price
        FROM products
        ORDER BY price DESC, product_id ASC
        LIMIT ? OFFSET ?
        """,
        (3, 0),
    )

    execute_and_print(
        connection,
        """
        SELECT product_id, product_name, price
        FROM products
        ORDER BY price DESC, product_id ASC
        LIMIT ? OFFSET ?
        """,
        (3, 3),
    )

    print(
        """
Pagination should use deterministic ordering. Adding a unique tie-breaker
such as product_id helps prevent unstable ordering when multiple rows have
the same sort value.

LIMIT/OFFSET pagination is simple but can become inefficient for very large
offsets. Some systems and workloads benefit from keyset (cursor-based)
pagination, such as:

    WHERE product_id > last_seen_id
    ORDER BY product_id
    LIMIT page_size
"""
    )


# ---------------------------------------------------------------------------
# Subqueries
# ---------------------------------------------------------------------------

def demonstrate_subqueries(connection: sqlite3.Connection) -> None:
    print_title("21. Subqueries")

    print_subtitle("Scalar subquery")

    execute_and_print(
        connection,
        """
        SELECT
            product_name,
            price,
            (
                SELECT AVG(price)
                FROM products
            ) AS average_price
        FROM products
        ORDER BY price DESC
        """,
    )

    print_subtitle("EXISTS")

    execute_and_print(
        connection,
        """
        SELECT c.customer_id, c.full_name
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
        )
        ORDER BY c.customer_id
        """,
    )

    print(
        """
EXISTS asks whether a matching row exists. It is often useful when the query
cares about existence rather than retrieving matching child rows.

The optimizer may transform logically equivalent queries, so performance
should be measured rather than inferred only from surface syntax.
"""
    )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def demonstrate_view(connection: sqlite3.Connection) -> None:
    print_title("22. Views")

    connection.execute(
        """
        CREATE VIEW customer_order_totals AS
        SELECT
            c.customer_id,
            c.full_name,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_spending
        FROM customers AS c
        LEFT JOIN orders AS o
            ON o.customer_id = c.customer_id
        LEFT JOIN order_items AS oi
            ON oi.order_id = o.order_id
        GROUP BY c.customer_id, c.full_name
        """
    )

    execute_and_print(
        connection,
        """
        SELECT *
        FROM customer_order_totals
        ORDER BY total_spending DESC
        """,
    )

    print(
        """
A view is a named query that can provide a reusable logical interface over
underlying tables.

Views can improve organization and expose only selected information, but
their behavior, updateability, and performance characteristics depend on
the DBMS and query definition.
"""
    )


# ---------------------------------------------------------------------------
# Realistic order operation
# ---------------------------------------------------------------------------

def place_order(
    connection: sqlite3.Connection,
    order_id: int,
    customer_id: int,
    requested_items: Iterable[tuple[int, int]],
) -> None:
    """
    Place an order atomically.

    requested_items contains:
        (product_id, quantity)

    The function:
      1. validates the request
      2. verifies customer existence
      3. verifies products and stock
      4. creates the order
      5. creates order items using the current product price
      6. decreases stock
      7. commits all changes together

    If any step fails, the transaction is rolled back.
    """
    items = list(requested_items)

    if not items:
        raise ValueError("An order must contain at least one product.")

    if order_id <= 0:
        raise ValueError("order_id must be positive.")

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    if any(product_id <= 0 or quantity <= 0 for product_id, quantity in items):
        raise ValueError("Product IDs and quantities must be positive.")

    with connection:
        customer = connection.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()

        if customer is None:
            raise ValueError("Customer does not exist.")

        # Consolidating duplicate product IDs makes the operation explicit.
        quantities: dict[int, int] = {}
        for product_id, quantity in items:
            quantities[product_id] = quantities.get(product_id, 0) + quantity

        product_rows: dict[int, sqlite3.Row] = {}

        for product_id in quantities:
            product = connection.execute(
                """
                SELECT product_id, product_name, price, stock_quantity
                FROM products
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchone()

            if product is None:
                raise ValueError(f"Product {product_id} does not exist.")

            if product["stock_quantity"] < quantities[product_id]:
                raise ValueError(
                    f"Insufficient stock for {product['product_name']}."
                )

            product_rows[product_id] = product

        connection.execute(
            """
            INSERT INTO orders (order_id, customer_id, status)
            VALUES (?, ?, ?)
            """,
            (order_id, customer_id, "PAID"),
        )

        for product_id, quantity in quantities.items():
            product = product_rows[product_id]

            connection.execute(
                """
                INSERT INTO order_items
                    (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    product_id,
                    quantity,
                    product["price"],
                ),
            )

            connection.execute(
                """
                UPDATE products
                SET stock_quantity = stock_quantity - ?
                WHERE product_id = ?
                """,
                (quantity, product_id),
            )


def demonstrate_realistic_operation(connection: sqlite3.Connection) -> None:
    print_title("23. Complete transactional operation")

    print_subtitle("Successful order")

    place_order(
        connection,
        order_id=2001,
        customer_id=3,
        requested_items=[
            (2, 1),
            (5, 2),
        ],
    )

    execute_and_print(
        connection,
        """
        SELECT
            o.order_id,
            c.full_name,
            p.product_name,
            oi.quantity,
            oi.unit_price,
            oi.quantity * oi.unit_price AS line_total
        FROM orders AS o
        JOIN customers AS c
            ON c.customer_id = o.customer_id
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        JOIN products AS p
            ON p.product_id = oi.product_id
        WHERE o.order_id = ?
        """,
        (2001,),
    )

    print_subtitle("Insufficient-stock failure")

    before_stock = connection.execute(
        """
        SELECT stock_quantity
        FROM products
        WHERE product_id = ?
        """,
        (1,),
    ).fetchone()["stock_quantity"]

    try:
        place_order(
            connection,
            order_id=2002,
            customer_id=3,
            requested_items=[
                (1, before_stock + 1000),
            ],
        )
    except ValueError as error:
        print("Order rejected:", error)

    after_order_exists = connection.execute(
        """
        SELECT order_id
        FROM orders
        WHERE order_id = ?
        """,
        (2002,),
    ).fetchone()

    after_stock = connection.execute(
        """
        SELECT stock_quantity
        FROM products
        WHERE product_id = ?
        """,
        (1,),
    ).fetchone()["stock_quantity"]

    print("Failed order exists:", bool(after_order_exists))
    print("Stock unchanged:", before_stock == after_stock)


# ---------------------------------------------------------------------------
# Database normalization example
# ---------------------------------------------------------------------------

def demonstrate_relationship_cardinality() -> None:
    print_title("24. Relationship cardinality")

    print(
        """
One-to-one
    One row in table A corresponds to at most one row in table B, and vice
    versa. A UNIQUE foreign key is commonly used to enforce this.

One-to-many
    One parent row can have many child rows.
    Example:
        customer -> orders

Many-to-many
    Rows on both sides can have multiple relationships.
    Example:
        orders <-> products

A many-to-many relationship is normally represented by an associative,
junction, or bridge table:
        order_items

This table stores the relationship plus attributes of that relationship,
such as quantity and unit_price.
"""
    )


# ---------------------------------------------------------------------------
# Common mistakes
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    print_title("25. Common SQL mistakes")

    mistakes = [
        (
            "Confusing a database with a table",
            "A database contains objects such as tables; a table stores rows.",
        ),
        (
            "Assuming row order is guaranteed",
            "Without ORDER BY, SQL does not promise a meaningful row order.",
        ),
        (
            "Using = NULL",
            "Use IS NULL or IS NOT NULL.",
        ),
        (
            "Updating without WHERE",
            "UPDATE can modify every row if no filter is supplied.",
        ),
        (
            "Deleting without WHERE",
            "DELETE can remove every row if no filter is supplied.",
        ),
        (
            "Skipping foreign keys",
            "Relationships can become invalid when referential integrity is not enforced.",
        ),
        (
            "Using string concatenation for SQL values",
            "Use parameterized queries to reduce injection risk and quoting errors.",
        ),
        (
            "Assuming SQL dialects are identical",
            "PostgreSQL, MySQL, SQL Server, Oracle, SQLite, and others differ in syntax and behavior.",
        ),
        (
            "Adding indexes to every column",
            "Indexes have storage and write-maintenance costs.",
        ),
        (
            "Putting all data in one huge table",
            "This often creates duplication, anomalies, and difficult maintenance.",
        ),
    ]

    for mistake, correction in mistakes:
        print(f"\nMistake: {mistake}")
        print(f"Correction: {correction}")


# ---------------------------------------------------------------------------
# Testing database behavior
# ---------------------------------------------------------------------------

def run_tests(connection: sqlite3.Connection) -> None:
    print_title("26. Executable tests")

    def assert_equal(actual: object, expected: object, description: str) -> None:
        if actual != expected:
            raise AssertionError(
                f"{description}: expected {expected!r}, got {actual!r}"
            )
        print(f"PASS: {description}")

    customer_count = connection.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    assert_equal(
        customer_count >= 5,
        True,
        "customers table contains the seeded and transactional customers",
    )

    product_count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    assert_equal(
        product_count >= 6,
        True,
        "products table contains seeded and added products",
    )

    order_customer = connection.execute(
        """
        SELECT customer_id
        FROM orders
        WHERE order_id = ?
        """,
        (2001,),
    ).fetchone()[0]

    assert_equal(
        order_customer,
        3,
        "order 2001 belongs to customer 3",
    )

    duplicate_failed = False

    try:
        connection.execute(
            """
            INSERT INTO customers (customer_id, full_name, email)
            VALUES (?, ?, ?)
            """,
            (500, "Duplicate", "asha@example.com"),
        )
    except sqlite3.IntegrityError:
        duplicate_failed = True

    assert_equal(
        duplicate_failed,
        True,
        "UNIQUE email constraint rejects duplicate email",
    )

    null_comparison_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM nullable_demo
        WHERE note = NULL
        """
    ).fetchone()[0]

    assert_equal(
        null_comparison_count,
        0,
        "NULL is not matched using the equality operator",
    )


# ---------------------------------------------------------------------------
# Cleanup demonstration
# ---------------------------------------------------------------------------

def demonstrate_delete_cascade(connection: sqlite3.Connection) -> None:
    print_title("27. Referential actions and ON DELETE CASCADE")

    print(
        """
orders references customers.

order_items references orders with:
    ON DELETE CASCADE

Therefore, deleting an order causes its order_items rows to be deleted
automatically.

This behavior must be designed carefully. Cascades can be useful for
dependent records, but an unexpected cascade can remove more data than
intended.
"""
    )

    item_count_before = connection.execute(
        """
        SELECT COUNT(*)
        FROM order_items
        WHERE order_id = ?
        """,
        (2001,),
    ).fetchone()[0]

    print("Items before order deletion:", item_count_before)

    connection.execute(
        "DELETE FROM orders WHERE order_id = ?",
        (2001,),
    )

    item_count_after = connection.execute(
        """
        SELECT COUNT(*)
        FROM order_items
        WHERE order_id = ?
        """,
        (2001,),
    ).fetchone()[0]

    print("Items after order deletion:", item_count_after)


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> None:
    print_title("SQL Introduction: complete executable study")

    demonstrate_database_fundamentals()

    connection = create_connection()

    try:
        create_schema(connection)
        inspect_schema(connection)
        seed_data(connection)
        demonstrate_select(connection)
        demonstrate_filtering(connection)
        demonstrate_update_delete(connection)
        create_orders(connection)
        demonstrate_joins(connection)
        demonstrate_aggregation(connection)
        demonstrate_constraints(connection)
        demonstrate_composite_key(connection)
        demonstrate_transactions(connection)
        demonstrate_sql_injection_prevention(connection)
        demonstrate_indexes(connection)
        demonstrate_execution_model(connection)
        demonstrate_normalization()
        demonstrate_data_types(connection)
        demonstrate_validation(connection)
        demonstrate_pagination(connection)
        demonstrate_subqueries(connection)
        demonstrate_view(connection)
        demonstrate_realistic_operation(connection)
        demonstrate_relationship_cardinality()
        demonstrate_common_mistakes()
        run_tests(connection)
        demonstrate_delete_cascade(connection)

        print_title("28. Final database state")

        execute_and_print(
            connection,
            """
            SELECT
                c.full_name,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS spending
            FROM customers AS c
            LEFT JOIN orders AS o
                ON o.customer_id = c.customer_id
            LEFT JOIN order_items AS oi
                ON oi.order_id = o.order_id
            GROUP BY c.customer_id, c.full_name
            ORDER BY spending DESC
            """,
        )

        print(
            """
The executable study has demonstrated the central SQL introduction concepts:
databases, relational tables, rows, columns, keys, constraints, schemas,
queries, relationships, joins, aggregation, transactions, security,
indexes, execution planning, normalization, and application integration.
"""
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
