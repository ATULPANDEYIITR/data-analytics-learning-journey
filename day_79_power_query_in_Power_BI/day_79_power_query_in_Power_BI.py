"""
Power Query in Power BI: Data Cleaning, Transformation, Merge,
Append, Data Types, and Query Dependencies.

Self-contained Power Query-style ETL simulation using Python's
standard library.
"""

from __future__ import annotations

import csv
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("power_query")


class DataType(Enum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    BOOLEAN = "boolean"


class QueryStatus(Enum):
    CREATED = "created"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryError(Exception):
    pass


class TransformationError(QueryError):
    pass


class DependencyError(QueryError):
    pass


@dataclass
class Table:
    name: str
    columns: list[str]
    rows: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        if not self.columns:
            raise ValueError("A table must have columns.")

        if len(self.columns) != len(set(self.columns)):
            raise ValueError("Duplicate column names are not allowed.")

        for index, row in enumerate(self.rows):
            if set(row) != set(self.columns):
                raise ValueError(
                    f"Invalid row structure at index {index}."
                )

    def copy(self, name: str | None = None) -> Table:
        return Table(
            name=name or self.name,
            columns=self.columns.copy(),
            rows=[row.copy() for row in self.rows]
        )

    def display(self) -> None:
        print(f"\nTable: {self.name}")
        print(f"Columns: {self.columns}")
        for row in self.rows:
            print(row)

    def row_count(self) -> int:
        return len(self.rows)


def clean_text(value: Any) -> Any:
    if value is None:
        return None

    if not isinstance(value, str):
        return value

    value = value.strip()
    value = re.sub(r"\s+", " ", value)

    return value if value else None


def remove_duplicates(
    table: Table,
    columns: list[str] | None = None
) -> Table:
    result = []
    seen = set()
    keys = columns or table.columns

    if not set(keys).issubset(table.columns):
        raise TransformationError("Unknown duplicate-check column.")

    for row in table.rows:
        key = tuple(row[column] for column in keys)

        if key not in seen:
            seen.add(key)
            result.append(row.copy())

    return Table(table.name, table.columns.copy(), result)


def remove_null_rows(
    table: Table,
    required_columns: list[str]
) -> Table:
    if not set(required_columns).issubset(table.columns):
        raise TransformationError("Unknown required column.")

    rows = [
        row.copy()
        for row in table.rows
        if all(row[column] is not None for column in required_columns)
    ]

    return Table(table.name, table.columns.copy(), rows)


def rename_columns(
    table: Table,
    mapping: dict[str, str]
) -> Table:
    if not set(mapping).issubset(table.columns):
        raise TransformationError("Cannot rename an unknown column.")

    new_columns = [
        mapping.get(column, column)
        for column in table.columns
    ]

    if len(new_columns) != len(set(new_columns)):
        raise TransformationError("Column rename creates duplicates.")

    rows = [
        {
            mapping.get(column, column): value
            for column, value in row.items()
        }
        for row in table.rows
    ]

    return Table(table.name, new_columns, rows)


def convert_value(value: Any, data_type: DataType) -> Any:
    if value is None:
        return None

    try:
        if data_type == DataType.TEXT:
            return str(value)

        if data_type == DataType.INTEGER:
            number = Decimal(str(value))
            if number != number.to_integral_value():
                raise ValueError("Non-integral value.")
            return int(number)

        if data_type == DataType.DECIMAL:
            return Decimal(str(value))

        if data_type == DataType.DATE:
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            return date.fromisoformat(str(value))

        if data_type == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value

            normalized = str(value).strip().lower()

            if normalized in {"true", "1", "yes"}:
                return True

            if normalized in {"false", "0", "no"}:
                return False

            raise ValueError("Invalid boolean value.")

    except (ValueError, TypeError, InvalidOperation) as exc:
        raise TransformationError(
            f"Cannot convert {value!r} to {data_type.value}."
        ) from exc

    raise TransformationError("Unsupported data type.")


def change_data_types(
    table: Table,
    schema: dict[str, DataType],
    strict: bool = True
) -> Table:
    if not set(schema).issubset(table.columns):
        raise TransformationError("Type schema contains unknown columns.")

    rows = []

    for index, row in enumerate(table.rows):
        converted = row.copy()

        for column, data_type in schema.items():
            try:
                converted[column] = convert_value(
                    row[column], data_type
                )
            except TransformationError:
                if strict:
                    raise
                logger.warning(
                    "Invalid value in row %d, column %s.",
                    index,
                    column
                )
                converted[column] = None

        rows.append(converted)

    return Table(table.name, table.columns.copy(), rows)


def filter_rows(
    table: Table,
    predicate: Callable[[dict[str, Any]], bool]
) -> Table:
    return Table(
        table.name,
        table.columns.copy(),
        [row.copy() for row in table.rows if predicate(row)]
    )


def add_column(
    table: Table,
    column_name: str,
    function: Callable[[dict[str, Any]], Any]
) -> Table:
    if column_name in table.columns:
        raise TransformationError("Column already exists.")

    columns = table.columns + [column_name]
    rows = []

    for row in table.rows:
        new_row = row.copy()
        new_row[column_name] = function(row.copy())
        rows.append(new_row)

    return Table(table.name, columns, rows)


def merge_tables(
    left: Table,
    right: Table,
    left_key: str,
    right_key: str,
    suffix: str = "_right"
) -> Table:
    """
    Implements a left outer merge.

    Multiple matching right-side rows produce multiple output rows.
    Unmatched left-side rows retain null values for right-side columns.
    """

    if left_key not in left.columns or right_key not in right.columns:
        raise TransformationError("Merge key does not exist.")

    right_columns = [
        column for column in right.columns
        if column != right_key
    ]

    renamed = {}

    for column in right_columns:
        output = column
        if output in left.columns:
            output = column + suffix

        if output in left.columns or output in renamed.values():
            raise TransformationError("Merge creates duplicate columns.")

        renamed[column] = output

    index: dict[Any, list[dict[str, Any]]] = {}

    for row in right.rows:
        key = row[right_key]
        index.setdefault(key, []).append(row)

    columns = left.columns + list(renamed.values())
    result = []

    for left_row in left.rows:
        matches = index.get(left_row[left_key], [])

        if not matches:
            output = left_row.copy()
            output.update({value: None for value in renamed.values()})
            result.append(output)
            continue

        for match in matches:
            output = left_row.copy()
            output.update({
                renamed[column]: match[column]
                for column in right_columns
            })
            result.append(output)

    return Table(
        f"{left.name}_merged_{right.name}",
        columns,
        result
    )


def append_tables(
    tables: list[Table],
    allow_missing_columns: bool = True
) -> Table:
    """
    Combines rows vertically.

    Missing columns are filled with None when allowed.
    """

    if not tables:
        raise TransformationError("At least one table is required.")

    columns = list(dict.fromkeys(
        column
        for table in tables
        for column in table.columns
    ))

    if not allow_missing_columns:
        expected = set(columns)

        if any(set(table.columns) != expected for table in tables):
            raise TransformationError("Table schemas do not match.")

    rows = []

    for table in tables:
        for row in table.rows:
            rows.append({
                column: row.get(column)
                for column in columns
            })

    return Table("appended_data", columns, rows)


def group_sales(table: Table) -> Table:
    groups: dict[str, Decimal] = {}

    for row in table.rows:
        region = row["region"]
        amount = row["amount"]

        groups[region] = groups.get(
            region, Decimal("0")
        ) + amount

    return Table(
        "regional_sales",
        ["region", "total_sales"],
        [
            {"region": region, "total_sales": amount}
            for region, amount in sorted(groups.items())
        ]
    )


def read_csv(path: Path, table_name: str) -> Table:
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise TransformationError("CSV has no header.")

        columns = list(reader.fieldnames)

        rows = [
            {column: clean_text(value) for column, value in row.items()}
            for row in reader
        ]

    table = Table(table_name, columns, rows)
    table.validate()
    return table


@dataclass
class Query:
    name: str
    dependencies: list[str]
    transform: Callable[[dict[str, Table]], Table]
    status: QueryStatus = QueryStatus.CREATED
    result: Table | None = None


class QueryEngine:
    """
    Evaluates dependent queries in topological order.
    """

    def __init__(self):
        self.queries: dict[str, Query] = {}

    def register(self, query: Query) -> None:
        if query.name in self.queries:
            raise DependencyError("Query already registered.")

        self.queries[query.name] = query

    def execution_order(self) -> list[str]:
        visited = set()
        active = set()
        order = []

        def visit(name: str) -> None:
            if name not in self.queries:
                raise DependencyError(f"Unknown query: {name}")

            if name in active:
                raise DependencyError("Circular query dependency.")

            if name in visited:
                return

            active.add(name)

            for dependency in self.queries[name].dependencies:
                visit(dependency)

            active.remove(name)
            visited.add(name)
            order.append(name)

        for name in self.queries:
            visit(name)

        return order

    def execute(self) -> dict[str, Table]:
        results = {}

        for name in self.execution_order():
            query = self.queries[name]
            query.status = QueryStatus.EVALUATING

            try:
                query.result = query.transform(results)
                query.result.validate()
                query.status = QueryStatus.COMPLETED
                results[name] = query.result

                logger.info("Executed query: %s", name)

            except Exception:
                query.status = QueryStatus.FAILED
                raise

        return results


def create_sample_data():
    customers = Table(
        "customers",
        ["customer_id", "customer_name", "region"],
        [
            {"customer_id": "1", "customer_name": "  Alice  ",
             "region": "North"},
            {"customer_id": "2", "customer_name": "Bob",
             "region": "South"},
            {"customer_id": "3", "customer_name": "Alice",
             "region": "North"},
        ]
    )

    orders = Table(
        "orders",
        ["order_id", "customer_id", "amount", "order_date"],
        [
            {"order_id": "101", "customer_id": "1",
             "amount": "1250.50", "order_date": "2026-01-10"},
            {"order_id": "102", "customer_id": "2",
             "amount": "800.00", "order_date": "2026-01-12"},
            {"order_id": "103", "customer_id": "1",
             "amount": "450.25", "order_date": "2026-02-02"},
            {"order_id": "104", "customer_id": "99",
             "amount": "300.00", "order_date": "2026-02-05"},
        ]
    )

    archived_orders = Table(
        "archived_orders",
        orders.columns.copy(),
        [
            {"order_id": "90", "customer_id": "2",
             "amount": "500.00", "order_date": "2025-12-15"}
        ]
    )

    return customers, orders, archived_orders


def main():
    customers, orders, archived_orders = create_sample_data()

    print("\n1. CLEANING")
    cleaned_customers = Table(
        customers.name,
        customers.columns.copy(),
        [
            {
                key: clean_text(value)
                for key, value in row.items()
            }
            for row in customers.rows
        ]
    )

    cleaned_customers = remove_duplicates(
        cleaned_customers, ["customer_id"]
    )
    cleaned_customers.display()

    print("\n2. DATA TYPE CONVERSION")
    typed_orders = change_data_types(
        orders,
        {
            "order_id": DataType.INTEGER,
            "customer_id": DataType.INTEGER,
            "amount": DataType.DECIMAL,
            "order_date": DataType.DATE
        }
    )
    typed_orders.display()

    print("\n3. FILTERING")
    recent_orders = filter_rows(
        typed_orders,
        lambda row: row["amount"] >= Decimal("500")
    )
    recent_orders.display()

    print("\n4. MERGE")
    typed_customers = change_data_types(
        cleaned_customers,
        {"customer_id": DataType.INTEGER}
    )

    merged = merge_tables(
        typed_orders,
        typed_customers,
        "customer_id",
        "customer_id"
    )
    merged.display()

    print("\n5. APPEND")
    typed_archived = change_data_types(
        archived_orders,
        {
            "order_id": DataType.INTEGER,
            "customer_id": DataType.INTEGER,
            "amount": DataType.DECIMAL,
            "order_date": DataType.DATE
        }
    )

    combined = append_tables([
        typed_orders,
        typed_archived
    ])
    combined.display()

    print("\n6. CUSTOM COLUMN")
    enriched = add_column(
        combined,
        "order_category",
        lambda row: (
            "High Value"
            if row["amount"] >= Decimal("1000")
            else "Standard"
        )
    )
    enriched.display()

    print("\n7. GROUPING")
    regional_input = Table(
        "regional_input",
        ["region", "amount"],
        [
            {"region": row["region"], "amount": row["amount"]}
            for row in merged.rows
            if row["region"] is not None
        ]
    )

    group_sales(regional_input).display()

    print("\n8. QUERY DEPENDENCIES")

    engine = QueryEngine()

    engine.register(Query(
        "source",
        [],
        lambda _: typed_orders
    ))

    engine.register(Query(
        "filtered",
        ["source"],
        lambda data: filter_rows(
            data["source"],
            lambda row: row["amount"] > Decimal("400")
        )
    ))

    engine.register(Query(
        "summary",
        ["filtered"],
        lambda data: Table(
            "summary",
            ["order_count", "total_amount"],
            [{
                "order_count": len(data["filtered"].rows),
                "total_amount": sum(
                    (
                        row["amount"]
                        for row in data["filtered"].rows
                    ),
                    Decimal("0")
                )
            }]
        )
    ))

    results = engine.execute()
    results["summary"].display()

    print("\n9. EXPORT")

    output = Path("power_query_output.json")

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "table": enriched.name,
                "columns": enriched.columns,
                "rows": [
                    {
                        key: (
                            value.isoformat()
                            if isinstance(value, (date, datetime))
                            else str(value)
                            if isinstance(value, Decimal)
                            else value
                        )
                        for key, value in row.items()
                    }
                    for row in enriched.rows
                ]
            },
            file,
            indent=2
        )

    print(f"Exported: {output.resolve()}")

    assert len(typed_orders.rows) == 4
    assert len(combined.rows) == 5
    assert len(merged.rows) == 4
    assert engine.queries["summary"].status == QueryStatus.COMPLETED

    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
