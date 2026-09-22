"""
SQL SELECT: SELECT, FROM, aliases, DISTINCT, expressions, and calculated columns

A standalone educational program that teaches the SELECT statement from
beginner to advanced practical usage.

The examples use Python's standard-library sqlite3 module, so no external
package is required. SQLite supports the SQL SELECT features demonstrated
here and provides an executable environment for experimentation.

The program progresses through:
1. Database creation and sample data
2. SELECT and FROM
3. Selecting individual and multiple columns
4. Column aliases
5. DISTINCT
6. Expressions
7. Calculated columns
8. NULL behavior
9. Type conversion and arithmetic
10. String expressions
11. Date/time expressions
12. CASE expressions
13. Aggregate expressions
14. SELECT behavior and evaluation concepts
15. Practical reporting examples
16. Edge cases and common mistakes
17. Validation and automated tests
18. A mini reporting case study
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DATABASE = ":memory:"


def create_connection() -> sqlite3.Connection:
    """Create an in-memory SQLite database with useful row access."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """
    Create a small sales database.

    The schema intentionally contains numeric, text, date-like, and NULL
    values so SELECT expressions can be demonstrated realistically.
    """
    connection.executescript(
        """
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY,
            department_name TEXT NOT NULL
        );

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department_id INTEGER,
            job_title TEXT NOT NULL,
            salary REAL,
            city TEXT,
            hire_date TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (department_id)
                REFERENCES departments(department_id)
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL,
            cost_price REAL NOT NULL,
            stock_quantity INTEGER,
            supplier TEXT
        );

        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            employee_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount_rate REAL NOT NULL DEFAULT 0,
            sale_date TEXT NOT NULL,
            region TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );
        """
    )


def insert_sample_data(connection: sqlite3.Connection) -> None:
    """Populate the database with deliberately varied educational data."""
    connection.executemany(
        """
        INSERT INTO departments (department_id, department_name)
        VALUES (?, ?)
        """,
        [
            (1, "Technology"),
            (2, "Finance"),
            (3, "Operations"),
            (4, "Human Resources"),
        ],
    )

    connection.executemany(
        """
        INSERT INTO employees (
            employee_id, first_name, last_name, department_id,
            job_title, salary, city, hire_date, active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "Aarav", "Sharma", 1, "Software Engineer", 85000, "Lucknow", "2022-04-10", 1),
            (2, "Meera", "Singh", 1, "Data Analyst", 72000, "Delhi", "2023-01-15", 1),
            (3, "Rohan", "Verma", 2, "Financial Analyst", 78000, "Mumbai", "2021-08-20", 1),
            (4, "Isha", "Patel", 3, "Operations Manager", 92000, "Pune", "2020-02-12", 1),
            (5, "Kabir", "Khan", 3, "Operations Analyst", 65000, "Lucknow", "2024-03-05", 1),
            (6, "Nisha", "Gupta", 4, "HR Specialist", None, "Delhi", "2023-09-18", 1),
            (7, "Dev", "Joshi", 1, "Software Engineer", 88000, "Bengaluru", "2019-11-01", 0),
        ],
    )

    connection.executemany(
        """
        INSERT INTO products (
            product_id, product_name, category,
            unit_price, cost_price, stock_quantity, supplier
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "Laptop Pro 14", "Computers", 1200.00, 850.00, 25, "TechSource"),
            (2, "Mechanical Keyboard", "Accessories", 95.00, 55.00, 80, "KeyWorks"),
            (3, "Wireless Mouse", "Accessories", 45.00, 20.00, 150, "KeyWorks"),
            (4, "4K Monitor", "Displays", 450.00, 310.00, 40, "VisionTech"),
            (5, "USB-C Hub", "Accessories", 65.00, 32.00, 0, "PortWorks"),
            (6, "Server Rack", "Infrastructure", 900.00, 690.00, 10, None),
        ],
    )

    connection.executemany(
        """
        INSERT INTO sales (
            sale_id, product_id, employee_id, quantity,
            unit_price, discount_rate, sale_date, region
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 1, 1, 2, 1200.00, 0.10, "2026-01-05", "North"),
            (2, 2, 2, 5, 95.00, 0.05, "2026-01-06", "North"),
            (3, 3, 3, 10, 45.00, 0.00, "2026-01-07", "West"),
            (4, 4, 4, 3, 450.00, 0.08, "2026-01-09", "West"),
            (5, 5, 5, 7, 65.00, 0.15, "2026-01-12", "North"),
            (6, 1, 2, 1, 1200.00, 0.00, "2026-01-15", "South"),
            (7, 6, 4, 2, 900.00, 0.05, "2026-02-01", "West"),
            (8, 3, 1, 20, 45.00, 0.10, "2026-02-03", "North"),
        ],
    )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def print_title(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_rows(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Sequence[object] = (),
    limit: int | None = None,
) -> list[sqlite3.Row]:
    """Execute SQL and display a compact tabular result."""
    cursor = connection.execute(sql, parameters)
    rows = cursor.fetchall()

    if limit is not None:
        rows = rows[:limit]

    if not rows:
        print("(no rows)")
        return rows

    columns = rows[0].keys()
    widths = {column: len(column) for column in columns}

    for row in rows:
        for column in columns:
            value = row[column]
            widths[column] = max(widths[column], len(str(value)))

    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in rows:
        print(
            " | ".join(
                str(row[column]).ljust(widths[column])
                for column in columns
            )
        )

    print(f"\nRows: {len(rows)}")
    return rows


def run_query(
    connection: sqlite3.Connection,
    description: str,
    sql: str,
    parameters: Sequence[object] = (),
) -> list[sqlite3.Row]:
    print_title(description)
    print("SQL:")
    print(sql.strip())
    if parameters:
        print(f"Parameters: {parameters}")
    print("\nResult:")
    return print_rows(connection, sql, parameters)


# ---------------------------------------------------------------------------
# 1. SELECT and FROM fundamentals
# ---------------------------------------------------------------------------

def demonstrate_select_and_from(connection: sqlite3.Connection) -> None:
    """
    SELECT chooses what values/columns the query returns.

    FROM identifies the table or other data source from which rows originate.

    Basic shape:
        SELECT column1, column2
        FROM table_name;
    """
    run_query(
        connection,
        "1. Selecting all columns with SELECT *",
        """
        SELECT *
        FROM employees;
        """,
    )

    run_query(
        connection,
        "2. Selecting one column",
        """
        SELECT first_name
        FROM employees;
        """,
    )

    run_query(
        connection,
        "3. Selecting multiple columns",
        """
        SELECT first_name, last_name, job_title
        FROM employees;
        """,
    )

    # Explicit columns are generally preferable to SELECT * in production
    # because they make the result contract clear and avoid accidentally
    # returning newly added columns.
    run_query(
        connection,
        "4. Explicit column selection",
        """
        SELECT employee_id, first_name, salary
        FROM employees;
        """,
    )


# ---------------------------------------------------------------------------
# 2. Column aliases
# ---------------------------------------------------------------------------

def demonstrate_aliases(connection: sqlite3.Connection) -> None:
    """
    An alias changes the name displayed for an output column.

    AS is explicit and readable:
        SELECT salary AS annual_salary

    SQLite also permits:
        SELECT salary annual_salary

    AS is recommended because it makes the intent obvious.
    """
    run_query(
        connection,
        "5. Column aliases",
        """
        SELECT
            first_name AS employee_first_name,
            last_name AS employee_last_name,
            salary AS annual_salary
        FROM employees;
        """,
    )

    run_query(
        connection,
        "6. Aliases with spaces",
        """
        SELECT
            first_name || ' ' || last_name AS "Employee Name",
            job_title AS "Job Title"
        FROM employees;
        """,
    )

    run_query(
        connection,
        "7. Alias for a calculated expression",
        """
        SELECT
            product_name,
            unit_price,
            unit_price * 1.18 AS price_with_tax
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 3. DISTINCT
# ---------------------------------------------------------------------------

def demonstrate_distinct(connection: sqlite3.Connection) -> None:
    """
    DISTINCT removes duplicate result rows.

    DISTINCT applies to the complete selected row, not just one arbitrary
    column. Therefore:

        SELECT DISTINCT city FROM employees

    removes duplicate cities.

    But:

        SELECT DISTINCT city, job_title FROM employees

    removes duplicates of the pair (city, job_title).
    """
    run_query(
        connection,
        "8. Duplicate values without DISTINCT",
        """
        SELECT city
        FROM employees;
        """,
    )

    run_query(
        connection,
        "9. Unique cities with DISTINCT",
        """
        SELECT DISTINCT city
        FROM employees;
        """,
    )

    run_query(
        connection,
        "10. DISTINCT applies to combinations of selected expressions",
        """
        SELECT DISTINCT city, job_title
        FROM employees;
        """,
    )

    run_query(
        connection,
        "11. DISTINCT categories",
        """
        SELECT DISTINCT category
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 4. Expressions and calculated columns
# ---------------------------------------------------------------------------

def demonstrate_expressions(connection: sqlite3.Connection) -> None:
    """
    An expression produces a value.

    Common operators:
        +   addition
        -   subtraction
        *   multiplication
        /   division
        %   remainder

    SQL expressions can combine columns, constants, functions, and operators.
    """
    run_query(
        connection,
        "12. Numeric expression",
        """
        SELECT
            product_name,
            unit_price,
            unit_price * 1.18 AS price_with_18_percent_tax
        FROM products;
        """,
    )

    run_query(
        connection,
        "13. Multiple calculated columns",
        """
        SELECT
            product_name,
            unit_price,
            cost_price,
            unit_price - cost_price AS gross_margin,
            (unit_price - cost_price) / unit_price AS margin_ratio
        FROM products;
        """,
    )

    run_query(
        connection,
        "14. Sales revenue calculation",
        """
        SELECT
            sale_id,
            quantity,
            unit_price,
            quantity * unit_price AS gross_revenue
        FROM sales;
        """,
    )

    run_query(
        connection,
        "15. Discount calculation",
        """
        SELECT
            sale_id,
            quantity * unit_price AS gross_revenue,
            discount_rate,
            quantity * unit_price * discount_rate AS discount_amount,
            quantity * unit_price * (1 - discount_rate) AS net_revenue
        FROM sales;
        """,
    )


# ---------------------------------------------------------------------------
# 5. String expressions
# ---------------------------------------------------------------------------

def demonstrate_string_expressions(connection: sqlite3.Connection) -> None:
    """Demonstrate concatenation and built-in text functions."""
    run_query(
        connection,
        "16. Combining first and last names",
        """
        SELECT
            first_name || ' ' || last_name AS full_name
        FROM employees;
        """,
    )

    run_query(
        connection,
        "17. Text transformations",
        """
        SELECT
            product_name,
            UPPER(product_name) AS uppercase_name,
            LOWER(category) AS lowercase_category,
            LENGTH(product_name) AS name_length
        FROM products;
        """,
    )

    run_query(
        connection,
        "18. Constructing a descriptive label",
        """
        SELECT
            product_name || ' - ' || category AS product_label
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 6. NULL behavior
# ---------------------------------------------------------------------------

def demonstrate_null_behavior(connection: sqlite3.Connection) -> None:
    """
    NULL represents missing/unknown data.

    NULL is not the same as zero, an empty string, or false.

    Arithmetic involving NULL generally produces NULL.
    SQLite's COALESCE function can replace NULL with a chosen value.
    """
    run_query(
        connection,
        "19. NULL values in a selected column",
        """
        SELECT
            first_name,
            salary
        FROM employees;
        """,
    )

    run_query(
        connection,
        "20. Calculating with NULL",
        """
        SELECT
            first_name,
            salary,
            salary * 1.10 AS salary_after_raise
        FROM employees;
        """,
    )

    run_query(
        connection,
        "21. Replacing NULL with COALESCE",
        """
        SELECT
            first_name,
            COALESCE(salary, 0) AS salary_or_zero
        FROM employees;
        """,
    )

    run_query(
        connection,
        "22. Handling a nullable supplier",
        """
        SELECT
            product_name,
            COALESCE(supplier, 'Supplier not recorded') AS supplier_name
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 7. Type conversion and numeric precision
# ---------------------------------------------------------------------------

def demonstrate_types(connection: sqlite3.Connection) -> None:
    """
    SQL engines differ in their type systems.

    SQLite uses dynamic typing, so explicit CAST can still be useful when
    communicating intent or controlling the type of an expression.
    """
    run_query(
        connection,
        "23. CAST expression",
        """
        SELECT
            quantity,
            CAST(quantity AS REAL) AS quantity_as_real
        FROM sales;
        """,
    )

    run_query(
        connection,
        "24. Rounded calculated value",
        """
        SELECT
            sale_id,
            ROUND(quantity * unit_price * (1 - discount_rate), 2)
                AS rounded_net_revenue
        FROM sales;
        """,
    )

    run_query(
        connection,
        "25. Integer versus real arithmetic",
        """
        SELECT
            5 / 2 AS integer_division_behavior,
            5.0 / 2 AS real_division_behavior;
        """,
    )


# ---------------------------------------------------------------------------
# 8. Date/time expressions
# ---------------------------------------------------------------------------

def demonstrate_date_expressions(connection: sqlite3.Connection) -> None:
    """
    SQLite commonly stores dates as TEXT in ISO-8601 format.

    SQLite provides date/time functions that can transform or calculate
    date-related values.
    """
    run_query(
        connection,
        "26. Extracting date components",
        """
        SELECT
            sale_date,
            strftime('%Y', sale_date) AS sale_year,
            strftime('%m', sale_date) AS sale_month
        FROM sales;
        """,
    )

    run_query(
        connection,
        "27. Date arithmetic",
        """
        SELECT
            sale_date,
            date(sale_date, '+30 days') AS thirty_days_later
        FROM sales;
        """,
    )


# ---------------------------------------------------------------------------
# 9. CASE expressions
# ---------------------------------------------------------------------------

def demonstrate_case(connection: sqlite3.Connection) -> None:
    """
    CASE creates conditional expressions.

    It is useful for classifications and business-friendly calculated
    columns without modifying the stored data.
    """
    run_query(
        connection,
        "28. Salary classification",
        """
        SELECT
            first_name,
            salary,
            CASE
                WHEN salary IS NULL THEN 'Unknown'
                WHEN salary >= 90000 THEN 'High'
                WHEN salary >= 70000 THEN 'Medium'
                ELSE 'Standard'
            END AS salary_band
        FROM employees;
        """,
    )

    run_query(
        connection,
        "29. Inventory status",
        """
        SELECT
            product_name,
            stock_quantity,
            CASE
                WHEN stock_quantity IS NULL THEN 'Unknown'
                WHEN stock_quantity = 0 THEN 'Out of stock'
                WHEN stock_quantity < 20 THEN 'Low stock'
                ELSE 'Available'
            END AS inventory_status
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 10. Aggregate expressions
# ---------------------------------------------------------------------------

def demonstrate_aggregates(connection: sqlite3.Connection) -> None:
    """
    Aggregate functions reduce multiple rows into summary values.

    Common aggregates:
        COUNT
        SUM
        AVG
        MIN
        MAX

    Although aggregate queries become especially useful with GROUP BY,
    simple aggregate SELECT statements are valuable fundamentals.
    """
    run_query(
        connection,
        "30. Counting rows",
        """
        SELECT COUNT(*) AS employee_count
        FROM employees;
        """,
    )

    run_query(
        connection,
        "31. Multiple aggregate expressions",
        """
        SELECT
            COUNT(*) AS product_count,
            MIN(unit_price) AS minimum_price,
            MAX(unit_price) AS maximum_price,
            AVG(unit_price) AS average_price
        FROM products;
        """,
    )

    run_query(
        connection,
        "32. Total sales quantity and revenue",
        """
        SELECT
            SUM(quantity) AS total_units,
            ROUND(SUM(quantity * unit_price), 2) AS gross_revenue
        FROM sales;
        """ ,
    )


# ---------------------------------------------------------------------------
# 11. SELECT with subqueries
# ---------------------------------------------------------------------------

def demonstrate_subqueries(connection: sqlite3.Connection) -> None:
    """
    A SELECT can contain another SELECT.

    Scalar subqueries can produce a single value that participates in an
    expression for every output row.
    """
    run_query(
        connection,
        "33. Scalar subquery inside SELECT",
        """
        SELECT
            product_name,
            unit_price,
            ROUND(
                unit_price - (SELECT AVG(unit_price) FROM products),
                2
            ) AS difference_from_average
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 12. Practical sales report
# ---------------------------------------------------------------------------

def demonstrate_sales_report(connection: sqlite3.Connection) -> None:
    """
    A realistic report combines columns, aliases, expressions, CASE,
    COALESCE, string concatenation, and date functions.
    """
    run_query(
        connection,
        "34. Complete sales reporting query",
        """
        SELECT
            s.sale_id AS transaction_id,
            p.product_name AS product,
            p.category AS category,
            COALESCE(e.first_name || ' ' || e.last_name, 'Unassigned')
                AS salesperson,
            s.quantity AS units,
            ROUND(s.quantity * s.unit_price, 2) AS gross_revenue,
            ROUND(s.quantity * s.unit_price * s.discount_rate, 2)
                AS discount_amount,
            ROUND(
                s.quantity * s.unit_price * (1 - s.discount_rate),
                2
            ) AS net_revenue,
            CASE
                WHEN s.discount_rate = 0 THEN 'No discount'
                WHEN s.discount_rate <= 0.10 THEN 'Standard discount'
                ELSE 'High discount'
            END AS discount_class,
            s.region AS region,
            s.sale_date AS sale_date
        FROM sales AS s
        JOIN products AS p
            ON p.product_id = s.product_id
        LEFT JOIN employees AS e
            ON e.employee_id = s.employee_id;
        """,
    )


# ---------------------------------------------------------------------------
# 13. SELECT expressions and alias limitations
# ---------------------------------------------------------------------------

def demonstrate_alias_rules(connection: sqlite3.Connection) -> None:
    """
    A SELECT-list alias is primarily an output name.

    Some SQL clauses can reference aliases depending on the database engine,
    but relying on aliases everywhere is unsafe. SQLite permits certain
    convenient usages that are not universally portable.

    The following query demonstrates an alias safely inside the output.
    """
    run_query(
        connection,
        "35. Reusing a calculation by repeating the expression",
        """
        SELECT
            product_name,
            unit_price * 1.18 AS price_with_tax,
            (unit_price * 1.18) - cost_price AS estimated_margin_after_tax
        FROM products;
        """,
    )

    run_query(
        connection,
        "36. A subquery can make a calculated result reusable",
        """
        SELECT
            product_name,
            price_with_tax,
            ROUND(price_with_tax - cost_price, 2) AS margin_after_tax
        FROM (
            SELECT
                product_name,
                cost_price,
                unit_price * 1.18 AS price_with_tax
            FROM products
        );
        """,
    )


# ---------------------------------------------------------------------------
# 14. Important SELECT edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases(connection: sqlite3.Connection) -> None:
    """Demonstrate common boundary conditions."""
    run_query(
        connection,
        "37. Literal values in SELECT",
        """
        SELECT
            42 AS answer,
            'SQL' AS technology,
            3.14159 AS approximate_pi;
        """,
    )

    run_query(
        connection,
        "38. Constant expression without a table",
        """
        SELECT
            10 + 20 AS result,
            100 * 0.18 AS tax_amount;
        """,
    )

    run_query(
        connection,
        "39. NULL expression",
        """
        SELECT
            NULL AS missing_value,
            NULL + 10 AS arithmetic_with_null,
            COALESCE(NULL, 10) AS recovered_value;
        """,
    )

    run_query(
        connection,
        "40. DISTINCT and NULL",
        """
        SELECT DISTINCT supplier
        FROM products;
        """,
    )


# ---------------------------------------------------------------------------
# 15. Automated validation
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    details: str


def run_tests(connection: sqlite3.Connection) -> list[TestResult]:
    """Test key SELECT concepts with executable assertions."""
    results: list[TestResult] = []

    def check(name: str, actual: object, expected: object) -> None:
        passed = actual == expected
        results.append(
            TestResult(
                name=name,
                passed=passed,
                details=f"expected={expected!r}, actual={actual!r}",
            )
        )

    rows = connection.execute(
        """
        SELECT first_name
        FROM employees
        ORDER BY employee_id;
        """
    ).fetchall()
    check("SELECT returns expected first employee", rows[0]["first_name"], "Aarav")

    rows = connection.execute(
        """
        SELECT DISTINCT city
        FROM employees;
        """
    ).fetchall()
    cities = {row["city"] for row in rows}
    check(
        "DISTINCT returns the expected city set",
        cities,
        {"Lucknow", "Delhi", "Mumbai", "Pune", "Bengaluru"},
    )

    row = connection.execute(
        """
        SELECT
            quantity * unit_price AS gross_revenue
        FROM sales
        WHERE sale_id = 1;
        """
    ).fetchone()
    check("Calculated revenue", row["gross_revenue"], 2400.0)

    row = connection.execute(
        """
        SELECT
            COALESCE(salary, 0) AS normalized_salary
        FROM employees
        WHERE employee_id = 6;
        """
    ).fetchone()
    check("COALESCE handles NULL", row["normalized_salary"], 0)

    row = connection.execute(
        """
        SELECT
            CASE
                WHEN stock_quantity = 0 THEN 'Out of stock'
                ELSE 'Available'
            END AS status
        FROM products
        WHERE product_id = 5;
        """
    ).fetchone()
    check("CASE classifies zero inventory", row["status"], "Out of stock")

    return results


def display_tests(results: Iterable[TestResult]) -> None:
    print_title("41. Automated SELECT tests")

    passed_count = 0

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name} ({result.details})")
        if result.passed:
            passed_count += 1

    print(f"\nPassed: {passed_count}/{len(results)}")

    if passed_count != len(results):
        raise AssertionError("At least one SQL SELECT test failed.")


# ---------------------------------------------------------------------------
# 16. SQL injection demonstration and safe parameterization
# ---------------------------------------------------------------------------

def demonstrate_safe_parameters(connection: sqlite3.Connection) -> None:
    """
    Values should be passed as parameters rather than concatenated into SQL.

    This is especially important when a SELECT query receives user input.
    Parameterization separates SQL structure from data values.
    """
    city = "Lucknow"

    run_query(
        connection,
        "42. Safe parameterized SELECT",
        """
        SELECT
            employee_id,
            first_name,
            last_name,
            city
        FROM employees
        WHERE city = ?;
        """,
        (city,),
    )


# ---------------------------------------------------------------------------
# 17. Performance considerations
# ---------------------------------------------------------------------------

def demonstrate_query_plan(connection: sqlite3.Connection) -> None:
    """
    SELECT performance depends on table size, selected expressions, indexes,
    joins, filtering, sorting, and database engine behavior.

    EXPLAIN QUERY PLAN is SQLite-specific but useful for observing access
    strategies.
    """
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_employees_city
        ON employees(city);
        """
    )

    run_query(
        connection,
        "43. Inspecting a SELECT query plan",
        """
        EXPLAIN QUERY PLAN
        SELECT employee_id, first_name
        FROM employees
        WHERE city = 'Lucknow';
        """,
    )


# ---------------------------------------------------------------------------
# 18. Complete case-study report
# ---------------------------------------------------------------------------

def build_executive_report(connection: sqlite3.Connection) -> None:
    """
    This report shows how the basic SELECT features combine into an
    application-level analytical output.
    """
    run_query(
        connection,
        "44. Executive product report",
        """
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.unit_price,
            p.cost_price,
            ROUND(p.unit_price - p.cost_price, 2) AS unit_margin,
            ROUND(
                (p.unit_price - p.cost_price) * 100.0 / p.unit_price,
                2
            ) AS margin_percentage,
            COALESCE(p.stock_quantity, 0) AS stock_units,
            CASE
                WHEN COALESCE(p.stock_quantity, 0) = 0 THEN 'OUT'
                WHEN p.stock_quantity < 20 THEN 'LOW'
                ELSE 'HEALTHY'
            END AS stock_status,
            CASE
                WHEN p.supplier IS NULL THEN 'Unknown supplier'
                ELSE p.supplier
            END AS supplier_name
        FROM products AS p;
        """,
    )


# ---------------------------------------------------------------------------
# 19. Main program
# ---------------------------------------------------------------------------

def main() -> None:
    connection = create_connection()

    try:
        create_schema(connection)
        insert_sample_data(connection)

        demonstrate_select_and_from(connection)
        demonstrate_aliases(connection)
        demonstrate_distinct(connection)
        demonstrate_expressions(connection)
        demonstrate_string_expressions(connection)
        demonstrate_null_behavior(connection)
        demonstrate_types(connection)
        demonstrate_date_expressions(connection)
        demonstrate_case(connection)
        demonstrate_aggregates(connection)
        demonstrate_subqueries(connection)
        demonstrate_sales_report(connection)
        demonstrate_alias_rules(connection)
        demonstrate_edge_cases()
    except TypeError:
        # This branch is intentionally never expected during normal execution.
        # It demonstrates that errors should be handled at an appropriate
        # application boundary rather than silently ignored.
        raise
    finally:
        # The connection remains available for the demonstrations above.
        pass

    demonstrate_safe_parameters(connection)
    demonstrate_query_plan(connection)
    build_executive_report(connection)

    results = run_tests(connection)
    display_tests(results)

    print_title("45. Completion")
    print(
        "The program has demonstrated SELECT, FROM, aliases, DISTINCT, "
        "expressions, calculated columns, NULL handling, CASE expressions, "
        "aggregates, subqueries, parameterization, testing, and query plans."
    )

    connection.close()


if __name__ == "__main__":
    main()
