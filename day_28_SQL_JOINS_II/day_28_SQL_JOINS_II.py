"""
SQL Joins II
============

Topic:
    Self joins, cross joins, multiple joins, join cardinality, and duplicate
    explosion.

This standalone study script teaches SQL join behavior from fundamentals to
advanced reasoning. It uses Python's standard library only and implements a
small relational engine in Python so the examples remain executable without
an external database.

The demonstrations use:
    - lists of dictionaries as relational tables
    - explicit join algorithms
    - cardinality analysis
    - duplicate detection
    - self joins
    - cross joins
    - multiple joins
    - one-to-one, one-to-many, many-to-many relationships
    - Cartesian products
    - duplicate explosion
    - pre-aggregation
    - semi-joins
    - anti-joins
    - join-order reasoning
    - validation and testing
    - performance measurements
    - production-oriented safeguards

The terminology and behavior are designed to correspond closely to SQL.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations, product
from time import perf_counter
from typing import Any, Callable, Iterable, Sequence


# ============================================================================
# 1. RELATIONAL FUNDAMENTALS
# ============================================================================

Row = dict[str, Any]
Table = list[Row]


def print_title(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def print_rows(rows: Sequence[Row], limit: int = 20) -> None:
    if not rows:
        print("(no rows)")
        return

    shown = list(rows[:limit])
    columns: list[str] = []

    for row in shown:
        for column in row:
            if column not in columns:
                columns.append(column)

    widths = {
        column: max(
            len(column),
            max(len(str(row.get(column, ""))) for row in shown),
        )
        for column in columns
    }

    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in shown:
        print(
            " | ".join(
                str(row.get(column, "")).ljust(widths[column])
                for column in columns
            )
        )

    if len(rows) > limit:
        print(f"... {len(rows) - limit} more row(s)")


def table_count(table: Table) -> int:
    return len(table)


def unique_key_count(table: Table, key: str) -> int:
    return len({row.get(key) for row in table})


def duplicate_key_groups(table: Table, key: str) -> dict[Any, int]:
    counts = Counter(row.get(key) for row in table)
    return {value: count for value, count in counts.items() if count > 1}


def column_names(table: Table) -> list[str]:
    columns: list[str] = []
    for row in table:
        for column in row:
            if column not in columns:
                columns.append(column)
    return columns


# ============================================================================
# 2. SAMPLE DATA
# ============================================================================

employees: Table = [
    {"employee_id": 1, "employee_name": "Asha", "manager_id": 4, "department_id": 10},
    {"employee_id": 2, "employee_name": "Bharat", "manager_id": 4, "department_id": 10},
    {"employee_id": 3, "employee_name": "Chitra", "manager_id": 5, "department_id": 20},
    {"employee_id": 4, "employee_name": "Dev", "manager_id": 6, "department_id": 10},
    {"employee_id": 5, "employee_name": "Esha", "manager_id": 6, "department_id": 20},
    {"employee_id": 6, "employee_name": "Farhan", "manager_id": None, "department_id": 30},
    {"employee_id": 7, "employee_name": "Gita", "manager_id": 4, "department_id": 10},
]

departments: Table = [
    {"department_id": 10, "department_name": "Engineering"},
    {"department_id": 20, "department_name": "Research"},
    {"department_id": 30, "department_name": "Security"},
]

projects: Table = [
    {"project_id": 101, "project_name": "Atlas", "department_id": 10},
    {"project_id": 102, "project_name": "Beacon", "department_id": 10},
    {"project_id": 103, "project_name": "Cipher", "department_id": 20},
    {"project_id": 104, "project_name": "Dragon", "department_id": 30},
]

employee_projects: Table = [
    {"employee_id": 1, "project_id": 101},
    {"employee_id": 1, "project_id": 102},
    {"employee_id": 2, "project_id": 101},
    {"employee_id": 3, "project_id": 103},
    {"employee_id": 4, "project_id": 101},
    {"employee_id": 4, "project_id": 102},
    {"employee_id": 4, "project_id": 104},
    {"employee_id": 5, "project_id": 103},
    {"employee_id": 6, "project_id": 104},
    {"employee_id": 7, "project_id": 102},
]

customers: Table = [
    {"customer_id": 1, "customer_name": "Acme"},
    {"customer_id": 2, "customer_name": "Globex"},
    {"customer_id": 3, "customer_name": "Initech"},
]

orders: Table = [
    {"order_id": 1001, "customer_id": 1, "order_total": 500},
    {"order_id": 1002, "customer_id": 1, "order_total": 300},
    {"order_id": 1003, "customer_id": 2, "order_total": 900},
    {"order_id": 1004, "customer_id": 3, "order_total": 200},
]

order_items: Table = [
    {"order_item_id": 1, "order_id": 1001, "product": "Keyboard", "quantity": 2},
    {"order_item_id": 2, "order_id": 1001, "product": "Mouse", "quantity": 1},
    {"order_item_id": 3, "order_id": 1002, "product": "Monitor", "quantity": 2},
    {"order_item_id": 4, "order_id": 1003, "product": "Laptop", "quantity": 1},
    {"order_item_id": 5, "order_id": 1003, "product": "Mouse", "quantity": 4},
    {"order_item_id": 6, "order_id": 1004, "product": "Keyboard", "quantity": 1},
]

payments: Table = [
    {"payment_id": 1, "order_id": 1001, "payment_method": "Card", "amount": 500},
    {"payment_id": 2, "order_id": 1002, "payment_method": "Card", "amount": 300},
    {"payment_id": 3, "order_id": 1003, "payment_method": "UPI", "amount": 500},
    {"payment_id": 4, "order_id": 1003, "payment_method": "Card", "amount": 400},
    {"payment_id": 5, "order_id": 1004, "payment_method": "UPI", "amount": 200},
]


# ============================================================================
# 3. BASIC JOIN IMPLEMENTATION
# ============================================================================

def combine_rows(
    left: Row,
    right: Row,
    *,
    left_prefix: str = "left",
    right_prefix: str = "right",
) -> Row:
    """
    Combine two rows while preserving both values when column names collide.

    SQL normally requires explicit column qualification such as:
        employees.employee_id
        managers.employee_id

    Prefixing makes the same idea visible in this Python simulation.
    """
    combined: Row = {}

    for key, value in left.items():
        if key in right:
            combined[f"{left_prefix}.{key}"] = value
        else:
            combined[key] = value

    for key, value in right.items():
        if key in left:
            combined[f"{right_prefix}.{key}"] = value
        else:
            combined[key] = value

    return combined


def inner_join(
    left: Table,
    right: Table,
    left_key: str,
    right_key: str,
) -> Table:
    """
    INNER JOIN returns only matching row pairs.

    If a left key occurs m times and a right key occurs n times,
    that key contributes m * n output rows.
    """
    index: dict[Any, list[Row]] = defaultdict(list)

    for right_row in right:
        index[right_row.get(right_key)].append(right_row)

    result: Table = []

    for left_row in left:
        matches = index.get(left_row.get(left_key), [])
        for right_row in matches:
            result.append(combine_rows(left_row, right_row))

    return result


def left_join(
    left: Table,
    right: Table,
    left_key: str,
    right_key: str,
) -> Table:
    """
    LEFT JOIN preserves every row from the left table.

    A non-matching right side is represented by None values for the right
    columns, which corresponds conceptually to SQL NULL.
    """
    index: dict[Any, list[Row]] = defaultdict(list)

    for right_row in right:
        index[right_row.get(right_key)].append(right_row)

    right_columns = column_names(right)
    result: Table = []

    for left_row in left:
        matches = index.get(left_row.get(left_key), [])

        if matches:
            for right_row in matches:
                result.append(combine_rows(left_row, right_row))
        else:
            null_right = {column: None for column in right_columns}
            result.append(combine_rows(left_row, null_right))

    return result


def cross_join(left: Table, right: Table) -> Table:
    """
    CROSS JOIN creates every possible pair.

    For |A| = m and |B| = n:
        |A CROSS JOIN B| = m * n
    """
    return [
        combine_rows(left_row, right_row)
        for left_row, right_row in product(left, right)
    ]


def self_join(
    table: Table,
    left_key: str,
    right_key: str,
    *,
    exclude_same_row: bool = False,
) -> Table:
    """
    Join a table to itself.

    The same physical table appears as two logical roles. For example:
        employees AS e
        employees AS m

    The aliases are conceptually important because employee_id and manager_id
    belong to different roles even though they come from the same table.
    """
    index: dict[Any, list[Row]] = defaultdict(list)

    for row in table:
        index[row.get(right_key)].append(row)

    result: Table = []

    for left_row in table:
        for right_row in index.get(left_row.get(left_key), []):
            if exclude_same_row and left_row is right_row:
                continue
            result.append(
                combine_rows(
                    left_row,
                    right_row,
                    left_prefix="employee",
                    right_prefix="manager",
                )
            )

    return result


# ============================================================================
# 4. INNER JOIN FUNDAMENTALS
# ============================================================================

print_title("1. INNER JOIN: BASIC MATCHING")

employee_department = inner_join(
    employees,
    departments,
    "department_id",
    "department_id",
)

print_rows(employee_department)

print(
    "\nInterpretation: each employee row is paired with every department row "
    "having the same department_id."
)


# ============================================================================
# 5. SELF JOIN
# ============================================================================

print_title("2. SELF JOIN: EMPLOYEE -> MANAGER")

employee_manager = self_join(
    employees,
    "manager_id",
    "employee_id",
)

for row in employee_manager:
    print(
        f"{row['employee.employee_name']} -> "
        f"{row['manager.employee_name']}"
    )

print(
    "\nA self join does not require a second physical table. SQL uses aliases "
    "to give the same table two logical identities."
)


# ============================================================================
# 6. SELF-JOIN EDGE CASES
# ============================================================================

print_title("3. SELF JOIN EDGE CASES")

missing_manager = [
    employee["employee_name"]
    for employee in employees
    if employee["manager_id"] is None
]

print("Employees with no manager:", missing_manager)

manager_ids = {employee["employee_id"] for employee in employees}

invalid_manager_references = [
    employee
    for employee in employees
    if employee["manager_id"] is not None
    and employee["manager_id"] not in manager_ids
]

print("Invalid manager references:", invalid_manager_references)

print(
    "\nImportant SQL behavior: NULL = NULL is not TRUE. "
    "A self join using '=' therefore does not match rows whose join key is NULL."
)


# ============================================================================
# 7. FINDING PAIRS WITH A SELF JOIN
# ============================================================================

print_title("4. SELF JOIN FOR SAME-DEPARTMENT EMPLOYEE PAIRS")

pairs: Table = []

for first, second in combinations(employees, 2):
    if (
        first["department_id"] == second["department_id"]
        and first["employee_id"] < second["employee_id"]
    ):
        pairs.append(
            {
                "employee_a": first["employee_name"],
                "employee_b": second["employee_name"],
                "department_id": first["department_id"],
            }
        )

print_rows(pairs)

print(
    "\nA common SQL pattern is e1.employee_id < e2.employee_id. "
    "That prevents both (A,B) and (B,A), and it prevents (A,A)."
)


# ============================================================================
# 8. CROSS JOIN
# ============================================================================

print_title("5. CROSS JOIN")

small_departments: Table = [
    {"department_id": 10, "department_name": "Engineering"},
    {"department_id": 20, "department_name": "Research"},
]

small_projects: Table = [
    {"project_id": 101, "project_name": "Atlas"},
    {"project_id": 102, "project_name": "Beacon"},
    {"project_id": 103, "project_name": "Cipher"},
]

cross_result = cross_join(small_departments, small_projects)

print_rows(cross_result)
print(
    f"\n{len(small_departments)} departments × "
    f"{len(small_projects)} projects = {len(cross_result)} combinations"
)

print(
    "\nCROSS JOIN has no matching predicate. It is a Cartesian product."
)


# ============================================================================
# 9. CROSS JOIN AND GENERATION OF COMBINATIONS
# ============================================================================

print_title("6. CROSS JOIN AS A PLANNING TOOL")

regions: Table = [
    {"region": "North"},
    {"region": "South"},
]

quarters: Table = [
    {"quarter": "Q1"},
    {"quarter": "Q2"},
    {"quarter": "Q3"},
    {"quarter": "Q4"},
]

planning_grid = cross_join(regions, quarters)
print_rows(planning_grid)

print(
    "\nThis is a legitimate use of a Cartesian product: generating every "
    "region-quarter planning combination."
)


# ============================================================================
# 10. JOIN CARDINALITY
# ============================================================================

print_title("7. JOIN CARDINALITY")

cardinality_examples = {
    "one-to-one": {
        "left": [1, 2, 3],
        "right": [1, 2, 3],
    },
    "one-to-many": {
        "left": [1, 2],
        "right": [1, 1, 2, 2, 2],
    },
    "many-to-many": {
        "left": [1, 1, 2],
        "right": [1, 1, 2, 2],
    },
}

for name, example in cardinality_examples.items():
    left_counts = Counter(example["left"])
    right_counts = Counter(example["right"])

    expected = sum(
        left_counts[key] * right_counts[key]
        for key in left_counts.keys() & right_counts.keys()
    )

    print(
        f"{name:15s}: "
        f"left={len(example['left'])}, "
        f"right={len(example['right'])}, "
        f"matching output={expected}"
    )


def estimate_join_cardinality(
    left: Table,
    right: Table,
    left_key: str,
    right_key: str,
) -> int:
    """
    Exact cardinality for the in-memory tables.

    For every shared key k:
        output(k) = count_left(k) * count_right(k)
    """
    left_counts = Counter(row.get(left_key) for row in left)
    right_counts = Counter(row.get(right_key) for row in right)

    return sum(
        left_counts[key] * right_counts[key]
        for key in left_counts.keys() & right_counts.keys()
    )


print(
    "\nEmployees × departments matching rows:",
    estimate_join_cardinality(
        employees,
        departments,
        "department_id",
        "department_id",
    ),
)


# ============================================================================
# 11. THE m × n RULE
# ============================================================================

print_title("8. THE m × n RULE")

left_duplicates: Table = [
    {"key": "A", "left_value": 1},
    {"key": "A", "left_value": 2},
    {"key": "A", "left_value": 3},
]

right_duplicates: Table = [
    {"key": "A", "right_value": "x"},
    {"key": "A", "right_value": "y"},
    {"key": "A", "right_value": "z"},
    {"key": "A", "right_value": "w"},
]

explosion = inner_join(
    left_duplicates,
    right_duplicates,
    "key",
    "key",
)

print_rows(explosion)
print(
    f"\n3 left rows × 4 right rows = {len(explosion)} joined rows."
)

print(
    "\nThis is not necessarily a database bug. It is the mathematically "
    "correct result when every matching pair is represented."
)


# ============================================================================
# 12. DUPLICATE EXPLOSION
# ============================================================================

print_title("9. DUPLICATE EXPLOSION IN MULTIPLE JOINS")

one_customer_orders = [
    row for row in orders if row["customer_id"] == 1
]

customer_one_items = [
    row
    for row in order_items
    if row["order_id"] in {1001, 1002}
]

customer_one_payments = [
    row
    for row in payments
    if row["order_id"] in {1001, 1002}
]

print("Orders for Acme:", len(one_customer_orders))
print("Items for Acme's orders:", len(customer_one_items))
print("Payments for Acme's orders:", len(customer_one_payments))

print(
    "\nA dangerous pattern is joining several independent one-to-many "
    "tables before aggregating."
)


# ============================================================================
# 13. A PRECISE DUPLICATE-EXPLOSION EXAMPLE
# ============================================================================

print_title("10. 3 × 4 DUPLICATE EXPLOSION")

one_order: Table = [
    {"order_id": 9001, "customer_id": 99}
]

three_items: Table = [
    {"order_id": 9001, "item": "A"},
    {"order_id": 9001, "item": "B"},
    {"order_id": 9001, "item": "C"},
]

four_payments: Table = [
    {"order_id": 9001, "payment": "P1"},
    {"order_id": 9001, "payment": "P2"},
    {"order_id": 9001, "payment": "P3"},
    {"order_id": 9001, "payment": "P4"},
]

order_items_join = inner_join(one_order, three_items, "order_id", "order_id")
order_items_payments = inner_join(
    order_items_join,
    four_payments,
    "right.order_id",
    "order_id",
)

print("Order × items:", len(order_items_join))
print("Order × items × payments:", len(order_items_payments))

print(
    "\nThe single order becomes 3 rows after joining items. "
    "Each of those 3 rows then matches all 4 payments, producing 12 rows."
)


# ============================================================================
# 14. WHY SUMS CAN BECOME WRONG
# ============================================================================

print_title("11. WRONG AGGREGATION AFTER DUPLICATE EXPLOSION")

items_total = sum(row["quantity"] for row in order_items if row["order_id"] == 1003)
payments_total = sum(row["amount"] for row in payments if row["order_id"] == 1003)

print("Actual item quantity for order 1003:", items_total)
print("Actual payment amount for order 1003:", payments_total)

order_1003_items = [
    row for row in order_items if row["order_id"] == 1003
]
order_1003_payments = [
    row for row in payments if row["order_id"] == 1003
]

naive_rows = [
    {
        "order_id": 1003,
        "quantity": item["quantity"],
        "payment_amount": payment["amount"],
    }
    for item in order_1003_items
    for payment in order_1003_payments
]

print("\nRows after directly combining independent child tables:")
print_rows(naive_rows)

naive_quantity = sum(row["quantity"] for row in naive_rows)
naive_payment = sum(row["payment_amount"] for row in naive_rows)

print("Naively summed quantity:", naive_quantity)
print("Naively summed payments:", naive_payment)

print(
    "\nThe child facts are repeated because item rows and payment rows form "
    "independent one-to-many relationships with the same order."
)


# ============================================================================
# 15. SAFE PRE-AGGREGATION
# ============================================================================

print_title("12. SAFE PRE-AGGREGATION")

def aggregate_sum(
    rows: Iterable[Row],
    group_key: str,
    value_key: str,
    output_key: str,
) -> Table:
    totals: defaultdict[Any, float] = defaultdict(float)

    for row in rows:
        value = row.get(value_key)
        if value is not None:
            totals[row.get(group_key)] += value

    return [
        {
            group_key: key,
            output_key: total,
        }
        for key, total in totals.items()
    ]


item_totals_by_order = aggregate_sum(
    order_items,
    "order_id",
    "quantity",
    "total_quantity",
)

payment_totals_by_order = aggregate_sum(
    payments,
    "order_id",
    "amount",
    "total_paid",
)

safe_result = inner_join(
    item_totals_by_order,
    payment_totals_by_order,
    "order_id",
    "order_id",
)

print_rows(safe_result)

print(
    "\nPre-aggregation reduces each one-to-many relationship to one row per "
    "order before combining the independent aggregates."
)


# ============================================================================
# 16. MULTIPLE JOINS
# ============================================================================

print_title("13. MULTIPLE JOINS: EMPLOYEE -> DEPARTMENT -> PROJECT")

employee_project_links = inner_join(
    employees,
    employee_projects,
    "employee_id",
    "employee_id",
)

employee_project_details = inner_join(
    employee_project_links,
    projects,
    "right.project_id",
    "project_id",
)

print_rows(employee_project_details)

print(
    "\nMultiple joins should be analyzed one relationship at a time. "
    "At every step, ask: what does one output row represent?"
)


# ============================================================================
# 17. ROW GRAIN
# ============================================================================

print_title("14. ROW GRAIN")

print(
    """
Row grain means the real-world entity or event represented by one row.

Examples:
    customers       -> one row per customer
    orders          -> one row per order
    order_items     -> one row per order item
    payments        -> one row per payment
    employee_projects -> one row per employee-project relationship

A join changes the grain when it combines relationships with different
multiplicities.
"""
)

print("orders grain:", "one row per order")
print("order_items grain:", "one row per order item")
print("payments grain:", "one row per payment")


# ============================================================================
# 18. CARDINALITY PROFILING
# ============================================================================

print_title("15. CARDINALITY PROFILING")

def profile_key(table: Table, key: str) -> dict[str, Any]:
    counts = Counter(row.get(key) for row in table)
    non_null_values = [value for value in counts if value is not None]

    return {
        "rows": len(table),
        "distinct_values": len(non_null_values),
        "null_count": counts.get(None, 0),
        "duplicate_groups": {
            value: count
            for value, count in counts.items()
            if value is not None and count > 1
        },
        "max_frequency": max(counts.values(), default=0),
    }


for name, table, key in [
    ("employees.department_id", employees, "department_id"),
    ("orders.customer_id", orders, "customer_id"),
    ("order_items.order_id", order_items, "order_id"),
    ("payments.order_id", payments, "order_id"),
]:
    print(f"\n{name}")
    print(profile_key(table, key))


# ============================================================================
# 19. IDENTIFYING UNIQUE KEYS
# ============================================================================

print_title("16. KEY UNIQUENESS")

for table_name, table, key in [
    ("employees", employees, "employee_id"),
    ("departments", departments, "department_id"),
    ("orders", orders, "order_id"),
    ("order_items", order_items, "order_id"),
    ("payments", payments, "order_id"),
]:
    duplicate_groups = duplicate_key_groups(table, key)
    print(
        f"{table_name:15s} {key:15s} "
        f"unique={len(duplicate_groups) == 0} "
        f"duplicate_groups={duplicate_groups}"
    )

print(
    "\nA unique key on the parent side is a major reason a join can be "
    "one-to-many rather than many-to-many."
)


# ============================================================================
# 20. MANY-TO-MANY RELATIONSHIP
# ============================================================================

print_title("17. MANY-TO-MANY RELATIONSHIP")

employees_on_projects = inner_join(
    employees,
    employee_projects,
    "employee_id",
    "employee_id",
)

many_to_many_view = inner_join(
    employees_on_projects,
    projects,
    "right.project_id",
    "project_id",
)

print_rows(many_to_many_view)

print(
    "\nThe employee-project bridge table converts a many-to-many relationship "
    "into two one-to-many relationships:"
)
print("employees -> employee_projects")
print("projects  -> employee_projects")


# ============================================================================
# 21. SEMI-JOIN
# ============================================================================

print_title("18. SEMI-JOIN: EXISTS-LIKE BEHAVIOR")

project_employee_ids = {row["employee_id"] for row in employee_projects}

employees_with_projects = [
    row
    for row in employees
    if row["employee_id"] in project_employee_ids
]

print_rows(employees_with_projects)

print(
    "\nA semi-join asks whether a matching row exists. "
    "It does not multiply the parent row once per matching child."
)


# ============================================================================
# 22. ANTI-JOIN
# ============================================================================

print_title("19. ANTI-JOIN: NOT EXISTS-LIKE BEHAVIOR")

employees_without_projects = [
    row
    for row in employees
    if row["employee_id"] not in project_employee_ids
]

print_rows(employees_without_projects)

print(
    "\nAnti-joins are useful for finding missing relationships. "
    "In SQL, NOT EXISTS is often clearer than trying to simulate the same "
    "logic with an ordinary inner join."
)


# ============================================================================
# 23. LEFT JOIN AND MISSING MATCHES
# ============================================================================

print_title("20. LEFT JOIN: PRESERVING UNMATCHED PARENTS")

all_employees_with_departments = left_join(
    employees,
    departments,
    "department_id",
    "department_id",
)

print_rows(all_employees_with_departments)

print(
    "\nA LEFT JOIN keeps every left-side row even when no matching right-side "
    "row exists."
)


# ============================================================================
# 24. NULL JOIN BEHAVIOR
# ============================================================================

print_title("21. NULL AND JOIN PREDICATES")

null_example_left = [
    {"id": 1, "key": None},
    {"id": 2, "key": "A"},
]

null_example_right = [
    {"id": 10, "key": None},
    {"id": 11, "key": "A"},
]

null_join = inner_join(
    null_example_left,
    null_example_right,
    "key",
    "key",
)

print_rows(null_join)

print(
    "\nThis simulator treats None as a non-match, mirroring ordinary SQL "
    "equality joins where NULL = NULL is not TRUE."
)


# ============================================================================
# 25. JOIN PREDICATE VS FILTER PREDICATE
# ============================================================================

print_title("22. JOIN CONDITION VS FILTER CONDITION")

engineering_employees = [
    row
    for row in employees
    if row["department_id"] == 10
]

engineering_departments = [
    row
    for row in departments
    if row["department_id"] == 10
]

filtered_join = inner_join(
    engineering_employees,
    engineering_departments,
    "department_id",
    "department_id",
)

print_rows(filtered_join)

print(
    "\nFiltering before a join can reduce the number of rows that participate "
    "in the join. The semantic effect must still be checked carefully, "
    "especially with OUTER JOINs."
)


# ============================================================================
# 26. MULTIPLE JOIN CARDINALITY ANALYSIS
# ============================================================================

print_title("23. STEP-BY-STEP MULTIPLE JOIN CARDINALITY")

step_one = inner_join(
    orders,
    order_items,
    "order_id",
    "order_id",
)

step_two = inner_join(
    step_one,
    payments,
    "order_id",
    "order_id",
)

print("Orders:", len(orders))
print("Orders × items:", len(step_one))
print("Orders × items × payments:", len(step_two))

print(
    "\nThe second join uses the order_id repeated in step_one. "
    "Every existing item row can match every payment row for that order."
)


# ============================================================================
# 27. DUPLICATE DIAGNOSTICS
# ============================================================================

print_title("24. DUPLICATE DIAGNOSTICS")

def count_by(rows: Iterable[Row], key: str) -> Counter:
    return Counter(row.get(key) for row in rows)


def report_multiplicity(
    rows: Table,
    key: str,
    *,
    label: str,
) -> None:
    counts = count_by(rows, key)
    print(f"\n{label}")
    for value, count in sorted(counts.items(), key=lambda item: str(item[0])):
        print(f"  {value!r}: {count} row(s)")


report_multiplicity(
    step_one,
    "order_id",
    label="Rows per order after joining items",
)

report_multiplicity(
    step_two,
    "order_id",
    label="Rows per order after joining items and payments",
)


# ============================================================================
# 28. DISTINCT IS NOT A UNIVERSAL FIX
# ============================================================================

print_title("25. WHY DISTINCT IS NOT A UNIVERSAL FIX")

print(
    """
Suppose an incorrect join produces:

    Order 1003 + Item A + Payment P1
    Order 1003 + Item A + Payment P2
    Order 1003 + Item B + Payment P1
    Order 1003 + Item B + Payment P2

SELECT DISTINCT cannot safely reconstruct the intended business fact.

If the selected columns contain payment or item attributes, those rows are
legitimately different.

The real fix is to model the intended relationship and aggregate at the
correct grain before combining independent one-to-many relationships.
"""
)


# ============================================================================
# 29. JOIN ORDER AND SEMANTICS
# ============================================================================

print_title("26. JOIN ORDER")

print(
    """
For inner joins, the optimizer may often reorder operations because inner
join is associative and commutative under appropriate relational conditions.

Conceptually:

    A INNER JOIN B INNER JOIN C

can often be evaluated as:

    (A JOIN B) JOIN C

or:

    A JOIN (B JOIN C)

But outer joins, filters, NULL behavior, and non-equivalent predicates can
make join order semantically significant.

Therefore:
    1. reason about logical semantics first,
    2. inspect cardinality,
    3. inspect the execution plan,
    4. optimize only after correctness is established.
"""
)


# ============================================================================
# 30. SIMPLE NESTED-LOOP VS HASH JOIN
# ============================================================================

print_title("27. JOIN ALGORITHM COMPARISON")

def nested_loop_join(
    left: Table,
    right: Table,
    left_key: str,
    right_key: str,
) -> Table:
    result: Table = []

    for left_row in left:
        for right_row in right:
            if (
                left_row.get(left_key) is not None
                and left_row.get(left_key) == right_row.get(right_key)
            ):
                result.append(combine_rows(left_row, right_row))

    return result


def hash_join(
    left: Table,
    right: Table,
    left_key: str,
    right_key: str,
) -> Table:
    index: dict[Any, list[Row]] = defaultdict(list)

    for right_row in right:
        key = right_row.get(right_key)
        if key is not None:
            index[key].append(right_row)

    result: Table = []

    for left_row in left:
        key = left_row.get(left_key)
        if key is None:
            continue

        for right_row in index.get(key, []):
            result.append(combine_rows(left_row, right_row))

    return result


test_left = [{"key": i, "value": i * 10} for i in range(1000)]
test_right = [{"key": i, "value": i * 20} for i in range(1000)]

start = perf_counter()
nested_result = nested_loop_join(test_left, test_right, "key", "key")
nested_time = perf_counter() - start

start = perf_counter()
hash_result = hash_join(test_left, test_right, "key", "key")
hash_time = perf_counter() - start

print("Nested-loop rows:", len(nested_result))
print("Hash-join rows:", len(hash_result))
print(f"Nested-loop time: {nested_time:.6f}s")
print(f"Hash-join time:   {hash_time:.6f}s")

print(
    "\nA nested-loop equality join has roughly O(N*M) comparison behavior. "
    "A hash join is commonly approximately O(N+M) for building and probing "
    "the hash structure, ignoring output size and hash-related details."
)


# ============================================================================
# 31. OUTPUT SIZE STILL MATTERS
# ============================================================================

print_title("28. OUTPUT SIZE CAN DOMINATE")

large_duplicate_left = [{"key": 1, "left": i} for i in range(100)]
large_duplicate_right = [{"key": 1, "right": i} for i in range(100)]

large_output = hash_join(
    large_duplicate_left,
    large_duplicate_right,
    "key",
    "key",
)

print(
    "100 matching left rows × 100 matching right rows =",
    len(large_output),
    "output rows",
)

print(
    "\nEven a fast join algorithm cannot make an unavoidable 10,000-row "
    "result logically disappear. Query design must consider result cardinality."
)


# ============================================================================
# 32. INDEXING CONCEPT
# ============================================================================

print_title("29. INDEXING CONCEPT")

print(
    """
A database index on a join key can make locating matching rows much faster.

Typical candidates include:
    orders.customer_id
    order_items.order_id
    payments.order_id
    employees.manager_id
    employees.department_id

The usefulness of an index depends on:
    - table size
    - selectivity
    - data distribution
    - query frequency
    - write cost
    - optimizer decisions
    - existing indexes
    - join algorithm

An index is not automatically beneficial for every query.
"""
)


# ============================================================================
# 33. DATA DISTRIBUTION AND SKEW
# ============================================================================

print_title("30. DATA SKEW")

skewed_left = [
    {"key": "HOT", "value": index}
    for index in range(1000)
] + [
    {"key": "COLD", "value": 1},
]

skewed_right = [
    {"key": "HOT", "value": index}
    for index in range(2000)
] + [
    {"key": "COLD", "value": 2},
]

hot_count = 1000 * 2000
cold_count = 1 * 1

print("HOT key output contribution:", hot_count)
print("COLD key output contribution:", cold_count)
print("Total expected output:", hot_count + cold_count)

print(
    "\nA small number of highly duplicated keys can dominate join output. "
    "This is known as data skew and can affect performance and memory usage."
)


# ============================================================================
# 34. MANY-TO-MANY BRIDGE TABLE VALIDATION
# ============================================================================

print_title("31. BRIDGE TABLE VALIDATION")

duplicate_links = employee_projects + [
    {"employee_id": 1, "project_id": 101}
]

link_pairs = [
    (row["employee_id"], row["project_id"])
    for row in duplicate_links
]

pair_counts = Counter(link_pairs)

print(
    "Duplicate employee-project relationships:",
    {
        pair: count
        for pair, count in pair_counts.items()
        if count > 1
    },
)

print(
    "\nA composite uniqueness rule on (employee_id, project_id) can prevent "
    "accidental duplicate bridge records."
)


# ============================================================================
# 35. REFERENTIAL-INTEGRITY CHECK
# ============================================================================

print_title("32. REFERENTIAL INTEGRITY")

employee_ids = {row["employee_id"] for row in employees}
project_ids = {row["project_id"] for row in projects}

invalid_employee_links = [
    row
    for row in employee_projects
    if row["employee_id"] not in employee_ids
]

invalid_project_links = [
    row
    for row in employee_projects
    if row["project_id"] not in project_ids
]

print("Invalid employee references:", invalid_employee_links)
print("Invalid project references:", invalid_project_links)


# ============================================================================
# 36. JOIN ASSERTIONS
# ============================================================================

print_title("33. CARDINALITY ASSERTIONS")

assert len(departments) == unique_key_count(departments, "department_id")
assert len(employees) == unique_key_count(employees, "employee_id")
assert len(orders) == unique_key_count(orders, "order_id")

assert len(cross_result) == len(small_departments) * len(small_projects)

assert estimate_join_cardinality(
    large_duplicate_left,
    large_duplicate_right,
    "key",
    "key",
) == 10000

print("All expected cardinality assertions passed.")


# ============================================================================
# 37. REALISTIC REPORTING PATTERN
# ============================================================================

print_title("34. REALISTIC CUSTOMER REPORT")

order_counts: defaultdict[Any, int] = defaultdict(int)
order_values: defaultdict[Any, float] = defaultdict(float)

for order in orders:
    order_counts[order["customer_id"]] += 1
    order_values[order["customer_id"]] += order["order_total"]

customer_metrics: Table = []

for customer in customers:
    customer_id = customer["customer_id"]
    customer_metrics.append(
        {
            "customer_id": customer_id,
            "customer_name": customer["customer_name"],
            "order_count": order_counts[customer_id],
            "total_order_value": order_values[customer_id],
        }
    )

print_rows(customer_metrics)

print(
    "\nThe aggregation is performed at customer grain before unrelated "
    "one-to-many relationships are combined."
)


# ============================================================================
# 38. JOINING AGGREGATED DATA
# ============================================================================

print_title("35. JOINING PRE-AGGREGATED RELATIONSHIPS")

customer_order_metrics = customer_metrics

customer_payment_totals: defaultdict[Any, float] = defaultdict(float)

for payment in payments:
    matching_orders = [
        order
        for order in orders
        if order["order_id"] == payment["order_id"]
    ]

    for order in matching_orders:
        customer_payment_totals[order["customer_id"]] += payment["amount"]

customer_payment_table = [
    {
        "customer_id": customer_id,
        "total_paid": total,
    }
    for customer_id, total in customer_payment_totals.items()
]

customer_report = left_join(
    customer_order_metrics,
    customer_payment_table,
    "customer_id",
    "customer_id",
)

print_rows(customer_report)


# ============================================================================
# 39. CONDITIONAL JOIN
# ============================================================================

print_title("36. CONDITIONAL JOIN CONCEPT")

employee_project_same_department: Table = []

for employee in employees:
    for link in employee_projects:
        if employee["employee_id"] != link["employee_id"]:
            continue

        matching_project = next(
            (
                project
                for project in projects
                if project["project_id"] == link["project_id"]
            ),
            None,
        )

        if matching_project is None:
            continue

        if employee["department_id"] == matching_project["department_id"]:
            employee_project_same_department.append(
                {
                    "employee": employee["employee_name"],
                    "project": matching_project["project_name"],
                    "department_id": employee["department_id"],
                }
            )

print_rows(employee_project_same_department)

print(
    "\nSQL join predicates can contain more than a simple equality. "
    "Additional predicates should be analyzed for both correctness and "
    "cardinality effects."
)


# ============================================================================
# 40. NON-EQUI JOIN CONCEPT
# ============================================================================

print_title("37. NON-EQUI JOIN")

salary_bands: Table = [
    {"band": "Junior", "minimum": 0, "maximum": 50000},
    {"band": "Mid", "minimum": 50001, "maximum": 100000},
    {"band": "Senior", "minimum": 100001, "maximum": 200000},
]

employee_salaries: Table = [
    {"employee_id": 1, "employee_name": "Asha", "salary": 72000},
    {"employee_id": 2, "employee_name": "Bharat", "salary": 45000},
    {"employee_id": 3, "employee_name": "Chitra", "salary": 130000},
]

salary_band_matches: Table = []

for employee in employee_salaries:
    for band in salary_bands:
        if band["minimum"] <= employee["salary"] <= band["maximum"]:
            salary_band_matches.append(
                {
                    "employee": employee["employee_name"],
                    "salary": employee["salary"],
                    "band": band["band"],
                }
            )

print_rows(salary_band_matches)

print(
    "\nA non-equality join can match ranges, dates, thresholds, or other "
    "conditions. Cardinality still must be checked."
)


# ============================================================================
# 41. OVERLAPPING RANGES AS A CARDINALITY TRAP
# ============================================================================

print_title("38. OVERLAPPING RANGE JOIN")

overlapping_ranges: Table = [
    {"label": "Range A", "minimum": 0, "maximum": 100},
    {"label": "Range B", "minimum": 50, "maximum": 150},
]

values: Table = [
    {"value_id": 1, "value": 75},
]

range_matches: Table = []

for value in values:
    for range_row in overlapping_ranges:
        if range_row["minimum"] <= value["value"] <= range_row["maximum"]:
            range_matches.append(
                {
                    "value_id": value["value_id"],
                    "value": value["value"],
                    "range": range_row["label"],
                }
            )

print_rows(range_matches)

print(
    "\nOne value matches two overlapping ranges. If the business rule "
    "requires exactly one range, enforce that invariant rather than relying "
    "on DISTINCT."
)


# ============================================================================
# 42. JOIN DEBUGGING WORKFLOW
# ============================================================================

print_title("39. JOIN DEBUGGING WORKFLOW")

debugging_steps = [
    "1. Define the intended row grain.",
    "2. Identify primary keys and foreign keys.",
    "3. Profile duplicates on every join key.",
    "4. Measure each input row count.",
    "5. Run the first join independently.",
    "6. Measure its output count.",
    "7. Group the output by the intended entity.",
    "8. Inspect unexpectedly high multiplicities.",
    "9. Add the next join only after validating the previous step.",
    "10. Pre-aggregate independent one-to-many relationships when required.",
    "11. Inspect NULL behavior.",
    "12. Inspect the database execution plan in production systems.",
]

for step in debugging_steps:
    print(step)


# ============================================================================
# 43. AUTOMATED CARDINALITY CHECK
# ============================================================================

print_title("40. AUTOMATED JOIN-CARDINALITY CHECK")

@dataclass
class JoinExpectation:
    name: str
    expected_max_rows_per_left_key: int | None
    expected_output_rows: int | None = None


def validate_join(
    left: Table,
    right: Table,
    result: Table,
    *,
    left_key: str,
    right_key: str,
    expectation: JoinExpectation,
) -> None:
    right_counts = Counter(row.get(right_key) for row in right)

    if expectation.expected_max_rows_per_left_key is not None:
        violations = {
            key: count
            for key, count in right_counts.items()
            if key is not None
            and count > expectation.expected_max_rows_per_left_key
        }

        if violations:
            raise AssertionError(
                f"{expectation.name}: right-side multiplicity violation: "
                f"{violations}"
            )

    if expectation.expected_output_rows is not None:
        if len(result) != expectation.expected_output_rows:
            raise AssertionError(
                f"{expectation.name}: expected "
                f"{expectation.expected_output_rows} rows, got {len(result)}"
            )


employee_department_result = inner_join(
    employees,
    departments,
    "department_id",
    "department_id",
)

validate_join(
    employees,
    departments,
    employee_department_result,
    left_key="department_id",
    right_key="department_id",
    expectation=JoinExpectation(
        name="employee_department",
        expected_max_rows_per_left_key=1,
        expected_output_rows=len(employees),
    ),
)

print("Employee-to-department cardinality validation passed.")


# ============================================================================
# 44. CASE STUDY: ORDER ANALYTICS
# ============================================================================

print_title("41. CASE STUDY: SAFE ORDER ANALYTICS")

@dataclass
class OrderAnalytics:
    order_id: int
    item_count: int
    total_quantity: int
    payment_count: int
    total_paid: float


def build_order_analytics(
    orders_table: Table,
    items_table: Table,
    payments_table: Table,
) -> list[OrderAnalytics]:
    item_count: Counter[int] = Counter()
    quantity_sum: Counter[int] = Counter()
    payment_count: Counter[int] = Counter()
    payment_sum: defaultdict[int, float] = defaultdict(float)

    for item in items_table:
        order_id = item["order_id"]
        item_count[order_id] += 1
        quantity_sum[order_id] += item["quantity"]

    for payment in payments_table:
        order_id = payment["order_id"]
        payment_count[order_id] += 1
        payment_sum[order_id] += payment["amount"]

    return [
        OrderAnalytics(
            order_id=order["order_id"],
            item_count=item_count[order["order_id"]],
            total_quantity=quantity_sum[order["order_id"]],
            payment_count=payment_count[order["order_id"]],
            total_paid=payment_sum[order["order_id"]],
        )
        for order in orders_table
    ]


analytics = build_order_analytics(
    orders,
    order_items,
    payments,
)

for record in analytics:
    print(record)


# ============================================================================
# 45. COMPARING NAIVE AND SAFE DESIGNS
# ============================================================================

print_title("42. NAIVE VS SAFE MULTI-JOIN DESIGN")

print(
    """
NAIVE:

    orders
      JOIN order_items
      JOIN payments

Potential result grain:
    one row per order-item-payment combination

SAFE FOR INDEPENDENT AGGREGATES:

    aggregate order_items by order
    aggregate payments by order
    join the two aggregates to orders

Result grain:
    one row per order

The second design makes the intended grain explicit.
"""
)


# ============================================================================
# 46. PRACTICAL PRODUCTION CHECKLIST
# ============================================================================

print_title("43. PRODUCTION JOIN CHECKLIST")

production_checklist = [
    "Know the grain of every table.",
    "Know which columns are unique.",
    "Know which columns are foreign keys.",
    "Check for NULL join keys.",
    "Check duplicate join keys.",
    "Estimate output cardinality before adding joins.",
    "Treat CROSS JOIN as intentionally multiplicative.",
    "Use aliases for self joins.",
    "Use bridge tables for many-to-many relationships.",
    "Pre-aggregate independent one-to-many facts before joining when appropriate.",
    "Do not use DISTINCT as a substitute for correct relational logic.",
    "Validate aggregates after complex joins.",
    "Use appropriate indexes in real database systems.",
    "Inspect execution plans for expensive production queries.",
    "Consider data skew and highly duplicated keys.",
    "Protect against unbounded Cartesian products.",
    "Test edge cases with NULLs and duplicate keys.",
]

for item in production_checklist:
    print(f"- {item}")


# ============================================================================
# 47. SQL PATTERN REFERENCE
# ============================================================================

print_title("44. SQL PATTERN REFERENCE")

sql_patterns = {
    "self join": (
        "SELECT e.employee_name, m.employee_name AS manager_name "
        "FROM employees AS e "
        "LEFT JOIN employees AS m ON e.manager_id = m.employee_id;"
    ),
    "cross join": (
        "SELECT d.department_name, p.project_name "
        "FROM departments AS d "
        "CROSS JOIN projects AS p;"
    ),
    "multiple joins": (
        "SELECT e.employee_name, p.project_name "
        "FROM employees AS e "
        "JOIN employee_projects AS ep ON ep.employee_id = e.employee_id "
        "JOIN projects AS p ON p.project_id = ep.project_id;"
    ),
    "semi join": (
        "SELECT e.* "
        "FROM employees AS e "
        "WHERE EXISTS ("
        "SELECT 1 FROM employee_projects AS ep "
        "WHERE ep.employee_id = e.employee_id"
        ");"
    ),
    "anti join": (
        "SELECT e.* "
        "FROM employees AS e "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM employee_projects AS ep "
        "WHERE ep.employee_id = e.employee_id"
        ");"
    ),
    "pre-aggregation": (
        "SELECT o.order_id, i.total_quantity, p.total_paid "
        "FROM orders AS o "
        "LEFT JOIN ("
        "SELECT order_id, SUM(quantity) AS total_quantity "
        "FROM order_items GROUP BY order_id"
        ") AS i ON i.order_id = o.order_id "
        "LEFT JOIN ("
        "SELECT order_id, SUM(amount) AS total_paid "
        "FROM payments GROUP BY order_id"
        ") AS p ON p.order_id = o.order_id;"
    ),
}

for name, sql in sql_patterns.items():
    print(f"\n{name.upper()}:\n{sql}")


# ============================================================================
# 48. FINAL KNOWLEDGE TEST
# ============================================================================

print_title("45. KNOWLEDGE TEST")

questions = [
    (
        "What is the output cardinality of a CROSS JOIN between 8 and 12 rows?",
        8 * 12,
    ),
    (
        "If one join key occurs 4 times on the left and 5 times on the right, "
        "how many matching pairs can it produce?",
        4 * 5,
    ),
    (
        "What relationship does a bridge table commonly represent?",
        "many-to-many",
    ),
]

for question, answer in questions:
    print(f"Q: {question}")
    print(f"A: {answer}\n")


# ============================================================================
# 49. FINAL ASSERTIONS
# ============================================================================

print_title("46. FINAL ASSERTIONS")

assert len(cross_join([{"x": 1}, {"x": 2}], [{"y": 1}, {"y": 2}, {"y": 3}])) == 6

assert estimate_join_cardinality(
    [
        {"key": "A"},
        {"key": "A"},
    ],
    [
        {"key": "A"},
        {"key": "A"},
        {"key": "A"},
    ],
    "key",
    "key",
) == 6

assert len(employees_without_projects) == 0

assert items_total == 5
assert payments_total == 900

print("All final assertions passed.")
print("\nSQL Joins II demonstrations completed successfully.")
