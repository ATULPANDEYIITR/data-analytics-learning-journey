"""
SQL JOINS I
===========

Topic:
    INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN, and join keys.

This standalone study script uses Python's built-in sqlite3 module to make
SQL joins executable and observable.

Learning progression:
    1. Relational-table fundamentals
    2. Primary keys and foreign keys
    3. Join keys
    4. INNER JOIN
    5. LEFT JOIN
    6. RIGHT JOIN
    7. FULL OUTER JOIN
    8. Composite join keys
    9. Joins with filters and aggregations
   10. One-to-many and many-to-many relationships
   11. NULL behavior
   12. Duplicate and non-unique keys
   13. Anti-joins and semi-joins
   14. Self joins
   15. Cross joins
   16. Query design, debugging, performance, and production concerns

No external packages are required.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Sequence


# ============================================================================
# 1. BASIC TERMINOLOGY
# ============================================================================

def explain_fundamentals() -> None:
    print("\n" + "=" * 78)
    print("1. SQL JOIN FUNDAMENTALS")
    print("=" * 78)

    concepts = {
        "Table": "A collection of rows organized into columns.",
        "Row": "One record in a table.",
        "Column": "One attribute or field of a record.",
        "Primary key": "A column or column set that uniquely identifies a row.",
        "Foreign key": "A column or column set referring to a key in another table.",
        "Join key": "The column or columns used to match rows between relations.",
        "INNER JOIN": "Returns rows for which the join condition matches on both sides.",
        "LEFT JOIN": "Keeps every row from the left table and matches rows from the right.",
        "RIGHT JOIN": "Keeps every row from the right table and matches rows from the left.",
        "FULL OUTER JOIN": "Keeps matched rows and unmatched rows from both sides.",
        "NULL": "Represents an unknown or missing value; it is not equal to zero or ''.",
    }

    for term, definition in concepts.items():
        print(f"{term:18} -> {definition}")


# ============================================================================
# 2. SAMPLE DATABASE
# ============================================================================

SCHEMA = """
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    employee_name TEXT NOT NULL,
    department_id INTEGER,
    manager_id INTEGER,
    salary INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL
);

CREATE TABLE employee_projects (
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE regional_sales (
    region TEXT NOT NULL,
    product TEXT NOT NULL,
    amount INTEGER NOT NULL,
    PRIMARY KEY (region, product)
);

CREATE TABLE regional_targets (
    region TEXT NOT NULL,
    product TEXT NOT NULL,
    target INTEGER NOT NULL,
    PRIMARY KEY (region, product)
);
"""


def create_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)

    connection.executemany(
        "INSERT INTO departments VALUES (?, ?)",
        [
            (10, "Engineering"),
            (20, "Finance"),
            (30, "Human Resources"),
            (40, "Security"),
            (50, "Research"),
        ],
    )

    connection.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Asha", 10, None, 95000),
            (2, "Ravi", 10, 1, 82000),
            (3, "Meera", 20, 1, 78000),
            (4, "Kabir", None, 1, 70000),
            (5, "Isha", 30, 1, 68000),
            (6, "Arjun", 40, 1, 88000),
        ],
    )

    connection.executemany(
        "INSERT INTO projects VALUES (?, ?)",
        [
            (101, "Cloud Migration"),
            (102, "Fraud Detection"),
            (103, "Security Audit"),
        ],
    )

    connection.executemany(
        "INSERT INTO employee_projects VALUES (?, ?, ?)",
        [
            (1, 101, "Architect"),
            (1, 103, "Lead"),
            (2, 101, "Developer"),
            (3, 102, "Analyst"),
            (6, 103, "Security Engineer"),
        ],
    )

    connection.executemany(
        "INSERT INTO regional_sales VALUES (?, ?, ?)",
        [
            ("North", "Laptop", 100000),
            ("North", "Phone", 70000),
            ("South", "Laptop", 85000),
            ("West", "Tablet", 45000),
        ],
    )

    connection.executemany(
        "INSERT INTO regional_targets VALUES (?, ?, ?)",
        [
            ("North", "Laptop", 90000),
            ("North", "Phone", 80000),
            ("South", "Laptop", 80000),
            ("East", "Tablet", 40000),
        ],
    )

    connection.commit()
    return connection


# ============================================================================
# 3. OUTPUT HELPERS
# ============================================================================

def print_rows(
    title: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> None:
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)

    rows = list(rows)

    if not rows:
        print("(no rows)")
        return

    widths = [
        max(
            len(str(column)),
            *(len(str(row[index])) for row in rows),
        )
        for index, column in enumerate(columns)
    ]

    header = " | ".join(
        str(column).ljust(widths[index])
        for index, column in enumerate(columns)
    )

    print(header)
    print("-+-".join("-" * width for width in widths))

    for row in rows:
        print(
            " | ".join(
                str(value).ljust(widths[index])
                for index, value in enumerate(row)
            )
        )


def execute_and_print(
    connection: sqlite3.Connection,
    title: str,
    query: str,
) -> list[tuple]:
    cursor = connection.execute(query)
    rows = cursor.fetchall()
    print_rows(title, [description[0] for description in cursor.description], rows)
    return rows


# ============================================================================
# 4. JOIN KEYS
# ============================================================================

def demonstrate_join_keys(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("2. JOIN KEYS")
    print("=" * 78)

    print(
        """
A join key establishes how rows from two tables correspond.

For employees and departments:

    employees.department_id = departments.department_id

The department_id in employees is a foreign key.
The department_id in departments is the primary key.

A key does not have to be a primary key on both sides. A common
one-to-many relationship has a unique key on one side and repeated
foreign-key values on the other side.
"""
    )

    execute_and_print(
        connection,
        "Employees and their department identifiers",
        """
        SELECT employee_id, employee_name, department_id
        FROM employees
        ORDER BY employee_id
        """,
    )


# ============================================================================
# 5. INNER JOIN
# ============================================================================

def demonstrate_inner_join(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("3. INNER JOIN")
    print("=" * 78)

    print(
        """
INNER JOIN returns only rows satisfying the join predicate.

Conceptually:

    left rows ∩ right rows

An employee whose department_id is NULL has no matching department and
therefore disappears from the INNER JOIN result.
"""
    )

    execute_and_print(
        connection,
        "INNER JOIN: employees with matching departments",
        """
        SELECT
            e.employee_id,
            e.employee_name,
            d.department_name
        FROM employees AS e
        INNER JOIN departments AS d
            ON e.department_id = d.department_id
        ORDER BY e.employee_id
        """,
    )

    # INNER JOIN and JOIN are equivalent when no other join modifier exists.
    execute_and_print(
        connection,
        "JOIN is shorthand for INNER JOIN",
        """
        SELECT e.employee_name, d.department_name
        FROM employees AS e
        JOIN departments AS d
            ON e.department_id = d.department_id
        ORDER BY e.employee_id
        """,
    )


# ============================================================================
# 6. LEFT JOIN
# ============================================================================

def demonstrate_left_join(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("4. LEFT JOIN")
    print("=" * 78)

    print(
        """
LEFT JOIN preserves every row from the left table.

When no right-side match exists, columns belonging to the right table
become NULL.

This makes LEFT JOIN useful for questions such as:

    Which employees exist, including employees without a department?

It is also useful for finding unmatched rows.
"""
    )

    execute_and_print(
        connection,
        "LEFT JOIN: every employee, including those without departments",
        """
        SELECT
            e.employee_id,
            e.employee_name,
            d.department_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
        ORDER BY e.employee_id
        """,
    )

    execute_and_print(
        connection,
        "LEFT JOIN used as an unmatched-row detector",
        """
        SELECT
            e.employee_id,
            e.employee_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE d.department_id IS NULL
        ORDER BY e.employee_id
        """,
    )


# ============================================================================
# 7. RIGHT JOIN
# ============================================================================

def demonstrate_right_join(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("5. RIGHT JOIN")
    print("=" * 78)

    print(
        """
RIGHT JOIN preserves every row from the right table.

SQLite versions that support RIGHT JOIN can execute it directly.
For maximum portability across SQLite installations, the equivalent
result can be obtained by reversing the table order and using LEFT JOIN.

The following demonstration intentionally uses the portable form:

    departments LEFT JOIN employees

This is equivalent to:

    employees RIGHT JOIN departments
"""
    )

    execute_and_print(
        connection,
        "RIGHT JOIN equivalent: all departments",
        """
        SELECT
            d.department_id,
            d.department_name,
            e.employee_name
        FROM departments AS d
        LEFT JOIN employees AS e
            ON d.department_id = e.department_id
        ORDER BY d.department_id, e.employee_id
        """,
    )


# ============================================================================
# 8. FULL OUTER JOIN
# ============================================================================

def demonstrate_full_outer_join(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("6. FULL OUTER JOIN")
    print("=" * 78)

    print(
        """
FULL OUTER JOIN preserves matched rows plus unmatched rows from both sides.

SQLite installations may differ in native FULL OUTER JOIN support.
A portable construction is:

    left-to-right LEFT JOIN
    UNION ALL
    right-only rows

The second branch is restricted to right-side rows with no left match.
"""
    )

    execute_and_print(
        connection,
        "FULL OUTER JOIN equivalent using UNION ALL",
        """
        SELECT
            d.department_id,
            d.department_name,
            e.employee_name
        FROM departments AS d
        LEFT JOIN employees AS e
            ON d.department_id = e.department_id

        UNION ALL

        SELECT
            d.department_id,
            d.department_name,
            e.employee_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE d.department_id IS NULL

        ORDER BY department_id, department_name, employee_name
        """,
    )


# ============================================================================
# 9. JOIN TYPE COMPARISON
# ============================================================================

def demonstrate_join_comparison(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("7. JOIN TYPE COMPARISON")
    print("=" * 78)

    queries = {
        "INNER JOIN count": """
            SELECT COUNT(*)
            FROM employees e
            INNER JOIN departments d
                ON e.department_id = d.department_id
        """,
        "LEFT JOIN count": """
            SELECT COUNT(*)
            FROM employees e
            LEFT JOIN departments d
                ON e.department_id = d.department_id
        """,
        "Departments count": """
            SELECT COUNT(*)
            FROM departments
        """,
    }

    for label, query in queries.items():
        print(f"{label:25}: {connection.execute(query).fetchone()[0]}")

    print(
        """
Expected reasoning:

    INNER JOIN removes unmatched employees.
    LEFT JOIN keeps all employees.
    The number of rows after a join is not necessarily the number of
    rows in either input table because one-to-many matches can multiply rows.
"""
    )


# ============================================================================
# 10. ONE-TO-MANY RELATIONSHIPS
# ============================================================================

def demonstrate_one_to_many(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("8. ONE-TO-MANY RELATIONSHIP")
    print("=" * 78)

    print(
        """
One department can contain many employees.

For example:

    Engineering -> Asha
                  Ravi

When a department row matches two employee rows, the department data
appears twice in the result. This is expected relational behavior.
"""
    )

    execute_and_print(
        connection,
        "Departments joined to employees",
        """
        SELECT
            d.department_name,
            e.employee_name
        FROM departments AS d
        LEFT JOIN employees AS e
            ON d.department_id = e.department_id
        ORDER BY d.department_id, e.employee_id
        """,
    )


# ============================================================================
# 11. MANY-TO-MANY RELATIONSHIPS
# ============================================================================

def demonstrate_many_to_many(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("9. MANY-TO-MANY RELATIONSHIP")
    print("=" * 78)

    print(
        """
Employees and projects have a many-to-many relationship.

An employee can work on multiple projects.
A project can contain multiple employees.

The junction table employee_projects resolves the relationship.

The join path is:

    employees
        |
        | employee_id
        v
    employee_projects
        |
        | project_id
        v
    projects
"""
    )

    execute_and_print(
        connection,
        "Employees and projects",
        """
        SELECT
            e.employee_name,
            p.project_name,
            ep.role
        FROM employees AS e
        INNER JOIN employee_projects AS ep
            ON e.employee_id = ep.employee_id
        INNER JOIN projects AS p
            ON ep.project_id = p.project_id
        ORDER BY e.employee_id, p.project_id
        """,
    )


# ============================================================================
# 12. COMPOSITE JOIN KEYS
# ============================================================================

def demonstrate_composite_keys(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("10. COMPOSITE JOIN KEYS")
    print("=" * 78)

    print(
        """
A composite key contains multiple columns.

The regional sales tables use:

    (region, product)

Matching only region would be incorrect because different products
within the same region are separate business records.

Correct predicate:

    sales.region = targets.region
    AND sales.product = targets.product
"""
    )

    execute_and_print(
        connection,
        "Correct composite-key INNER JOIN",
        """
        SELECT
            s.region,
            s.product,
            s.amount,
            t.target
        FROM regional_sales AS s
        INNER JOIN regional_targets AS t
            ON s.region = t.region
           AND s.product = t.product
        ORDER BY s.region, s.product
        """,
    )

    execute_and_print(
        connection,
        "Composite-key LEFT JOIN with variance",
        """
        SELECT
            s.region,
            s.product,
            s.amount,
            t.target,
            CASE
                WHEN t.target IS NULL THEN NULL
                ELSE s.amount - t.target
            END AS variance
        FROM regional_sales AS s
        LEFT JOIN regional_targets AS t
            ON s.region = t.region
           AND s.product = t.product
        ORDER BY s.region, s.product
        """,
    )


# ============================================================================
# 13. JOIN CONDITIONS AND FILTER CONDITIONS
# ============================================================================

def demonstrate_on_vs_where(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("11. ON VS WHERE WITH OUTER JOINS")
    print("=" * 78)

    print(
        """
For an outer join, moving a condition between ON and WHERE can change
the result.

Condition in ON:
    Controls which right-side rows can match while preserving left rows.

Condition in WHERE:
    Filters the completed result.

This distinction is one of the most common sources of accidental
LEFT JOIN -> INNER JOIN behavior.
"""
    )

    execute_and_print(
        connection,
        "Filter inside ON: all employees remain",
        """
        SELECT
            e.employee_name,
            d.department_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
           AND d.department_id = 10
        ORDER BY e.employee_id
        """,
    )

    execute_and_print(
        connection,
        "Filter inside WHERE: unmatched rows are removed",
        """
        SELECT
            e.employee_name,
            d.department_name
        FROM employees AS e
        LEFT JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE d.department_id = 10
        ORDER BY e.employee_id
        """,
    )


# ============================================================================
# 14. NULL SEMANTICS
# ============================================================================

def demonstrate_null_behavior(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("12. NULL BEHAVIOR")
    print("=" * 78)

    print(
        """
NULL means an absent/unknown value.

Important rules:

    NULL = NULL
        does not evaluate to TRUE.

Use:

    IS NULL
    IS NOT NULL

Do not use:

    = NULL
    <> NULL

An unmatched side of an outer join is represented using NULLs.
"""
    )

    execute_and_print(
        connection,
        "Employees whose department_id is NULL",
        """
        SELECT employee_id, employee_name
        FROM employees
        WHERE department_id IS NULL
        """,
    )

    execute_and_print(
        connection,
        "Incorrect-looking NULL comparison",
        """
        SELECT employee_id, employee_name
        FROM employees
        WHERE department_id = NULL
        """,
    )


# ============================================================================
# 15. DUPLICATE JOIN KEYS
# ============================================================================

def demonstrate_duplicate_keys(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("13. DUPLICATE JOIN KEYS AND ROW MULTIPLICATION")
    print("=" * 78)

    connection.execute(
        "CREATE TABLE employee_aliases (employee_id INTEGER, alias TEXT)"
    )

    connection.executemany(
        "INSERT INTO employee_aliases VALUES (?, ?)",
        [
            (1, "Asha P."),
            (1, "Architect Asha"),
            (2, "Ravi K."),
        ],
    )

    execute_and_print(
        connection,
        "One employee can match multiple alias rows",
        """
        SELECT
            e.employee_name,
            a.alias
        FROM employees AS e
        LEFT JOIN employee_aliases AS a
            ON e.employee_id = a.employee_id
        WHERE e.employee_id IN (1, 2)
        ORDER BY e.employee_id, a.alias
        """,
    )

    print(
        """
If one left row matches N right rows, that left row can produce N result rows.

This is not automatically a bug. It becomes a bug when the query author
expected one result row per employee but joined to a non-unique relation.
"""
    )


# ============================================================================
# 16. SEMI-JOIN AND ANTI-JOIN PATTERNS
# ============================================================================

def demonstrate_semi_and_anti_joins(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("14. SEMI-JOIN AND ANTI-JOIN PATTERNS")
    print("=" * 78)

    print(
        """
A semi-join asks:

    Which employees have at least one project?

EXISTS is often clearer than joining when only existence matters.

An anti-join asks:

    Which employees have no projects?

NOT EXISTS is a robust pattern for this purpose.
"""
    )

    execute_and_print(
        connection,
        "Semi-join using EXISTS",
        """
        SELECT
            e.employee_id,
            e.employee_name
        FROM employees AS e
        WHERE EXISTS (
            SELECT 1
            FROM employee_projects AS ep
            WHERE ep.employee_id = e.employee_id
        )
        ORDER BY e.employee_id
        """,
    )

    execute_and_print(
        connection,
        "Anti-join using NOT EXISTS",
        """
        SELECT
            e.employee_id,
            e.employee_name
        FROM employees AS e
        WHERE NOT EXISTS (
            SELECT 1
            FROM employee_projects AS ep
            WHERE ep.employee_id = e.employee_id
        )
        ORDER BY e.employee_id
        """,
    )


# ============================================================================
# 17. SELF JOIN
# ============================================================================

def demonstrate_self_join(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("15. SELF JOIN")
    print("=" * 78)

    print(
        """
A self join joins a table to itself.

The employees table contains manager_id, which refers back to
employees.employee_id.

Aliases distinguish the two logical roles:

    employee
    manager
"""
    )

    execute_and_print(
        connection,
        "Employees and their managers",
        """
        SELECT
            employee.employee_name AS employee,
            manager.employee_name AS manager
        FROM employees AS employee
        LEFT JOIN employees AS manager
            ON employee.manager_id = manager.employee_id
        ORDER BY employee.employee_id
        """,
    )


# ============================================================================
# 18. CROSS JOIN
# ============================================================================

def demonstrate_cross_join(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("16. CROSS JOIN")
    print("=" * 78)

    print(
        """
CROSS JOIN produces the Cartesian product.

If table A has m rows and table B has n rows:

    result rows = m * n

It is useful for intentionally generating combinations, but an accidental
missing join predicate can create a huge Cartesian product.
"""
    )

    execute_and_print(
        connection,
        "Intentional small Cartesian product",
        """
        SELECT
            d.department_name,
            p.project_name
        FROM departments AS d
        CROSS JOIN projects AS p
        WHERE d.department_id IN (10, 20)
        ORDER BY d.department_id, p.project_id
        """,
    )


# ============================================================================
# 19. AGGREGATION AFTER JOIN
# ============================================================================

def demonstrate_aggregation(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("17. JOIN + GROUP BY + AGGREGATION")
    print("=" * 78)

    execute_and_print(
        connection,
        "Employee count by department",
        """
        SELECT
            d.department_name,
            COUNT(e.employee_id) AS employee_count,
            COALESCE(AVG(e.salary), 0) AS average_salary
        FROM departments AS d
        LEFT JOIN employees AS e
            ON d.department_id = e.department_id
        GROUP BY
            d.department_id,
            d.department_name
        ORDER BY d.department_id
        """,
    )

    print(
        """
COUNT(e.employee_id) counts matched employees because employee_id is
NULL for an unmatched LEFT JOIN row.

COUNT(*) would count the preserved department row itself, producing
different semantics for departments with zero employees.
"""
    )


# ============================================================================
# 20. JOIN WITH MULTIPLE CONDITIONS
# ============================================================================

def demonstrate_multiple_join_conditions(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("18. MULTIPLE JOIN CONDITIONS")
    print("=" * 78)

    execute_and_print(
        connection,
        "Composite matching plus a business rule",
        """
        SELECT
            s.region,
            s.product,
            s.amount,
            t.target
        FROM regional_sales AS s
        LEFT JOIN regional_targets AS t
            ON s.region = t.region
           AND s.product = t.product
           AND t.target > 0
        ORDER BY s.region, s.product
        """,
    )


# ============================================================================
# 21. QUERY PLAN
# ============================================================================

def demonstrate_query_plan(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("19. PERFORMANCE AND QUERY PLANS")
    print("=" * 78)

    print(
        """
Join performance depends on factors such as:

    - number of rows
    - selectivity of predicates
    - available indexes
    - uniqueness of join keys
    - statistics
    - join order
    - database optimizer
    - memory and disk behavior

An index on a frequently used join key can reduce the work required to
locate matching rows.

EXPLAIN QUERY PLAN reveals the optimizer's chosen strategy in SQLite.
"""
    )

    connection.execute(
        "CREATE INDEX idx_employees_department_id "
        "ON employees(department_id)"
    )

    rows = connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT e.employee_name, d.department_name
        FROM employees AS e
        JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE d.department_id = 10
        """
    ).fetchall()

    for row in rows:
        print(row)


# ============================================================================
# 22. PRACTICAL DEBUGGING CHECKLIST
# ============================================================================

def demonstrate_debugging_checklist() -> None:
    print("\n" + "=" * 78)
    print("20. JOIN DEBUGGING CHECKLIST")
    print("=" * 78)

    checklist = [
        "1. Identify the intended grain: one row per what?",
        "2. Identify the join key on each side.",
        "3. Check whether each key is unique.",
        "4. Confirm data types are compatible.",
        "5. Test the join with a small SELECT.",
        "6. Compare row counts before and after the join.",
        "7. Look for duplicate matches.",
        "8. Check NULL values.",
        "9. Verify ON conditions.",
        "10. Check whether WHERE accidentally removes outer-join rows.",
        "11. Inspect the query plan for large datasets.",
        "12. Add indexes when justified by workload and query patterns.",
    ]

    for item in checklist:
        print(item)


# ============================================================================
# 23. VALIDATION TESTS
# ============================================================================

def run_validation_tests(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("21. AUTOMATED VALIDATION")
    print("=" * 78)

    inner_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM employees e
        INNER JOIN departments d
            ON e.department_id = d.department_id
        """
    ).fetchone()[0]

    left_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM employees e
        LEFT JOIN departments d
            ON e.department_id = d.department_id
        """
    ).fetchone()[0]

    null_department_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM employees
        WHERE department_id IS NULL
        """
    ).fetchone()[0]

    assert inner_count == 5
    assert left_count == 6
    assert null_department_count == 1

    employee_project_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM employees e
        JOIN employee_projects ep
            ON e.employee_id = ep.employee_id
        """
    ).fetchone()[0]

    assert employee_project_count == 5

    print("All validation tests passed.")


# ============================================================================
# 24. INTERACTIVE EXAMPLE
# ============================================================================

def parameterized_join_example(connection: sqlite3.Connection) -> None:
    print("\n" + "=" * 78)
    print("22. PARAMETERIZED JOIN QUERY")
    print("=" * 78)

    department_id = 10

    # Parameters should be passed separately rather than concatenated into SQL.
    # This avoids SQL injection and handles escaping correctly.
    cursor = connection.execute(
        """
        SELECT
            e.employee_name,
            d.department_name,
            e.salary
        FROM employees AS e
        INNER JOIN departments AS d
            ON e.department_id = d.department_id
        WHERE d.department_id = ?
        ORDER BY e.employee_name
        """,
        (department_id,),
    )

    print_rows(
        "Employees in the requested department",
        [description[0] for description in cursor.description],
        cursor.fetchall(),
    )


# ============================================================================
# 25. ADVANCED RELATIONAL REASONING
# ============================================================================

def explain_advanced_reasoning() -> None:
    print("\n" + "=" * 78)
    print("23. ADVANCED JOIN REASONING")
    print("=" * 78)

    print(
        """
Important distinctions:

1. Join predicate versus filter predicate
   A join predicate determines row correspondence.
   A filter predicate determines which final rows remain.

2. Key uniqueness versus key validity
   A foreign key can be valid without being unique.
   Repeated foreign keys naturally produce one-to-many results.

3. INNER JOIN versus LEFT JOIN
   INNER JOIN answers "where there is a match".
   LEFT JOIN answers "keep everything from the left, whether matched or not".

4. RIGHT JOIN versus reversed LEFT JOIN
   RIGHT JOIN can usually be expressed by reversing table order and
   applying LEFT JOIN.

5. FULL OUTER JOIN
   It preserves unmatched rows on both sides and therefore exposes
   records that exist in only one relation.

6. NULL and missing matches
   NULL values generated by an outer join are different from stored
   NULL values conceptually, even though SQL represents both as NULL.

7. Join explosion
   If multiple rows on each side share a key, the result can grow
   multiplicatively.

8. Relational grain
   Before writing a join, determine what one result row represents.
   This prevents many accidental aggregation and duplication errors.

9. Indexing
   Indexes can accelerate matching but have storage and write-maintenance
   costs. An index is not automatically beneficial for every column.

10. Security
    Never construct SQL by concatenating untrusted values.
    Use parameterized queries.

11. Correctness before optimization
    A fast incorrect join is still incorrect.
    Establish the intended relationships and result grain first.

12. Optimizer behavior
    SQL describes the desired result, while the database optimizer chooses
    an execution strategy. Different database engines may choose different
    join algorithms such as nested-loop, hash join, or merge join.
"""
    )


# ============================================================================
# 26. MAIN
# ============================================================================

def main() -> None:
    explain_fundamentals()

    connection = create_database()

    try:
        demonstrate_join_keys(connection)
        demonstrate_inner_join(connection)
        demonstrate_left_join(connection)
        demonstrate_right_join(connection)
        demonstrate_full_outer_join(connection)
        demonstrate_join_comparison(connection)
        demonstrate_one_to_many(connection)
        demonstrate_many_to_many(connection)
        demonstrate_composite_keys(connection)
        demonstrate_on_vs_where(connection)
        demonstrate_null_behavior(connection)
        demonstrate_duplicate_keys(connection)
        demonstrate_semi_and_anti_joins(connection)
        demonstrate_self_join(connection)
        demonstrate_cross_join(connection)
        demonstrate_aggregation(connection)
        demonstrate_multiple_join_conditions(connection)
        demonstrate_query_plan(connection)
        demonstrate_debugging_checklist()
        parameterized_join_example(connection)
        explain_advanced_reasoning()
        run_validation_tests(connection)

        print("\n" + "=" * 78)
        print("STUDY SCRIPT COMPLETED SUCCESSFULLY")
        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
