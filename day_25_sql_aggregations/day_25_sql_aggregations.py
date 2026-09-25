"""
SQL Aggregations: COUNT, SUM, AVG, MIN, MAX, NULL Handling, and Aggregate Expressions

This standalone study file uses Python's built-in sqlite3 module to demonstrate
SQL aggregation from beginner to advanced level.

The examples intentionally use NULL values because NULL handling is one of the
most important sources of mistakes in SQL aggregation.
"""

import sqlite3
from decimal import Decimal
from statistics import mean


def print_title(title):
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def print_rows(cursor):
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    print(" | ".join(columns))
    print("-" * max(20, len(" | ".join(columns)) + 3))

    for row in rows:
        print(" | ".join("NULL" if value is None else str(value) for value in row))


def execute_and_print(connection, sql, parameters=()):
    cursor = connection.execute(sql, parameters)
    print_rows(cursor)


def scalar(connection, sql, parameters=()):
    return connection.execute(sql, parameters).fetchone()[0]


def create_database():
    connection = sqlite3.connect(":memory:")

    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL,
            bonus REAL,
            performance_score REAL
        );

        INSERT INTO employees
            (employee_id, employee_name, department, salary, bonus, performance_score)
        VALUES
            (1, 'Asha',   'Engineering', 90000, 10000, 92),
            (2, 'Ravi',   'Engineering', 85000, NULL,  88),
            (3, 'Meera',  'Engineering', NULL,  8000,  95),
            (4, 'Kabir',  'Sales',        70000, 7000, 81),
            (5, 'Nisha',  'Sales',        72000, NULL,  79),
            (6, 'Arjun',  'Sales',        NULL,  5000, NULL),
            (7, 'Isha',   'HR',           65000, 4000, 91),
            (8, 'Vikram', 'HR',           62000, NULL, 85),
            (9, 'Tara',   'Research',     NULL, NULL, NULL);

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER,
            unit_price REAL,
            discount REAL,
            order_status TEXT
        );

        INSERT INTO orders
            (order_id, customer, category, quantity, unit_price, discount, order_status)
        VALUES
            (101, 'Alice', 'Laptop',  2, 80000, 0.10, 'completed'),
            (102, 'Bob',   'Phone',   3, 30000, NULL, 'completed'),
            (103, 'Alice', 'Monitor', 1, 20000, 0.05, 'completed'),
            (104, 'Cara',  'Phone',   2, NULL,  0.10, 'pending'),
            (105, 'Bob',   'Laptop',  1, 80000, NULL, 'completed'),
            (106, 'Cara',  'Tablet',  4, 25000, 0.15, 'completed'),
            (107, 'Alice', 'Tablet',  NULL, 25000, 0.05, 'cancelled');
        """
    )

    return connection


def beginner_count_examples(connection):
    print_title("1. COUNT: Counting Rows and Values")

    print("COUNT(*) counts rows, including rows containing NULL values.")
    execute_and_print(
        connection,
        """
        SELECT COUNT(*) AS total_employees
        FROM employees;
        """,
    )

    print("\nCOUNT(column) counts only non-NULL values in that column.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS all_rows,
            COUNT(salary) AS employees_with_salary,
            COUNT(bonus) AS employees_with_bonus,
            COUNT(performance_score) AS employees_with_score
        FROM employees;
        """,
    )

    print("\nCOUNT(DISTINCT column) counts distinct non-NULL values.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(DISTINCT department) AS distinct_departments
        FROM employees;
        """,
    )

    print("\nCounting NULL and non-NULL values explicitly.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS total,
            COUNT(salary) AS salary_present,
            COUNT(*) - COUNT(salary) AS salary_missing
        FROM employees;
        """,
    )


def sum_examples(connection):
    print_title("2. SUM: Adding Numeric Values")

    print("SUM ignores NULL values.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(salary) AS total_salary,
            SUM(bonus) AS total_bonus
        FROM employees;
        """,
    )

    print("\nSUM over an expression.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(salary + COALESCE(bonus, 0)) AS total_compensation
        FROM employees;
        """,
    )

    print("\nConditional aggregation using CASE.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(CASE WHEN department = 'Engineering' THEN 1 ELSE 0 END)
                AS engineering_count,
            SUM(CASE WHEN salary >= 80000 THEN 1 ELSE 0 END)
                AS high_salary_count
        FROM employees;
        """,
    )

    print("\nSUM returns NULL when there are no non-NULL input values.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(performance_score) AS score_sum_for_impossible_condition
        FROM employees
        WHERE department = 'DoesNotExist';
        """,
    )

    print("\nCOALESCE can convert a NULL aggregate result into zero.")
    execute_and_print(
        connection,
        """
        SELECT
            COALESCE(SUM(performance_score), 0) AS safe_sum
        FROM employees
        WHERE department = 'DoesNotExist';
        """,
    )


def average_examples(connection):
    print_title("3. AVG: Calculating Averages")

    print("AVG ignores NULL values and averages only non-NULL inputs.")
    execute_and_print(
        connection,
        """
        SELECT
            AVG(salary) AS average_salary,
            AVG(performance_score) AS average_score
        FROM employees;
        """,
    )

    print("\nAVG is conceptually SUM(value) / COUNT(value).")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(salary) AS salary_sum,
            COUNT(salary) AS salary_count,
            SUM(salary) / COUNT(salary) AS calculated_average,
            AVG(salary) AS built_in_average
        FROM employees;
        """,
    )

    print("\nAVG does not mean SUM(value) / COUNT(*).")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS rows,
            COUNT(salary) AS salary_values,
            AVG(salary) AS correct_average,
            SUM(salary) / COUNT(*) AS incorrect_if_nulls_exist
        FROM employees;
        """,
    )

    print("\nAverage salary by department.")
    execute_and_print(
        connection,
        """
        SELECT
            department,
            COUNT(*) AS employee_rows,
            COUNT(salary) AS salary_values,
            AVG(salary) AS average_salary
        FROM employees
        GROUP BY department
        ORDER BY department;
        """,
    )


def min_max_examples(connection):
    print_title("4. MIN and MAX")

    print("MIN and MAX ignore NULL values when at least one non-NULL value exists.")
    execute_and_print(
        connection,
        """
        SELECT
            MIN(salary) AS minimum_salary,
            MAX(salary) AS maximum_salary,
            MIN(performance_score) AS minimum_score,
            MAX(performance_score) AS maximum_score
        FROM employees;
        """,
    )

    print("\nMIN and MAX can operate on dates and text too, subject to data type rules.")
    execute_and_print(
        connection,
        """
        SELECT
            MIN(employee_name) AS alphabetically_first_name,
            MAX(employee_name) AS alphabetically_last_name
        FROM employees;
        """,
    )

    print("\nAggregate values grouped by department.")
    execute_and_print(
        connection,
        """
        SELECT
            department,
            MIN(salary) AS minimum_salary,
            MAX(salary) AS maximum_salary
        FROM employees
        GROUP BY department
        ORDER BY department;
        """,
    )


def group_by_examples(connection):
    print_title("5. GROUP BY and Aggregation")

    print("GROUP BY divides rows into groups before aggregate functions operate.")
    execute_and_print(
        connection,
        """
        SELECT
            department,
            COUNT(*) AS employee_count,
            SUM(COALESCE(salary, 0)) AS salary_sum,
            AVG(salary) AS average_salary,
            MIN(salary) AS minimum_salary,
            MAX(salary) AS maximum_salary
        FROM employees
        GROUP BY department
        ORDER BY department;
        """,
    )

    print("\nMultiple grouping columns.")
    execute_and_print(
        connection,
        """
        SELECT
            department,
            CASE
                WHEN salary >= 80000 THEN 'High'
                WHEN salary IS NULL THEN 'Unknown'
                ELSE 'Standard'
            END AS salary_band,
            COUNT(*) AS employee_count
        FROM employees
        GROUP BY
            department,
            CASE
                WHEN salary >= 80000 THEN 'High'
                WHEN salary IS NULL THEN 'Unknown'
                ELSE 'Standard'
            END
        ORDER BY department, salary_band;
        """,
    )


def having_examples(connection):
    print_title("6. WHERE vs HAVING")

    print(
        "WHERE filters individual rows before grouping; "
        "HAVING filters groups after aggregation."
    )

    execute_and_print(
        connection,
        """
        SELECT
            department,
            COUNT(*) AS employee_count,
            AVG(salary) AS average_salary
        FROM employees
        WHERE department <> 'HR'
        GROUP BY department
        HAVING COUNT(*) >= 2
        ORDER BY department;
        """,
    )

    print("\nHAVING can filter on aggregate expressions.")
    execute_and_print(
        connection,
        """
        SELECT
            department,
            AVG(salary) AS average_salary
        FROM employees
        GROUP BY department
        HAVING AVG(salary) >= 70000
        ORDER BY average_salary DESC;
        """,
    )


def distinct_and_duplicates(connection):
    print_title("7. DISTINCT with Aggregates")

    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS rows,
            COUNT(customer) AS customer_values,
            COUNT(DISTINCT customer) AS unique_customers
        FROM orders;
        """,
    )

    print("\nCOUNT(DISTINCT ...) is different from COUNT(...).")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(category) AS category_values,
            COUNT(DISTINCT category) AS unique_categories
        FROM orders;
        """,
    )


def aggregate_expressions(connection):
    print_title("8. Aggregate Expressions")

    print("An aggregate can operate on a calculated expression for every row.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(quantity * unit_price) AS gross_value
        FROM orders;
        """,
    )

    print("\nApplying discounts with COALESCE.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(
                quantity * unit_price *
                (1 - COALESCE(discount, 0))
            ) AS net_value
        FROM orders
        WHERE order_status = 'completed';
        """,
    )

    print("\nAVG of a row-level expression.")
    execute_and_print(
        connection,
        """
        SELECT
            AVG(
                quantity * unit_price *
                (1 - COALESCE(discount, 0))
            ) AS average_order_value
        FROM orders
        WHERE order_status = 'completed';
        """,
    )

    print("\nDifferent NULL strategies produce different meanings.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(quantity * unit_price) AS natural_sum,
            SUM(
                COALESCE(quantity, 0) *
                COALESCE(unit_price, 0)
            ) AS null_as_zero_sum
        FROM orders;
        """,
    )


def null_semantics(connection):
    print_title("9. NULL Handling")

    print("NULL means unknown or missing; it is not the same as zero or an empty string.")

    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS total,
            COUNT(bonus) AS known_bonus,
            SUM(bonus) AS sum_bonus,
            AVG(bonus) AS average_bonus,
            MIN(bonus) AS minimum_bonus,
            MAX(bonus) AS maximum_bonus
        FROM employees;
        """,
    )

    print("\nUse IS NULL and IS NOT NULL, not = NULL.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS employees_without_bonus
        FROM employees
        WHERE bonus IS NULL;
        """,
    )

    print("\nCOALESCE substitutes a fallback value.")
    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            bonus,
            COALESCE(bonus, 0) AS bonus_for_calculation
        FROM employees
        ORDER BY employee_id;
        """,
    )

    print("\nNULLIF can intentionally produce NULL.")
    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            salary,
            bonus,
            salary / NULLIF(bonus, 0) AS salary_to_bonus_ratio
        FROM employees
        ORDER BY employee_id;
        """,
    )


def conditional_aggregation(connection):
    print_title("10. Conditional Aggregation")

    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS total_employees,
            SUM(CASE WHEN salary >= 80000 THEN 1 ELSE 0 END)
                AS salary_80000_or_more,
            SUM(CASE WHEN salary IS NULL THEN 1 ELSE 0 END)
                AS salary_missing,
            SUM(CASE WHEN bonus IS NULL THEN 1 ELSE 0 END)
                AS bonus_missing
        FROM employees;
        """,
    )

    print("\nConditional sums can create compact business reports.")
    execute_and_print(
        connection,
        """
        SELECT
            department,
            SUM(CASE WHEN performance_score >= 90 THEN 1 ELSE 0 END)
                AS high_performers,
            SUM(CASE WHEN performance_score < 90 THEN 1 ELSE 0 END)
                AS below_90,
            COUNT(performance_score) AS scored_employees
        FROM employees
        GROUP BY department
        ORDER BY department;
        """,
    )


def order_analytics(connection):
    print_title("11. Realistic Order Analytics")

    execute_and_print(
        connection,
        """
        SELECT
            category,
            COUNT(*) AS order_rows,
            COUNT(quantity) AS orders_with_quantity,
            SUM(quantity) AS units_ordered,
            AVG(quantity) AS average_quantity,
            MIN(quantity) AS minimum_quantity,
            MAX(quantity) AS maximum_quantity
        FROM orders
        GROUP BY category
        ORDER BY category;
        """,
    )

    print("\nRevenue report for completed orders.")
    execute_and_print(
        connection,
        """
        SELECT
            category,
            COUNT(*) AS completed_orders,
            SUM(
                quantity * unit_price *
                (1 - COALESCE(discount, 0))
            ) AS net_revenue,
            AVG(
                quantity * unit_price *
                (1 - COALESCE(discount, 0))
            ) AS average_order_value
        FROM orders
        WHERE order_status = 'completed'
        GROUP BY category
        HAVING SUM(
            quantity * unit_price *
            (1 - COALESCE(discount, 0))
        ) > 0
        ORDER BY net_revenue DESC;
        """,
    )


def empty_set_behavior(connection):
    print_title("12. Empty-Set Behavior")

    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS count_rows,
            COUNT(salary) AS count_salary,
            SUM(salary) AS sum_salary,
            AVG(salary) AS avg_salary,
            MIN(salary) AS min_salary,
            MAX(salary) AS max_salary
        FROM employees
        WHERE 1 = 0;
        """,
    )

    print(
        "\nImportant distinction: COUNT returns 0 for an empty input, "
        "while SUM, AVG, MIN, and MAX return NULL."
    )


def integer_division_and_types(connection):
    print_title("13. Numeric Types and Aggregate Expressions")

    connection.executescript(
        """
        CREATE TABLE measurements (
            id INTEGER PRIMARY KEY,
            successful INTEGER NOT NULL,
            attempts INTEGER NOT NULL
        );

        INSERT INTO measurements VALUES
            (1, 8, 10),
            (2, 5, 10),
            (3, 9, 10);
        """
    )

    print("Be explicit about numeric intent when calculating ratios.")
    execute_and_print(
        connection,
        """
        SELECT
            SUM(successful) AS successful,
            SUM(attempts) AS attempts,
            CAST(SUM(successful) AS REAL) / NULLIF(SUM(attempts), 0)
                AS success_rate
        FROM measurements;
        """,
    )


def advanced_grouping_patterns(connection):
    print_title("14. Advanced Aggregation Patterns")

    print("Aggregation can be combined with CASE to build segments.")
    execute_and_print(
        connection,
        """
        SELECT
            CASE
                WHEN salary IS NULL THEN 'Unknown'
                WHEN salary < 70000 THEN 'Below 70K'
                WHEN salary < 85000 THEN '70K to 84,999'
                ELSE '85K+'
            END AS salary_segment,
            COUNT(*) AS employees,
            AVG(salary) AS average_salary
        FROM employees
        GROUP BY
            CASE
                WHEN salary IS NULL THEN 'Unknown'
                WHEN salary < 70000 THEN 'Below 70K'
                WHEN salary < 85000 THEN '70K to 84,999'
                ELSE '85K+'
            END
        ORDER BY salary_segment;
        """,
    )

    print("\nA scalar subquery can compare an aggregate to each row.")
    execute_and_print(
        connection,
        """
        SELECT
            employee_name,
            department,
            salary
        FROM employees
        WHERE salary > (
            SELECT AVG(salary)
            FROM employees
        )
        ORDER BY salary DESC;
        """,
    )


def debugging_queries(connection):
    print_title("15. Debugging Aggregation Queries")

    print("When an aggregate result looks wrong, inspect row counts before aggregating.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS rows_after_filter,
            COUNT(salary) AS rows_with_salary
        FROM employees
        WHERE department = 'Engineering';
        """,
    )

    print("\nInspect the underlying rows.")
    execute_and_print(
        connection,
        """
        SELECT
            employee_id,
            employee_name,
            department,
            salary,
            bonus
        FROM employees
        WHERE department = 'Engineering'
        ORDER BY employee_id;
        """,
    )

    print("\nA useful debugging technique is to expose intermediate expressions.")
    execute_and_print(
        connection,
        """
        SELECT
            order_id,
            quantity,
            unit_price,
            discount,
            quantity * unit_price AS gross_value,
            COALESCE(discount, 0) AS normalized_discount,
            quantity * unit_price *
                (1 - COALESCE(discount, 0)) AS net_value
        FROM orders
        ORDER BY order_id;
        """,
    )


def performance_and_design_notes(connection):
    print_title("16. Performance and Production Considerations")

    print("SQLite query plan example:")
    execute_and_print(
        connection,
        """
        EXPLAIN QUERY PLAN
        SELECT
            department,
            COUNT(*),
            AVG(salary)
        FROM employees
        GROUP BY department;
        """,
    )

    print(
        """
Production considerations:
1. Filter unnecessary rows before aggregation when the business meaning allows it.
2. Index columns frequently used in WHERE, JOIN, or GROUP BY operations when justified.
3. Do not add indexes blindly; indexes consume storage and can slow writes.
4. COUNT(*) and COUNT(column) answer different questions.
5. Treat NULL deliberately rather than automatically converting every NULL to zero.
6. Use decimal-capable numeric types for financial systems where exact monetary arithmetic
   is required by the database platform.
7. Validate whether an aggregate represents rows, distinct entities, or weighted values.
8. Be careful with joins because one-to-many joins can multiply rows before aggregation.
9. Test empty groups, NULL-heavy data, duplicate values, and zero denominators.
10. Examine query plans and real workload characteristics before optimizing.
"""
    )


def join_multiplication_demo(connection):
    print_title("17. Join Multiplication: A Major Aggregation Pitfall")

    connection.executescript(
        """
        CREATE TABLE employee_projects (
            employee_id INTEGER,
            project_name TEXT
        );

        INSERT INTO employee_projects VALUES
            (1, 'Atlas'),
            (1, 'Beacon'),
            (2, 'Atlas'),
            (3, 'Cipher');
        """
    )

    print("A join can duplicate employee rows.")
    execute_and_print(
        connection,
        """
        SELECT
            e.employee_name,
            e.salary,
            p.project_name
        FROM employees AS e
        JOIN employee_projects AS p
            ON p.employee_id = e.employee_id
        ORDER BY e.employee_id, p.project_name;
        """,
    )

    print("\nCounting joined rows is not always equivalent to counting employees.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(*) AS joined_rows,
            COUNT(DISTINCT e.employee_id) AS distinct_employees
        FROM employees AS e
        JOIN employee_projects AS p
            ON p.employee_id = e.employee_id;
        """,
    )

    print("\nUse COUNT(DISTINCT ...) when the question concerns unique entities.")
    execute_and_print(
        connection,
        """
        SELECT
            COUNT(DISTINCT e.employee_id) AS employees,
            SUM(e.salary) AS potentially_multiplied_salary
        FROM employees AS e
        JOIN employee_projects AS p
            ON p.employee_id = e.employee_id;
        """,
    )


def python_equivalent_demo():
    print_title("18. Python Perspective: SQL Aggregates as Concepts")

    values = [10, 20, None, 30, None]

    non_null_values = [value for value in values if value is not None]

    print("Input:", values)
    print("COUNT(*) concept:", len(values))
    print("COUNT(value) concept:", len(non_null_values))
    print("SUM(value) concept:", sum(non_null_values))
    print("AVG(value) concept:", mean(non_null_values))
    print("MIN(value) concept:", min(non_null_values))
    print("MAX(value) concept:", max(non_null_values))

    empty_values = []
    print("\nEmpty input:")
    print("COUNT(*) concept:", len(empty_values))
    print("SUM/AVG/MIN/MAX concept:", None)


def mini_validation_tests(connection):
    print_title("19. Automated Validation Tests")

    tests = [
        (
            "COUNT(*) counts every employee",
            scalar(connection, "SELECT COUNT(*) FROM employees") == 9,
        ),
        (
            "COUNT(salary) ignores NULL salary values",
            scalar(connection, "SELECT COUNT(salary) FROM employees") == 7,
        ),
        (
            "COUNT(DISTINCT department) counts four departments",
            scalar(
                connection,
                "SELECT COUNT(DISTINCT department) FROM employees",
            )
            == 4,
        ),
        (
            "MIN salary ignores NULL",
            scalar(connection, "SELECT MIN(salary) FROM employees") == 62000,
        ),
        (
            "MAX salary ignores NULL",
            scalar(connection, "SELECT MAX(salary) FROM employees") == 90000,
        ),
        (
            "SUM over an impossible filter is NULL",
            scalar(
                connection,
                "SELECT SUM(salary) FROM employees WHERE 1 = 0",
            )
            is None,
        ),
    ]

    passed = 0

    for description, result in tests:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {description}")
        passed += int(result)

    print(f"\nPassed {passed}/{len(tests)} tests.")

    if passed != len(tests):
        raise AssertionError("One or more SQL aggregation tests failed.")


def main():
    print_title("SQL AGGREGATIONS: COMPLETE PRACTICAL STUDY")
    print(
        """
Topics covered:
- COUNT(*), COUNT(column), COUNT(DISTINCT column)
- SUM
- AVG
- MIN and MAX
- NULL semantics
- COALESCE and NULLIF
- aggregate expressions
- GROUP BY
- HAVING
- WHERE versus HAVING
- conditional aggregation
- DISTINCT
- empty-set behavior
- numeric ratios
- joins and aggregation
- debugging
- performance and production considerations
- automated validation
"""
    )

    connection = create_database()

    try:
        beginner_count_examples(connection)
        sum_examples(connection)
        average_examples(connection)
        min_max_examples(connection)
        group_by_examples(connection)
        having_examples(connection)
        distinct_and_duplicates(connection)
        aggregate_expressions(connection)
        null_semantics(connection)
        conditional_aggregation(connection)
        order_analytics(connection)
        empty_set_behavior(connection)
        integer_division_and_types(connection)
        advanced_grouping_patterns(connection)
        debugging_queries(connection)
        performance_and_design_notes(connection)
        join_multiplication_demo(connection)
        python_equivalent_demo()
        mini_validation_tests(connection)

        print_title("20. Study Checklist")
        checklist = [
            "I can distinguish COUNT(*) from COUNT(column).",
            "I understand that most aggregate functions ignore NULL inputs.",
            "I understand why AVG uses only non-NULL values.",
            "I can use GROUP BY to aggregate rows by category.",
            "I can use HAVING to filter aggregated groups.",
            "I can build aggregate expressions such as SUM(quantity * price).",
            "I can use COALESCE when a missing value should have a defined fallback.",
            "I can use COUNT(DISTINCT ...) for unique-entity counts.",
            "I can recognize join multiplication before trusting aggregate results.",
            "I can test aggregate behavior with empty and NULL-heavy datasets.",
        ]

        for item in checklist:
            print(f"[ ] {item}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
