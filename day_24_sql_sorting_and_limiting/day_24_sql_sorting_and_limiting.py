"""
SQL Sorting & Limiting
======================

Topic:
    ORDER BY, ASC, DESC, LIMIT, OFFSET, and deterministic ordering.

This standalone study script uses Python's standard-library sqlite3 module to
execute real SQL against an in-memory relational database.

The examples progress from basic sorting and limiting to:
- single-column ordering
- ascending and descending order
- multiple sort keys
- NULL ordering
- LIMIT and OFFSET
- pagination
- deterministic ordering
- tie-breaking with unique keys
- expressions in ORDER BY
- aliases in ORDER BY
- conditional ordering
- top-N queries
- keyset-pagination concepts
- duplicate and changing data
- validation and error handling
- query plans and indexes
- performance considerations
- common mistakes
- realistic reporting examples

No external packages are required.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


DATABASE = ":memory:"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def heading(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def subheading(title: str) -> None:
    print("\n" + "-" * 88)
    print(title)
    print("-" * 88)


def print_rows(
    rows: Sequence[sqlite3.Row],
    columns: Sequence[str] | None = None,
) -> None:
    """Print SQLite rows in a readable table."""
    if not rows:
        print("(no rows)")
        return

    if columns is None:
        columns = rows[0].keys()

    values = []
    for row in rows:
        values.append([str(row[column]) for column in columns])

    widths = []
    for index, column in enumerate(columns):
        widths.append(
            max(
                len(str(column)),
                *(len(row[index]) for row in values),
            )
        )

    header = " | ".join(
        str(column).ljust(widths[index])
        for index, column in enumerate(columns)
    )
    separator = "-+-".join("-" * width for width in widths)

    print(header)
    print(separator)

    for row in values:
        print(
            " | ".join(
                row[index].ljust(widths[index])
                for index in range(len(columns))
            )
        )


def execute_and_print(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Iterable[Any] = (),
) -> list[sqlite3.Row]:
    """Execute a SELECT statement and display its SQL and result."""
    print(f"\nSQL:\n{sql.strip()}")
    if parameters:
        print(f"Parameters: {tuple(parameters)}")

    cursor = connection.execute(sql, tuple(parameters))
    rows = cursor.fetchall()
    print_rows(rows)
    return rows


def explain_query_plan(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Iterable[Any] = (),
) -> None:
    """Display SQLite's query-plan information."""
    rows = connection.execute(
        "EXPLAIN QUERY PLAN " + sql,
        tuple(parameters),
    ).fetchall()

    print(f"\nQuery plan for:\n{sql.strip()}")
    for row in rows:
        print(dict(row))


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def create_database() -> sqlite3.Connection:
    """
    Create a small employee database.

    The table intentionally contains:
    - duplicate salaries
    - duplicate department names
    - NULL values
    - dates
    - text values
    - a unique primary key

    These characteristics make ordering behavior easier to study.
    """
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary INTEGER NOT NULL CHECK (salary >= 0),
            performance_score REAL,
            hire_date TEXT NOT NULL,
            city TEXT
        );

        INSERT INTO employees
            (employee_id, employee_name, department, salary,
             performance_score, hire_date, city)
        VALUES
            (1,  'Aarav',  'Engineering', 125000, 9.2, '2021-04-15', 'Delhi'),
            (2,  'Meera',  'Engineering', 125000, 8.8, '2022-08-21', 'Mumbai'),
            (3,  'Kabir',  'Engineering', 98000,  9.5, '2023-01-10', 'Pune'),
            (4,  'Anaya',  'Engineering', 87000,  NULL, '2024-02-19', 'Lucknow'),
            (5,  'Vihaan', 'Finance',     110000, 8.9, '2020-07-01', 'Delhi'),
            (6,  'Ishita', 'Finance',     110000, 9.1, '2021-11-12', 'Bengaluru'),
            (7,  'Rohan',  'Finance',      92000,  7.8, '2023-05-04', 'Mumbai'),
            (8,  'Diya',   'Finance',      76000,  NULL, '2024-06-30', 'Pune'),
            (9,  'Arjun',  'Sales',       105000, 8.4, '2021-02-17', 'Delhi'),
            (10, 'Sara',   'Sales',       105000, 8.7, '2022-03-28', 'Hyderabad'),
            (11, 'Advik',  'Sales',        88000, 7.9, '2023-09-11', 'Lucknow'),
            (12, 'Tara',   'Sales',        69000,  NULL, '2024-01-05', NULL),
            (13, 'Neil',   'Operations',   99000, 8.1, '2020-12-19', 'Delhi'),
            (14, 'Kiara',  'Operations',   91000, 9.0, '2022-10-07', 'Mumbai'),
            (15, 'Yash',   'Operations',   91000, 8.3, '2023-03-14', 'Pune'),
            (16, 'Naina',  'Operations',   72000, 7.5, '2024-05-23', 'Lucknow');
        """
    )

    return connection


# ---------------------------------------------------------------------------
# Fundamental concepts
# ---------------------------------------------------------------------------

def demonstrate_unspecified_order(connection: sqlite3.Connection) -> None:
    heading("1. ORDER WITHOUT ORDER BY")

    print(
        """
SQL tables represent sets of rows. SQL does not promise that a SELECT
without ORDER BY returns rows in a particular logical order.

The database may return rows in an order that happens to look stable because
of an implementation detail, an index, or the physical access path.

That apparent stability is not a correctness guarantee.

Use ORDER BY whenever result order matters.
"""
    )

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        """,
    )


def demonstrate_ascending(connection: sqlite3.Connection) -> None:
    heading("2. ORDER BY ASC")

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        ORDER BY salary ASC
        """,
    )

    print(
        """
ASC means ascending order.

For numeric values:
    small -> large

For text:
    database collation rules determine the ordering.

ASC is the default direction when no direction is supplied, so:

    ORDER BY salary

is equivalent to:

    ORDER BY salary ASC
"""
    )


def demonstrate_descending(connection: sqlite3.Connection) -> None:
    heading("3. ORDER BY DESC")

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        ORDER BY salary DESC
        """,
    )

    print(
        """
DESC means descending order.

For numeric values:
    large -> small

Typical use cases include:
- highest salaries
- newest records
- highest scores
- largest transactions
- most recent events
"""
    )


# ---------------------------------------------------------------------------
# Multiple columns and deterministic ordering
# ---------------------------------------------------------------------------

def demonstrate_multiple_sort_keys(connection: sqlite3.Connection) -> None:
    heading("4. MULTIPLE ORDER BY COLUMNS")

    execute_and_print(
        connection,
        """
        SELECT employee_name, department, salary
        FROM employees
        ORDER BY department ASC, salary DESC
        """,
    )

    print(
        """
The database first sorts by department.

Inside each department, it sorts by salary descending.

Conceptually:

    ORDER BY primary_key ASC,
             secondary_key DESC

The second key is used only when rows tie on the first key.
"""
    )


def demonstrate_deterministic_ordering(connection: sqlite3.Connection) -> None:
    heading("5. DETERMINISTIC ORDERING")

    subheading("Non-unique ordering key")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC
        """,
    )

    print(
        """
Several employees have exactly the same salary.

ORDER BY salary DESC specifies the salary ordering, but it does not specify
how equal-salary rows must be arranged relative to each other.

When LIMIT or OFFSET is involved, relying on an unspecified tie order can
produce unstable pagination.

A robust solution is to add a unique tie-breaker.
"""
    )

    subheading("Unique tie-breaker")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        """,
    )

    print(
        """
Because employee_id is unique, the complete ordering is deterministic for
this fixed dataset.

A common production pattern is:

    ORDER BY business_sort_column DESC,
             primary_key ASC

The direction of the unique key should be chosen deliberately.
"""
    )


# ---------------------------------------------------------------------------
# LIMIT
# ---------------------------------------------------------------------------

def demonstrate_limit(connection: sqlite3.Connection) -> None:
    heading("6. LIMIT")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5
        """,
    )

    print(
        """
LIMIT restricts how many rows are returned.

The critical ordering principle is:

    ORDER BY ... LIMIT ...

If LIMIT is used without ORDER BY, the database is free to return any
qualifying rows.

For "top 5 highest salaries", ORDER BY is therefore part of the meaning of
the query, not merely presentation.
"""
    )


def demonstrate_limit_zero(connection: sqlite3.Connection) -> None:
    heading("7. LIMIT 0")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name
        FROM employees
        ORDER BY employee_id
        LIMIT 0
        """,
    )

    print(
        """
LIMIT 0 returns no rows.

It can be useful for:
- checking a query's shape
- application metadata workflows
- testing
- validating generated SQL
"""
    )


# ---------------------------------------------------------------------------
# OFFSET
# ---------------------------------------------------------------------------

def demonstrate_offset(connection: sqlite3.Connection) -> None:
    heading("8. OFFSET")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5 OFFSET 5
        """,
    )

    print(
        """
OFFSET skips rows before returning the limited result set.

LIMIT 5 OFFSET 5 means:

    skip the first 5 rows
    return the next 5 rows

For page number p and page size s:

    OFFSET = (p - 1) * s

For page 3 with 5 rows per page:

    OFFSET = (3 - 1) * 5
           = 10
"""
    )


def demonstrate_offset_pagination(connection: sqlite3.Connection) -> None:
    heading("9. OFFSET-BASED PAGINATION")

    page_size = 4

    for page_number in range(1, 5):
        offset = (page_number - 1) * page_size

        rows = execute_and_print(
            connection,
            """
            SELECT employee_id, employee_name, salary
            FROM employees
            ORDER BY salary DESC, employee_id ASC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        )

        print(
            f"Page {page_number}: {len(rows)} row(s), "
            f"page size={page_size}, offset={offset}"
        )

    print(
        """
OFFSET pagination is simple and convenient.

Its main limitation is performance for large offsets. The database may need
to locate and process many earlier rows before producing the requested page.

It can also become semantically unstable when rows are inserted, deleted,
or updated between page requests.
"""
    )


# ---------------------------------------------------------------------------
# NULL ordering
# ---------------------------------------------------------------------------

def demonstrate_null_ordering(connection: sqlite3.Connection) -> None:
    heading("10. NULL AND ORDER BY")

    print(
        """
NULL represents an unknown or missing value.

NULL is not the same thing as:
- zero
- an empty string
- false

Different database systems have different default NULL ordering rules.
Therefore, portable applications should make NULL placement explicit when
the position of NULL values matters.
"""
    )

    subheading("SQLite default behavior for ascending score order")

    execute_and_print(
        connection,
        """
        SELECT employee_name, performance_score
        FROM employees
        ORDER BY performance_score ASC
        """,
    )

    subheading("Explicitly place NULL values last")

    execute_and_print(
        connection,
        """
        SELECT employee_name, performance_score
        FROM employees
        ORDER BY
            CASE WHEN performance_score IS NULL THEN 1 ELSE 0 END,
            performance_score ASC,
            employee_id ASC
        """,
    )

    print(
        """
The CASE expression creates a sorting group:

    non-NULL -> 0
    NULL     -> 1

The first sort key therefore places non-NULL values before NULL values.
The actual score then sorts the non-NULL rows.
employee_id completes the tie-breaking.
"""
    )


# ---------------------------------------------------------------------------
# Expressions and aliases
# ---------------------------------------------------------------------------

def demonstrate_order_by_expression(connection: sqlite3.Connection) -> None:
    heading("11. ORDER BY EXPRESSIONS")

    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            salary,
            salary * 1.10 AS projected_salary
        FROM employees
        ORDER BY projected_salary DESC, employee_id ASC
        LIMIT 5
        """,
    )

    print(
        """
ORDER BY can sort by an expression or a SELECT-list alias.

This is useful for:
- calculated prices
- scores
- percentages
- normalized values
- computed business metrics
"""
    )


def demonstrate_conditional_sorting(connection: sqlite3.Connection) -> None:
    heading("12. CONDITIONAL ORDERING")

    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            department,
            performance_score
        FROM employees
        ORDER BY
            CASE
                WHEN performance_score IS NULL THEN 1
                WHEN performance_score >= 9.0 THEN 0
                ELSE 2
            END,
            performance_score DESC,
            employee_id ASC
        """,
    )

    print(
        """
CASE in ORDER BY can encode business-specific priority.

This query places:
1. employees with scores >= 9 first
2. scored employees below 9 next
3. employees without scores last

The exact business rule should be documented because ORDER BY expressions
can become difficult to maintain when they contain too much logic.
"""
    )


# ---------------------------------------------------------------------------
# Top-N and bottom-N
# ---------------------------------------------------------------------------

def demonstrate_top_and_bottom_n(connection: sqlite3.Connection) -> None:
    heading("13. TOP-N AND BOTTOM-N QUERIES")

    subheading("Top 3 salaries")

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 3
        """,
    )

    subheading("Bottom 3 salaries")

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        ORDER BY salary ASC, employee_id ASC
        LIMIT 3
        """,
    )

    print(
        """
The direction of ORDER BY determines whether LIMIT returns the highest or
lowest values.

Top-N:
    ORDER BY metric DESC
    LIMIT N

Bottom-N:
    ORDER BY metric ASC
    LIMIT N
"""
    )


# ---------------------------------------------------------------------------
# Per-group top-N
# ---------------------------------------------------------------------------

def demonstrate_per_group_top_n(connection: sqlite3.Connection) -> None:
    heading("14. TOP-N PER GROUP")

    print(
        """
LIMIT applies to the complete result set.

It does not mean "N rows for every department."

For top-N per group, use a window function such as ROW_NUMBER().
"""
    )

    execute_and_print(
        connection,
        """
        SELECT
            employee_id,
            employee_name,
            department,
            salary
        FROM (
            SELECT
                employee_id,
                employee_name,
                department,
                salary,
                ROW_NUMBER() OVER (
                    PARTITION BY department
                    ORDER BY salary DESC, employee_id ASC
                ) AS position_in_department
            FROM employees
        )
        WHERE position_in_department <= 2
        ORDER BY department ASC, position_in_department ASC
        """,
    )


# ---------------------------------------------------------------------------
# OFFSET versus keyset pagination
# ---------------------------------------------------------------------------

def demonstrate_keyset_pagination(connection: sqlite3.Connection) -> None:
    heading("15. KEYSET PAGINATION")

    print(
        """
Keyset pagination, sometimes called seek pagination, avoids large OFFSET
values by using the values of the last row from the previous page.

Suppose the stable ordering is:

    ORDER BY salary DESC, employee_id ASC

After receiving a row with:

    salary = 105000
    employee_id = 9

the next page can request rows that occur after that row:

    salary < 105000
    OR
    (salary = 105000 AND employee_id > 9)

This is especially useful for large, continuously changing datasets.
"""
    )

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5
        """,
    )

    last_salary = 105000
    last_employee_id = 9

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        WHERE
            salary < ?
            OR (salary = ? AND employee_id > ?)
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5
        """,
        (last_salary, last_salary, last_employee_id),
    )

    print(
        """
Keyset pagination requires a suitable ordering scheme and a cursor
containing the values needed to continue that ordering.

It is not a universal replacement for OFFSET. Random access to page 50,
for example, is naturally expressed with OFFSET, while sequential
"next page" navigation is a strong use case for keyset pagination.
"""
    )


# ---------------------------------------------------------------------------
# Dynamic ORDER BY safety
# ---------------------------------------------------------------------------

def demonstrate_safe_dynamic_ordering(connection: sqlite3.Connection) -> None:
    heading("16. SAFE DYNAMIC ORDER BY")

    print(
        """
SQL parameters are designed for values, not arbitrary SQL identifiers.

This is valid:

    WHERE department = ?

This does not work as a normal value parameter:

    ORDER BY ?

If an application lets a user choose a sort column, do not concatenate
arbitrary input directly into SQL.

Instead, use an allow-list that maps safe application names to known SQL
identifiers.
"""
    )

    allowed_sort_columns = {
        "name": "employee_name",
        "salary": "salary",
        "score": "performance_score",
        "hire_date": "hire_date",
    }

    requested_sort = "salary"
    requested_direction = "desc"

    sort_column = allowed_sort_columns.get(requested_sort)
    direction = requested_direction.upper()

    if sort_column is None:
        raise ValueError("Unsupported sort column")

    if direction not in {"ASC", "DESC"}:
        raise ValueError("Unsupported sort direction")

    sql = f"""
        SELECT employee_id, employee_name, salary, performance_score
        FROM employees
        ORDER BY {sort_column} {direction}, employee_id ASC
        LIMIT ?
    """

    execute_and_print(connection, sql, (5,))

    print(
        """
The SQL fragment is constructed only after both inputs have been validated
against fixed allow-lists.

The LIMIT value is still parameterized because it is a value.
"""
    )


# ---------------------------------------------------------------------------
# Validation and edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases(connection: sqlite3.Connection) -> None:
    heading("17. EDGE CASES")

    subheading("LIMIT larger than the result set")

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        ORDER BY employee_id
        LIMIT 1000
        """,
    )

    subheading("OFFSET beyond the end")

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        ORDER BY employee_id
        LIMIT 10 OFFSET 1000
        """,
    )

    subheading("Negative LIMIT in SQLite")

    execute_and_print(
        connection,
        """
        SELECT employee_name
        FROM employees
        ORDER BY employee_id
        LIMIT -1
        """,
    )

    print(
        """
SQL dialects differ in edge-case syntax and semantics.

SQLite interprets LIMIT -1 as "no LIMIT". Other database systems may reject
such syntax or use different behavior.

Application code should validate pagination inputs before sending them to a
database when the application contract requires non-negative finite limits.
"""
    )


def validate_pagination(page: int, page_size: int) -> int:
    """Validate application-level pagination values."""
    if page < 1:
        raise ValueError("Page must be >= 1.")

    if page_size < 1:
        raise ValueError("Page size must be >= 1.")

    if page_size > 100:
        raise ValueError("Page size must not exceed 100.")

    return (page - 1) * page_size


def demonstrate_pagination_validation() -> None:
    heading("18. APPLICATION-LEVEL PAGINATION VALIDATION")

    valid_cases = [
        (1, 10),
        (2, 20),
        (5, 25),
    ]

    for page, page_size in valid_cases:
        offset = validate_pagination(page, page_size)
        print(
            f"page={page}, page_size={page_size}, calculated_offset={offset}"
        )

    invalid_cases = [
        (0, 10),
        (1, 0),
        (1, 101),
    ]

    for page, page_size in invalid_cases:
        try:
            validate_pagination(page, page_size)
        except ValueError as error:
            print(
                f"Rejected page={page}, page_size={page_size}: {error}"
            )


# ---------------------------------------------------------------------------
# Comparison of ordering strategies
# ---------------------------------------------------------------------------

def demonstrate_ordering_patterns(connection: sqlite3.Connection) -> None:
    heading("19. ORDERING PATTERNS")

    patterns = {
        "Lowest salary first": """
            SELECT employee_name, salary
            FROM employees
            ORDER BY salary ASC, employee_id ASC
            LIMIT 5
        """,
        "Highest salary first": """
            SELECT employee_name, salary
            FROM employees
            ORDER BY salary DESC, employee_id ASC
            LIMIT 5
        """,
        "Newest hires first": """
            SELECT employee_name, hire_date
            FROM employees
            ORDER BY hire_date DESC, employee_id ASC
            LIMIT 5
        """,
        "Alphabetical names": """
            SELECT employee_name
            FROM employees
            ORDER BY employee_name ASC, employee_id ASC
            LIMIT 5
        """,
    }

    for description, sql in patterns.items():
        subheading(description)
        execute_and_print(connection, sql)


# ---------------------------------------------------------------------------
# Indexing and performance
# ---------------------------------------------------------------------------

def create_performance_index(connection: sqlite3.Connection) -> None:
    heading("20. INDEXES AND ORDER BY PERFORMANCE")

    print(
        """
Sorting can require substantial work for large datasets.

An index may help the database satisfy filtering and ordering requirements
without sorting every qualifying row from scratch.

Create an index matching a common stable ordering:
"""
    )

    connection.execute(
        """
        CREATE INDEX idx_employees_salary_employee_id
        ON employees (salary DESC, employee_id ASC)
        """
    )

    connection.commit()

    explain_query_plan(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5
        """,
    )

    print(
        """
Index design is workload-dependent.

An index has costs:
- storage consumption
- additional write work
- maintenance
- memory/cache pressure

Do not create an index for every possible ORDER BY clause.

Use actual query workloads and query plans to guide indexing decisions.
"""
    )


def demonstrate_large_dataset_performance() -> None:
    heading("21. LARGE DATASET PERFORMANCE DEMONSTRATION")

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE transactions (
            transaction_id INTEGER PRIMARY KEY,
            amount INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    rows = [
        (
            transaction_id,
            (transaction_id * 7919) % 1_000_000,
            f"2026-01-{(transaction_id % 28) + 1:02d}",
        )
        for transaction_id in range(1, 50_001)
    ]

    connection.executemany(
        """
        INSERT INTO transactions
            (transaction_id, amount, created_at)
        VALUES (?, ?, ?)
        """,
        rows,
    )
    connection.commit()

    query_without_index = """
        SELECT transaction_id, amount
        FROM transactions
        ORDER BY amount DESC, transaction_id ASC
        LIMIT 20
    """

    start = time.perf_counter()
    connection.execute(query_without_index).fetchall()
    elapsed_without_index = time.perf_counter() - start

    connection.execute(
        """
        CREATE INDEX idx_transactions_amount_id
        ON transactions (amount DESC, transaction_id ASC)
        """
    )
    connection.commit()

    start = time.perf_counter()
    connection.execute(query_without_index).fetchall()
    elapsed_with_index = time.perf_counter() - start

    print(f"Rows inserted: {len(rows):,}")
    print(f"Query time without index: {elapsed_without_index:.6f} seconds")
    print(f"Query time with index:    {elapsed_with_index:.6f} seconds")

    explain_query_plan(connection, query_without_index)

    print(
        """
Benchmark timings depend on hardware, database version, cache state,
dataset size, and execution environment.

The important lesson is not a particular timing value. The lesson is that
ORDER BY can become a significant operation at scale and that a suitable
index can sometimes allow the database to read rows in the required order.
"""
    )

    connection.close()


# ---------------------------------------------------------------------------
# Realistic reporting examples
# ---------------------------------------------------------------------------

def demonstrate_business_queries(connection: sqlite3.Connection) -> None:
    heading("22. REALISTIC BUSINESS QUERIES")

    subheading("Highest-paid Engineering employees")

    execute_and_print(
        connection,
        """
        SELECT employee_name, salary
        FROM employees
        WHERE department = 'Engineering'
        ORDER BY salary DESC, employee_id ASC
        LIMIT 3
        """,
    )

    subheading("Newest five employees")

    execute_and_print(
        connection,
        """
        SELECT employee_name, department, hire_date
        FROM employees
        ORDER BY hire_date DESC, employee_id ASC
        LIMIT 5
        """,
    )

    subheading("Finance employees sorted by performance")

    execute_and_print(
        connection,
        """
        SELECT employee_name, performance_score
        FROM employees
        WHERE department = 'Finance'
        ORDER BY
            performance_score DESC,
            employee_id ASC
        """,
    )

    subheading("Page two of employees ordered by name")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, department
        FROM employees
        ORDER BY employee_name ASC, employee_id ASC
        LIMIT 5 OFFSET 5
        """,
    )


# ---------------------------------------------------------------------------
# Transactional consistency and pagination
# ---------------------------------------------------------------------------

def demonstrate_pagination_instability(connection: sqlite3.Connection) -> None:
    heading("23. WHY PAGINATION NEEDS A STABLE ORDER")

    print(
        """
Imagine page 1 and page 2 are requested separately.

If the ordering uses only a non-unique value such as salary, equal-salary
rows have no explicit relative position.

Even with a deterministic tie-breaker, OFFSET pagination can still be
affected by changes to the dataset between requests.

For example:
- a new row is inserted before the current page
- a row is deleted
- a row's sort value changes

The result can contain duplicates or skipped rows across pages.

Keyset pagination can reduce these problems for sequential navigation, but
the application still needs a clear consistency model when exact snapshots
are required.
"""
    )

    subheading("Stable ordering used by the examples")

    execute_and_print(
        connection,
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5
        """,
    )


# ---------------------------------------------------------------------------
# Common mistakes
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes(connection: sqlite3.Connection) -> None:
    heading("24. COMMON MISTAKES")

    mistakes = [
        (
            "Mistake: LIMIT without ORDER BY",
            """
            SELECT employee_name
            FROM employees
            LIMIT 5
            """,
        ),
        (
            "Mistake: non-deterministic ties",
            """
            SELECT employee_name, salary
            FROM employees
            ORDER BY salary DESC
            LIMIT 5
            """,
        ),
        (
            "Better: deterministic top-N",
            """
            SELECT employee_name, salary
            FROM employees
            ORDER BY salary DESC, employee_id ASC
            LIMIT 5
            """,
        ),
        (
            "Better: deterministic pagination",
            """
            SELECT employee_name, salary
            FROM employees
            ORDER BY salary DESC, employee_id ASC
            LIMIT 5 OFFSET 5
            """,
        ),
    ]

    for description, sql in mistakes:
        subheading(description)
        execute_and_print(connection, sql)


# ---------------------------------------------------------------------------
# SQL clause ordering
# ---------------------------------------------------------------------------

def demonstrate_logical_query_order(connection: sqlite3.Connection) -> None:
    heading("25. WHERE, ORDER BY, LIMIT, AND LOGICAL PROCESSING")

    execute_and_print(
        connection,
        """
        SELECT employee_name, department, salary
        FROM employees
        WHERE salary >= 90000
        ORDER BY salary DESC, employee_id ASC
        LIMIT 5
        """,
    )

    print(
        """
A useful conceptual model is:

    FROM
    WHERE
    GROUP BY
    HAVING
    SELECT
    ORDER BY
    LIMIT/OFFSET

This is a simplified logical processing model rather than a literal
description of the physical execution plan.

The optimizer may choose a different physical strategy while preserving the
query's required result semantics.
"""
    )


# ---------------------------------------------------------------------------
# Testing deterministic order
# ---------------------------------------------------------------------------

def demonstrate_ordering_tests(connection: sqlite3.Connection) -> None:
    heading("26. TESTING ORDERED QUERIES")

    rows = connection.execute(
        """
        SELECT employee_id, employee_name, salary
        FROM employees
        ORDER BY salary DESC, employee_id ASC
        LIMIT 10
        """
    ).fetchall()

    salaries_and_ids = [
        (row["salary"], row["employee_id"])
        for row in rows
    ]

    assert all(
        salaries_and_ids[index] >= salaries_and_ids[index + 1]
        for index in range(len(salaries_and_ids) - 1)
    ), "Salary ordering failed."

    for index in range(len(salaries_and_ids) - 1):
        current_salary, current_id = salaries_and_ids[index]
        next_salary, next_id = salaries_and_ids[index + 1]

        if current_salary == next_salary:
            assert current_id < next_id, (
                "Tie-breaking by employee_id failed."
            )

    assert len(rows) <= 10, "LIMIT failed."

    print("Deterministic ordering assertions passed.")
    print("LIMIT assertion passed.")
    print("Tie-breaking assertions passed.")


# ---------------------------------------------------------------------------
# SQL dialect considerations
# ---------------------------------------------------------------------------

def print_dialect_notes() -> None:
    heading("27. SQL DIALECT CONSIDERATIONS")

    print(
        """
The concepts are broadly shared across SQL databases, but exact syntax can
differ.

SQLite:
    LIMIT n OFFSET m

PostgreSQL:
    LIMIT n OFFSET m

MySQL:
    LIMIT m, n
    or
    LIMIT n OFFSET m

SQL Server commonly uses:
    ORDER BY ...
    OFFSET m ROWS
    FETCH NEXT n ROWS ONLY

Oracle supports:
    FETCH FIRST n ROWS ONLY
    and OFFSET/FETCH syntax in modern versions.

Because SQL dialects differ, production code should follow the syntax and
optimizer behavior of the target database.

Do not assume that a feature demonstrated in SQLite has identical behavior
or performance characteristics in every database system.
"""
    )


# ---------------------------------------------------------------------------
# Security considerations
# ---------------------------------------------------------------------------

def print_security_notes() -> None:
    heading("28. SECURITY CONSIDERATIONS")

    print(
        """
ORDER BY and pagination often become dynamic in web applications.

Potential unsafe pattern:

    ORDER BY <raw user input>

If raw input is concatenated into SQL, an attacker may be able to inject SQL.

Safer design:

1. Allow only known sort-field names.
2. Map application names to fixed SQL identifiers.
3. Allow only ASC or DESC.
4. Parameterize value-based filters.
5. Validate page numbers and page sizes.
6. Apply reasonable maximum page sizes.
7. Avoid exposing arbitrary SQL fragments through API parameters.
8. Log rejected sort requests when security monitoring requires it.

SQL parameters protect values. They do not automatically turn arbitrary
identifiers or SQL syntax into safe values.
"""
    )


# ---------------------------------------------------------------------------
# Final reference table
# ---------------------------------------------------------------------------

def print_reference() -> None:
    heading("29. QUICK REFERENCE")

    reference = [
        ("ORDER BY salary", "Ascending order by salary"),
        ("ORDER BY salary ASC", "Explicit ascending order"),
        ("ORDER BY salary DESC", "Descending order"),
        (
            "ORDER BY department, salary DESC",
            "Department first, then salary descending",
        ),
        (
            "ORDER BY salary DESC, employee_id ASC",
            "Stable tie-breaking",
        ),
        ("LIMIT 10", "Return at most 10 rows"),
        ("LIMIT 10 OFFSET 20", "Skip 20, then return up to 10"),
        (
            "ORDER BY score DESC LIMIT 5",
            "Top five rows by score",
        ),
        (
            "ORDER BY score ASC LIMIT 5",
            "Bottom five rows by score",
        ),
        (
            "ROW_NUMBER() OVER (...)",
            "Useful for top-N per group",
        ),
    ]

    print_rows(
        [
            {
                "SQL pattern": pattern,
                "Meaning": meaning,
            }
            for pattern, meaning in reference
        ],
        columns=["SQL pattern", "Meaning"],
    )


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        """
SQL Sorting & Limiting Study Program

Core concepts:
    ORDER BY
    ASC
    DESC
    LIMIT
    OFFSET
    deterministic ordering
    pagination
    tie-breaking
    performance
    security
    keyset pagination
"""
    )

    connection = create_database()

    try:
        demonstrate_unspecified_order(connection)
        demonstrate_ascending(connection)
        demonstrate_descending(connection)
        demonstrate_multiple_sort_keys(connection)
        demonstrate_deterministic_ordering(connection)
        demonstrate_limit(connection)
        demonstrate_limit_zero(connection)
        demonstrate_offset(connection)
        demonstrate_offset_pagination(connection)
        demonstrate_null_ordering(connection)
        demonstrate_order_by_expression(connection)
        demonstrate_conditional_sorting(connection)
        demonstrate_top_and_bottom_n(connection)
        demonstrate_per_group_top_n(connection)
        demonstrate_keyset_pagination(connection)
        demonstrate_safe_dynamic_ordering(connection)
        demonstrate_edge_cases(connection)
        demonstrate_pagination_validation()
        demonstrate_ordering_patterns(connection)
        create_performance_index(connection)
        demonstrate_large_dataset_performance()
        demonstrate_business_queries(connection)
        demonstrate_pagination_instability(connection)
        demonstrate_common_mistakes(connection)
        demonstrate_logical_query_order(connection)
        demonstrate_ordering_tests(connection)
        print_dialect_notes()
        print_security_notes()
        print_reference()

        heading("STUDY CHECKLIST")

        checklist = [
            "ORDER BY controls the requested result ordering.",
            "ASC means ascending and is the default direction.",
            "DESC means descending.",
            "Multiple ORDER BY keys define hierarchical ordering.",
            "LIMIT restricts the number of returned rows.",
            "OFFSET skips rows before LIMIT is applied to the result.",
            "LIMIT without ORDER BY does not define which rows are returned.",
            "Non-unique sort keys can leave tie ordering unspecified.",
            "A unique tie-breaker makes the requested order deterministic.",
            "OFFSET pagination can become expensive at large offsets.",
            "Keyset pagination can be efficient for sequential navigation.",
            "NULL ordering should be made explicit when its placement matters.",
            "Dynamic sort columns should be selected from an allow-list.",
            "Indexes can sometimes eliminate or reduce explicit sorting work.",
            "Query plans should be inspected for performance-sensitive queries.",
        ]

        for item in checklist:
            print(f"[x] {item}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
