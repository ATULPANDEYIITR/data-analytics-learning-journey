#!/usr/bin/env python3
"""
SQL Window Functions I
======================

A self-contained executable learning model for:

    OVER
    PARTITION BY
    ORDER BY
    ROW_NUMBER
    RANK
    DENSE_RANK

The program uses Python's standard library to model the result sets produced
by SQL window functions. It deliberately separates:

    - ordinary aggregation, which collapses rows
    - window calculations, which preserve the original rows
    - partitioning, which creates independent calculation groups
    - ordering, which determines calculation sequence
    - ROW_NUMBER, which assigns a unique sequential position
    - RANK, which gives equal values the same rank and leaves gaps
    - DENSE_RANK, which gives equal values the same rank without gaps

It also demonstrates ties, NULL-like values, deterministic ordering,
top-N-per-group analysis, validation, and performance considerations.

Run:

    python sql_window_functions_i.py
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Iterable, Sequence
from collections import defaultdict
import csv
import io
import math
import random
import statistics
import tempfile


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SalesRow:
    sale_id: int
    employee: str
    department: str
    region: str
    product: str
    amount: Decimal

    def as_dict(self) -> dict[str, Any]:
        return {
            "sale_id": self.sale_id,
            "employee": self.employee,
            "department": self.department,
            "region": self.region,
            "product": self.product,
            "amount": self.amount,
        }


SALES_DATA: list[SalesRow] = [
    SalesRow(101, "Asha", "Engineering", "North", "Cloud", Decimal("9200.00")),
    SalesRow(102, "Ravi", "Engineering", "North", "Security", Decimal("8700.00")),
    SalesRow(103, "Meera", "Engineering", "South", "Cloud", Decimal("9200.00")),
    SalesRow(104, "Kabir", "Engineering", "South", "Data", Decimal("7600.00")),
    SalesRow(105, "Isha", "Sales", "North", "Enterprise", Decimal("12500.00")),
    SalesRow(106, "Arjun", "Sales", "North", "Cloud", Decimal("9800.00")),
    SalesRow(107, "Neha", "Sales", "South", "Enterprise", Decimal("12500.00")),
    SalesRow(108, "Vikram", "Sales", "South", "Analytics", Decimal("8100.00")),
    SalesRow(109, "Tara", "Finance", "North", "Audit", Decimal("6700.00")),
    SalesRow(110, "Dev", "Finance", "North", "Risk", Decimal("6700.00")),
    SalesRow(111, "Pooja", "Finance", "South", "Risk", Decimal("5900.00")),
    SalesRow(112, "Nikhil", "Finance", "South", "Audit", Decimal("5100.00")),
]


# ---------------------------------------------------------------------------
# Generic SQL-like helpers
# ---------------------------------------------------------------------------

def sql_sort_key(
    row: dict[str, Any],
    columns: Sequence[tuple[str, bool]],
) -> tuple[Any, ...]:
    """
    Build a sortable key.

    Each tuple is (column_name, descending).

    SQL has database-specific NULL ordering rules. This educational model
    keeps None values explicitly sortable by placing them before real values
    for ascending order and after real values for descending order.
    """
    result: list[Any] = []

    for column, descending in columns:
        value = row.get(column)

        if value is None:
            null_marker = 0 if not descending else 1
            result.append((null_marker, None))
        else:
            non_null_marker = 1 if not descending else 0
            result.append((non_null_marker, _descending_value(value) if descending else value))

    return tuple(result)


class _DescendingValue:
    """Wrapper providing reverse comparison without changing the source value."""

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value

    def __lt__(self, other: "_DescendingValue") -> bool:
        return other.value < self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _DescendingValue) and self.value == other.value


def _descending_value(value: Any) -> _DescendingValue:
    return _DescendingValue(value)


def order_rows(
    rows: Iterable[dict[str, Any]],
    columns: Sequence[tuple[str, bool]],
) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: sql_sort_key(row, columns))


def partition_rows(
    rows: Sequence[dict[str, Any]],
    partition_columns: Sequence[str],
) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    """
    Equivalent in spirit to PARTITION BY.

    PARTITION BY does not remove rows. It creates independent logical windows.
    """
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = tuple(row[column] for column in partition_columns)
        groups[key].append(row)

    return groups


def clone_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def format_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def print_table(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[str] | None = None,
    title: str | None = None,
) -> None:
    if title:
        print(f"\n{title}")
        print("-" * len(title))

    if not rows:
        print("(no rows)")
        return

    selected_columns = list(columns) if columns else list(rows[0].keys())
    widths = {
        column: max(
            len(column),
            *(len(format_value(row.get(column))) for row in rows),
        )
        for column in selected_columns
    }

    header = " | ".join(column.ljust(widths[column]) for column in selected_columns)
    separator = "-+-".join("-" * widths[column] for column in selected_columns)

    print(header)
    print(separator)

    for row in rows:
        print(
            " | ".join(
                format_value(row.get(column)).ljust(widths[column])
                for column in selected_columns
            )
        )


def decimal_average(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise ValueError("Cannot calculate an average of an empty sequence.")
    return sum(values, Decimal("0")) / Decimal(len(values))


# ---------------------------------------------------------------------------
# Loading data in a table-like representation
# ---------------------------------------------------------------------------

def sales_as_dicts() -> list[dict[str, Any]]:
    return [row.as_dict() for row in SALES_DATA]


def load_sales_from_csv(csv_text: str) -> list[dict[str, Any]]:
    """
    Demonstrate that window calculations normally happen after relational
    data has been loaded into a result set. The function performs validation
    before returning records.
    """
    required = {
        "sale_id",
        "employee",
        "department",
        "region",
        "product",
        "amount",
    }

    reader = csv.DictReader(io.StringIO(csv_text))

    if reader.fieldnames is None:
        raise ValueError("CSV input has no header row.")

    missing = required - set(reader.fieldnames)
    if missing:
        raise ValueError(f"CSV input is missing columns: {sorted(missing)}")

    result: list[dict[str, Any]] = []

    for line_number, raw in enumerate(reader, start=2):
        try:
            sale_id = int(raw["sale_id"])
            amount = Decimal(raw["amount"])
        except (TypeError, ValueError, ArithmeticError) as exc:
            raise ValueError(
                f"Invalid sale_id or amount on CSV line {line_number}"
            ) from exc

        if amount < 0:
            raise ValueError(f"Negative amount on CSV line {line_number}")

        result.append(
            {
                "sale_id": sale_id,
                "employee": raw["employee"],
                "department": raw["department"],
                "region": raw["region"],
                "product": raw["product"],
                "amount": amount,
            }
        )

    return result


# ---------------------------------------------------------------------------
# Ordinary aggregation versus window calculations
# ---------------------------------------------------------------------------

def aggregate_by_department(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Ordinary GROUP BY-style aggregation.

    Notice that several source rows become one output row per department.
    This is fundamentally different from a window function.
    """
    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    counts: defaultdict[str, int] = defaultdict(int)

    for row in rows:
        department = row["department"]
        totals[department] += row["amount"]
        counts[department] += 1

    return [
        {
            "department": department,
            "sales_count": counts[department],
            "department_total": totals[department],
        }
        for department in sorted(totals)
    ]


def window_sum_by_department(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Window-style equivalent of:

        SUM(amount) OVER (PARTITION BY department)

    Every original row survives, while the department total is attached to it.
    """
    result = clone_rows(rows)
    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for row in result:
        totals[row["department"]] += row["amount"]

    for row in result:
        row["department_total"] = totals[row["department"]]

    return result


# ---------------------------------------------------------------------------
# OVER and PARTITION BY
# ---------------------------------------------------------------------------

def demonstrate_partition_by(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Assign a department-local count.

    Conceptually:

        COUNT(*) OVER (
            PARTITION BY department
        )

    There is no ORDER BY because counting the entire partition does not need
    a sequence.
    """
    result = clone_rows(rows)
    partitions = partition_rows(result, ["department"])

    for members in partitions.values():
        count = len(members)
        for row in members:
            row["department_count"] = count

    return result


def demonstrate_multiple_partition_columns(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Demonstrate a compound partition:

        PARTITION BY department, region

    Engineering/North and Engineering/South are independent windows.
    """
    result = clone_rows(rows)
    partitions = partition_rows(result, ["department", "region"])

    for members in partitions.values():
        amount_total = sum(
            (row["amount"] for row in members),
            Decimal("0"),
        )
        for row in members:
            row["department_region_total"] = amount_total

    return result


# ---------------------------------------------------------------------------
# ORDER BY inside a window
# ---------------------------------------------------------------------------

def add_row_number(
    rows: Sequence[dict[str, Any]],
    partition_columns: Sequence[str],
    order_columns: Sequence[tuple[str, bool]],
    output_column: str = "row_number",
) -> list[dict[str, Any]]:
    """
    Simulate:

        ROW_NUMBER() OVER (
            PARTITION BY ...
            ORDER BY ...
        )

    ROW_NUMBER always produces a unique sequence within each partition.

    A unique tie-breaker such as sale_id is important when deterministic output
    matters. Without one, equal ordering values may have implementation-defined
    or engine-dependent ordering.
    """
    result = clone_rows(rows)
    partitions = partition_rows(result, partition_columns)

    for members in partitions.values():
        ordered = order_rows(members, order_columns)

        for position, row in enumerate(ordered, start=1):
            row[output_column] = position

    return result


def add_rank(
    rows: Sequence[dict[str, Any]],
    partition_columns: Sequence[str],
    order_column: str,
    descending: bool = True,
    output_column: str = "rank",
) -> list[dict[str, Any]]:
    """
    Simulate:

        RANK() OVER (
            PARTITION BY ...
            ORDER BY amount DESC
        )

    Equal ordering values share a rank. The next rank jumps according to the
    number of tied rows.
    """
    result = clone_rows(rows)
    partitions = partition_rows(result, partition_columns)

    for members in partitions.values():
        ordered = order_rows(members, [(order_column, descending)])

        previous_value: Any = object()
        current_rank = 0

        for position, row in enumerate(ordered, start=1):
            value = row[order_column]

            if value != previous_value:
                current_rank = position
                previous_value = value

            row[output_column] = current_rank

    return result


def add_dense_rank(
    rows: Sequence[dict[str, Any]],
    partition_columns: Sequence[str],
    order_column: str,
    descending: bool = True,
    output_column: str = "dense_rank",
) -> list[dict[str, Any]]:
    """
    Simulate:

        DENSE_RANK() OVER (
            PARTITION BY ...
            ORDER BY amount DESC
        )

    Equal values share a rank, but the next distinct value receives the next
    consecutive rank instead of skipping positions.
    """
    result = clone_rows(rows)
    partitions = partition_rows(result, partition_columns)

    for members in partitions.values():
        ordered = order_rows(members, [(order_column, descending)])

        previous_value: Any = object()
        current_rank = 0

        for row in ordered:
            value = row[order_column]

            if value != previous_value:
                current_rank += 1
                previous_value = value

            row[output_column] = current_rank

    return result


# ---------------------------------------------------------------------------
# Tie behavior
# ---------------------------------------------------------------------------

def demonstrate_ties(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Produce all three ranking functions for each department.

    For Sales/North:

        12500 -> ROW_NUMBER 1/2, RANK 1, DENSE_RANK 1
         9800 -> ROW_NUMBER 3,   RANK 3, DENSE_RANK 2

    RANK skips rank 2 because two rows occupy rank 1.
    DENSE_RANK does not skip it.
    """
    base = clone_rows(rows)

    ranked = add_row_number(
        base,
        ["department"],
        [("amount", True), ("sale_id", False)],
        "row_number",
    )

    ranked = add_rank(
        ranked,
        ["department"],
        "amount",
        True,
        "rank",
    )

    ranked = add_dense_rank(
        ranked,
        ["department"],
        "amount",
        True,
        "dense_rank",
    )

    return order_rows(
        ranked,
        [("department", False), ("amount", True), ("sale_id", False)],
    )


# ---------------------------------------------------------------------------
# Top-N per group
# ---------------------------------------------------------------------------

def top_n_per_department(
    rows: Sequence[dict[str, Any]],
    n: int,
) -> list[dict[str, Any]]:
    """
    A common SQL pattern:

        ROW_NUMBER() OVER (
            PARTITION BY department
            ORDER BY amount DESC, sale_id
        )

    followed by:

        WHERE row_number <= n

    The filtering occurs after the window result is logically available.
    """
    if n < 1:
        raise ValueError("n must be at least 1.")

    ranked = add_row_number(
        rows,
        ["department"],
        [("amount", True), ("sale_id", False)],
    )

    return [
        row
        for row in ranked
        if row["row_number"] <= n
    ]


def top_n_with_ties_per_department(
    rows: Sequence[dict[str, Any]],
    n: int,
) -> list[dict[str, Any]]:
    """
    Use RANK instead of ROW_NUMBER when business semantics require all rows
    tied at the cutoff to survive.

    This can return more than n rows in a department.
    """
    if n < 1:
        raise ValueError("n must be at least 1.")

    ranked = add_rank(
        rows,
        ["department"],
        "amount",
        True,
        "rank",
    )

    return [
        row
        for row in ranked
        if row["rank"] <= n
    ]


# ---------------------------------------------------------------------------
# Practical reporting workflow
# ---------------------------------------------------------------------------

def department_leaderboard(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build a department leaderboard where each employee sale is retained.

    The output combines:
        - partitioning by department
        - deterministic ORDER BY
        - ROW_NUMBER for a unique position
        - RANK for competition ranking
        - DENSE_RANK for distinct-value ranking

    The sale_id tie-breaker is deliberately used only for ROW_NUMBER.
    RANK and DENSE_RANK are based only on amount, so equal amounts remain tied.
    """
    result = add_row_number(
        rows,
        ["department"],
        [("amount", True), ("sale_id", False)],
        "row_number",
    )

    result = add_rank(
        result,
        ["department"],
        "amount",
        True,
        "rank",
    )

    result = add_dense_rank(
        result,
        ["department"],
        "amount",
        True,
        "dense_rank",
    )

    return order_rows(
        result,
        [("department", False), ("row_number", False)],
    )


# ---------------------------------------------------------------------------
# Validation and failure conditions
# ---------------------------------------------------------------------------

def validate_window_input(
    rows: Sequence[dict[str, Any]],
    required_columns: Sequence[str],
) -> None:
    """
    Fail early when the data cannot support the requested window operation.
    """
    if not rows:
        raise ValueError("Window calculation requires at least one row.")

    missing = [
        column
        for column in required_columns
        if column not in rows[0]
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for index, row in enumerate(rows):
        for column in required_columns:
            if row[column] is None:
                raise ValueError(
                    f"NULL-like value in required column '{column}' "
                    f"at row index {index}."
                )


def validate_rank_invariants(
    rows: Sequence[dict[str, Any]],
) -> None:
    """
    Verify mathematical properties of the simulated ranking functions.
    """
    for department, members in partition_rows(rows, ["department"]).items():
        ordered = order_rows(members, [("amount", True), ("sale_id", False)])

        row_numbers = [row["row_number"] for row in ordered]
        if row_numbers != list(range(1, len(ordered) + 1)):
            raise AssertionError(
                f"ROW_NUMBER invariant failed for partition {department}"
            )

        previous_amount = None
        for row in ordered:
            amount = row["amount"]

            if previous_amount is not None and amount > previous_amount:
                raise AssertionError(
                    f"Ordering invariant failed for partition {department}"
                )

            previous_amount = amount

        rank_values = [row["rank"] for row in ordered]
        dense_values = [row["dense_rank"] for row in ordered]

        if any(value < 1 for value in rank_values):
            raise AssertionError("RANK must start at 1.")

        if any(value < 1 for value in dense_values):
            raise AssertionError("DENSE_RANK must start at 1.")

        if any(
            rank_values[i] > rank_values[i + 1]
            for i in range(len(rank_values) - 1)
        ):
            raise AssertionError("RANK must not decrease.")

        if any(
            dense_values[i] > dense_values[i + 1]
            for i in range(len(dense_values) - 1)
        ):
            raise AssertionError("DENSE_RANK must not decrease.")


# ---------------------------------------------------------------------------
# A miniature query planner model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WindowSpecification:
    """
    Represent the important pieces of an SQL window specification.

    This is not a SQL parser. It is a small typed representation used to make
    the relationship between OVER, PARTITION BY and ORDER BY explicit.
    """

    partition_by: tuple[str, ...] = ()
    order_by: tuple[tuple[str, bool], ...] = ()

    def describe(self) -> str:
        pieces = []

        if self.partition_by:
            pieces.append(
                "PARTITION BY " + ", ".join(self.partition_by)
            )

        if self.order_by:
            order_text = ", ".join(
                f"{column} {'DESC' if descending else 'ASC'}"
                for column, descending in self.order_by
            )
            pieces.append("ORDER BY " + order_text)

        return "OVER (" + " ".join(pieces) + ")"


def apply_window_function(
    rows: Sequence[dict[str, Any]],
    specification: WindowSpecification,
    function_name: str,
    value_column: str | None = None,
) -> list[dict[str, Any]]:
    """
    Dispatch common window functions from a structured specification.

    This makes the SQL relationship explicit:

        function(...) OVER (...)

    while keeping the execution implementation in Python.
    """
    name = function_name.upper()

    if name == "ROW_NUMBER":
        return add_row_number(
            rows,
            specification.partition_by,
            specification.order_by,
        )

    if name == "RANK":
        if value_column is None:
            raise ValueError("RANK requires an ordering value column.")
        if len(specification.order_by) != 1:
            raise ValueError(
                "This simplified RANK model expects exactly one ORDER BY column."
            )

        column, descending = specification.order_by[0]
        if column != value_column:
            raise ValueError(
                "value_column must match the sole ORDER BY column."
            )

        return add_rank(
            rows,
            specification.partition_by,
            value_column,
            descending,
        )

    if name == "DENSE_RANK":
        if value_column is None:
            raise ValueError("DENSE_RANK requires an ordering value column.")
        if len(specification.order_by) != 1:
            raise ValueError(
                "This simplified DENSE_RANK model expects exactly one "
                "ORDER BY column."
            )

        column, descending = specification.order_by[0]
        if column != value_column:
            raise ValueError(
                "value_column must match the sole ORDER BY column."
            )

        return add_dense_rank(
            rows,
            specification.partition_by,
            value_column,
            descending,
        )

    raise ValueError(f"Unsupported window function: {function_name}")


# ---------------------------------------------------------------------------
# Performance model
# ---------------------------------------------------------------------------

def estimate_sort_work(row_count: int) -> float:
    """
    Roughly illustrate why ORDER BY inside a window can require sorting.

    This is not a database cost model. It only provides the familiar
    O(n log n) comparison-sort growth for educational purposes.
    """
    if row_count <= 1:
        return 0.0
    return row_count * math.log2(row_count)


def generate_synthetic_rows(
    count: int,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Create deterministic data for a small performance demonstration.
    """
    if count < 0:
        raise ValueError("count cannot be negative.")

    random_generator = random.Random(seed)
    departments = ["Engineering", "Sales", "Finance", "Operations"]

    return [
        {
            "sale_id": index,
            "employee": f"Employee-{index}",
            "department": random_generator.choice(departments),
            "amount": Decimal(
                random_generator.randint(1_000, 100_000)
            ),
        }
        for index in range(1, count + 1)
    ]


# ---------------------------------------------------------------------------
# Demonstration sections
# ---------------------------------------------------------------------------

def show_foundation(rows: Sequence[dict[str, Any]]) -> None:
    print("\n=== Relational rows before window processing ===")
    print_table(
        rows,
        ["sale_id", "employee", "department", "region", "amount"],
    )

    print("\nA window function adds information to these rows.")
    print("It does not collapse the rows in the way ordinary GROUP BY does.")


def show_group_by_vs_window(rows: Sequence[dict[str, Any]]) -> None:
    grouped = aggregate_by_department(rows)
    print_table(
        grouped,
        ["department", "sales_count", "department_total"],
        "Ordinary GROUP BY-style aggregation",
    )

    windowed = window_sum_by_department(rows)
    print_table(
        windowed,
        ["sale_id", "employee", "department", "amount", "department_total"],
        "Window-style department total",
    )


def show_over_and_partition(rows: Sequence[dict[str, Any]]) -> None:
    department_counts = demonstrate_partition_by(rows)

    print_table(
        department_counts,
        ["sale_id", "employee", "department", "department_count"],
        "PARTITION BY department",
    )

    compound = demonstrate_multiple_partition_columns(rows)

    print_table(
        compound,
        [
            "sale_id",
            "department",
            "region",
            "amount",
            "department_region_total",
        ],
        "PARTITION BY department, region",
    )


def show_row_number(rows: Sequence[dict[str, Any]]) -> None:
    ranked = add_row_number(
        rows,
        ["department"],
        [("amount", True), ("sale_id", False)],
    )

    ordered = order_rows(
        ranked,
        [("department", False), ("row_number", False)],
    )

    print_table(
        ordered,
        ["department", "row_number", "employee", "amount", "sale_id"],
        "ROW_NUMBER within each department",
    )


def show_ranking(rows: Sequence[dict[str, Any]]) -> None:
    leaderboard = department_leaderboard(rows)

    print_table(
        leaderboard,
        [
            "department",
            "employee",
            "amount",
            "row_number",
            "rank",
            "dense_rank",
        ],
        "ROW_NUMBER vs RANK vs DENSE_RANK",
    )


def show_top_n(rows: Sequence[dict[str, Any]]) -> None:
    top_two = top_n_per_department(rows, 2)

    print_table(
        order_rows(top_two, [("department", False), ("row_number", False)]),
        ["department", "row_number", "employee", "amount"],
        "Top two rows per department using ROW_NUMBER",
    )

    top_two_ties = top_n_with_ties_per_department(rows, 2)

    print_table(
        order_rows(top_two_ties, [("department", False), ("rank", False)]),
        ["department", "rank", "employee", "amount"],
        "Top two ranks per department using RANK",
    )


def show_query_specification(rows: Sequence[dict[str, Any]]) -> None:
    specification = WindowSpecification(
        partition_by=("department",),
        order_by=(("amount", True), ("sale_id", False)),
    )

    print("\nStructured window specification:")
    print(specification.describe())

    result = apply_window_function(
        rows,
        specification,
        "ROW_NUMBER",
    )

    print_table(
        order_rows(result, [("department", False), ("row_number", False)]),
        ["department", "employee", "amount", "row_number"],
        "Execution from the structured window specification",
    )


def show_edge_cases(rows: Sequence[dict[str, Any]]) -> None:
    print("\n=== Edge cases and deterministic behavior ===")

    tie_rows = [
        {
            "sale_id": 1,
            "department": "A",
            "employee": "First",
            "amount": Decimal("100"),
        },
        {
            "sale_id": 2,
            "department": "A",
            "employee": "Second",
            "amount": Decimal("100"),
        },
        {
            "sale_id": 3,
            "department": "A",
            "employee": "Third",
            "amount": Decimal("90"),
        },
    ]

    row_number_result = add_row_number(
        tie_rows,
        ["department"],
        [("amount", True), ("sale_id", False)],
    )

    rank_result = add_rank(
        tie_rows,
        ["department"],
        "amount",
        True,
    )

    dense_result = add_dense_rank(
        tie_rows,
        ["department"],
        "amount",
        True,
    )

    print_table(
        [
            {
                "employee": row["employee"],
                "amount": row["amount"],
                "row_number": row["row_number"],
                "rank": rank_result[index]["rank"],
                "dense_rank": dense_result[index]["dense_rank"],
            }
            for index, row in enumerate(row_number_result)
        ],
        ["employee", "amount", "row_number", "rank", "dense_rank"],
        "Explicit tie behavior",
    )

    print(
        "\nROW_NUMBER needs a deterministic tie-breaker when reproducible "
        "ordering is required."
    )
    print(
        "RANK and DENSE_RANK intentionally preserve equal ordering values as ties."
    )


def show_validation(rows: Sequence[dict[str, Any]]) -> None:
    print("\n=== Validation and failure handling ===")

    validate_window_input(
        rows,
        ["sale_id", "department", "amount"],
    )

    try:
        top_n_per_department(rows, 0)
    except ValueError as exc:
        print(f"Rejected invalid top-N request: {exc}")

    try:
        apply_window_function(
            rows,
            WindowSpecification(
                partition_by=("department",),
                order_by=(("amount", True),),
            ),
            "UNSUPPORTED_FUNCTION",
        )
    except ValueError as exc:
        print(f"Rejected unsupported window function: {exc}")

    try:
        validate_window_input(
            [{"department": "Engineering"}],
            ["department", "amount"],
        )
    except ValueError as exc:
        print(f"Rejected incomplete input: {exc}")


def show_csv_workflow() -> None:
    csv_text = """sale_id,employee,department,region,product,amount
201,Ananya,Engineering,North,Cloud,9100.00
202,Bharat,Engineering,South,Security,8800.00
203,Chitra,Sales,North,Enterprise,12500.00
204,Danish,Sales,South,Analytics,7600.00
"""

    loaded = load_sales_from_csv(csv_text)
    ranked = add_rank(
        loaded,
        ["department"],
        "amount",
        True,
    )

    print_table(
        ranked,
        ["sale_id", "employee", "department", "amount", "rank"],
        "Window processing after CSV validation",
    )


def show_performance_model() -> None:
    print("\n=== Performance model ===")

    for size in [10, 100, 1_000, 10_000]:
        estimate = estimate_sort_work(size)
        print(
            f"{size:>6} rows -> approximate sort comparison growth: "
            f"{estimate:,.0f}"
        )

    print(
        "\nPARTITION BY itself groups rows conceptually, while ORDER BY "
        "often introduces sorting work inside each partition."
    )
    print(
        "A database optimizer may exploit indexes, existing order, parallelism, "
        "or other execution strategies, so this Python estimate is not a "
        "prediction of actual SQL runtime."
    )


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def run_self_tests(rows: Sequence[dict[str, Any]]) -> None:
    print("\n=== Self-tests ===")

    validate_window_input(
        rows,
        ["sale_id", "employee", "department", "amount"],
    )

    grouped = aggregate_by_department(rows)
    departments = {row["department"] for row in rows}

    assert len(grouped) == len(departments)

    windowed = window_sum_by_department(rows)
    assert len(windowed) == len(rows)

    for department, members in partition_rows(rows, ["department"]).items():
        expected_total = sum(
            (row["amount"] for row in members),
            Decimal("0"),
        )

        observed_totals = {
            row["department_total"]
            for row in windowed
            if row["department"] == department[0]
        }

        assert observed_totals == {expected_total}

    leaderboard = department_leaderboard(rows)
    validate_rank_invariants(leaderboard)

    for department, members in partition_rows(leaderboard, ["department"]).items():
        assert len(members) == len(
            partition_rows(rows, ["department"])[department]
        )

    sales = [
        row
        for row in leaderboard
        if row["department"] == "Sales"
    ]

    sales_amounts = [row["amount"] for row in sales]
    assert sales_amounts == sorted(sales_amounts, reverse=True)

    sales_12500 = [
        row for row in sales if row["amount"] == Decimal("12500.00")
    ]
    assert len(sales_12500) == 2
    assert {row["rank"] for row in sales_12500} == {1}
    assert {row["dense_rank"] for row in sales_12500} == {1}

    sales_9800 = [
        row for row in sales if row["amount"] == Decimal("9800.00")
    ]
    assert {row["rank"] for row in sales_9800} == {3}
    assert {row["dense_rank"] for row in sales_9800} == {2}

    top_two = top_n_per_department(rows, 2)
    for _, members in partition_rows(top_two, ["department"]).items():
        assert len(members) <= 2

    tie_top_two = top_n_with_ties_per_department(rows, 2)
    sales_tie_top = [
        row for row in tie_top_two if row["department"] == "Sales"
    ]
    assert len(sales_tie_top) == 2

    assert WindowSpecification(
        partition_by=("department",),
        order_by=(("amount", True),),
    ).describe() == "OVER (PARTITION BY department ORDER BY amount DESC)"

    print("All window-function invariants passed.")


# ---------------------------------------------------------------------------
# Advanced practical example: distinct-value bands
# ---------------------------------------------------------------------------

def build_sales_bands(
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Create a business-friendly band using DENSE_RANK.

    This differs from ROW_NUMBER because the band represents the distinct
    sales amount rather than a physical row position.

    Equal amounts therefore receive the same band.
    """
    result = add_dense_rank(
        rows,
        ["department"],
        "amount",
        True,
        "amount_band",
    )

    for row in result:
        band = row["amount_band"]

        if band == 1:
            label = "Highest amount"
        elif band == 2:
            label = "Second distinct amount"
        else:
            label = "Lower distinct amount"

        row["amount_band_label"] = label

    return result


def show_advanced_business_case(rows: Sequence[dict[str, Any]]) -> None:
    bands = build_sales_bands(rows)

    print_table(
        order_rows(
            bands,
            [("department", False), ("amount", True), ("sale_id", False)],
        ),
        [
            "department",
            "employee",
            "amount",
            "amount_band",
            "amount_band_label",
        ],
        "Distinct-value bands using DENSE_RANK",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    rows = sales_as_dicts()

    show_foundation(rows)
    show_group_by_vs_window(rows)
    show_over_and_partition(rows)
    show_row_number(rows)
    show_ranking(rows)
    show_top_n(rows)
    show_query_specification(rows)
    show_edge_cases(rows)
    show_validation(rows)
    show_csv_workflow()
    show_performance_model()
    show_advanced_business_case(rows)
    run_self_tests(rows)

    print("\n=== Completion ===")
    print(
        "The executable examples model OVER, PARTITION BY, ORDER BY, "
        "ROW_NUMBER, RANK, and DENSE_RANK while preserving the distinction "
        "between row-level window calculations and row-collapsing aggregation."
    )


if __name__ == "__main__":
    main()
