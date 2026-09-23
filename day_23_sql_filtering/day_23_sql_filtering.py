"""
SQL Filtering: WHERE, comparison operators, AND, OR, NOT, IN, BETWEEN, LIKE, IS NULL

A standalone study script that teaches SQL filtering from beginner to advanced
concepts through executable Python examples.

The examples use SQLite from Python's standard library, so no external package
is required.

The database models a small company with departments, employees, customers,
products, and orders. The examples demonstrate how SQL filtering works and why
different predicates behave differently.

Run:
    python sql_filtering.py
"""

import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# 1. DATABASE SETUP
# ---------------------------------------------------------------------------

def create_database() -> sqlite3.Connection:
    """Create an in-memory SQLite database and populate realistic sample data."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY,
            department_name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL
        );

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            department_id INTEGER,
            job_title TEXT NOT NULL,
            salary REAL NOT NULL CHECK (salary >= 0),
            age INTEGER CHECK (age >= 18),
            city TEXT,
            email TEXT,
            manager_id INTEGER,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            hire_date TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(department_id),
            FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            city TEXT,
            email TEXT,
            membership_level TEXT,
            credit_limit REAL,
            referred_by INTEGER,
            FOREIGN KEY (referred_by) REFERENCES customers(customer_id)
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK (price >= 0),
            stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
            discontinued INTEGER NOT NULL DEFAULT 0 CHECK (discontinued IN (0, 1))
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            order_total REAL NOT NULL CHECK (order_total >= 0),
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            shipped_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        INSERT INTO departments VALUES
            (1, 'Engineering', 'Bengaluru'),
            (2, 'Finance', 'Mumbai'),
            (3, 'Human Resources', 'Delhi'),
            (4, 'Sales', 'Lucknow'),
            (5, 'Security', 'Hyderabad');

        INSERT INTO employees
            (employee_id, employee_name, department_id, job_title, salary, age,
             city, email, manager_id, active, hire_date)
        VALUES
            (1, 'Aarav Sharma', 1, 'Engineering Manager', 145000, 42,
             'Bengaluru', 'aarav@example.com', NULL, 1, '2018-04-15'),
            (2, 'Priya Singh', 1, 'Senior Python Developer', 118000, 34,
             'Lucknow', 'priya@example.com', 1, 1, '2020-06-10'),
            (3, 'Rahul Verma', 1, 'Software Engineer', 92000, 28,
             'Delhi', 'rahul@example.com', 1, 1, '2022-01-17'),
            (4, 'Neha Gupta', 2, 'Financial Analyst', 87000, 31,
             'Mumbai', 'neha@example.com', 7, 1, '2021-09-20'),
            (5, 'Vikram Rao', 2, 'Accountant', 71000, 39,
             'Pune', NULL, 7, 1, '2019-02-11'),
            (6, 'Ananya Mehta', 3, 'HR Specialist', 68000, 29,
             'Delhi', 'ananya@example.com', NULL, 1, '2023-03-05'),
            (7, 'Karan Malhotra', 2, 'Finance Manager', 130000, 45,
             'Mumbai', 'karan@example.com', NULL, 1, '2017-11-01'),
            (8, 'Ishita Kapoor', 4, 'Sales Executive', 76000, 27,
             'Lucknow', 'ishita@example.com', 10, 1, '2022-08-12'),
            (9, 'Dev Patel', 4, 'Sales Executive', 73000, 30,
             'Ahmedabad', 'dev@example.com', 10, 1, '2021-12-01'),
            (10, 'Riya Nair', 4, 'Sales Manager', 110000, 38,
             'Kochi', 'riya@example.com', NULL, 1, '2019-07-19'),
            (11, 'Arjun Das', 5, 'Security Engineer', 105000, 33,
             'Hyderabad', 'arjun@example.com', 12, 1, '2021-05-24'),
            (12, 'Meera Joshi', 5, 'Security Manager', 138000, 41,
             'Pune', 'meera@example.com', NULL, 1, '2016-10-08'),
            (13, 'Kabir Khan', 1, 'Intern', 35000, 21,
             'Jaipur', 'kabir@example.com', 2, 0, '2024-01-15'),
            (14, 'Sara Ali', NULL, 'Consultant', 98000, 36,
             NULL, 'sara@example.com', NULL, 1, '2020-10-10');

        INSERT INTO customers VALUES
            (1, 'Aditi Shah', 'Mumbai', 'aditi@example.com', 'Gold', 150000, NULL),
            (2, 'Rohan Kumar', 'Delhi', 'rohan@example.com', 'Silver', 75000, 1),
            (3, 'Sneha Roy', 'Kolkata', NULL, 'Bronze', 25000, NULL),
            (4, 'Manish Jain', 'Lucknow', 'manish@example.com', 'Gold', 125000, 2),
            (5, 'Tanya Bose', NULL, 'tanya@example.com', 'Silver', NULL, NULL),
            (6, 'Nikhil Sethi', 'Bengaluru', 'nikhil@example.com', 'Platinum', 250000, 1),
            (7, 'Pooja Iyer', 'Pune', 'pooja@example.com', 'Bronze', 30000, 4);

        INSERT INTO products VALUES
            (1, 'Laptop Pro', 'Electronics', 120000, 15, 0),
            (2, 'Wireless Mouse', 'Electronics', 1800, 100, 0),
            (3, 'Mechanical Keyboard', 'Electronics', 6500, 40, 0),
            (4, 'Office Chair', 'Furniture', 18500, 20, 0),
            (5, 'Standing Desk', 'Furniture', 32000, 8, 0),
            (6, 'Legacy Monitor', 'Electronics', 14000, 0, 1),
            (7, 'Security Token', 'Security', 4500, 60, 0),
            (8, 'Firewall Appliance', 'Security', 85000, 5, 0);

        INSERT INTO orders
            (order_id, customer_id, product_id, quantity, order_total,
             order_date, status, shipped_date)
        VALUES
            (1001, 1, 1, 1, 120000, '2026-01-05', 'Shipped', '2026-01-07'),
            (1002, 2, 2, 3, 5400, '2026-01-11', 'Delivered', '2026-01-12'),
            (1003, 3, 7, 2, 9000, '2026-02-14', 'Pending', NULL),
            (1004, 4, 5, 1, 32000, '2026-02-20', 'Delivered', '2026-02-23'),
            (1005, 5, 3, 2, 13000, '2026-03-02', 'Cancelled', NULL),
            (1006, 6, 8, 1, 85000, '2026-03-15', 'Shipped', '2026-03-18'),
            (1007, 7, 4, 2, 37000, '2026-04-01', 'Delivered', '2026-04-03'),
            (1008, 1, 7, 5, 22500, '2026-04-12', 'Pending', NULL);
        """
    )

    return connection


# ---------------------------------------------------------------------------
# 2. BASIC DISPLAY HELPERS
# ---------------------------------------------------------------------------

def print_rows(rows: Iterable[sqlite3.Row], title: str = "") -> None:
    """Print SQLite rows in a readable table-like format."""
    rows = list(rows)

    if title:
        print(f"\n--- {title} ---")

    if not rows:
        print("(no rows)")
        return

    columns = rows[0].keys()
    widths = {
        column: max(
            len(str(column)),
            *(len(str(row[column])) if row[column] is not None else 4 for row in rows),
        )
        for column in columns
    }

    header = " | ".join(f"{column:<{widths[column]}}" for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in rows:
        values = []
        for column in columns:
            value = row[column]
            display_value = "NULL" if value is None else str(value)
            values.append(f"{display_value:<{widths[column]}}")
        print(" | ".join(values))


def execute_and_print(
    connection: sqlite3.Connection,
    query: str,
    parameters: tuple[Any, ...] = (),
    title: str = "",
) -> list[sqlite3.Row]:
    """Execute a query and print its result."""
    rows = connection.execute(query, parameters).fetchall()
    print_rows(rows, title)
    return rows


# ---------------------------------------------------------------------------
# 3. WHAT FILTERING MEANS
# ---------------------------------------------------------------------------

def demonstrate_basic_where(connection: sqlite3.Connection) -> None:
    """
    WHERE filters rows.

    SQL concept:
        SELECT columns
        FROM table
        WHERE condition;

    The condition is evaluated for each candidate row. Rows for which the
    WHERE expression evaluates to TRUE are retained.

    SQLite uses three-valued logic:
        TRUE
        FALSE
        UNKNOWN

    UNKNOWN is particularly important when NULL participates in an expression.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        WHERE salary > 100000
        ORDER BY salary DESC;
        """,
        title="Employees with salary greater than 100000",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, city
        FROM employees
        WHERE city = 'Lucknow';
        """,
        title="Employees whose city is Lucknow",
    )


# ---------------------------------------------------------------------------
# 4. COMPARISON OPERATORS
# ---------------------------------------------------------------------------

def demonstrate_comparison_operators(connection: sqlite3.Connection) -> None:
    """
    Common comparison operators:

        =       equal to
        <>      not equal to
        !=      not equal to
        >       greater than
        <       less than
        >=      greater than or equal to
        <=      less than or equal to

    SQL comparisons are expressions. The result is used as a predicate in
    WHERE, HAVING, JOIN conditions, CASE expressions, and other contexts.

    Important:
        SQL uses = for equality.
        SQL does not use Python's == operator.
    """

    queries = [
        (
            """
            SELECT employee_name, salary
            FROM employees
            WHERE salary = 98000;
            """,
            "Equal to",
        ),
        (
            """
            SELECT employee_name, salary
            FROM employees
            WHERE salary <> 98000;
            """,
            "Not equal to using <>",
        ),
        (
            """
            SELECT employee_name, salary
            FROM employees
            WHERE salary != 98000;
            """,
            "Not equal to using !=",
        ),
        (
            """
            SELECT employee_name, age
            FROM employees
            WHERE age > 40;
            """,
            "Greater than",
        ),
        (
            """
            SELECT employee_name, age
            FROM employees
            WHERE age < 30;
            """,
            "Less than",
        ),
        (
            """
            SELECT employee_name, salary
            FROM employees
            WHERE salary >= 100000;
            """,
            "Greater than or equal to",
        ),
        (
            """
            SELECT employee_name, salary
            FROM employees
            WHERE salary <= 70000;
            """,
            "Less than or equal to",
        ),
    ]

    for query, title in queries:
        execute_and_print(connection, query, title=title)


# ---------------------------------------------------------------------------
# 5. AND
# ---------------------------------------------------------------------------

def demonstrate_and(connection: sqlite3.Connection) -> None:
    """
    AND requires all connected conditions to evaluate to TRUE.

    Example:
        salary >= 80000 AND age < 40

    Both conditions must be true for a row to survive the WHERE filter.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, salary, age
        FROM employees
        WHERE salary >= 80000
          AND age < 40
        ORDER BY salary DESC;
        """,
        title="Salary >= 80000 AND age < 40",
    )

    # More conditions can be combined.
    execute_and_print(
        connection,
        """
        SELECT employee_name, department_id, salary, active
        FROM employees
        WHERE active = 1
          AND salary >= 90000
          AND department_id = 1;
        """,
        title="Three conditions joined with AND",
    )


# ---------------------------------------------------------------------------
# 6. OR
# ---------------------------------------------------------------------------

def demonstrate_or(connection: sqlite3.Connection) -> None:
    """
    OR retains a row when at least one condition is TRUE.

    Parentheses matter when AND and OR are mixed. SQL generally evaluates
    AND before OR, but explicit parentheses make the intended logic obvious.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, city, department_id
        FROM employees
        WHERE city = 'Lucknow'
           OR city = 'Mumbai';
        """,
        title="Employees in Lucknow OR Mumbai",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary, department_id
        FROM employees
        WHERE (department_id = 1 OR department_id = 5)
          AND salary >= 100000;
        """,
        title="Engineering OR Security, with salary threshold",
    )


# ---------------------------------------------------------------------------
# 7. NOT
# ---------------------------------------------------------------------------

def demonstrate_not(connection: sqlite3.Connection) -> None:
    """
    NOT reverses a logical predicate.

        NOT TRUE    -> FALSE
        NOT FALSE   -> TRUE
        NOT UNKNOWN -> UNKNOWN

    NOT can be applied to a condition or used with operators such as IN,
    BETWEEN, and LIKE.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, city
        FROM employees
        WHERE NOT city = 'Delhi';
        """,
        title="Employees whose city is not Delhi",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, department_id
        FROM employees
        WHERE NOT (department_id = 1 OR department_id = 2);
        """,
        title="Employees outside departments 1 and 2",
    )


# ---------------------------------------------------------------------------
# 8. IN
# ---------------------------------------------------------------------------

def demonstrate_in(connection: sqlite3.Connection) -> None:
    """
    IN tests whether a value belongs to a specified set.

    Instead of:
        city = 'Delhi' OR city = 'Mumbai' OR city = 'Lucknow'

    we can write:
        city IN ('Delhi', 'Mumbai', 'Lucknow')

    NOT IN is the inverse, with an important NULL caveat discussed later.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, city
        FROM employees
        WHERE city IN ('Delhi', 'Mumbai', 'Lucknow')
        ORDER BY city, employee_name;
        """,
        title="IN with a list of cities",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, department_id
        FROM employees
        WHERE department_id NOT IN (1, 2, 3);
        """,
        title="NOT IN",
    )

    # IN can also use a subquery.
    execute_and_print(
        connection,
        """
        SELECT employee_name, department_id
        FROM employees
        WHERE department_id IN (
            SELECT department_id
            FROM departments
            WHERE location IN ('Bengaluru', 'Hyderabad')
        );
        """,
        title="IN with a subquery",
    )


# ---------------------------------------------------------------------------
# 9. BETWEEN
# ---------------------------------------------------------------------------

def demonstrate_between(connection: sqlite3.Connection) -> None:
    """
    BETWEEN is inclusive.

        salary BETWEEN 80000 AND 100000

    means:

        salary >= 80000
        AND
        salary <= 100000

    This is an important distinction because some beginners expect the upper
    boundary to be excluded as in Python's range().
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        WHERE salary BETWEEN 80000 AND 100000
        ORDER BY salary;
        """,
        title="Salary between 80000 and 100000, inclusive",
    )

    execute_and_print(
        connection,
        """
        SELECT order_id, order_date, order_total
        FROM orders
        WHERE order_date BETWEEN '2026-02-01' AND '2026-03-31'
        ORDER BY order_date;
        """,
        title="Orders between two ISO-formatted dates",
    )

    # NOT BETWEEN is the logical inverse.
    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE price NOT BETWEEN 5000 AND 50000;
        """,
        title="Products outside the inclusive price range",
    )


# ---------------------------------------------------------------------------
# 10. LIKE
# ---------------------------------------------------------------------------

def demonstrate_like(connection: sqlite3.Connection) -> None:
    """
    LIKE performs pattern matching.

    In standard SQL and SQLite:
        %  matches zero or more characters.
        _  matches exactly one character.

    Examples:
        'A%'      starts with A
        '%a'      ends with a
        '%dev%'   contains dev
        '_a%'     second character is a

    LIKE is different from =:
        name = 'Aarav Sharma'
    tests exact equality.

        name LIKE 'Aarav%'
    tests a pattern.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE employee_name LIKE 'A%';
        """,
        title="Names beginning with A",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE employee_name LIKE '%a';
        """,
        title="Names ending with a",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE employee_name LIKE '%ar%';
        """,
        title="Names containing 'ar'",
    )

    execute_and_print(
        connection,
        """
        SELECT product_name
        FROM products
        WHERE product_name LIKE '%Desk%';
        """,
        title="Product names containing Desk",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE employee_name LIKE '_e%';
        """,
        title="Names whose second character is e",
    )


# ---------------------------------------------------------------------------
# 11. IS NULL AND IS NOT NULL
# ---------------------------------------------------------------------------

def demonstrate_null(connection: sqlite3.Connection) -> None:
    """
    NULL means missing, unknown, or not applicable data. It is not the same
    as zero, an empty string, or the text 'NULL'.

    Incorrect:
        WHERE email = NULL

    Correct:
        WHERE email IS NULL

    Also:
        WHERE email IS NOT NULL

    The reason is SQL's three-valued logic. Comparing a normal value to NULL
    does not produce TRUE or FALSE; it produces UNKNOWN.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, email
        FROM employees
        WHERE email IS NULL;
        """,
        title="Employees with missing email",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, email
        FROM employees
        WHERE email IS NOT NULL;
        """,
        title="Employees with an email",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, city
        FROM employees
        WHERE city IS NULL;
        """,
        title="Employees with unknown city",
    )

    # Demonstrate the common incorrect expression.
    execute_and_print(
        connection,
        """
        SELECT employee_name, email
        FROM employees
        WHERE email = NULL;
        """,
        title="Incorrect NULL comparison: email = NULL",
    )


# ---------------------------------------------------------------------------
# 12. THREE-VALUED LOGIC
# ---------------------------------------------------------------------------

def demonstrate_three_valued_logic(connection: sqlite3.Connection) -> None:
    """
    SQL's logical model contains TRUE, FALSE, and UNKNOWN.

    Important examples:

        NULL = 5       -> UNKNOWN
        NULL <> 5      -> UNKNOWN
        NULL = NULL    -> UNKNOWN
        NULL > 5       -> UNKNOWN

    WHERE keeps only rows for which the predicate evaluates to TRUE.

    This explains why:
        WHERE email = NULL
    returns no rows.
    """
    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            email,
            email = NULL AS equality_test,
            email <> NULL AS inequality_test,
            email IS NULL AS is_null_test
        FROM employees
        WHERE employee_id IN (4, 5, 14);
        """,
        title="NULL comparison versus IS NULL",
    )

    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            city,
            city = 'Delhi' AS city_is_delhi,
            city <> 'Delhi' AS city_is_not_delhi
        FROM employees
        WHERE employee_id = 14;
        """,
        title="NULL causes UNKNOWN in ordinary comparisons",
    )


# ---------------------------------------------------------------------------
# 13. OPERATOR PRECEDENCE
# ---------------------------------------------------------------------------

def demonstrate_precedence(connection: sqlite3.Connection) -> None:
    """
    A practical precedence rule:

        NOT
        AND
        OR

    Parentheses should be used whenever the business rule could be
    misunderstood.

    Compare these two expressions:

        city = 'Delhi' OR city = 'Mumbai' AND salary > 100000

    and:

        (city = 'Delhi' OR city = 'Mumbai') AND salary > 100000

    They do not mean the same thing.
    """
    execute_and_print(
        connection,
        """
        SELECT employee_name, city, salary
        FROM employees
        WHERE city = 'Delhi'
           OR city = 'Mumbai'
          AND salary > 100000;
        """,
        title="AND evaluated before OR",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, city, salary
        FROM employees
        WHERE (city = 'Delhi' OR city = 'Mumbai')
          AND salary > 100000;
        """,
        title="Explicit parentheses change the logic",
    )


# ---------------------------------------------------------------------------
# 14. COMBINING FILTER OPERATORS
# ---------------------------------------------------------------------------

def demonstrate_complex_filters(connection: sqlite3.Connection) -> None:
    """
    Real queries often combine several filtering operators.

    The following example asks for active employees who:
        - are in Engineering or Security,
        - earn between 90000 and 140000,
        - and have an email address.
    """
    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            department_id,
            salary,
            email
        FROM employees
        WHERE active = 1
          AND department_id IN (1, 5)
          AND salary BETWEEN 90000 AND 140000
          AND email IS NOT NULL
        ORDER BY salary DESC;
        """,
        title="Combined filtering example",
    )


# ---------------------------------------------------------------------------
# 15. FILTERING TEXT, NUMBERS, AND DATES
# ---------------------------------------------------------------------------

def demonstrate_data_types(connection: sqlite3.Connection) -> None:
    """
    Filtering depends on the type and representation of the data.

    Numeric:
        salary > 100000

    Text:
        city = 'Delhi'

    ISO-formatted dates:
        order_date >= '2026-03-01'

    SQLite can compare ISO date strings chronologically because the
    YYYY-MM-DD representation sorts naturally.
    """
    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE price >= 30000;
        """,
        title="Numeric filtering",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, city
        FROM employees
        WHERE city = 'Pune';
        """,
        title="Text filtering",
    )

    execute_and_print(
        connection,
        """
        SELECT order_id, order_date, status
        FROM orders
        WHERE order_date >= '2026-03-01'
          AND order_date < '2026-04-01'
        ORDER BY order_date;
        """,
        title="Date filtering using a half-open range",
    )


# ---------------------------------------------------------------------------
# 16. HALF-OPEN DATE RANGES
# ---------------------------------------------------------------------------

def demonstrate_half_open_dates(connection: sqlite3.Connection) -> None:
    """
    For timestamp columns, this pattern is often safer:

        timestamp >= start
        AND timestamp < end

    instead of:

        timestamp BETWEEN start AND end

    For example, to retrieve all records during March:

        >= 2026-03-01
        <  2026-04-01

    The approach avoids guessing the final second or microsecond of the month.
    """
    execute_and_print(
        connection,
        """
        SELECT order_id, order_date, status
        FROM orders
        WHERE order_date >= '2026-03-01'
          AND order_date < '2026-04-01'
        ORDER BY order_date;
        """,
        title="Half-open March date range",
    )


# ---------------------------------------------------------------------------
# 17. PARAMETERIZED FILTERS
# ---------------------------------------------------------------------------

def demonstrate_parameterized_queries(connection: sqlite3.Connection) -> None:
    """
    Dynamic values should be supplied as parameters rather than concatenated
    directly into SQL strings.

    Unsafe style:
        f"SELECT ... WHERE city = '{city}'"

    Safer style:
        "SELECT ... WHERE city = ?"
        followed by (city,)

    Parameterization separates SQL structure from data and helps prevent SQL
    injection.
    """
    minimum_salary = 90000
    city = "Bengaluru"

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary, city
        FROM employees
        WHERE salary >= ?
          AND city = ?;
        """,
        (minimum_salary, city),
        title="Parameterized filter",
    )


# ---------------------------------------------------------------------------
# 18. SAFE DYNAMIC FILTER BUILDING
# ---------------------------------------------------------------------------

def build_employee_filter(
    minimum_salary: float | None = None,
    maximum_salary: float | None = None,
    cities: list[str] | None = None,
    active_only: bool = False,
) -> tuple[str, list[Any]]:
    """
    Build only the dynamic predicate portions while keeping values parameterized.

    SQL identifiers and SQL syntax are controlled by the program. User-provided
    values become parameters.

    This is a useful pattern for search screens and reporting applications.
    """
    conditions: list[str] = []
    parameters: list[Any] = []

    if minimum_salary is not None:
        conditions.append("salary >= ?")
        parameters.append(minimum_salary)

    if maximum_salary is not None:
        conditions.append("salary <= ?")
        parameters.append(maximum_salary)

    if cities:
        placeholders = ", ".join("?" for _ in cities)
        conditions.append(f"city IN ({placeholders})")
        parameters.extend(cities)

    if active_only:
        conditions.append("active = 1")

    where_clause = " AND ".join(conditions) if conditions else "1 = 1"

    return where_clause, parameters


def demonstrate_dynamic_filter_builder(connection: sqlite3.Connection) -> None:
    """Demonstrate safe construction of optional filters."""
    where_clause, parameters = build_employee_filter(
        minimum_salary=70000,
        maximum_salary=120000,
        cities=["Lucknow", "Delhi", "Mumbai"],
        active_only=True,
    )

    query = f"""
        SELECT employee_name, salary, city, active
        FROM employees
        WHERE {where_clause}
        ORDER BY salary DESC;
    """

    execute_and_print(
        connection,
        query,
        tuple(parameters),
        title="Safe dynamic filter builder",
    )


# ---------------------------------------------------------------------------
# 19. EXISTS AS AN ADVANCED FILTER
# ---------------------------------------------------------------------------

def demonstrate_exists(connection: sqlite3.Connection) -> None:
    """
    EXISTS asks whether a subquery produces at least one row.

    It is especially useful when filtering a parent table based on the
    existence of related child records.

    Example:
        Find customers who have at least one pending order.
    """
    execute_and_print(
        connection,
        """
        SELECT
            c.customer_id,
            c.customer_name
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Pending'
        )
        ORDER BY c.customer_id;
        """,
        title="Customers with at least one pending order",
    )

    execute_and_print(
        connection,
        """
        SELECT
            c.customer_id,
            c.customer_name
        FROM customers AS c
        WHERE NOT EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
        );
        """,
        title="Customers with no orders",
    )


# ---------------------------------------------------------------------------
# 20. NOT IN AND NULL
# ---------------------------------------------------------------------------

def demonstrate_not_in_null_problem(connection: sqlite3.Connection) -> None:
    """
    NOT IN has a subtle interaction with NULL.

    Conceptually:

        value NOT IN (1, 2, NULL)

    cannot be safely interpreted as a simple true/false membership test for
    every value because comparison with NULL produces UNKNOWN.

    This is one reason NOT EXISTS is often safer when a subquery may contain
    NULL values.

    We create a small demonstration table.
    """
    connection.execute("CREATE TABLE nullable_department_values (department_id INTEGER)")
    connection.executemany(
        "INSERT INTO nullable_department_values VALUES (?)",
        [(1,), (2,), (None,)],
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, department_id
        FROM employees
        WHERE department_id NOT IN (
            SELECT department_id
            FROM nullable_department_values
        );
        """,
        title="NOT IN with a subquery containing NULL",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name, department_id
        FROM employees AS e
        WHERE NOT EXISTS (
            SELECT 1
            FROM nullable_department_values AS d
            WHERE d.department_id = e.department_id
        );
        """,
        title="NOT EXISTS alternative",
    )


# ---------------------------------------------------------------------------
# 21. FILTERING WITH CASE
# ---------------------------------------------------------------------------

def demonstrate_case_with_filtering(connection: sqlite3.Connection) -> None:
    """
    CASE is not itself a WHERE operator, but it can classify values while a
    WHERE predicate restricts the rows being processed.

    This is useful when a query needs both filtering and categorization.
    """
    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            salary,
            CASE
                WHEN salary >= 120000 THEN 'Executive/high salary'
                WHEN salary >= 90000 THEN 'Mid/high salary'
                WHEN salary >= 60000 THEN 'Standard salary'
                ELSE 'Lower salary'
            END AS salary_band
        FROM employees
        WHERE active = 1
        ORDER BY salary DESC;
        """,
        title="Filtered rows with CASE classification",
    )


# ---------------------------------------------------------------------------
# 22. FILTERING AFTER JOIN
# ---------------------------------------------------------------------------

def demonstrate_join_filtering(connection: sqlite3.Connection) -> None:
    """
    WHERE commonly filters joined results.

    The join combines rows. The WHERE clause then restricts the combined
    result set.

    This example retrieves active employees in departments located in
    Bengaluru or Hyderabad.
    """
    execute_and_print(
        connection,
        """
        SELECT
            e.employee_name,
            d.department_name,
            d.location,
            e.salary
        FROM employees AS e
        INNER JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE e.active = 1
          AND d.location IN ('Bengaluru', 'Hyderabad')
        ORDER BY d.department_name, e.employee_name;
        """,
        title="Filtering joined tables",
    )


# ---------------------------------------------------------------------------
# 23. WHERE AND OUTER JOIN
# ---------------------------------------------------------------------------

def demonstrate_left_join_null_behavior(connection: sqlite3.Connection) -> None:
    """
    A LEFT JOIN keeps unmatched rows from the left table.

    A condition placed in WHERE can remove those unmatched rows if it rejects
    NULL values from the right table.

    Compare:
        LEFT JOIN ... ON condition

    with:
        LEFT JOIN ...
        WHERE right_table.column = ...

    The placement of the predicate can change the meaning of the query.
    """
    execute_and_print(
        connection,
        """
        SELECT
            e.employee_name,
            d.department_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE e.employee_id IN (14, 1);
        """,
        title="LEFT JOIN retains an employee without a department",
    )

    execute_and_print(
        connection,
        """
        SELECT
            e.employee_name,
            d.department_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE d.department_name = 'Engineering';
        """,
        title="WHERE on right table removes unmatched NULL department",
    )

    execute_and_print(
        connection,
        """
        SELECT
            e.employee_name,
            d.department_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
           AND d.department_name = 'Engineering'
        WHERE e.employee_id IN (14, 1);
        """,
        title="Moving the predicate into ON preserves LEFT JOIN behavior",
    )


# ---------------------------------------------------------------------------
# 24. FILTERING AND AGGREGATION
# ---------------------------------------------------------------------------

def demonstrate_where_vs_having(connection: sqlite3.Connection) -> None:
    """
    WHERE filters rows before grouping.

    HAVING filters groups after GROUP BY.

    Example:
        WHERE salary >= 70000
    filters individual employees.

        HAVING AVG(salary) >= 90000
    filters grouped departments.

    Although HAVING is not part of the requested core operator list, this
    distinction is essential when WHERE is used with aggregation.
    """
    execute_and_print(
        connection,
        """
        SELECT
            department_id,
            COUNT(*) AS employee_count,
            AVG(salary) AS average_salary
        FROM employees
        WHERE active = 1
        GROUP BY department_id
        HAVING AVG(salary) >= 90000
        ORDER BY average_salary DESC;
        """,
        title="WHERE before GROUP BY, HAVING after grouping",
    )


# ---------------------------------------------------------------------------
# 25. QUERY PLAN AND INDEXING
# ---------------------------------------------------------------------------

def demonstrate_query_plan(connection: sqlite3.Connection) -> None:
    """
    Filtering performance depends on data volume, indexes, selectivity,
    expressions, and the database optimizer.

    SQLite's EXPLAIN QUERY PLAN provides a useful demonstration.

    We add an index on salary and inspect a filter that can use it.
    """
    connection.execute(
        "CREATE INDEX idx_employees_salary ON employees(salary)"
    )

    rows = connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT employee_name
        FROM employees
        WHERE salary >= 100000;
        """
    ).fetchall()

    print("\n--- Query plan for indexed salary filter ---")
    for row in rows:
        print(tuple(row))

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        WHERE salary >= 100000
        ORDER BY salary;
        """,
        title="Filter using an indexed column",
    )


# ---------------------------------------------------------------------------
# 26. COMMON MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes(connection: sqlite3.Connection) -> None:
    """
    Several common mistakes are demonstrated directly.
    """

    # Mistake 1: using == instead of =.
    # SQLite accepts == as an equality operator, but portable SQL should use =.
    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE city = 'Lucknow';
        """,
        title="Portable equality syntax: =",
    )

    # Mistake 2: using = NULL.
    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE email = NULL;
        """,
        title="Mistake: email = NULL",
    )

    # Mistake 3: forgetting parentheses.
    execute_and_print(
        connection,
        """
        SELECT employee_name, city, salary
        FROM employees
        WHERE city = 'Delhi'
           OR city = 'Mumbai'
          AND salary >= 100000;
        """,
        title="Potentially ambiguous mixed AND/OR expression",
    )

    # Explicit version.
    execute_and_print(
        connection,
        """
        SELECT employee_name, city, salary
        FROM employees
        WHERE (city = 'Delhi' OR city = 'Mumbai')
          AND salary >= 100000;
        """,
        title="Explicit and safer logical expression",
    )


# ---------------------------------------------------------------------------
# 27. VALIDATION WITH ASSERTIONS
# ---------------------------------------------------------------------------

def demonstrate_filter_validation(connection: sqlite3.Connection) -> None:
    """
    SQL filtering logic can be tested just like application logic.

    Assertions below verify expected properties of the result.
    """
    rows = connection.execute(
        """
        SELECT employee_name, salary
        FROM employees
        WHERE salary > 100000;
        """
    ).fetchall()

    assert all(row["salary"] > 100000 for row in rows)
    assert all(row["salary"] is not None for row in rows)

    null_email_rows = connection.execute(
        """
        SELECT employee_name, email
        FROM employees
        WHERE email IS NULL;
        """
    ).fetchall()

    assert all(row["email"] is None for row in null_email_rows)

    print("\n--- Filtering assertions ---")
    print("Salary predicate test: PASS")
    print("NULL predicate test: PASS")


# ---------------------------------------------------------------------------
# 28. MINI REPORTING SYSTEM
# ---------------------------------------------------------------------------

@dataclass
class EmployeeFilter:
    """Application-level representation of optional employee filters."""

    minimum_salary: float | None = None
    maximum_salary: float | None = None
    cities: list[str] | None = None
    department_ids: list[int] | None = None
    active_only: bool = False
    name_pattern: str | None = None
    require_email: bool = False


class EmployeeRepository:
    """
    Small repository-style component.

    It separates application filtering inputs from SQL execution. This is
    useful in larger applications because SQL construction is centralized.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def search(self, employee_filter: EmployeeFilter) -> list[sqlite3.Row]:
        conditions: list[str] = []
        parameters: list[Any] = []

        if employee_filter.minimum_salary is not None:
            conditions.append("salary >= ?")
            parameters.append(employee_filter.minimum_salary)

        if employee_filter.maximum_salary is not None:
            conditions.append("salary <= ?")
            parameters.append(employee_filter.maximum_salary)

        if employee_filter.cities:
            placeholders = ", ".join("?" for _ in employee_filter.cities)
            conditions.append(f"city IN ({placeholders})")
            parameters.extend(employee_filter.cities)

        if employee_filter.department_ids:
            placeholders = ", ".join("?" for _ in employee_filter.department_ids)
            conditions.append(f"department_id IN ({placeholders})")
            parameters.extend(employee_filter.department_ids)

        if employee_filter.active_only:
            conditions.append("active = 1")

        if employee_filter.name_pattern is not None:
            conditions.append("employee_name LIKE ?")
            parameters.append(employee_filter.name_pattern)

        if employee_filter.require_email:
            conditions.append("email IS NOT NULL")

        where_clause = " AND ".join(conditions) or "1 = 1"

        query = f"""
            SELECT
                employee_id,
                employee_name,
                department_id,
                salary,
                city,
                email,
                active
            FROM employees
            WHERE {where_clause}
            ORDER BY employee_name;
        """

        return self.connection.execute(query, parameters).fetchall()


def demonstrate_repository(connection: sqlite3.Connection) -> None:
    """Use the repository to run a realistic multi-filter search."""
    repository = EmployeeRepository(connection)

    criteria = EmployeeFilter(
        minimum_salary=70000,
        maximum_salary=140000,
        cities=["Lucknow", "Delhi", "Pune", "Hyderabad"],
        active_only=True,
        name_pattern="%a%",
        require_email=True,
    )

    rows = repository.search(criteria)
    print_rows(rows, "Repository-style multi-filter employee search")


# ---------------------------------------------------------------------------
# 29. PERFORMANCE DISCUSSION THROUGH CODE
# ---------------------------------------------------------------------------

def demonstrate_filter_selectivity(connection: sqlite3.Connection) -> None:
    """
    Selectivity describes how strongly a predicate reduces the number of rows.

    A highly selective filter may return very few rows:
        employee_id = 11

    A less selective filter may return many rows:
        active = 1

    Indexes are generally most useful when the optimizer can efficiently
    identify a subset of rows rather than scanning the entire table.
    """
    queries = [
        (
            """
            SELECT COUNT(*)
            FROM employees
            WHERE employee_id = 11;
            """,
            "Highly selective primary-key filter",
        ),
        (
            """
            SELECT COUNT(*)
            FROM employees
            WHERE active = 1;
            """,
            "Less selective boolean filter",
        ),
    ]

    for query, title in queries:
        count = connection.execute(query).fetchone()[0]
        print(f"\n--- {title} ---")
        print(f"Matching rows: {count}")


# ---------------------------------------------------------------------------
# 30. SECURITY CONSIDERATIONS
# ---------------------------------------------------------------------------

def demonstrate_sql_injection_safe_pattern(
    connection: sqlite3.Connection,
) -> None:
    """
    SQL injection occurs when untrusted input is interpreted as SQL syntax.

    Do not construct a query like:

        SELECT ... WHERE city = '<user input>'

    Instead, use placeholders:

        SELECT ... WHERE city = ?

    The following demonstration treats the input as data.
    """
    user_supplied_city = "' OR 1=1 --"

    rows = connection.execute(
        """
        SELECT employee_name, city
        FROM employees
        WHERE city = ?;
        """,
        (user_supplied_city,),
    ).fetchall()

    print("\n--- Parameterized input security demonstration ---")
    print(f"Input treated as data: {user_supplied_city!r}")
    print(f"Rows returned: {len(rows)}")


# ---------------------------------------------------------------------------
# 31. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases(connection: sqlite3.Connection) -> None:
    """
    Important edge cases include:

    - Empty IN lists cannot be written identically across all SQL dialects.
    - NULL behaves differently from ordinary values.
    - BETWEEN includes both boundaries.
    - LIKE pattern characters have special meanings.
    - AND/OR precedence can change results.
    - NOT IN can behave unexpectedly with NULL.
    - Text comparisons can depend on collation and database settings.
    - Date filtering depends on how dates/timestamps are stored.
    """
    execute_and_print(
        connection,
        """
        SELECT product_name, price
        FROM products
        WHERE price BETWEEN 18500 AND 32000
        ORDER BY price;
        """,
        title="BETWEEN includes both endpoints",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE employee_name LIKE '%_%';
        """,
        title="LIKE underscore pattern",
    )

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        WHERE NOT (salary < 80000);
        """,
        title="NOT around a comparison",
    )


# ---------------------------------------------------------------------------
# 32. COMPLETE WORKFLOW
# ---------------------------------------------------------------------------

def run_all_lessons(connection: sqlite3.Connection) -> None:
    """Run the complete progression of lessons."""
    lessons = [
        demonstrate_basic_where,
        demonstrate_comparison_operators,
        demonstrate_and,
        demonstrate_or,
        demonstrate_not,
        demonstrate_in,
        demonstrate_between,
        demonstrate_like,
        demonstrate_null,
        demonstrate_three_valued_logic,
        demonstrate_precedence,
        demonstrate_complex_filters,
        demonstrate_data_types,
        demonstrate_half_open_dates,
        demonstrate_parameterized_queries,
        demonstrate_dynamic_filter_builder,
        demonstrate_exists,
        demonstrate_not_in_null_problem,
        demonstrate_case_with_filtering,
        demonstrate_join_filtering,
        demonstrate_left_join_null_behavior,
        demonstrate_where_vs_having,
        demonstrate_query_plan,
        demonstrate_common_mistakes,
        demonstrate_filter_validation,
        demonstrate_repository,
        demonstrate_filter_selectivity,
        demonstrate_sql_injection_safe_pattern,
        demonstrate_edge_cases,
    ]

    for lesson in lessons:
        print("\n" + "=" * 78)
        print(lesson.__name__.replace("_", " ").upper())
        print("=" * 78)
        lesson(connection)


# ---------------------------------------------------------------------------
# 33. MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    """Create the database, run all demonstrations, and close the connection."""
    connection = create_database()

    try:
        print("=" * 78)
        print("SQL FILTERING: COMPLETE PYTHON STUDY PROGRAM")
        print("=" * 78)
        print(
            """
Topics:
    WHERE
    comparison operators
    AND
    OR
    NOT
    IN
    BETWEEN
    LIKE
    IS NULL / IS NOT NULL
    three-valued logic
    operator precedence
    parameterized queries
    dynamic filters
    subqueries and EXISTS
    JOIN filtering
    WHERE versus HAVING
    indexing and query plans
    SQL injection prevention
    testing and edge cases
"""
        )

        run_all_lessons(connection)

        print("\n" + "=" * 78)
        print("ALL LESSONS COMPLETED")
        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
