"""
Advanced Power Query: Query Folding, Custom Columns, Conditional Columns,
Parameters, and Reusable Transformations

This standalone study script models the core ideas behind advanced Power Query
workflows using Python. Power Query itself uses the M language, but Python is
used here to make the underlying data-transformation mechanics executable and
observable without requiring Power BI or Excel.

The examples progress from fundamental transformation concepts to a small
query-planning engine that distinguishes foldable operations from operations
that must execute locally.

Key Power Query concepts covered:
- Query and transformation pipelines
- Source queries
- Query folding
- Foldable versus non-foldable transformations
- Projection, filtering, sorting, grouping, joins
- Custom columns
- Conditional columns
- Parameters
- Reusable transformation functions
- Type handling
- Null handling
- Error handling
- Transformation ordering
- Performance implications
- Privacy and security considerations
- Incremental-style filtering
- Query diagnostics concepts
- Native-query boundaries
- Advanced reusable transformation patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable, Mapping, Sequence
import math
import statistics
import time


# ============================================================================
# 1. FUNDAMENTALS: TABULAR DATA AND TRANSFORMATIONS
# ============================================================================

Row = dict[str, Any]
Table = list[Row]


def print_section(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_table(rows: Sequence[Row], columns: Sequence[str] | None = None) -> None:
    """Print a small table without external dependencies."""
    if not rows:
        print("(empty table)")
        return

    if columns is None:
        columns = list(rows[0].keys())

    widths = {
        column: max(
            len(str(column)),
            *(len(str(row.get(column, ""))) for row in rows)
        )
        for column in columns
    }

    header = " | ".join(str(column).ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)

    for row in rows:
        print(" | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))


print_section("1. A transformation pipeline")

source_sales: Table = [
    {"OrderID": 1001, "Customer": "Alpha", "Region": "North", "Amount": 1250.0},
    {"OrderID": 1002, "Customer": "Beta", "Region": "South", "Amount": 800.0},
    {"OrderID": 1003, "Customer": "Gamma", "Region": "North", "Amount": 2150.0},
    {"OrderID": 1004, "Customer": "Delta", "Region": "West", "Amount": 430.0},
]

print_table(source_sales)


def filter_rows(table: Iterable[Row], predicate: Callable[[Row], bool]) -> Table:
    """Equivalent in spirit to Table.SelectRows in Power Query."""
    return [dict(row) for row in table if predicate(row)]


def select_columns(table: Iterable[Row], columns: Sequence[str]) -> Table:
    """Equivalent in spirit to Table.SelectColumns."""
    return [{column: row.get(column) for column in columns} for row in table]


def add_column(
    table: Iterable[Row],
    column_name: str,
    expression: Callable[[Row], Any],
) -> Table:
    """Equivalent in spirit to Table.AddColumn."""
    result: Table = []

    for row in table:
        new_row = dict(row)
        new_row[column_name] = expression(row)
        result.append(new_row)

    return result


north_sales = filter_rows(source_sales, lambda row: row["Region"] == "North")
north_sales = select_columns(
    north_sales,
    ["OrderID", "Customer", "Region", "Amount"],
)
north_sales = add_column(
    north_sales,
    "Tax",
    lambda row: round(row["Amount"] * 0.18, 2),
)

print("\nFiltered and transformed rows:")
print_table(north_sales)


# ============================================================================
# 2. POWER QUERY M CONCEPTS
# ============================================================================

print_section("2. Power Query M concepts represented by Python")

m_examples = {
    "filter": 'Table.SelectRows(Source, each [Region] = "North")',
    "select": 'Table.SelectColumns(Source, {"OrderID", "Customer", "Amount"})',
    "custom_column": 'Table.AddColumn(Source, "Tax", each [Amount] * 0.18)',
    "conditional_column": (
        'Table.AddColumn(Source, "Band", '
        'each if [Amount] >= 2000 then "High" else "Standard")'
    ),
    "parameter": 'Table.SelectRows(Source, each [Amount] >= MinimumAmount)',
    "reusable_function": (
        '(inputTable as table, threshold as number) as table => '
        'Table.SelectRows(inputTable, each [Amount] >= threshold)'
    ),
}

for name, expression in m_examples.items():
    print(f"{name:20} -> {expression}")


# ============================================================================
# 3. CUSTOM COLUMNS
# ============================================================================

print_section("3. Custom columns")

def classify_amount(amount: float) -> str:
    """
    A custom-column calculation.

    In Power Query, a custom column is commonly created with an expression
    such as: each [Amount] * 0.18
    """
    if amount < 0:
        return "Invalid"
    if amount >= 2000:
        return "High"
    if amount >= 1000:
        return "Medium"
    return "Low"


with_custom_column = add_column(
    source_sales,
    "AmountBand",
    lambda row: classify_amount(float(row["Amount"])),
)

print_table(with_custom_column)


# ============================================================================
# 4. CONDITIONAL COLUMNS
# ============================================================================

print_section("4. Conditional columns")

def risk_category(row: Row) -> str:
    """
    Represents an ordered if/else business rule.

    Power Query equivalent in M:
        each if [Amount] >= 2000 then "High"
        else if [Amount] >= 1000 then "Medium"
        else "Low"
    """
    amount = row.get("Amount")

    if amount is None:
        return "Unknown"

    if amount >= 2000:
        return "High"

    if amount >= 1000:
        return "Medium"

    return "Low"


conditional_result = add_column(
    source_sales,
    "RiskCategory",
    risk_category,
)

print_table(conditional_result)


# ============================================================================
# 5. NULLS, TYPES, AND ERRORS
# ============================================================================

print_section("5. Null handling, type conversion, and errors")

messy_data: Table = [
    {"Product": "A", "Amount": "1250.50"},
    {"Product": "B", "Amount": None},
    {"Product": "C", "Amount": "not-a-number"},
    {"Product": "D", "Amount": "-20"},
]


def safe_decimal(value: Any) -> Decimal | None:
    """Convert common input values while treating invalid values as null."""
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


typed_data = add_column(
    messy_data,
    "TypedAmount",
    lambda row: safe_decimal(row["Amount"]),
)

print_table(typed_data)


def amount_status(row: Row) -> str:
    amount = row.get("TypedAmount")

    if amount is None:
        return "MissingOrInvalid"

    if amount < 0:
        return "Negative"

    return "Valid"


validated_data = add_column(
    typed_data,
    "Status",
    amount_status,
)

print_table(validated_data)


# ============================================================================
# 6. QUERY FOLDING
# ============================================================================

print_section("6. Query folding")

print(
    """
Query folding means Power Query attempts to translate transformations in a
query into operations understood by the underlying data source.

For a relational database, a conceptual pipeline such as:

    Source -> Filter -> Select Columns -> Sort

may be translated into SQL resembling:

    SELECT OrderID, Customer, Amount
    FROM Sales
    WHERE Region = 'North'
    ORDER BY Amount DESC

The important performance principle is that filtering close to the source
can reduce the amount of data transferred to the Power Query engine.

Not every M transformation can be translated to every source. A transformation
may be foldable for one connector and non-foldable for another.
"""
)


# ============================================================================
# 7. A SIMPLE QUERY PLAN MODEL
# ============================================================================

@dataclass
class Operation:
    """A simplified representation of a Power Query transformation."""

    name: str
    sql_fragment: str | None
    foldable: bool
    description: str


@dataclass
class QueryPlan:
    """A small educational model of a transformation pipeline."""

    source_name: str
    operations: list[Operation] = field(default_factory=list)

    def add(self, operation: Operation) -> "QueryPlan":
        self.operations.append(operation)
        return self

    @property
    def folding_stops_at(self) -> str | None:
        for operation in self.operations:
            if not operation.foldable:
                return operation.name
        return None

    def folded_operations(self) -> list[Operation]:
        result: list[Operation] = []

        for operation in self.operations:
            if not operation.foldable:
                break
            result.append(operation)

        return result

    def generate_sql(self) -> str:
        """
        Generate conceptual SQL for the foldable prefix.

        This is educational and is not intended to replace a connector's
        actual SQL generation.
        """
        folded = self.folded_operations()

        select_clause = "*"
        where_clauses: list[str] = []
        order_clause = None

        for operation in folded:
            if operation.name == "SelectColumns":
                select_clause = operation.sql_fragment or "*"
            elif operation.name == "FilterRows":
                if operation.sql_fragment:
                    where_clauses.append(operation.sql_fragment)
            elif operation.name == "Sort":
                order_clause = operation.sql_fragment

        sql = f"SELECT {select_clause} FROM {self.source_name}"

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        if order_clause:
            sql += " ORDER BY " + order_clause

        return sql + ";"


foldable_plan = (
    QueryPlan("Sales")
    .add(
        Operation(
            "FilterRows",
            "Region = 'North'",
            True,
            "Filters rows using a source-translatable equality predicate.",
        )
    )
    .add(
        Operation(
            "SelectColumns",
            "OrderID, Customer, Amount",
            True,
            "Keeps only required columns.",
        )
    )
    .add(
        Operation(
            "Sort",
            "Amount DESC",
            True,
            "Sorts using a source-supported ordering.",
        )
    )
)

print("Folding stops at:", foldable_plan.folding_stops_at or "end of plan")
print("Conceptual folded SQL:")
print(foldable_plan.generate_sql())


# ============================================================================
# 8. NON-FOLDABLE TRANSFORMATION
# ============================================================================

print_section("8. Folding boundary")

non_foldable_plan = (
    QueryPlan("Sales")
    .add(
        Operation(
            "FilterRows",
            "Region = 'North'",
            True,
            "Foldable source filter.",
        )
    )
    .add(
        Operation(
            "SelectColumns",
            "OrderID, Customer, Amount",
            True,
            "Foldable projection.",
        )
    )
    .add(
        Operation(
            "PythonStyleCustomCalculation",
            None,
            False,
            "Arbitrary local code is not assumed to be source-translatable.",
        )
    )
    .add(
        Operation(
            "Sort",
            "Amount DESC",
            True,
            "This operation appears after the folding boundary.",
        )
    )
)

print(
    "Folding stops at:",
    non_foldable_plan.folding_stops_at,
)
print("Folded SQL prefix:")
print(non_foldable_plan.generate_sql())

print(
    """
A folding boundary matters because operations after the boundary may execute
inside the Power Query engine rather than at the source. Depending on the
connector and operation, this can increase source reads, memory use, CPU use,
refresh duration, and data transfer.
"""
)


# ============================================================================
# 9. OPERATION ORDER MATTERS
# ============================================================================

print_section("9. Transformation ordering")

large_dataset: Table = [
    {
        "OrderID": index,
        "Region": "North" if index % 10 == 0 else "Other",
        "Amount": float(index * 10),
    }
    for index in range(1, 10001)
]


def expensive_local_calculation(row: Row) -> float:
    """Artificially represent a CPU-heavy custom transformation."""
    value = float(row["Amount"])
    return math.sqrt(value + 1) * math.log(value + 2)


start = time.perf_counter()

late_filter = add_column(
    large_dataset,
    "Calculated",
    expensive_local_calculation,
)
late_filter = filter_rows(
    late_filter,
    lambda row: row["Region"] == "North",
)

late_duration = time.perf_counter() - start

start = time.perf_counter()

early_filter = filter_rows(
    large_dataset,
    lambda row: row["Region"] == "North",
)
early_filter = add_column(
    early_filter,
    "Calculated",
    expensive_local_calculation,
)

early_duration = time.perf_counter() - start

print(f"Rows before filtering: {len(large_dataset):,}")
print(f"Rows after filtering:  {len(early_filter):,}")
print(f"Late filtering time:   {late_duration:.6f} seconds")
print(f"Early filtering time:  {early_duration:.6f} seconds")

print(
    """
The exact timings depend on hardware and runtime, but the structural lesson is
more important: reduce rows and columns as early as practical, especially
before expensive non-foldable work.
"""
)


# ============================================================================
# 10. PARAMETERS
# ============================================================================

print_section("10. Parameters")

@dataclass(frozen=True)
class QueryParameters:
    minimum_amount: float = 1000.0
    selected_region: str = "North"
    include_negative: bool = False


parameters = QueryParameters(
    minimum_amount=1000,
    selected_region="North",
    include_negative=False,
)


def apply_parameters(table: Table, params: QueryParameters) -> Table:
    """
    Apply reusable parameter-driven filtering.

    Conceptual Power Query M:
        Table.SelectRows(
            Source,
            each [Amount] >= MinimumAmount and [Region] = SelectedRegion
        )
    """
    def predicate(row: Row) -> bool:
        amount = row.get("Amount")
        region = row.get("Region")

        if amount is None:
            return False

        if not params.include_negative and amount < 0:
            return False

        return (
            amount >= params.minimum_amount
            and region == params.selected_region
        )

    return filter_rows(table, predicate)


parameterized_result = apply_parameters(source_sales, parameters)
print_table(parameterized_result)


# ============================================================================
# 11. REUSABLE TRANSFORMATION FUNCTIONS
# ============================================================================

print_section("11. Reusable transformations")

def standardize_sales_table(
    table: Iterable[Row],
    *,
    minimum_amount: float = 0.0,
) -> Table:
    """
    Reusable transformation pipeline.

    Power Query functions often accept a table and parameters and return
    another table. The same idea is modeled here with a Python function.
    """
    selected = select_columns(
        table,
        ["OrderID", "Customer", "Region", "Amount"],
    )

    filtered = filter_rows(
        selected,
        lambda row: (
            row.get("Amount") is not None
            and row["Amount"] >= minimum_amount
        ),
    )

    normalized = add_column(
        filtered,
        "CustomerNormalized",
        lambda row: str(row["Customer"]).strip().upper(),
    )

    return normalized


reusable_result = standardize_sales_table(
    source_sales,
    minimum_amount=500,
)

print_table(reusable_result)


# ============================================================================
# 12. FUNCTION COMPOSITION
# ============================================================================

print_section("12. Function composition")

Transformation = Callable[[Table], Table]


def compose(*transformations: Transformation) -> Transformation:
    """Compose table transformations into one reusable pipeline."""
    def pipeline(table: Table) -> Table:
        result = table
        for transformation in transformations:
            result = transformation(result)
        return result

    return pipeline


north_only: Transformation = lambda table: filter_rows(
    table,
    lambda row: row.get("Region") == "North",
)

high_value: Transformation = lambda table: filter_rows(
    table,
    lambda row: row.get("Amount", 0) >= 1000,
)

add_margin_estimate: Transformation = lambda table: add_column(
    table,
    "EstimatedMargin",
    lambda row: round(float(row["Amount"]) * 0.22, 2),
)

sales_pipeline = compose(
    north_only,
    high_value,
    add_margin_estimate,
)

composed_result = sales_pipeline(source_sales)
print_table(composed_result)


# ============================================================================
# 13. CONDITIONAL LOGIC WITH MULTIPLE RULES
# ============================================================================

print_section("13. Complex conditional logic")

customer_data: Table = [
    {"Customer": "A", "Amount": 5000, "DaysOverdue": 0, "Region": "North"},
    {"Customer": "B", "Amount": 1500, "DaysOverdue": 15, "Region": "South"},
    {"Customer": "C", "Amount": 700, "DaysOverdue": 45, "Region": "West"},
    {"Customer": "D", "Amount": 3000, "DaysOverdue": 90, "Region": "North"},
]


def credit_action(row: Row) -> str:
    amount = row.get("Amount")
    overdue = row.get("DaysOverdue")

    if amount is None or overdue is None:
        return "Review"

    if overdue >= 60:
        return "Collections"

    if overdue >= 30 and amount >= 2000:
        return "SeniorReview"

    if overdue >= 15:
        return "Reminder"

    if amount >= 3000:
        return "Preferred"

    return "Standard"


credit_result = add_column(
    customer_data,
    "CreditAction",
    credit_action,
)

print_table(credit_result)


# ============================================================================
# 14. GROUPING AND AGGREGATION
# ============================================================================

print_section("14. Grouping and aggregation")

def group_sum(
    table: Iterable[Row],
    group_column: str,
    value_column: str,
) -> Table:
    """Educational equivalent of grouping followed by Sum."""
    totals: dict[Any, float] = {}

    for row in table:
        key = row.get(group_column)
        value = row.get(value_column)

        if value is None:
            continue

        totals[key] = totals.get(key, 0.0) + float(value)

    return [
        {group_column: key, f"Total{value_column}": round(total, 2)}
        for key, total in totals.items()
    ]


grouped_sales = group_sum(
    source_sales,
    "Region",
    "Amount",
)

print_table(grouped_sales)


# ============================================================================
# 15. JOINS
# ============================================================================

print_section("15. Joins")

customers: Table = [
    {"Customer": "Alpha", "Segment": "Enterprise"},
    {"Customer": "Beta", "Segment": "SMB"},
    {"Customer": "Gamma", "Segment": "Enterprise"},
    {"Customer": "Delta", "Segment": "SMB"},
]


def inner_join(
    left: Iterable[Row],
    right: Iterable[Row],
    key: str,
    suffix: str = "_right",
) -> Table:
    """
    Hash-based inner join.

    This demonstrates why appropriate source-side joins can be substantially
    more efficient than materializing large tables locally.
    """
    index: dict[Any, list[Row]] = {}

    for row in right:
        index.setdefault(row.get(key), []).append(row)

    result: Table = []

    for left_row in left:
        matches = index.get(left_row.get(key), [])

        for right_row in matches:
            merged = dict(left_row)

            for column, value in right_row.items():
                if column == key:
                    continue

                target_column = (
                    column
                    if column not in merged
                    else column + suffix
                )

                merged[target_column] = value

            result.append(merged)

    return result


joined = inner_join(
    source_sales,
    customers,
    "Customer",
)

print_table(joined)


# ============================================================================
# 16. SOURCE TYPES AND FOLDABILITY
# ============================================================================

print_section("16. Connector-aware thinking")

connector_examples = [
    ("SQL Server", "Relational database", "Often extensive folding"),
    ("PostgreSQL", "Relational database", "Many relational operations fold"),
    ("Excel workbook", "File source", "Folding is much more limited"),
    ("CSV file", "File source", "Most transformation work is local"),
    ("OData", "Web/structured source", "Connector-dependent folding"),
    ("Web API", "HTTP service", "Folding depends strongly on connector"),
]

print_table(
    [
        {
            "Source": source,
            "Category": category,
            "Typical behavior": behavior,
        }
        for source, category, behavior in connector_examples
    ]
)

print(
    """
Foldability is not a property of an M expression in isolation.

It depends on:
- the connector,
- the source system,
- the specific operation,
- the expression,
- the data type,
- connector capabilities,
- and sometimes the point in the transformation pipeline.

Therefore, "this operation folds" should normally be understood as
"this operation can fold in this particular source/connector context."
"""
)


# ============================================================================
# 17. QUERY DIAGNOSTICS MODEL
# ============================================================================

print_section("17. Query diagnostics concepts")

@dataclass
class QueryMetrics:
    rows_read: int
    rows_returned: int
    elapsed_ms: float
    source_operations: int
    local_operations: int


def estimate_metrics(
    source_rows: int,
    returned_rows: int,
    operations: Sequence[Operation],
) -> QueryMetrics:
    """Simple educational performance model."""
    foldable_count = 0
    local_count = 0

    folding_active = True

    for operation in operations:
        if folding_active and operation.foldable:
            foldable_count += 1
        else:
            folding_active = False
            local_count += 1

    estimated_rows_read = (
        returned_rows
        if folding_active
        else source_rows
    )

    estimated_elapsed = (
        2.0
        + estimated_rows_read * 0.002
        + local_count * estimated_rows_read * 0.001
    )

    return QueryMetrics(
        rows_read=estimated_rows_read,
        rows_returned=returned_rows,
        elapsed_ms=estimated_elapsed,
        source_operations=foldable_count,
        local_operations=local_count,
    )


metrics = estimate_metrics(
    source_rows=1_000_000,
    returned_rows=25_000,
    operations=non_foldable_plan.operations,
)

print(metrics)


# ============================================================================
# 18. INCREMENTAL-STYLE DATE FILTERING
# ============================================================================

print_section("18. Parameterized date filtering")

transactions: Table = [
    {"TransactionID": 1, "TransactionDate": date(2026, 9, 1), "Amount": 100},
    {"TransactionID": 2, "TransactionDate": date(2026, 9, 5), "Amount": 250},
    {"TransactionID": 3, "TransactionDate": date(2026, 8, 20), "Amount": 900},
    {"TransactionID": 4, "TransactionDate": date(2026, 9, 15), "Amount": 450},
]

range_start = date(2026, 9, 1)
range_end = date(2026, 9, 16)


def filter_date_range(
    table: Iterable[Row],
    column: str,
    start_date: date,
    end_date: date,
) -> Table:
    """
    Use an inclusive start and exclusive end.

    The half-open interval [start, end) avoids overlap when adjacent date
    partitions are processed.
    """
    return filter_rows(
        table,
        lambda row: (
            row.get(column) is not None
            and start_date <= row[column] < end_date
        ),
    )


date_filtered = filter_date_range(
    transactions,
    "TransactionDate",
    range_start,
    range_end,
)

print_table(date_filtered)


# ============================================================================
# 19. REUSABLE NORMALIZATION FUNCTION
# ============================================================================

print_section("19. Reusable data-cleaning function")

def normalize_customer_names(table: Iterable[Row]) -> Table:
    """
    Normalize whitespace and capitalization.

    In Power Query, such logic is often encapsulated in a reusable M function
    and invoked against multiple tables.
    """
    result: Table = []

    for row in table:
        new_row = dict(row)
        value = new_row.get("Customer")

        if value is not None:
            new_row["Customer"] = " ".join(str(value).split()).title()

        result.append(new_row)

    return result


dirty_customers: Table = [
    {"Customer": "  alpha   ltd "},
    {"Customer": "BETA LTD"},
    {"Customer": None},
]

print_table(normalize_customer_names(dirty_customers))


# ============================================================================
# 20. CACHING / BUFFERING CONCEPT
# ============================================================================

print_section("20. Buffering and repeated evaluation")

class LazyTable:
    """
    Educational lazy table.

    Power Query has lazy evaluation characteristics. Buffering can materialize
    data, but buffering is not a universal performance optimization.

    This class demonstrates the difference between repeatedly executing a
    producer and caching its materialized result.
    """

    def __init__(self, producer: Callable[[], Table]):
        self._producer = producer
        self._cache: Table | None = None

    def evaluate(self) -> Table:
        return self._producer()

    def buffer(self) -> Table:
        if self._cache is None:
            self._cache = self._producer()
        return self._cache


evaluation_counter = {"count": 0}


def expensive_source() -> Table:
    evaluation_counter["count"] += 1
    return [{"ID": 1}, {"ID": 2}]


lazy_table = LazyTable(expensive_source)

lazy_table.evaluate()
lazy_table.evaluate()

print("Evaluations without buffering:", evaluation_counter["count"])

evaluation_counter["count"] = 0

lazy_table = LazyTable(expensive_source)
lazy_table.buffer()
lazy_table.buffer()

print("Evaluations with educational buffer:", evaluation_counter["count"])

print(
    """
Important caution:
Buffering/materialization can increase memory use and can sometimes prevent
beneficial query folding. It should be used for a demonstrated reason rather
than as a default performance technique.
"""
)


# ============================================================================
# 21. SECURITY CONSIDERATIONS
# ============================================================================

print_section("21. Security and governance considerations")

print(
    """
Power Query security is not limited to M syntax.

Important considerations include:
- Do not embed passwords or access tokens directly in M expressions.
- Use managed credentials and the platform's credential mechanisms.
- Treat parameters as inputs, not automatically as trusted values.
- Avoid constructing unsafe native SQL from untrusted strings.
- Understand data-source privacy levels and their effect on query combination.
- Restrict access to sensitive source data.
- Apply least privilege to database accounts.
- Be careful when combining sources with different confidentiality levels.
- Avoid unnecessarily materializing sensitive data into intermediate files.
- Validate external inputs used by reusable functions.
- Review native queries and custom connectors before production use.
"""
)


# ============================================================================
# 22. NATIVE QUERY BOUNDARY
# ============================================================================

print_section("22. Native query and folding boundaries")

native_query_plan = QueryPlan("Sales").add(
    Operation(
        "NativeQuery",
        "OrderID, Customer, Region, Amount",
        False,
        "A native query can establish a source-side operation but may create "
        "connector-specific folding constraints.",
    )
)

print("Native-query operation:", native_query_plan.operations[0].name)
print("Folding state:", "boundary" if not native_query_plan.operations[0].foldable else "active")


# ============================================================================
# 23. EDGE CASES
# ============================================================================

print_section("23. Important edge cases")

edge_cases: Table = [
    {"ID": 1, "Amount": 0},
    {"ID": 2, "Amount": None},
    {"ID": 3, "Amount": -100},
    {"ID": 4, "Amount": float("nan")},
    {"ID": 5, "Amount": 10_000_000_000},
]


def safe_band(row: Row) -> str:
    amount = row.get("Amount")

    if amount is None:
        return "Null"

    if isinstance(amount, float) and math.isnan(amount):
        return "NaN"

    if amount < 0:
        return "Negative"

    if amount == 0:
        return "Zero"

    if amount >= 1_000_000:
        return "VeryHigh"

    return "Positive"


edge_result = add_column(
    edge_cases,
    "Band",
    safe_band,
)

print_table(edge_result)


# ============================================================================
# 24. COMMON MISTAKES
# ============================================================================

print_section("24. Common mistakes")

mistakes = [
    (
        "Filtering too late",
        "Large datasets are carried through expensive transformations before reduction."
    ),
    (
        "Assuming every M function folds",
        "Foldability depends on the source and connector."
    ),
    (
        "Ignoring data types",
        "Text, number, date, datetime, logical, and null values behave differently."
    ),
    (
        "Overusing custom columns",
        "Complex local logic may prevent folding or increase refresh cost."
    ),
    (
        "Using parameters without validation",
        "Unexpected parameter values can produce empty or incorrect results."
    ),
    (
        "Buffering everything",
        "Materialization can increase memory use and interrupt useful source execution."
    ),
    (
        "Hard-coding business rules",
        "Repeated rules become difficult to maintain and test."
    ),
    (
        "Ignoring privacy boundaries",
        "Combining sources can have governance and data-isolation implications."
    ),
]

for mistake, impact in mistakes:
    print(f"- {mistake}: {impact}")


# ============================================================================
# 25. ADVANCED DESIGN: TRANSFORMATION SPECIFICATIONS
# ============================================================================

print_section("25. Declarative transformation specifications")

@dataclass(frozen=True)
class TransformationSpec:
    name: str
    function: Transformation
    foldable: bool
    purpose: str


def execute_specs(
    table: Table,
    specifications: Sequence[TransformationSpec],
) -> Table:
    """Execute a reusable declarative transformation pipeline."""
    result = table

    for specification in specifications:
        result = specification.function(result)

    return result


specifications = [
    TransformationSpec(
        "Filter North",
        north_only,
        True,
        "Reduce source rows using a simple predicate.",
    ),
    TransformationSpec(
        "Filter High Value",
        high_value,
        True,
        "Reduce rows further using an amount predicate.",
    ),
    TransformationSpec(
        "Calculate Margin",
        add_margin_estimate,
        False,
        "Apply a local custom calculation.",
    ),
]

spec_result = execute_specs(source_sales, specifications)
print_table(spec_result)

print("\nTransformation specification:")
for spec in specifications:
    print(
        f"{spec.name:22} | "
        f"foldable={spec.foldable!s:5} | "
        f"{spec.purpose}"
    )


# ============================================================================
# 26. PERFORMANCE COMPLEXITY
# ============================================================================

print_section("26. Complexity considerations")

print(
    """
Common conceptual costs:

Filtering a table:
    O(n)

Selecting columns:
    O(n * c) in a simple row/column model

Hash-based join:
    Average O(n + m)

Sorting:
    Usually O(n log n)

Grouping with a hash table:
    Average O(n)

A source database can often execute filtering, joining, grouping, and sorting
using indexes, query optimizers, statistics, parallel execution, and
source-specific algorithms. Performing equivalent work locally can therefore
have very different performance characteristics.
"""
)


# ============================================================================
# 27. TESTING REUSABLE TRANSFORMATIONS
# ============================================================================

print_section("27. Testing transformations")

def assert_equal(actual: Any, expected: Any, description: str) -> None:
    if actual != expected:
        raise AssertionError(
            f"{description}: expected {expected!r}, got {actual!r}"
        )

    print(f"PASS: {description}")


test_table = [
    {"Customer": "  alpha  ", "Amount": 100},
    {"Customer": "Beta", "Amount": 500},
]

cleaned = standardize_sales_table(
    test_table,
    minimum_amount=100,
)

assert_equal(
    cleaned[0]["CustomerNormalized"],
    "ALPHA",
    "Customer normalization",
)

assert_equal(
    len(cleaned),
    2,
    "Minimum amount filtering",
)

assert_equal(
    standardize_sales_table(test_table, minimum_amount=600),
    [],
    "Filtering all rows",
)


# ============================================================================
# 28. A COMPLETE MINI PIPELINE
# ============================================================================

print_section("28. Complete mini ETL pipeline")

raw_orders: Table = [
    {
        "OrderID": 1,
        "Customer": " alpha ",
        "Region": "North",
        "Amount": "1500",
        "OrderDate": date(2026, 9, 1),
    },
    {
        "OrderID": 2,
        "Customer": "beta",
        "Region": "South",
        "Amount": "700",
        "OrderDate": date(2026, 9, 3),
    },
    {
        "OrderID": 3,
        "Customer": "gamma",
        "Region": "North",
        "Amount": "2500",
        "OrderDate": date(2026, 9, 5),
    },
    {
        "OrderID": 4,
        "Customer": "delta",
        "Region": "North",
        "Amount": "bad",
        "OrderDate": date(2026, 9, 7),
    },
]


def production_style_pipeline(
    table: Iterable[Row],
    *,
    region: str,
    minimum_amount: Decimal,
    start_date: date,
    end_date: date,
) -> Table:
    """
    Demonstrates an ordered, parameterized transformation pipeline.

    The conceptual order is:
        1. Restrict source rows.
        2. Keep required fields.
        3. Convert types.
        4. Remove invalid values.
        5. Normalize text.
        6. Add business classifications.
    """
    result = filter_rows(
        table,
        lambda row: (
            row.get("Region") == region
            and row.get("OrderDate") is not None
            and start_date <= row["OrderDate"] < end_date
        ),
    )

    result = select_columns(
        result,
        ["OrderID", "Customer", "Region", "Amount", "OrderDate"],
    )

    result = add_column(
        result,
        "AmountDecimal",
        lambda row: safe_decimal(row.get("Amount")),
    )

    result = filter_rows(
        result,
        lambda row: (
            row.get("AmountDecimal") is not None
            and row["AmountDecimal"] >= minimum_amount
        ),
    )

    result = add_column(
        result,
        "CustomerNormalized",
        lambda row: " ".join(str(row["Customer"]).split()).title(),
    )

    result = add_column(
        result,
        "AmountBand",
        lambda row: (
            "High"
            if row["AmountDecimal"] >= Decimal("2000")
            else "Standard"
        ),
    )

    return result


production_result = production_style_pipeline(
    raw_orders,
    region="North",
    minimum_amount=Decimal("1000"),
    start_date=date(2026, 9, 1),
    end_date=date(2026, 10, 1),
)

print_table(production_result)


# ============================================================================
# 29. FINAL CONCEPT CHECK
# ============================================================================

print_section("29. Concept check")

questions = [
    (
        "What is query folding?",
        "Translating supported transformations into source-side operations."
    ),
    (
        "Why filter early?",
        "To reduce rows before expensive processing and potentially reduce source transfer."
    ),
    (
        "What is a custom column?",
        "A derived field calculated from existing row values or other expressions."
    ),
    (
        "What is a conditional column?",
        "A derived field whose value depends on ordered business rules."
    ),
    (
        "What is a parameter?",
        "A configurable input used to control a query or transformation."
    ),
    (
        "Why use reusable functions?",
        "To centralize transformation logic and apply it consistently."
    ),
    (
        "Does every transformation fold?",
        "No. Folding depends on the source, connector, expression, and context."
    ),
]

for question, answer in questions:
    print(f"\nQ: {question}\nA: {answer}")


print_section("Study file execution completed")
print(
    "The examples demonstrate Power Query concepts through executable Python "
    "models, including folding-aware pipeline design, custom and conditional "
    "columns, parameters, reusable transformations, validation, performance, "
    "and production-oriented considerations."
)
