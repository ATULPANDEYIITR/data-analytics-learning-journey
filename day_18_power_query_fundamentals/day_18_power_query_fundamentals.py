"""
Power Query Fundamentals: ETL, Importing, Transformation, Data Types,
Filtering, Merging, and Appending

This standalone study script models the core ideas behind Power Query
using only Python's standard library.

Power Query is an ETL/data-preparation technology. Its central workflow is:

    Extract -> Transform -> Load

The examples below use Python to make the same data-engineering concepts
visible without requiring Excel, Power BI, or third-party packages.

Topics demonstrated:
- ETL fundamentals
- Source ingestion
- Schema inspection
- Data types
- Type conversion
- Missing values
- Text and numeric transformations
- Filtering
- Sorting
- Column selection and renaming
- Derived columns
- Data validation
- Deduplication
- Grouping and aggregation
- Joins/merges
- Appending
- Query-style pipelines
- Query folding as a conceptual optimization
- Error handling
- Data quality checks
- Idempotent transformations
- Reproducible pipelines
- Performance considerations
- A complete sales-data ETL case study
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable
import csv
import io
import json
import math
import statistics
import time


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL ETL CONCEPTS
# ---------------------------------------------------------------------------

print("=" * 78)
print("POWER QUERY FUNDAMENTALS: ETL WITH PYTHON")
print("=" * 78)

print(
    """
ETL means:

Extract:
    Obtain data from a source such as CSV, Excel, SQL, JSON, an API, or
    another application.

Transform:
    Clean, type, filter, reshape, combine, validate, and enrich the data.

Load:
    Put the prepared result into a destination such as a worksheet,
    database, data model, report, or application.

Power Query organizes these operations as repeatable query steps.
"""
)


# ---------------------------------------------------------------------------
# 2. EXTRACT: IMPORTING DATA
# ---------------------------------------------------------------------------

sales_csv = """OrderID,OrderDate,CustomerID,ProductID,Quantity,UnitPrice,Region
1001,2026-01-05,C001,P100,2,1250.50,North
1002,2026-01-06,C002,P200,5,299.99,South
1003,2026-01-07,C003,P100,1,1250.50,West
1004,2026-01-08,C001,P300,3,850.00,North
1005,2026-01-09,C004,P200,4,299.99,East
1006,2026-01-10,C005,P400,2,1750.00,South
1007,2026-01-11,C006,P300,6,850.00,West
1008,2026-01-12,C007,P100,2,1250.50,East
1009,2026-01-13,C008,P200,1,299.99,North
1010,2026-01-14,C009,P400,3,1750.00,South
"""

customers_csv = """CustomerID,CustomerName,Segment
C001,Atul Pandey,Professional
C002,Neha Sharma,Enterprise
C003,Rahul Verma,SMB
C004,Priya Singh,Enterprise
C005,Arjun Mehta,Professional
C006,Simran Kaur,SMB
C007,Karan Gupta,Professional
C008,Ananya Rao,Enterprise
C009,Vivek Mishra,SMB
"""

products_csv = """ProductID,ProductName,Category
P100,Laptop,Computing
P200,Keyboard,Accessories
P300,Monitor,Computing
P400,Server,Infrastructure
"""


def read_csv_text(text: str) -> list[dict[str, str]]:
    """Extract rows from CSV text into Python dictionaries."""
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


sales_raw = read_csv_text(sales_csv)
customers_raw = read_csv_text(customers_csv)
products_raw = read_csv_text(products_csv)

print("\nEXTRACTED SALES ROWS:", len(sales_raw))
print("FIRST RAW ROW:", sales_raw[0])


# ---------------------------------------------------------------------------
# 3. SCHEMA AND DATA TYPES
# ---------------------------------------------------------------------------

def inspect_schema(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    """
    Inspect Python-level types in each column.

    Power Query explicitly tracks column data types. Correct typing matters
    because filtering, arithmetic, dates, sorting, and joins depend on it.
    """
    schema: dict[str, set[str]] = {}

    if not rows:
        return schema

    for column in rows[0]:
        schema[column] = {type(row.get(column)).__name__ for row in rows}

    return schema


print("\nRAW SCHEMA:")
for column, types in inspect_schema(sales_raw).items():
    print(f"  {column}: {', '.join(sorted(types))}")

print(
    """
CSV extraction initially produces text values. A numeric-looking "5" is
still text until explicitly converted. A date-looking "2026-01-05" is
also text until converted to a date.

This corresponds to the Power Query idea of assigning correct data types
after importing data.
"""
)


# ---------------------------------------------------------------------------
# 4. DATA TYPE CONVERSION
# ---------------------------------------------------------------------------

def to_integer(value: Any) -> int:
    """Convert a value to int while rejecting invalid values."""
    if value is None or str(value).strip() == "":
        raise ValueError("Integer value is missing")

    return int(str(value).strip())


def to_decimal(value: Any) -> Decimal:
    """Convert numeric input to Decimal for exact monetary arithmetic."""
    if value is None or str(value).strip() == "":
        raise ValueError("Decimal value is missing")

    try:
        return Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def to_date(value: Any) -> datetime:
    """Convert ISO date text to a Python datetime."""
    if value is None or str(value).strip() == "":
        raise ValueError("Date value is missing")

    return datetime.strptime(str(value).strip(), "%Y-%m-%d")


def type_sales_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Apply an explicit schema to sales data."""
    typed = []

    for row in rows:
        typed.append(
            {
                "OrderID": to_integer(row["OrderID"]),
                "OrderDate": to_date(row["OrderDate"]),
                "CustomerID": row["CustomerID"].strip(),
                "ProductID": row["ProductID"].strip(),
                "Quantity": to_integer(row["Quantity"]),
                "UnitPrice": to_decimal(row["UnitPrice"]),
                "Region": row["Region"].strip(),
            }
        )

    return typed


sales = type_sales_rows(sales_raw)

print("\nTYPED FIRST ROW:")
for key, value in sales[0].items():
    print(f"  {key}: {value!r} ({type(value).__name__})")


# ---------------------------------------------------------------------------
# 5. BASIC TRANSFORMATIONS
# ---------------------------------------------------------------------------

def clean_text(value: str) -> str:
    """
    Normalize text.

    Equivalent concepts in Power Query include Trim, Clean, Replace Values,
    and text transformation functions.
    """
    return " ".join(value.strip().split())


def clean_sales_text(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []

    for row in rows:
        new_row = dict(row)
        new_row["CustomerID"] = clean_text(new_row["CustomerID"])
        new_row["ProductID"] = clean_text(new_row["ProductID"])
        new_row["Region"] = clean_text(new_row["Region"]).title()
        result.append(new_row)

    return result


sales = clean_sales_text(sales)


# ---------------------------------------------------------------------------
# 6. DERIVED COLUMNS
# ---------------------------------------------------------------------------

def add_sales_amount(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Add a calculated column.

    In Power Query this corresponds conceptually to adding a Custom Column.
    """
    result = []

    for row in rows:
        new_row = dict(row)
        new_row["SalesAmount"] = (
            Decimal(new_row["Quantity"]) * new_row["UnitPrice"]
        )
        result.append(new_row)

    return result


sales = add_sales_amount(sales)

print("\nCALCULATED COLUMN:")
print(
    sales[0]["Quantity"],
    "*",
    sales[0]["UnitPrice"],
    "=",
    sales[0]["SalesAmount"],
)


# ---------------------------------------------------------------------------
# 7. FILTERING
# ---------------------------------------------------------------------------

def filter_rows(
    rows: Iterable[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """
    Generic filtering function.

    Power Query filtering removes rows that do not satisfy conditions.
    """
    return [row for row in rows if predicate(row)]


north_sales = filter_rows(sales, lambda row: row["Region"] == "North")

large_orders = filter_rows(sales, lambda row: row["Quantity"] >= 4)

high_value_orders = filter_rows(
    sales,
    lambda row: row["SalesAmount"] >= Decimal("2000"),
)

print("\nFILTERING")
print("North rows:", len(north_sales))
print("Quantity >= 4:", len(large_orders))
print("SalesAmount >= 2000:", len(high_value_orders))


# ---------------------------------------------------------------------------
# 8. SELECTING AND RENAMING COLUMNS
# ---------------------------------------------------------------------------

def select_columns(
    rows: list[dict[str, Any]],
    columns: list[str],
) -> list[dict[str, Any]]:
    """Keep only selected columns."""
    return [{column: row[column] for column in columns} for row in rows]


def rename_columns(
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Rename columns without changing their values."""
    result = []

    for row in rows:
        result.append(
            {
                mapping.get(column, column): value
                for column, value in row.items()
            }
        )

    return result


compact_sales = select_columns(
    sales,
    ["OrderID", "OrderDate", "CustomerID", "SalesAmount"],
)

compact_sales = rename_columns(
    compact_sales,
    {"SalesAmount": "Revenue"},
)

print("\nSELECTED AND RENAMED COLUMNS:")
print(compact_sales[0])


# ---------------------------------------------------------------------------
# 9. SORTING
# ---------------------------------------------------------------------------

sales_by_value = sorted(
    sales,
    key=lambda row: row["SalesAmount"],
    reverse=True,
)

print("\nTOP THREE ORDERS BY VALUE:")
for row in sales_by_value[:3]:
    print(row["OrderID"], row["SalesAmount"])


# ---------------------------------------------------------------------------
# 10. MISSING VALUES AND ERROR HANDLING
# ---------------------------------------------------------------------------

def safe_decimal(value: Any) -> Decimal | None:
    """
    Return None rather than terminating the complete ETL pipeline.

    Power Query can represent missing values as null and can handle errors
    explicitly. Production pipelines should distinguish valid nulls from
    malformed values rather than silently hiding data-quality problems.
    """
    try:
        if value is None or str(value).strip() == "":
            return None
        return to_decimal(value)
    except ValueError:
        return None


dirty_rows = [
    {"Product": "Laptop", "Price": "1250.50"},
    {"Product": "Keyboard", "Price": ""},
    {"Product": "Monitor", "Price": "not-a-number"},
]

print("\nMISSING VALUE / ERROR HANDLING:")
for row in dirty_rows:
    print(row["Product"], "=>", safe_decimal(row["Price"]))


# ---------------------------------------------------------------------------
# 11. DATA VALIDATION
# ---------------------------------------------------------------------------

def validate_sales(rows: list[dict[str, Any]]) -> list[str]:
    """Return validation errors instead of silently accepting bad records."""
    errors = []

    for row_number, row in enumerate(rows, start=1):
        if row["Quantity"] <= 0:
            errors.append(
                f"Row {row_number}: Quantity must be greater than zero"
            )

        if row["UnitPrice"] < 0:
            errors.append(
                f"Row {row_number}: UnitPrice cannot be negative"
            )

        if not row["CustomerID"]:
            errors.append(f"Row {row_number}: CustomerID is required")

        if not row["ProductID"]:
            errors.append(f"Row {row_number}: ProductID is required")

    return errors


validation_errors = validate_sales(sales)

print("\nVALIDATION:")
print("Errors:", validation_errors if validation_errors else "None")


# ---------------------------------------------------------------------------
# 12. DEDUPLICATION
# ---------------------------------------------------------------------------

def distinct_rows(
    rows: list[dict[str, Any]],
    key_columns: list[str],
) -> list[dict[str, Any]]:
    """
    Remove duplicate business keys.

    Choosing the correct key is essential. Removing duplicates using every
    column is not always equivalent to identifying duplicate business rows.
    """
    seen: set[tuple[Any, ...]] = set()
    result = []

    for row in rows:
        key = tuple(row[column] for column in key_columns)

        if key not in seen:
            seen.add(key)
            result.append(row)

    return result


duplicate_demo = sales + [dict(sales[0])]

print("\nDEDUPLICATION:")
print("Before:", len(duplicate_demo))
print(
    "After:",
    len(distinct_rows(duplicate_demo, ["OrderID"])),
)


# ---------------------------------------------------------------------------
# 13. MERGING DATASETS
# ---------------------------------------------------------------------------

def index_rows(
    rows: list[dict[str, Any]],
    key: str,
) -> dict[Any, dict[str, Any]]:
    """
    Build an index for efficient equality joins.

    A hash index changes a repeated linear lookup into approximately O(1)
    average lookup time per row.
    """
    index = {}

    for row in rows:
        index[row[key]] = row

    return index


def left_merge(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    left_key: str,
    right_key: str,
    right_prefix: str = "",
) -> list[dict[str, Any]]:
    """
    Perform a left join.

    Conceptually this corresponds to Power Query Merge Queries with a
    Left Outer join.
    """
    right_index = index_rows(right, right_key)
    result = []

    for left_row in left:
        merged = dict(left_row)
        right_row = right_index.get(left_row[left_key])

        if right_row is None:
            for key in right[0]:
                if key != right_key:
                    merged[f"{right_prefix}{key}"] = None
        else:
            for key, value in right_row.items():
                if key != right_key:
                    merged[f"{right_prefix}{key}"] = value

        result.append(merged)

    return result


customers = [
    {
        "CustomerID": row["CustomerID"].strip(),
        "CustomerName": row["CustomerName"].strip(),
        "Segment": row["Segment"].strip(),
    }
    for row in customers_raw
]

products = [
    {
        "ProductID": row["ProductID"].strip(),
        "ProductName": row["ProductName"].strip(),
        "Category": row["Category"].strip(),
    }
    for row in products_raw
]

sales_with_customers = left_merge(
    sales,
    customers,
    "CustomerID",
    "CustomerID",
)

sales_enriched = left_merge(
    sales_with_customers,
    products,
    "ProductID",
    "ProductID",
)

print("\nMERGED DATA:")
for row in sales_enriched[:2]:
    print(row)


# ---------------------------------------------------------------------------
# 14. JOIN TYPES
# ---------------------------------------------------------------------------

def inner_merge(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    left_key: str,
    right_key: str,
) -> list[dict[str, Any]]:
    """Return rows for which matching keys exist on both sides."""
    right_index = index_rows(right, right_key)
    result = []

    for left_row in left:
        right_row = right_index.get(left_row[left_key])

        if right_row is not None:
            merged = dict(left_row)

            for key, value in right_row.items():
                if key != right_key:
                    merged[f"right_{key}"] = value

            result.append(merged)

    return result


inner_result = inner_merge(
    sales,
    customers,
    "CustomerID",
    "CustomerID",
)

print("\nINNER JOIN ROWS:", len(inner_result))

print(
    """
Common relational join types:

Left Outer:
    Keep every row from the left table and matching rows from the right.

Inner:
    Keep only rows with a match on both sides.

Right Outer:
    Keep every row from the right table and matching rows from the left.

Full Outer:
    Keep rows appearing on either side.

Anti joins:
    Return rows that do not have a matching key.

The correct join depends on the business meaning of the data.
"""
)


# ---------------------------------------------------------------------------
# 15. APPENDING DATASETS
# ---------------------------------------------------------------------------

january = [
    {"OrderID": 1, "Region": "North", "Revenue": Decimal("100")},
    {"OrderID": 2, "Region": "South", "Revenue": Decimal("200")},
]

february = [
    {"OrderID": 3, "Region": "North", "Revenue": Decimal("150")},
    {"OrderID": 4, "Region": "West", "Revenue": Decimal("300")},
]


def append_tables(
    first: list[dict[str, Any]],
    second: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Stack rows vertically.

    This corresponds conceptually to Power Query Append Queries.

    Append and merge are different:

        Merge  = combine columns based on matching keys.
        Append = combine rows from similarly structured tables.
    """
    return [dict(row) for row in first] + [dict(row) for row in second]


combined_months = append_tables(january, february)

print("\nAPPEND RESULT:")
for row in combined_months:
    print(row)


# ---------------------------------------------------------------------------
# 16. GROUPING AND AGGREGATION
# ---------------------------------------------------------------------------

def group_sum(
    rows: list[dict[str, Any]],
    group_column: str,
    value_column: str,
) -> dict[Any, Decimal]:
    """Group rows and calculate a sum for each group."""
    totals: dict[Any, Decimal] = {}

    for row in rows:
        group_value = row[group_column]
        totals[group_value] = (
            totals.get(group_value, Decimal("0"))
            + Decimal(row[value_column])
        )

    return totals


regional_revenue = group_sum(
    sales_enriched,
    "Region",
    "SalesAmount",
)

print("\nREGIONAL REVENUE:")
for region, revenue in sorted(regional_revenue.items()):
    print(region, revenue)


def group_statistics(
    rows: list[dict[str, Any]],
    group_column: str,
    value_column: str,
) -> dict[Any, dict[str, float]]:
    """Calculate count, sum, mean, minimum, and maximum by group."""
    groups: dict[Any, list[float]] = {}

    for row in rows:
        groups.setdefault(row[group_column], []).append(
            float(row[value_column])
        )

    output = {}

    for group, values in groups.items():
        output[group] = {
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
        }

    return output


print("\nREGIONAL STATISTICS:")
for region, stats in group_statistics(
    sales_enriched,
    "Region",
    "SalesAmount",
).items():
    print(region, stats)


# ---------------------------------------------------------------------------
# 17. QUERY-STYLE TRANSFORMATION PIPELINE
# ---------------------------------------------------------------------------

@dataclass
class QueryStep:
    """Represent one named transformation step."""
    name: str
    operation: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]


class DataQuery:
    """
    A small educational query-pipeline abstraction.

    Power Query stores transformation steps rather than requiring the user
    to manually repeat every operation each time source data changes.
    """

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.source = rows
        self.steps: list[QueryStep] = []

    def add_step(
        self,
        name: str,
        operation: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    ) -> "DataQuery":
        self.steps.append(QueryStep(name, operation))
        return self

    def execute(self) -> list[dict[str, Any]]:
        current = [dict(row) for row in self.source]

        for step in self.steps:
            current = step.operation(current)

        return current

    def describe(self) -> list[str]:
        return [step.name for step in self.steps]


query = (
    DataQuery(sales)
    .add_step(
        "Filter North region",
        lambda rows: filter_rows(
            rows,
            lambda row: row["Region"] == "North",
        ),
    )
    .add_step(
        "Keep high-value orders",
        lambda rows: filter_rows(
            rows,
            lambda row: row["SalesAmount"] > Decimal("1000"),
        ),
    )
    .add_step(
        "Sort by revenue",
        lambda rows: sorted(
            rows,
            key=lambda row: row["SalesAmount"],
            reverse=True,
        ),
    )
)

query_result = query.execute()

print("\nQUERY STEPS:")
for step_number, step_name in enumerate(query.describe(), start=1):
    print(f"{step_number}. {step_name}")

print("\nQUERY RESULT:")
for row in query_result:
    print(row["OrderID"], row["Region"], row["SalesAmount"])


# ---------------------------------------------------------------------------
# 18. POWER QUERY M LANGUAGE CONCEPTUAL MAPPING
# ---------------------------------------------------------------------------

print(
    """
Power Query terminology and Python equivalents:

Power Query concept       Python demonstration
-------------------------------------------------------------
Source                    sales_csv / read_csv_text
Table                     list[dict]
Column                    dictionary key
Row                       dictionary
Changed Type              type_sales_rows
Trim/Clean                clean_text
Filter Rows               filter_rows
Custom Column             add_sales_amount
Choose Columns            select_columns
Rename Columns            rename_columns
Sort Rows                 sorted
Remove Duplicates         distinct_rows
Merge Queries             left_merge / inner_merge
Append Queries            append_tables
Group By                  group_sum / group_statistics
Null                      None
Error handling            safe_decimal / validation
Applied Steps             DataQuery.steps
Refresh                   DataQuery.execute()
"""
)


# ---------------------------------------------------------------------------
# 19. DATA QUALITY: REFERENTIAL INTEGRITY
# ---------------------------------------------------------------------------

def find_unmatched_keys(
    fact_rows: list[dict[str, Any]],
    dimension_rows: list[dict[str, Any]],
    fact_key: str,
    dimension_key: str,
) -> list[Any]:
    """Find fact-table keys that do not exist in the dimension table."""
    dimension_keys = {
        row[dimension_key]
        for row in dimension_rows
    }

    return [
        row[fact_key]
        for row in fact_rows
        if row[fact_key] not in dimension_keys
    ]


print("\nREFERENTIAL INTEGRITY CHECK:")
print(
    "Unmatched customers:",
    find_unmatched_keys(
        sales,
        customers,
        "CustomerID",
        "CustomerID",
    ),
)
print(
    "Unmatched products:",
    find_unmatched_keys(
        sales,
        products,
        "ProductID",
        "ProductID",
    ),
)


# ---------------------------------------------------------------------------
# 20. DATE TRANSFORMATIONS
# ---------------------------------------------------------------------------

def add_date_attributes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Derive calendar attributes from a typed date.

    Date decomposition is common in analytical data preparation.
    """
    result = []

    for row in rows:
        new_row = dict(row)
        date = new_row["OrderDate"]
        new_row["Year"] = date.year
        new_row["Month"] = date.month
        new_row["MonthName"] = date.strftime("%B")
        new_row["Quarter"] = (date.month - 1) // 3 + 1
        new_row["DayOfWeek"] = date.strftime("%A")
        result.append(new_row)

    return result


sales_with_dates = add_date_attributes(sales_enriched)

print("\nDATE ATTRIBUTES:")
print(
    sales_with_dates[0]["Year"],
    sales_with_dates[0]["MonthName"],
    f"Q{sales_with_dates[0]['Quarter']}",
    sales_with_dates[0]["DayOfWeek"],
)


# ---------------------------------------------------------------------------
# 21. CONDITIONAL LOGIC
# ---------------------------------------------------------------------------

def add_order_classification(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create a category using business rules."""
    result = []

    for row in rows:
        new_row = dict(row)
        amount = row["SalesAmount"]

        if amount >= Decimal("4000"):
            classification = "Very High"
        elif amount >= Decimal("2000"):
            classification = "High"
        elif amount >= Decimal("1000"):
            classification = "Medium"
        else:
            classification = "Low"

        new_row["OrderValueClass"] = classification
        result.append(new_row)

    return result


classified_sales = add_order_classification(sales_with_dates)

print("\nORDER CLASSIFICATION:")
for row in classified_sales[:5]:
    print(row["OrderID"], row["SalesAmount"], row["OrderValueClass"])


# ---------------------------------------------------------------------------
# 22. EDGE CASES
# ---------------------------------------------------------------------------

edge_cases = [
    {"Quantity": 0, "UnitPrice": Decimal("100")},
    {"Quantity": -2, "UnitPrice": Decimal("100")},
    {"Quantity": 2, "UnitPrice": Decimal("0")},
    {"Quantity": 2, "UnitPrice": Decimal("-50")},
]

print("\nEDGE-CASE VALIDATION:")

for case in edge_cases:
    valid = (
        case["Quantity"] > 0
        and case["UnitPrice"] >= 0
    )
    print(case, "=>", "valid" if valid else "invalid")


print(
    """
Important edge cases in ETL include:

- Empty source
- Missing columns
- Missing values
- Invalid numeric text
- Invalid dates
- Duplicate keys
- Null join keys
- Unmatched merge records
- Inconsistent spelling or capitalization
- Leading/trailing whitespace
- Negative quantities
- Negative prices
- Zero values
- Unexpected columns
- Changed source schema
- Different data types between appended tables
- Very large datasets
- Encoding problems
- Locale-dependent decimal separators
- Time-zone differences
"""
)


# ---------------------------------------------------------------------------
# 23. SCHEMA VALIDATION
# ---------------------------------------------------------------------------

def require_columns(
    rows: list[dict[str, Any]],
    required_columns: set[str],
) -> None:
    """Fail early if a required source column is missing."""
    if not rows:
        raise ValueError("Source contains no rows")

    actual_columns = set(rows[0])
    missing = required_columns - actual_columns

    if missing:
        raise ValueError(
            "Required columns are missing: "
            + ", ".join(sorted(missing))
        )


require_columns(
    sales_raw,
    {
        "OrderID",
        "OrderDate",
        "CustomerID",
        "ProductID",
        "Quantity",
        "UnitPrice",
        "Region",
    },
)

print("\nSCHEMA VALIDATION: passed")


# ---------------------------------------------------------------------------
# 24. PERFORMANCE: LINEAR SEARCH VS INDEXED JOIN
# ---------------------------------------------------------------------------

def linear_lookup(
    rows: list[dict[str, Any]],
    key_column: str,
    target: Any,
) -> dict[str, Any] | None:
    """O(n) lookup."""
    for row in rows:
        if row[key_column] == target:
            return row

    return None


customer_index = index_rows(customers, "CustomerID")

print("\nLOOKUP PERFORMANCE CONCEPT:")
print("Linear lookup:", linear_lookup(customers, "CustomerID", "C001"))
print("Indexed lookup:", customer_index.get("C001"))

print(
    """
For n fact rows and m dimension rows:

Repeated linear joins can approach O(n*m).

Building a hash index first generally produces approximately:

    O(m) to build the index
    O(n) average lookup work

or approximately O(n + m).

Power Query performance can also benefit from query folding, where
supported source systems execute transformations at the source instead of
sending all raw records to the client.
"""
)


# ---------------------------------------------------------------------------
# 25. QUERY FOLDING CONCEPT
# ---------------------------------------------------------------------------

print(
    """
QUERY FOLDING CONCEPT

Suppose a SQL source contains ten million rows and the query only needs
North-region records.

Without source-side filtering:

    Database -> 10,000,000 rows -> Power Query -> filter

With query folding:

    Database executes WHERE Region = 'North'
    Database -> smaller result -> Power Query

Benefits can include:
- Less network transfer
- Less client memory
- Less client CPU
- Faster refresh

Not every transformation can fold to every source. Complex custom logic,
unsupported functions, privacy boundaries, and certain transformations may
prevent folding.
"""
)


# ---------------------------------------------------------------------------
# 26. IDEMPOTENCE
# ---------------------------------------------------------------------------

def normalize_region(value: str) -> str:
    """An idempotent normalization function."""
    return clean_text(value).title()


region_once = normalize_region("  north ")
region_twice = normalize_region(region_once)

print("\nIDEMPOTENCE:")
print("Once :", repr(region_once))
print("Twice:", repr(region_twice))
print("Same :", region_once == region_twice)

print(
    """
An idempotent transformation produces the same result when applied again.

This is useful in refreshable ETL systems because rerunning a cleanup
operation should not progressively corrupt the data.
"""
)


# ---------------------------------------------------------------------------
# 27. COMPLETE END-TO-END PIPELINE
# ---------------------------------------------------------------------------

def build_sales_dataset(
    sales_source: str,
    customer_source: str,
    product_source: str,
) -> list[dict[str, Any]]:
    """
    Complete reusable ETL pipeline.

    Extract -> Validate schema -> Type -> Clean -> Calculate ->
    Merge customers -> Merge products -> Add date attributes ->
    Add classification -> Validate.
    """
    raw_sales = read_csv_text(sales_source)
    raw_customers = read_csv_text(customer_source)
    raw_products = read_csv_text(product_source)

    require_columns(
        raw_sales,
        {
            "OrderID",
            "OrderDate",
            "CustomerID",
            "ProductID",
            "Quantity",
            "UnitPrice",
            "Region",
        },
    )

    typed_sales = type_sales_rows(raw_sales)
    typed_sales = clean_sales_text(typed_sales)
    typed_sales = add_sales_amount(typed_sales)

    clean_customers = [
        {
            "CustomerID": clean_text(row["CustomerID"]),
            "CustomerName": clean_text(row["CustomerName"]),
            "Segment": clean_text(row["Segment"]),
        }
        for row in raw_customers
    ]

    clean_products = [
        {
            "ProductID": clean_text(row["ProductID"]),
            "ProductName": clean_text(row["ProductName"]),
            "Category": clean_text(row["Category"]),
        }
        for row in raw_products
    ]

    merged = left_merge(
        typed_sales,
        clean_customers,
        "CustomerID",
        "CustomerID",
    )

    merged = left_merge(
        merged,
        clean_products,
        "ProductID",
        "ProductID",
    )

    merged = add_date_attributes(merged)
    merged = add_order_classification(merged)

    errors = validate_sales(typed_sales)

    if errors:
        raise ValueError(
            "Sales validation failed: " + "; ".join(errors)
        )

    return merged


start_time = time.perf_counter()

final_dataset = build_sales_dataset(
    sales_csv,
    customers_csv,
    products_csv,
)

elapsed = time.perf_counter() - start_time

print("\nEND-TO-END ETL")
print("Rows produced:", len(final_dataset))
print("Execution time:", f"{elapsed:.6f}", "seconds")

print("\nFINAL DATASET SAMPLE:")
for row in final_dataset[:3]:
    printable = dict(row)

    # Dates and Decimal values are converted only for display.
    printable["OrderDate"] = printable["OrderDate"].isoformat()
    printable["UnitPrice"] = str(printable["UnitPrice"])
    printable["SalesAmount"] = str(printable["SalesAmount"])

    print(json.dumps(printable, indent=2))


# ---------------------------------------------------------------------------
# 28. TESTING TRANSFORMATIONS
# ---------------------------------------------------------------------------

def assert_equal(actual: Any, expected: Any, description: str) -> None:
    """Small assertion helper for educational ETL testing."""
    if actual != expected:
        raise AssertionError(
            f"{description}: expected {expected!r}, got {actual!r}"
        )

    print("PASS:", description)


assert_equal(
    len(final_dataset),
    10,
    "All sales rows remain after left merges",
)

assert_equal(
    final_dataset[0]["SalesAmount"],
    Decimal("2501.00"),
    "Calculated sales amount",
)

assert_equal(
    final_dataset[0]["CustomerName"],
    "Atul Pandey",
    "Customer merge",
)

assert_equal(
    final_dataset[0]["ProductName"],
    "Laptop",
    "Product merge",
)

assert_equal(
    final_dataset[0]["Quarter"],
    1,
    "Quarter calculation",
)


# ---------------------------------------------------------------------------
# 29. EXPORT: LOAD
# ---------------------------------------------------------------------------

def serialize_for_json(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert dates and Decimal values into JSON-compatible values."""
    output = []

    for row in rows:
        converted = {}

        for key, value in row.items():
            if isinstance(value, datetime):
                converted[key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, Decimal):
                converted[key] = float(value)
            else:
                converted[key] = value

        output.append(converted)

    return output


json_output = json.dumps(
    serialize_for_json(final_dataset[:2]),
    indent=2,
)

print("\nLOAD-READY JSON SAMPLE:")
print(json_output)


# ---------------------------------------------------------------------------
# 30. PRACTICAL DESIGN PRINCIPLES
# ---------------------------------------------------------------------------

print(
    """
PRACTICAL POWER QUERY PRINCIPLES

1. Understand the source before transforming it.
2. Assign correct data types early.
3. Validate required columns.
4. Clean text consistently.
5. Make business rules explicit.
6. Keep transformations deterministic.
7. Use meaningful query-step names.
8. Separate source, transformation, and output responsibilities.
9. Validate keys before merging.
10. Understand the difference between merge and append.
11. Handle nulls deliberately.
12. Do not silently discard data-quality errors.
13. Prefer source-side processing when query folding is available.
14. Avoid unnecessary repeated scans of large datasets.
15. Keep transformations refreshable and reproducible.
16. Test important business rules.
17. Consider locale, date, decimal, and encoding behavior.
18. Protect sensitive data during extraction and loading.
19. Document assumptions and expected schemas.
20. Design for source-schema changes rather than assuming they cannot happen.
"""
)


print("\n" + "=" * 78)
print("ETL STUDY SCRIPT COMPLETE")
print("=" * 78)
