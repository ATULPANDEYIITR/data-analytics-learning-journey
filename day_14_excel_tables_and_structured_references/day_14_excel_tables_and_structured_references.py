"""
Excel Tables & Structured References
====================================

A comprehensive, executable study script covering:

- Excel Tables
- Table names and table ranges
- Structured references
- Row, column, and special-item specifiers
- Calculated columns
- Totals rows
- Sorting and filtering
- Dynamic ranges
- Table expansion and contraction
- Slicer concepts and implementation considerations
- Table formulas
- Cross-table references
- Aggregations
- Validation
- Common mistakes
- Edge cases
- Performance considerations
- Workbook inspection
- Practical reporting patterns
- Testing and verification

The script creates an Excel workbook demonstrating the concepts and also
prints educational explanations and Python-side equivalents.

Dependency:
    pip install openpyxl

Note:
    openpyxl can create and manipulate Excel Tables, formulas, filters,
    sorting definitions, and workbook structure. Excel slicers are an
    advanced Excel feature whose complete creation/editing is not exposed
    by openpyxl's high-level API. The script therefore demonstrates slicer
    concepts and documents the limitation rather than pretending to create
    a real slicer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from collections import defaultdict
from statistics import mean

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.worksheet.table import Table, TableStyleInfo
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.dimensions import ColumnDimension
except ImportError as exc:
    raise SystemExit(
        "This script requires openpyxl.\n"
        "Install it with: pip install openpyxl"
    ) from exc


OUTPUT_FILE = Path("excel_tables_structured_references_demo.xlsx")


# ---------------------------------------------------------------------------
# 1. Basic data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SalesRecord:
    """Represents one row in the demonstration sales table."""

    order_id: str
    order_date: str
    region: str
    salesperson: str
    product: str
    category: str
    quantity: int
    unit_price: float
    discount: float
    status: str

    @property
    def gross_sales(self) -> float:
        """Equivalent to Quantity * Unit Price."""
        return self.quantity * self.unit_price

    @property
    def net_sales(self) -> float:
        """Equivalent to Gross Sales * (1 - Discount)."""
        return self.gross_sales * (1 - self.discount)


SALES_DATA = [
    SalesRecord("ORD-1001", "2026-01-05", "North", "Aarav", "Laptop", "Electronics", 2, 85000, 0.05, "Completed"),
    SalesRecord("ORD-1002", "2026-01-07", "South", "Diya", "Monitor", "Electronics", 4, 18000, 0.10, "Completed"),
    SalesRecord("ORD-1003", "2026-01-09", "West", "Kabir", "Desk", "Furniture", 3, 12500, 0.00, "Completed"),
    SalesRecord("ORD-1004", "2026-01-12", "East", "Meera", "Chair", "Furniture", 8, 6500, 0.05, "Completed"),
    SalesRecord("ORD-1005", "2026-01-15", "North", "Aarav", "Keyboard", "Accessories", 10, 2500, 0.08, "Completed"),
    SalesRecord("ORD-1006", "2026-01-18", "South", "Diya", "Mouse", "Accessories", 15, 1200, 0.00, "Completed"),
    SalesRecord("ORD-1007", "2026-01-20", "West", "Kabir", "Laptop", "Electronics", 1, 92000, 0.12, "Pending"),
    SalesRecord("ORD-1008", "2026-01-23", "East", "Meera", "Monitor", "Electronics", 5, 17500, 0.07, "Completed"),
    SalesRecord("ORD-1009", "2026-01-26", "North", "Aarav", "Desk", "Furniture", 2, 13500, 0.03, "Cancelled"),
    SalesRecord("ORD-1010", "2026-01-29", "South", "Diya", "Chair", "Furniture", 6, 6200, 0.05, "Completed"),
    SalesRecord("ORD-1011", "2026-02-02", "West", "Kabir", "Keyboard", "Accessories", 12, 2300, 0.04, "Completed"),
    SalesRecord("ORD-1012", "2026-02-05", "East", "Meera", "Mouse", "Accessories", 20, 1100, 0.02, "Completed"),
]


CUSTOMER_DATA = [
    ("C001", "Acme Technologies", "North", "Enterprise"),
    ("C002", "Bright Retail", "South", "SMB"),
    ("C003", "Cobalt Systems", "West", "Enterprise"),
    ("C004", "Delta Services", "East", "SMB"),
    ("C005", "Evergreen Labs", "North", "Enterprise"),
]


# ---------------------------------------------------------------------------
# 2. Educational output helpers
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    """Print a clearly separated educational section."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain(message: str) -> None:
    """Print one educational explanation."""
    print(message)


# ---------------------------------------------------------------------------
# 3. Structured-reference terminology
# ---------------------------------------------------------------------------

def teach_terminology() -> None:
    print_section("1. Excel Table terminology")

    terminology = {
        "Table": (
            "A named Excel object containing a rectangular dataset with "
            "headers, data rows, and optional totals."
        ),
        "Table name": (
            "The identifier used to refer to the table, such as SalesTable."
        ),
        "Header": (
            "A column label such as Quantity, Region, or Net Sales."
        ),
        "Data body": (
            "The rows containing actual records. In structured references, "
            "this can be represented by TableName[#Data]."
        ),
        "Structured reference": (
            "A readable formula reference such as "
            "SalesTable[Net Sales] instead of E2:E100."
        ),
        "Calculated column": (
            "A table column where one formula is automatically propagated "
            "through the table's data rows."
        ),
        "Totals row": (
            "An optional special row that can calculate totals, averages, "
            "counts, and other summaries."
        ),
        "Slicer": (
            "An interactive visual filtering control commonly used with "
            "Excel Tables and PivotTables."
        ),
        "Dynamic range": (
            "A range that grows or changes automatically as data changes."
        ),
    }

    for term, definition in terminology.items():
        print(f"{term}: {definition}")


# ---------------------------------------------------------------------------
# 4. Structured-reference syntax demonstration
# ---------------------------------------------------------------------------

def teach_structured_reference_syntax() -> None:
    print_section("2. Structured-reference syntax")

    examples = [
        ("SalesTable[Region]",
         "References the Region data column."),
        ("SalesTable[[#Headers],[Region]]",
         "References the Region header cell."),
        ("SalesTable[[#Data],[Region]]",
         "References Region data rows only."),
        ("SalesTable[[#Totals],[Net Sales]]",
         "References the Net Sales cell in the totals row."),
        ("SalesTable[[#All],[Region]]",
         "References the complete Region column including header/totals context."),
        ("SalesTable[@Quantity]",
         "References Quantity from the current row."),
        ("SalesTable[@[Unit Price]]",
         "References Unit Price from the current row."),
        ("SalesTable[[#This Row],[Quantity]]",
         "Explicit current-row reference."),
        ("SalesTable[[Quantity]:[Net Sales]]",
         "References a contiguous group of columns."),
        ("SalesTable[[Quantity]:[Quantity]]",
         "References one selected column using range-style structured syntax."),
    ]

    for formula, meaning in examples:
        print(f"{formula:<48} -> {meaning}")

    print("\nCommon formula:")
    print("=SalesTable[@Quantity]*SalesTable[@[Unit Price]]")

    print("\nConditional aggregation:")
    print('=SUMIFS(SalesTable[Net Sales],SalesTable[Region],"North")')

    print("\nAverage by category:")
    print('=AVERAGEIFS(SalesTable[Net Sales],SalesTable[Category],"Electronics")')


# ---------------------------------------------------------------------------
# 5. Python equivalents of common Excel table operations
# ---------------------------------------------------------------------------

def python_sum(values: Iterable[float]) -> float:
    return sum(values)


def python_filter(
    records: Sequence[SalesRecord],
    predicate,
) -> list[SalesRecord]:
    return [record for record in records if predicate(record)]


def python_sort(
    records: Sequence[SalesRecord],
    key,
    reverse: bool = False,
) -> list[SalesRecord]:
    return sorted(records, key=key, reverse=reverse)


def demonstrate_python_equivalents() -> None:
    print_section("3. Python equivalents of Table operations")

    north_records = python_filter(
        SALES_DATA,
        lambda record: record.region == "North",
    )

    print("Excel equivalent:")
    print('=FILTER(SalesTable,SalesTable[Region]="North")')

    print("\nPython equivalent:")
    for record in north_records:
        print(record.order_id, record.region, record.net_sales)

    sorted_sales = python_sort(
        SALES_DATA,
        key=lambda record: record.net_sales,
        reverse=True,
    )

    print("\nTop three records by net sales:")
    for record in sorted_sales[:3]:
        print(record.order_id, round(record.net_sales, 2))

    completed_sales = python_filter(
        SALES_DATA,
        lambda record: record.status == "Completed",
    )

    total_completed = python_sum(
        record.net_sales for record in completed_sales
    )

    print("\nCompleted sales:")
    print(round(total_completed, 2))


# ---------------------------------------------------------------------------
# 6. Workbook styling
# ---------------------------------------------------------------------------

def style_header_row(ws, row_number: int = 1) -> None:
    """Apply readable formatting to a worksheet header."""
    fill = PatternFill(fill_type="solid", fgColor="1F4E78")
    font = Font(color="FFFFFF", bold=True)
    alignment = Alignment(horizontal="center", vertical="center")
    bottom = Side(style="thin", color="D9E2F3")
    border = Border(bottom=bottom)

    for cell in ws[row_number]:
        if cell.value is not None:
            cell.fill = fill
            cell.font = font
            cell.alignment = alignment
            cell.border = border


def auto_size_columns(ws, minimum: int = 10, maximum: int = 32) -> None:
    """Size columns according to their visible contents."""
    for column_cells in ws.columns:
        values = [
            str(cell.value)
            for cell in column_cells
            if cell.value is not None
        ]

        if not values:
            continue

        width = min(
            maximum,
            max(minimum, max(len(value) for value in values) + 2),
        )

        column_letter = get_column_letter(column_cells[0].column)
        ws.column_dimensions[column_letter].width = width


# ---------------------------------------------------------------------------
# 7. Creating the main Excel Table
# ---------------------------------------------------------------------------

def create_sales_table(ws) -> Table:
    """
    Create SalesTable.

    The table intentionally includes formula columns. Excel will interpret
    formulas such as:

        =[@Quantity]*[@[Unit Price]]

    as calculated-column formulas when the workbook is opened in Excel.
    """

    headers = [
        "Order ID",
        "Order Date",
        "Region",
        "Salesperson",
        "Product",
        "Category",
        "Quantity",
        "Unit Price",
        "Discount",
        "Gross Sales",
        "Net Sales",
        "Status",
    ]

    ws.append(headers)

    for record in SALES_DATA:
        ws.append([
            record.order_id,
            record.order_date,
            record.region,
            record.salesperson,
            record.product,
            record.category,
            record.quantity,
            record.unit_price,
            record.discount,
            f"=[@Quantity]*[@[Unit Price]]",
            f"=[@[Gross Sales]]*(1-[@Discount])",
            record.status,
        ])

    # Excel Table range includes header and data rows.
    last_row = ws.max_row
    table_ref = f"A1:L{last_row}"

    table = Table(
        displayName="SalesTable",
        ref=table_ref,
    )

    style = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )

    table.tableStyleInfo = style

    # The table's AutoFilter is generated as part of the table object.
    ws.add_table(table)

    # Excel Table formulas are stored as formulas. openpyxl does not
    # calculate them. Excel calculates them when the workbook is opened.
    for row in range(2, last_row + 1):
        ws.cell(row=row, column=8).number_format = '#,##0.00'
        ws.cell(row=row, column=9).number_format = '0.00%'
        ws.cell(row=row, column=10).number_format = '#,##0.00'
        ws.cell(row=row, column=11).number_format = '#,##0.00'

    return table


# ---------------------------------------------------------------------------
# 8. Calculated columns
# ---------------------------------------------------------------------------

def demonstrate_calculated_columns(ws) -> None:
    print_section("4. Calculated columns")

    print(
        "A calculated column applies one logical formula to every row "
        "of an Excel Table."
    )

    print("\nGross Sales:")
    print("=[@Quantity]*[@[Unit Price]]")

    print("\nNet Sales:")
    print("=[@[Gross Sales]]*(1-[@Discount])")

    print(
        "\nThe @ symbol means the formula is referring to the current row."
    )

    # Add a derived column to demonstrate another calculated column.
    table = ws.tables["SalesTable"]

    # We already created 12 columns. Add a new worksheet column M.
    ws["M1"] = "High Value Order"

    for row in range(2, ws.max_row + 1):
        ws.cell(
            row=row,
            column=13,
            value='=IF([@[Net Sales]]>=50000,"Yes","No")',
        )

    # Expand table range to include the new calculated column.
    table.ref = f"A1:M{ws.max_row}"

    for cell in ws["M"]:
        if cell.row > 1:
            cell.alignment = Alignment(horizontal="center")


# ---------------------------------------------------------------------------
# 9. Totals row
# ---------------------------------------------------------------------------

def create_totals_sheet(wb) -> None:
    print_section("5. Totals rows and aggregation")

    ws = wb.create_sheet("Totals Examples")

    ws["A1"] = "Formula"
    ws["B1"] = "Purpose"

    examples = [
        (
            "=SUBTOTAL(109,SalesTable[Net Sales])",
            "Sum visible Net Sales rows. Useful with filtering.",
        ),
        (
            "=SUBTOTAL(101,SalesTable[Net Sales])",
            "Average visible Net Sales rows.",
        ),
        (
            "=SUBTOTAL(103,SalesTable[Order ID])",
            "Count visible non-empty Order IDs.",
        ),
        (
            '=SUMIFS(SalesTable[Net Sales],SalesTable[Region],"North")',
            "Sum North-region sales.",
        ),
        (
            '=COUNTIFS(SalesTable[Status],"Completed")',
            "Count completed orders.",
        ),
        (
            '=AVERAGEIFS(SalesTable[Net Sales],SalesTable[Category],"Furniture")',
            "Average Furniture sales.",
        ),
    ]

    for row_index, (formula, purpose) in enumerate(examples, start=2):
        ws.cell(row=row_index, column=1, value=formula)
        ws.cell(row=row_index, column=2, value=purpose)

    style_header_row(ws)
    auto_size_columns(ws)

    print("Totals-row formulas are especially useful because SUBTOTAL can")
    print("respect filtered rows, unlike a simple SUM in many reporting cases.")


# ---------------------------------------------------------------------------
# 10. Sorting and filtering
# ---------------------------------------------------------------------------

def create_filter_examples(wb) -> None:
    print_section("6. Sorting and filtering")

    ws = wb.create_sheet("Filter Examples")

    ws.append(["Concept", "Excel expression or operation", "Meaning"])

    rows = [
        (
            "Filter by region",
            'SalesTable[Region] = "North"',
            "Display only North-region records.",
        ),
        (
            "Filter by status",
            'SalesTable[Status] = "Completed"',
            "Display only completed orders.",
        ),
        (
            "Filter by sales",
            'SalesTable[Net Sales] >= 50000',
            "Display records meeting a sales threshold.",
        ),
        (
            "Sort descending",
            "Sort Net Sales largest to smallest",
            "Prioritize high-value orders.",
        ),
        (
            "Sort by multiple columns",
            "Region ascending, Net Sales descending",
            "Group regions while ranking sales within each group.",
        ),
    ]

    for row in rows:
        ws.append(row)

    style_header_row(ws)
    auto_size_columns(ws)

    print(
        "Excel Tables automatically provide filter dropdowns in their "
        "header row."
    )
    print(
        "Sorting changes row order. Filtering hides rows without deleting "
        "the underlying records."
    )


# ---------------------------------------------------------------------------
# 11. Dynamic range demonstration
# ---------------------------------------------------------------------------

def create_dynamic_range_examples(wb) -> None:
    print_section("7. Dynamic ranges")

    ws = wb.create_sheet("Dynamic Ranges")

    ws.append(["Technique", "Example", "Behavior"])

    examples = [
        (
            "Excel Table",
            "SalesTable[Net Sales]",
            "Automatically expands as new table rows are added.",
        ),
        (
            "Table data",
            "SalesTable[#Data]",
            "Refers to the table's data body.",
        ),
        (
            "Entire table",
            "SalesTable[#All]",
            "Includes table-related regions such as headers and totals.",
        ),
        (
            "Legacy dynamic formula",
            "INDEX($A:$A,2):INDEX($A:$A,COUNTA($A:$A))",
            "Can construct a changing range without a Table.",
        ),
        (
            "Dynamic-array approach",
            "FILTER(...)",
            "Returns a dynamically sized result.",
        ),
    ]

    for row in examples:
        ws.append(row)

    style_header_row(ws)
    auto_size_columns(ws)

    print(
        "A Table is usually preferable to manually maintained ranges "
        "when the data represents a list or dataset."
    )


# ---------------------------------------------------------------------------
# 12. Slicer concepts
# ---------------------------------------------------------------------------

def create_slicer_explanation(wb) -> None:
    print_section("8. Slicers")

    ws = wb.create_sheet("Slicer Concepts")

    ws.append(["Concept", "Explanation"])

    rows = [
        (
            "Slicer",
            "A visual control containing buttons representing filter values.",
        ),
        (
            "Typical Table use",
            "Filter Region, Category, Salesperson, or Status.",
        ),
        (
            "Benefit",
            "Users can see active selections more clearly than ordinary filter menus.",
        ),
        (
            "Multiple selections",
            "A slicer can often select several categories simultaneously.",
        ),
        (
            "Clear filter",
            "The slicer provides a visible mechanism to remove its filter.",
        ),
        (
            "Limitation in this script",
            "openpyxl does not expose complete high-level slicer creation/editing support.",
        ),
    ]

    for row in rows:
        ws.append(row)

    style_header_row(ws)
    auto_size_columns(ws)

    print(
        "A slicer is not the same thing as a normal AutoFilter."
    )
    print(
        "AutoFilter works through header dropdowns. A slicer provides a "
        "visual filtering interface."
    )


# ---------------------------------------------------------------------------
# 13. Cross-table structured references
# ---------------------------------------------------------------------------

def create_customer_table(wb) -> None:
    ws = wb.create_sheet("Customers")

    ws.append([
        "Customer ID",
        "Customer Name",
        "Region",
        "Customer Type",
    ])

    for customer in CUSTOMER_DATA:
        ws.append(customer)

    table = Table(
        displayName="CustomerTable",
        ref=f"A1:D{ws.max_row}",
    )

    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium4",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )

    ws.add_table(table)

    style_header_row(ws)
    auto_size_columns(ws)


def create_cross_table_examples(wb) -> None:
    print_section("9. Cross-table references")

    ws = wb.create_sheet("Cross Table Examples")

    ws.append(["Formula", "Purpose"])

    examples = [
        (
            '=SUMIFS(SalesTable[Net Sales],SalesTable[Region],CustomerTable[@Region])',
            "Aggregate sales for the current customer's region.",
        ),
        (
            '=COUNTIFS(SalesTable[Region],CustomerTable[@Region])',
            "Count sales rows matching the current customer's region.",
        ),
        (
            '=XLOOKUP([@[Customer ID]],CustomerTable[Customer ID],CustomerTable[Customer Name],"Not found")',
            "Look up a customer name by Customer ID.",
        ),
    ]

    for row in examples:
        ws.append(row)

    style_header_row(ws)
    auto_size_columns(ws)


# ---------------------------------------------------------------------------
# 14. Data validation
# ---------------------------------------------------------------------------

def create_validation_examples(wb) -> None:
    print_section("10. Data validation")

    ws = wb.create_sheet("Validation")

    ws.append(["Order ID", "Region", "Status", "Category"])

    validation_rows = [
        ("NEW-001", "North", "Completed", "Electronics"),
        ("NEW-002", "South", "Pending", "Furniture"),
    ]

    for row in validation_rows:
        ws.append(row)

    region_validation = DataValidation(
        type="list",
        formula1='"North,South,East,West"',
        allow_blank=False,
    )

    status_validation = DataValidation(
        type="list",
        formula1='"Completed,Pending,Cancelled"',
        allow_blank=False,
    )

    category_validation = DataValidation(
        type="list",
        formula1='"Electronics,Furniture,Accessories"',
        allow_blank=False,
    )

    ws.add_data_validation(region_validation)
    ws.add_data_validation(status_validation)
    ws.add_data_validation(category_validation)

    region_validation.add("B2:B1000")
    status_validation.add("C2:C1000")
    category_validation.add("D2:D1000")

    style_header_row(ws)
    auto_size_columns(ws)

    print(
        "Validation reduces inconsistent categorical values such as "
        "'North', 'north', and 'NORTH'."
    )


# ---------------------------------------------------------------------------
# 15. Conditional formatting
# ---------------------------------------------------------------------------

def create_conditional_formatting(wb) -> None:
    print_section("11. Conditional formatting with table data")

    ws = wb.create_sheet("Conditional Formatting")

    ws.append(["Order ID", "Net Sales", "Status"])

    for record in SALES_DATA:
        ws.append([
            record.order_id,
            record.net_sales,
            record.status,
        ])

    high_value_rule = CellIsRule(
        operator="greaterThanOrEqual",
        formula=["50000"],
        fill=PatternFill(fill_type="solid", fgColor="C6EFCE"),
    )

    ws.conditional_formatting.add(
        f"B2:B{ws.max_row}",
        high_value_rule,
    )

    style_header_row(ws)
    auto_size_columns(ws)

    for row in range(2, ws.max_row + 1):
        ws.cell(row=row, column=2).number_format = '#,##0.00'


# ---------------------------------------------------------------------------
# 16. Formula patterns
# ---------------------------------------------------------------------------

def create_formula_library(wb) -> None:
    print_section("12. Formula patterns using structured references")

    ws = wb.create_sheet("Formula Library")

    ws.append(["Pattern", "Formula", "Purpose"])

    formulas = [
        (
            "Current row multiplication",
            "=[@Quantity]*[@[Unit Price]]",
            "Calculate gross sales.",
        ),
        (
            "Current row percentage adjustment",
            "=[@[Gross Sales]]*(1-[@Discount])",
            "Calculate net sales.",
        ),
        (
            "SUM",
            "=SUM(SalesTable[Net Sales])",
            "Sum an entire table column.",
        ),
        (
            "AVERAGE",
            "=AVERAGE(SalesTable[Net Sales])",
            "Calculate average sales.",
        ),
        (
            "COUNT",
            "=COUNT(SalesTable[Quantity])",
            "Count numeric quantity values.",
        ),
        (
            "COUNTA",
            "=COUNTA(SalesTable[Order ID])",
            "Count non-empty Order IDs.",
        ),
        (
            "MAX",
            "=MAX(SalesTable[Net Sales])",
            "Find highest sales value.",
        ),
        (
            "MIN",
            "=MIN(SalesTable[Net Sales])",
            "Find lowest sales value.",
        ),
        (
            "SUMIFS",
            '=SUMIFS(SalesTable[Net Sales],SalesTable[Region],"North")',
            "Conditional sum.",
        ),
        (
            "COUNTIFS",
            '=COUNTIFS(SalesTable[Region],"North",SalesTable[Status],"Completed")',
            "Conditional count using multiple criteria.",
        ),
        (
            "AVERAGEIFS",
            '=AVERAGEIFS(SalesTable[Net Sales],SalesTable[Category],"Electronics")',
            "Conditional average.",
        ),
        (
            "IF",
            '=IF([@[Net Sales]]>=50000,"High","Normal")',
            "Classify current row.",
        ),
        (
            "AND",
            '=IF(AND([@Status]="Completed",[@[Net Sales]]>=50000),"Priority","Normal")',
            "Combine conditions.",
        ),
        (
            "COUNTIF",
            '=COUNTIF(SalesTable[Status],"Completed")',
            "Count one category.",
        ),
    ]

    for row in formulas:
        ws.append(row)

    style_header_row(ws)
    auto_size_columns(ws, maximum=65)


# ---------------------------------------------------------------------------
# 17. Edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print_section("13. Edge cases")

    empty_records: list[SalesRecord] = []

    print("Empty dataset:")
    print("Python sum:", sum(record.net_sales for record in empty_records))

    print("\nZero quantity:")
    zero_quantity = SalesRecord(
        "EDGE-001",
        "2026-02-10",
        "North",
        "Aarav",
        "Test Product",
        "Test",
        0,
        1000,
        0.10,
        "Completed",
    )
    print("Gross sales:", zero_quantity.gross_sales)
    print("Net sales:", zero_quantity.net_sales)

    print("\n100% discount:")
    full_discount = SalesRecord(
        "EDGE-002",
        "2026-02-10",
        "North",
        "Aarav",
        "Test Product",
        "Test",
        10,
        1000,
        1.0,
        "Completed",
    )
    print("Net sales:", full_discount.net_sales)

    print("\nNegative discount:")
    negative_discount = SalesRecord(
        "EDGE-003",
        "2026-02-10",
        "North",
        "Aarav",
        "Test Product",
        "Test",
        10,
        1000,
        -0.10,
        "Completed",
    )
    print(
        "Net sales:",
        negative_discount.net_sales,
        "(mathematically valid but usually requires business validation)",
    )

    print("\nDuplicate order IDs:")
    print(
        "Excel Tables do not automatically guarantee uniqueness. "
        "Use validation or formulas when IDs must be unique."
    )

    print("\nBlank rows:")
    print(
        "Avoid intentionally inserting blank rows inside a dataset. "
        "Tables are designed for contiguous records."
    )


# ---------------------------------------------------------------------------
# 18. Common mistakes
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    print_section("14. Common mistakes")

    mistakes = [
        (
            "Using ordinary ranges everywhere",
            "Hard-coded ranges can become stale when new records are added.",
        ),
        (
            "Using inconsistent headers",
            "Structured references depend on exact table column names.",
        ),
        (
            "Duplicate table names",
            "Excel table names must be unique within the workbook.",
        ),
        (
            "Spaces handled incorrectly",
            "Column names containing spaces require bracket syntax such as [Unit Price].",
        ),
        (
            "Expecting Python to calculate Excel formulas",
            "openpyxl writes formulas but does not calculate them like Excel.",
        ),
        (
            "Confusing filter and delete",
            "Filtering hides records; it does not remove them.",
        ),
        (
            "Overusing volatile formulas",
            "Volatile formulas can increase recalculation cost in large workbooks.",
        ),
        (
            "Uncontrolled table growth",
            "Appending huge volumes of unnecessary formatting or formulas can increase workbook size.",
        ),
        (
            "Assuming every Excel feature is available in openpyxl",
            "Some advanced features, including complete slicer manipulation, require Excel-specific mechanisms.",
        ),
    ]

    for mistake, explanation in mistakes:
        print(f"{mistake}: {explanation}")


# ---------------------------------------------------------------------------
# 19. Performance considerations
# ---------------------------------------------------------------------------

def performance_demo() -> None:
    print_section("15. Performance considerations")

    print(
        "Structured references improve maintainability, but readability "
        "does not eliminate Excel calculation costs."
    )

    print("\nImportant performance principles:")
    principles = [
        "Keep datasets reasonably structured and avoid unnecessary formulas.",
        "Prefer one well-designed calculated column over thousands of unrelated formulas.",
        "Avoid excessive volatile functions such as OFFSET and INDIRECT when a Table can solve the same problem.",
        "Use SUMIFS, COUNTIFS, and related functions carefully on very large datasets.",
        "Consider PivotTables, Power Query, or the Data Model for large analytical workloads.",
        "Avoid excessive conditional formatting across entire worksheets.",
        "Keep lookup keys clean and consistent.",
        "Do not duplicate the same expensive calculation in many separate formulas.",
        "Use Excel Tables to reduce manually maintained ranges.",
    ]

    for principle in principles:
        print(f"- {principle}")


# ---------------------------------------------------------------------------
# 20. Security and data integrity
# ---------------------------------------------------------------------------

def security_and_integrity() -> None:
    print_section("16. Security and data integrity")

    points = [
        "Treat externally supplied Excel files as untrusted input.",
        "Do not enable macros merely because a workbook contains a Table.",
        "Use data validation for controlled categories.",
        "Protect formula columns when users should not modify calculations.",
        "Protect worksheets where appropriate, while remembering that worksheet protection is not equivalent to encryption.",
        "Avoid exposing confidential data through hidden worksheets alone.",
        "Validate imported records before they become part of a reporting table.",
        "Use stable identifiers rather than relying on row numbers as record identity.",
    ]

    for point in points:
        print(f"- {point}")


# ---------------------------------------------------------------------------
# 21. Real-world reporting model
# ---------------------------------------------------------------------------

def create_dashboard_examples(wb) -> None:
    print_section("17. Practical reporting model")

    ws = wb.create_sheet("Dashboard")

    ws["A1"] = "Sales Dashboard Formula Examples"
    ws["A1"].font = Font(size=16, bold=True)

    dashboard_rows = [
        ("Total Net Sales", "=SUM(SalesTable[Net Sales])"),
        ("Average Order Value", "=AVERAGE(SalesTable[Net Sales])"),
        ("Completed Orders", '=COUNTIF(SalesTable[Status],"Completed")'),
        ("Pending Orders", '=COUNTIF(SalesTable[Status],"Pending")'),
        ("Cancelled Orders", '=COUNTIF(SalesTable[Status],"Cancelled")'),
        (
            "North Sales",
            '=SUMIFS(SalesTable[Net Sales],SalesTable[Region],"North")',
        ),
        (
            "Electronics Sales",
            '=SUMIFS(SalesTable[Net Sales],SalesTable[Category],"Electronics")',
        ),
        (
            "High Value Orders",
            '=COUNTIF(SalesTable[High Value Order],"Yes")',
        ),
    ]

    ws["A3"] = "Metric"
    ws["B3"] = "Formula"

    for index, (metric, formula) in enumerate(dashboard_rows, start=4):
        ws.cell(index, 1, metric)
        ws.cell(index, 2, formula)

    style_header_row(ws, row_number=3)
    auto_size_columns(ws, maximum=65)

    for row in range(4, ws.max_row + 1):
        ws.cell(row=row, column=2).number_format = '#,##0.00'


# ---------------------------------------------------------------------------
# 22. Testing workbook structure
# ---------------------------------------------------------------------------

def validate_workbook(path: Path) -> None:
    print_section("18. Workbook validation")

    workbook = load_workbook(path, data_only=False)

    expected_sheets = {
        "Sales",
        "Customers",
        "Totals Examples",
        "Filter Examples",
        "Dynamic Ranges",
        "Slicer Concepts",
        "Cross Table Examples",
        "Validation",
        "Conditional Formatting",
        "Formula Library",
        "Dashboard",
    }

    actual_sheets = set(workbook.sheetnames)

    missing_sheets = expected_sheets - actual_sheets

    if missing_sheets:
        raise AssertionError(
            f"Missing expected worksheets: {sorted(missing_sheets)}"
        )

    sales_sheet = workbook["Sales"]

    if "SalesTable" not in sales_sheet.tables:
        raise AssertionError("SalesTable was not created.")

    sales_table = sales_sheet.tables["SalesTable"]

    if not sales_table.ref.startswith("A1:"):
        raise AssertionError(
            f"Unexpected SalesTable reference: {sales_table.ref}"
        )

    # Validate that formula cells contain structured references.
    gross_formula = sales_sheet["J2"].value
    net_formula = sales_sheet["K2"].value

    if "[@Quantity]" not in gross_formula:
        raise AssertionError("Gross Sales formula is not structured.")

    if "[@[Gross Sales]]" not in net_formula:
        raise AssertionError("Net Sales formula is not structured.")

    if "[@Discount]" not in net_formula:
        raise AssertionError("Discount reference is missing.")

    print("Workbook structure validation passed.")
    print("Sheets:", ", ".join(workbook.sheetnames))
    print("SalesTable range:", sales_table.ref)
    print("Gross Sales formula:", gross_formula)
    print("Net Sales formula:", net_formula)


# ---------------------------------------------------------------------------
# 23. Build complete workbook
# ---------------------------------------------------------------------------

def build_workbook(path: Path) -> None:
    workbook = Workbook()

    # Remove default sheet and create named worksheets explicitly.
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    sales_ws = workbook.create_sheet("Sales")

    create_sales_table(sales_ws)
    demonstrate_calculated_columns(sales_ws)

    style_header_row(sales_ws)
    sales_ws.freeze_panes = "A2"
    sales_ws.auto_filter.ref = "A1:M13"

    # Highlight high-value calculated-column results.
    high_value_fill = PatternFill(
        fill_type="solid",
        fgColor="FFF2CC",
    )

    for row in range(2, sales_ws.max_row + 1):
        if row % 2 == 0:
            sales_ws.cell(row=row, column=13).fill = high_value_fill

    auto_size_columns(sales_ws, maximum=24)

    create_customer_table(workbook)
    create_totals_sheet(workbook)
    create_filter_examples(workbook)
    create_dynamic_range_examples(workbook)
    create_slicer_explanation(workbook)
    create_cross_table_examples(workbook)
    create_validation_examples(workbook)
    create_conditional_formatting(workbook)
    create_formula_library(workbook)
    create_dashboard_examples(workbook)

    # Workbook calculation settings.
    #
    # openpyxl stores formulas but does not evaluate them. Setting automatic
    # calculation requests Excel to recalculate when the workbook is opened.
    try:
        workbook.calculation.fullCalcOnLoad = True
        workbook.calculation.forceFullCalc = True
        workbook.calculation.calcMode = "auto"
    except AttributeError:
        # Older openpyxl versions may expose calculation properties
        # differently. Formula storage remains valid.
        pass

    workbook.save(path)


# ---------------------------------------------------------------------------
# 24. Data analysis without Excel
# ---------------------------------------------------------------------------

def perform_python_analysis() -> None:
    print_section("19. Python-side analysis of the same table")

    total_sales = sum(record.net_sales for record in SALES_DATA)

    completed = [
        record
        for record in SALES_DATA
        if record.status == "Completed"
    ]

    completed_sales = sum(record.net_sales for record in completed)

    by_region: dict[str, float] = defaultdict(float)
    by_category: dict[str, float] = defaultdict(float)

    for record in SALES_DATA:
        by_region[record.region] += record.net_sales
        by_category[record.category] += record.net_sales

    print(f"Total net sales: {total_sales:,.2f}")
    print(f"Completed net sales: {completed_sales:,.2f}")

    print("\nSales by region:")
    for region, value in sorted(by_region.items()):
        print(f"  {region}: {value:,.2f}")

    print("\nSales by category:")
    for category, value in sorted(by_category.items()):
        print(f"  {category}: {value:,.2f}")

    print("\nAverage order value:")
    print(f"  {mean(record.net_sales for record in SALES_DATA):,.2f}")


# ---------------------------------------------------------------------------
# 25. Comparison of references
# ---------------------------------------------------------------------------

def compare_reference_styles() -> None:
    print_section("20. Ordinary references versus structured references")

    comparisons = [
        (
            "Ordinary range",
            "=SUM(K2:K13)",
            "Compact but dependent on row boundaries.",
        ),
        (
            "Structured column",
            "=SUM(SalesTable[Net Sales])",
            "Readable and expands with the Table.",
        ),
        (
            "Current-row reference",
            "=[@[Gross Sales]]*(1-[@Discount])",
            "Clearly expresses row-level business logic.",
        ),
        (
            "Dynamic array",
            '=FILTER(SalesTable,SalesTable[Region]="North")',
            "Returns a changing result set.",
        ),
    ]

    for reference_type, formula, implication in comparisons:
        print(f"{reference_type}:")
        print(f"  Formula: {formula}")
        print(f"  Implication: {implication}")


# ---------------------------------------------------------------------------
# 26. Table design principles
# ---------------------------------------------------------------------------

def table_design_principles() -> None:
    print_section("21. Table design principles")

    principles = [
        "Use one clear header row.",
        "Keep each column semantically consistent.",
        "Store one record per row.",
        "Avoid merged cells inside a data table.",
        "Avoid blank rows inside the dataset.",
        "Use meaningful table names such as SalesTable or CustomerTable.",
        "Use stable identifiers such as Order ID.",
        "Keep calculations in calculated columns when row-level logic is required.",
        "Use structured references for maintainable formulas.",
        "Use validation for controlled categories.",
        "Separate raw data from presentation where practical.",
        "Use filters and slicers for interactive exploration.",
        "Use PivotTables or the Data Model for more advanced aggregation needs.",
    ]

    for index, principle in enumerate(principles, start=1):
        print(f"{index:02d}. {principle}")


# ---------------------------------------------------------------------------
# 27. Production considerations
# ---------------------------------------------------------------------------

def production_considerations() -> None:
    print_section("22. Production considerations")

    considerations = [
        (
            "Data volume",
            "Excel Tables are excellent for ordinary business datasets, "
            "but extremely large datasets may be better handled through "
            "Power Query, Power Pivot, databases, or analytical systems.",
        ),
        (
            "Formula maintenance",
            "Structured references reduce manual range maintenance and make "
            "business formulas easier to interpret.",
        ),
        (
            "User interaction",
            "Filters are useful for occasional selection. Slicers are useful "
            "when dashboard users repeatedly filter the same dimensions.",
        ),
        (
            "Data quality",
            "A Table does not automatically guarantee correct data. "
            "Validation, controlled inputs, duplicate checks, and business "
            "rules remain necessary.",
        ),
        (
            "Compatibility",
            "Modern structured-reference syntax is closely associated with "
            "Excel Tables. Formula availability can differ across Excel versions.",
        ),
        (
            "Automation",
            "Python can create and inspect workbook structures, but Excel "
            "itself is responsible for calculating formulas when using openpyxl.",
        ),
    ]

    for name, explanation in considerations:
        print(f"{name}: {explanation}")


# ---------------------------------------------------------------------------
# 28. Complete execution
# ---------------------------------------------------------------------------

def main() -> None:
    print_section("Excel Tables & Structured References Study Script")

    teach_terminology()
    teach_structured_reference_syntax()
    demonstrate_python_equivalents()
    demonstrate_common_mistakes()
    demonstrate_edge_cases()
    compare_reference_styles()
    table_design_principles()
    performance_demo()
    security_and_integrity()
    production_considerations()
    perform_python_analysis()

    print_section("Creating demonstration workbook")

    build_workbook(OUTPUT_FILE)

    print(f"Workbook created: {OUTPUT_FILE.resolve()}")

    validate_workbook(OUTPUT_FILE)

    print_section("Important workbook behavior")

    explain(
        "Open the generated workbook in Microsoft Excel to see the Table "
        "styles, filter controls, formulas, validation controls, and "
        "calculation behavior."
    )

    explain(
        "Formula values may appear blank or stale when inspected by Python "
        "because openpyxl writes formulas but does not calculate them. "
        "Excel recalculates the workbook when opened."
    )

    explain(
        "The Sales worksheet contains SalesTable. The Customers worksheet "
        "contains CustomerTable. These names are used in the structured "
        "reference examples."
    )

    explain(
        "The Slicer Concepts worksheet documents slicers separately because "
        "complete slicer creation is not exposed through openpyxl's normal "
        "high-level API."
    )

    print_section("Study checklist")

    checklist = [
        "Identify a Table by its name.",
        "Read a structured reference such as SalesTable[Net Sales].",
        "Understand @ as the current-row reference.",
        "Understand #Headers, #Data, #Totals, and #All.",
        "Recognize a calculated column.",
        "Use SUMIFS and COUNTIFS with table columns.",
        "Distinguish filtering from sorting.",
        "Explain why Tables provide dynamic ranges.",
        "Distinguish AutoFilter from slicers.",
        "Recognize the limitations of openpyxl formula calculation.",
        "Apply data validation to maintain consistent table values.",
        "Evaluate performance and maintainability when designing large workbooks.",
    ]

    for item in checklist:
        print(f"[ ] {item}")

    print("\nStudy workbook ready.")


if __name__ == "__main__":
    main()
