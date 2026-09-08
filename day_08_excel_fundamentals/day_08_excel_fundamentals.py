"""
Excel Fundamentals: A Beginner-to-Advanced Study Script

This script teaches core Microsoft Excel concepts using Python simulations.
Python cannot control Excel directly without external libraries, so the examples
model workbook behavior, formulas, references, ranges, formatting, named ranges,
and common spreadsheet operations.

Topics covered:
1. Workbook structure
2. Worksheets
3. Cells
4. Ranges
5. Rows and columns
6. Cell formatting
7. Basic formulas
8. Formula evaluation
9. Relative references
10. Absolute references
11. Mixed references
12. Named ranges
13. Common functions
14. Error values
15. Data validation concepts
16. Copying formulas
17. Common Excel shortcuts
18. Common mistakes
19. Performance considerations
20. Spreadsheet design and production practices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re
import math


# =============================================================================
# SECTION 1: EXCEL FUNDAMENTAL CONCEPTS
# =============================================================================

"""
Excel terminology:

Workbook:
    The complete Excel file. A workbook may contain multiple worksheets.

Worksheet:
    A single spreadsheet inside a workbook.

Row:
    Horizontal collection of cells identified by numbers: 1, 2, 3...

Column:
    Vertical collection of cells identified by letters: A, B, C... Z, AA...

Cell:
    The intersection of a row and a column.
    Examples:
        A1
        B5
        AA100

Range:
    A group of one or more cells.
    Examples:
        A1:A10      Vertical range
        A1:D1       Horizontal range
        A1:D10      Rectangular range

Formula:
    An expression beginning with "=" that calculates a result.
    Examples:
        =A1+B1
        =SUM(A1:A10)
        =AVERAGE(B1:B10)

Reference:
    A formula's pointer to another cell or range.
"""


# =============================================================================
# SECTION 2: COLUMN LETTER AND COLUMN NUMBER CONVERSION
# =============================================================================

def column_letter_to_number(column_letters: str) -> int:
    """
    Convert an Excel column letter into a column number.

    Examples:
        A  -> 1
        Z  -> 26
        AA -> 27
        AB -> 28
        ZZ -> 702
    """
    column_letters = column_letters.upper().strip()

    if not column_letters.isalpha():
        raise ValueError(
            f"Invalid Excel column reference: {column_letters!r}. "
            "A column must contain alphabetic characters."
        )

    result = 0

    for character in column_letters:
        value = ord(character) - ord("A") + 1
        result = result * 26 + value

    return result


def column_number_to_letter(column_number: int) -> str:
    """
    Convert a positive Excel column number into column letters.

    Examples:
        1  -> A
        26 -> Z
        27 -> AA
        28 -> AB
    """
    if not isinstance(column_number, int) or column_number < 1:
        raise ValueError("Excel column numbers must be positive integers.")

    letters = ""

    while column_number > 0:
        column_number -= 1
        remainder = column_number % 26
        letters = chr(ord("A") + remainder) + letters
        column_number //= 26

    return letters


print("=" * 80)
print("SECTION 2: COLUMN CONVERSION")
print("=" * 80)

for column in ["A", "Z", "AA", "AB", "AZ", "BA", "ZZ"]:
    number = column_letter_to_number(column)
    print(f"{column:>3} -> {number}")

print()

for number in [1, 26, 27, 28, 52, 53, 702]:
    letter = column_number_to_letter(number)
    print(f"{number:>3} -> {letter}")


# =============================================================================
# SECTION 3: CELL REFERENCES
# =============================================================================

@dataclass(frozen=True)
class CellReference:
    """
    Represents an Excel cell reference.

    Examples:
        A1
        $A$1
        A$1
        $A1

    Absolute references:
        $A$1

    Relative references:
        A1

    Mixed references:
        $A1
        A$1
    """

    column: str
    row: int
    column_absolute: bool = False
    row_absolute: bool = False

    def __post_init__(self):
        object.__setattr__(self, "column", self.column.upper())

        if not self.column.isalpha():
            raise ValueError("Column reference must contain letters.")

        if self.row < 1:
            raise ValueError("Row number must be at least 1.")

    @property
    def column_number(self) -> int:
        return column_letter_to_number(self.column)

    def __str__(self) -> str:
        column_part = f"${self.column}" if self.column_absolute else self.column
        row_part = f"${self.row}" if self.row_absolute else str(self.row)
        return f"{column_part}{row_part}"


CELL_REFERENCE_PATTERN = re.compile(
    r"^(?P<column_absolute>\$?)(?P<column>[A-Za-z]+)"
    r"(?P<row_absolute>\$?)(?P<row>[1-9][0-9]*)$"
)


def parse_cell_reference(reference: str) -> CellReference:
    """
    Parse an Excel-style cell reference.

    Examples:
        A1
        $A$1
        A$1
        $A1
    """
    reference = reference.strip()

    match = CELL_REFERENCE_PATTERN.match(reference)

    if not match:
        raise ValueError(f"Invalid cell reference: {reference!r}")

    return CellReference(
        column=match.group("column"),
        row=int(match.group("row")),
        column_absolute=match.group("column_absolute") == "$",
        row_absolute=match.group("row_absolute") == "$",
    )


print("\n" + "=" * 80)
print("SECTION 3: CELL REFERENCES")
print("=" * 80)

references = ["A1", "$A$1", "A$1", "$A1", "AA100"]

for reference_text in references:
    reference = parse_cell_reference(reference_text)

    print(
        f"Reference: {reference!s:>6} | "
        f"Column: {reference.column:<3} | "
        f"Row: {reference.row:<4} | "
        f"Column absolute: {reference.column_absolute} | "
        f"Row absolute: {reference.row_absolute}"
    )


# =============================================================================
# SECTION 4: RELATIVE, ABSOLUTE, AND MIXED REFERENCES
# =============================================================================

def copy_cell_reference(
    reference: CellReference,
    row_offset: int,
    column_offset: int,
) -> CellReference:
    """
    Simulate Excel's behavior when a formula is copied.

    Relative components move.
    Absolute components remain fixed.

    Example:
        Formula in C2: =A2*$B$1

        Copy one row down:
            A2    -> A3
            $B$1  -> $B$1
    """
    original_column_number = reference.column_number

    if reference.column_absolute:
        new_column_number = original_column_number
    else:
        new_column_number = original_column_number + column_offset

    if reference.row_absolute:
        new_row = reference.row
    else:
        new_row = reference.row + row_offset

    if new_column_number < 1 or new_row < 1:
        raise ValueError(
            "Copying this reference would move it outside the worksheet."
        )

    return CellReference(
        column=column_number_to_letter(new_column_number),
        row=new_row,
        column_absolute=reference.column_absolute,
        row_absolute=reference.row_absolute,
    )


print("\n" + "=" * 80)
print("SECTION 4: RELATIVE, ABSOLUTE, AND MIXED REFERENCES")
print("=" * 80)

reference_examples = ["A1", "$A$1", "A$1", "$A1"]

print("Copy each reference one row down and one column right:\n")

for reference_text in reference_examples:
    original = parse_cell_reference(reference_text)
    copied = copy_cell_reference(
        original,
        row_offset=1,
        column_offset=1,
    )

    print(f"{original} -> {copied}")


# =============================================================================
# SECTION 5: CELL FORMATTING
# =============================================================================

@dataclass
class CellFormat:
    """
    Simplified representation of Excel formatting.

    Real Excel formatting supports many more options, including:
    - Font family
    - Font size
    - Font color
    - Bold
    - Italic
    - Underline
    - Fill color
    - Borders
    - Alignment
    - Number format
    - Text rotation
    - Protection
    """

    bold: bool = False
    italic: bool = False
    underline: bool = False

    horizontal_alignment: str = "general"
    vertical_alignment: str = "bottom"

    number_format: str = "General"

    fill_color: Optional[str] = None
    font_color: Optional[str] = None


# =============================================================================
# SECTION 6: CELL AND WORKSHEET IMPLEMENTATION
# =============================================================================

@dataclass
class Cell:
    """
    A simplified Excel cell.

    A cell can contain:
    - Text
    - Number
    - Boolean
    - Formula
    - Error value
    - Empty value
    """

    value: Any = None
    formula: Optional[str] = None
    cell_format: CellFormat = field(default_factory=CellFormat)

    def is_formula(self) -> bool:
        return self.formula is not None

    def is_empty(self) -> bool:
        return self.value is None and self.formula is None


class Worksheet:
    """
    Simplified worksheet implementation.

    Internally, cells are stored in a dictionary.

    Key:
        Cell coordinate, such as "A1"

    Value:
        Cell object
    """

    def __init__(self, name: str):
        if not name or not name.strip():
            raise ValueError("Worksheet name cannot be empty.")

        self.name = name
        self.cells: Dict[str, Cell] = {}

    @staticmethod
    def normalize_coordinate(coordinate: str) -> str:
        reference = parse_cell_reference(
            coordinate.replace("$", "")
        )

        return f"{reference.column}{reference.row}"

    def set_value(self, coordinate: str, value: Any) -> None:
        coordinate = self.normalize_coordinate(coordinate)

        cell = self.cells.get(coordinate, Cell())
        cell.value = value
        cell.formula = None

        self.cells[coordinate] = cell

    def set_formula(self, coordinate: str, formula: str) -> None:
        coordinate = self.normalize_coordinate(coordinate)

        if not formula.startswith("="):
            raise ValueError(
                "Excel formulas must begin with '='."
            )

        cell = self.cells.get(coordinate, Cell())
        cell.formula = formula
        cell.value = None

        self.cells[coordinate] = cell

    def get_cell(self, coordinate: str) -> Cell:
        coordinate = self.normalize_coordinate(coordinate)

        return self.cells.get(coordinate, Cell())

    def get_value(self, coordinate: str) -> Any:
        coordinate = self.normalize_coordinate(coordinate)
        cell = self.get_cell(coordinate)

        if cell.formula is not None:
            return self.evaluate_formula(cell.formula)

        return cell.value

    def set_format(
        self,
        coordinate: str,
        cell_format: CellFormat,
    ) -> None:
        coordinate = self.normalize_coordinate(coordinate)

        cell = self.cells.get(coordinate, Cell())
        cell.cell_format = cell_format

        self.cells[coordinate] = cell

    def display_cell(self, coordinate: str) -> None:
        cell = self.get_cell(coordinate)

        print(
            f"{coordinate}: "
            f"value={cell.value!r}, "
            f"formula={cell.formula!r}, "
            f"format={cell.cell_format}"
        )

    def evaluate_formula(self, formula: str) -> Any:
        """
        Evaluate a small educational subset of Excel formulas.

        Supported:
            =A1+B1
            =A1-B1
            =A1*B1
            =A1/B1
            =SUM(A1:A10)
            =AVERAGE(A1:A10)
            =MIN(A1:A10)
            =MAX(A1:A10)
            =COUNT(A1:A10)

        This is intentionally not a complete Excel formula engine.
        """

        expression = formula.strip()

        if not expression.startswith("="):
            raise ValueError("Formula must start with '='.")

        expression = expression[1:].strip()

        function_match = re.match(
            r"^(SUM|AVERAGE|MIN|MAX|COUNT)\(([^)]+)\)$",
            expression,
            flags=re.IGNORECASE,
        )

        if function_match:
            function_name = function_match.group(1).upper()
            argument = function_match.group(2).strip()

            values = self.get_range_values(argument)

            numeric_values = [
                value
                for value in values
                if isinstance(value, (int, float))
                and not isinstance(value, bool)
            ]

            if function_name == "SUM":
                return sum(numeric_values)

            if function_name == "AVERAGE":
                if not numeric_values:
                    return "#DIV/0!"
                return sum(numeric_values) / len(numeric_values)

            if function_name == "MIN":
                if not numeric_values:
                    return 0
                return min(numeric_values)

            if function_name == "MAX":
                if not numeric_values:
                    return 0
                return max(numeric_values)

            if function_name == "COUNT":
                return len(numeric_values)

        arithmetic_expression = expression

        def replace_reference(match: re.Match) -> str:
            reference_text = match.group(0)
            normalized = reference_text.replace("$", "")
            value = self.get_value(normalized)

            if value is None:
                value = 0

            if isinstance(value, str):
                raise ValueError(
                    f"Cannot perform arithmetic directly on text value "
                    f"in {reference_text}: {value!r}"
                )

            return repr(value)

        arithmetic_expression = re.sub(
            r"\$?[A-Za-z]{1,3}\$?[1-9][0-9]*",
            replace_reference,
            arithmetic_expression,
        )

        if not re.fullmatch(
            r"[0-9+\-*/().,\s]+",
            arithmetic_expression,
        ):
            return "#VALUE!"

        try:
            result = eval(
                arithmetic_expression,
                {"__builtins__": {}},
                {},
            )

            if isinstance(result, (int, float)):
                if isinstance(result, float) and math.isinf(result):
                    return "#DIV/0!"

            return result

        except ZeroDivisionError:
            return "#DIV/0!"
        except Exception:
            return "#VALUE!"

    def get_range_coordinates(
        self,
        range_reference: str,
    ) -> List[str]:
        """
        Convert an Excel range into individual coordinates.

        Examples:
            A1:A3 -> A1, A2, A3
            A1:C1 -> A1, B1, C1
            A1:B2 -> A1, B1, A2, B2
        """

        range_reference = range_reference.replace("$", "").strip()

        if ":" not in range_reference:
            return [self.normalize_coordinate(range_reference)]

        start_text, end_text = range_reference.split(":", maxsplit=1)

        start = parse_cell_reference(start_text)
        end = parse_cell_reference(end_text)

        start_column = start.column_number
        end_column = end.column_number

        start_row = start.row
        end_row = end.row

        if start_column > end_column:
            start_column, end_column = end_column, start_column

        if start_row > end_row:
            start_row, end_row = end_row, start_row

        coordinates = []

        for row in range(start_row, end_row + 1):
            for column_number in range(
                start_column,
                end_column + 1,
            ):
                column = column_number_to_letter(
                    column_number
                )

                coordinates.append(
                    f"{column}{row}"
                )

        return coordinates

    def get_range_values(
        self,
        range_reference: str,
    ) -> List[Any]:
        coordinates = self.get_range_coordinates(
            range_reference
        )

        return [
            self.get_value(coordinate)
            for coordinate in coordinates
        ]


# =============================================================================
# SECTION 7: WORKBOOK IMPLEMENTATION
# =============================================================================

class Workbook:
    """
    Simplified Excel workbook.

    Contains:
    - Multiple worksheets
    - Named ranges
    """

    def __init__(self):
        self.worksheets: Dict[str, Worksheet] = {}
        self.named_ranges: Dict[str, Tuple[str, str]] = {}

    def add_worksheet(
        self,
        name: str,
    ) -> Worksheet:
        if name in self.worksheets:
            raise ValueError(
                f"Worksheet already exists: {name!r}"
            )

        worksheet = Worksheet(name)
        self.worksheets[name] = worksheet

        return worksheet

    def get_worksheet(
        self,
        name: str,
    ) -> Worksheet:
        if name not in self.worksheets:
            raise KeyError(
                f"Worksheet does not exist: {name!r}"
            )

        return self.worksheets[name]

    def define_named_range(
        self,
        name: str,
        worksheet_name: str,
        range_reference: str,
    ) -> None:
        """
        Define a named range.

        Examples of names:
            SalesData
            TaxRate
            MonthlyExpenses

        Excel naming restrictions include:
        - Names cannot contain spaces.
        - Names generally cannot begin with a number.
        - Names cannot conflict with cell references.
        """

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_.]*",
            name,
        ):
            raise ValueError(
                "Named range must begin with a letter or underscore "
                "and contain only letters, numbers, underscores, or periods."
            )

        if worksheet_name not in self.worksheets:
            raise KeyError(
                f"Worksheet does not exist: {worksheet_name!r}"
            )

        self.named_ranges[name] = (
            worksheet_name,
            range_reference,
        )

    def get_named_range_values(
        self,
        name: str,
    ) -> List[Any]:
        if name not in self.named_ranges:
            raise KeyError(
                f"Named range does not exist: {name!r}"
            )

        worksheet_name, range_reference = (
            self.named_ranges[name]
        )

        worksheet = self.get_worksheet(
            worksheet_name
        )

        return worksheet.get_range_values(
            range_reference
        )


# =============================================================================
# SECTION 8: CREATING A BASIC WORKBOOK
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 8: WORKBOOK, WORKSHEET, AND CELLS")
print("=" * 80)

workbook = Workbook()

sales_sheet = workbook.add_worksheet(
    "Sales"
)

expenses_sheet = workbook.add_worksheet(
    "Expenses"
)

sales_sheet.set_value(
    "A1",
    "Product"
)

sales_sheet.set_value(
    "B1",
    "Quantity"
)

sales_sheet.set_value(
    "C1",
    "Price"
)

sales_sheet.set_value(
    "D1",
    "Revenue"
)

sales_sheet.set_value(
    "A2",
    "Laptop"
)

sales_sheet.set_value(
    "B2",
    3
)

sales_sheet.set_value(
    "C2",
    75000
)

sales_sheet.set_formula(
    "D2",
    "=B2*C2"
)

sales_sheet.set_value(
    "A3",
    "Monitor"
)

sales_sheet.set_value(
    "B3",
    5
)

sales_sheet.set_value(
    "C3",
    25000
)

sales_sheet.set_formula(
    "D3",
    "=B3*C3"
)

sales_sheet.set_value(
    "A4",
    "Keyboard"
)

sales_sheet.set_value(
    "B4",
    10
)

sales_sheet.set_value(
    "C4",
    3000
)

sales_sheet.set_formula(
    "D4",
    "=B4*C4"
)

for coordinate in [
    "A1", "B1", "C1", "D1",
    "A2", "B2", "C2", "D2",
    "A3", "B3", "C3", "D3",
    "A4", "B4", "C4", "D4",
]:
    value = sales_sheet.get_value(
        coordinate
    )

    print(
        f"{coordinate:<3} -> {value!r}"
    )


# =============================================================================
# SECTION 9: CELL FORMATTING
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 9: FORMATTING")
print("=" * 80)

header_format = CellFormat(
    bold=True,
    horizontal_alignment="center",
    vertical_alignment="center",
    fill_color="Light Gray",
)

currency_format = CellFormat(
    number_format="₹#,##0.00",
)

integer_format = CellFormat(
    number_format="0",
)

for coordinate in ["A1", "B1", "C1", "D1"]:
    sales_sheet.set_format(
        coordinate,
        header_format,
    )

for coordinate in ["C2", "C3", "C4", "D2", "D3", "D4"]:
    sales_sheet.set_format(
        coordinate,
        currency_format,
    )

for coordinate in ["B2", "B3", "B4"]:
    sales_sheet.set_format(
        coordinate,
        integer_format,
    )

sales_sheet.display_cell("A1")
sales_sheet.display_cell("C2")
sales_sheet.display_cell("D4")

print(
    "\nFormatting affects presentation, not necessarily "
    "the underlying numeric value."
)


# =============================================================================
# SECTION 10: RANGES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 10: RANGES")
print("=" * 80)

range_examples = [
    "A1:A4",
    "B2:B4",
    "A1:D4",
    "D2:D4",
]

for range_reference in range_examples:
    coordinates = sales_sheet.get_range_coordinates(
        range_reference
    )

    values = sales_sheet.get_range_values(
        range_reference
    )

    print(
        f"\nRange: {range_reference}"
    )

    print(
        f"Coordinates: {coordinates}"
    )

    print(
        f"Values: {values}"
    )


# =============================================================================
# SECTION 11: COMMON EXCEL FORMULAS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 11: BASIC FORMULAS")
print("=" * 80)

sales_sheet.set_formula(
    "D5",
    "=SUM(D2:D4)"
)

sales_sheet.set_formula(
    "D6",
    "=AVERAGE(D2:D4)"
)

sales_sheet.set_formula(
    "D7",
    "=MIN(D2:D4)"
)

sales_sheet.set_formula(
    "D8",
    "=MAX(D2:D4)"
)

sales_sheet.set_formula(
    "D9",
    "=COUNT(D2:D4)"
)

formula_cells = {
    "D5": "SUM",
    "D6": "AVERAGE",
    "D7": "MIN",
    "D8": "MAX",
    "D9": "COUNT",
}

for coordinate, function_name in formula_cells.items():
    print(
        f"{function_name:<8} "
        f"{sales_sheet.get_cell(coordinate).formula:<20} "
        f"-> {sales_sheet.get_value(coordinate)}"
    )


# =============================================================================
# SECTION 12: RELATIVE REFERENCES IN PRACTICE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 12: RELATIVE REFERENCES")
print("=" * 80)

print(
    """
Suppose D2 contains:

    =B2*C2

When copied from D2 to D3, Excel changes it to:

    =B3*C3

This happens because B2 and C2 are relative references.
"""
)

formula_references = [
    parse_cell_reference("B2"),
    parse_cell_reference("C2"),
]

for reference in formula_references:
    copied_reference = copy_cell_reference(
        reference,
        row_offset=1,
        column_offset=0,
    )

    print(
        f"{reference} copied one row down -> "
        f"{copied_reference}"
    )


# =============================================================================
# SECTION 13: ABSOLUTE REFERENCES IN PRACTICE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 13: ABSOLUTE REFERENCES")
print("=" * 80)

tax_sheet = workbook.add_worksheet(
    "TaxCalculation"
)

tax_sheet.set_value(
    "A1",
    "Amount"
)

tax_sheet.set_value(
    "B1",
    "Tax"
)

tax_sheet.set_value(
    "D1",
    "Tax Rate"
)

tax_sheet.set_value(
    "E1",
    0.18
)

amounts = [1000, 2500, 5000]

for index, amount in enumerate(
    amounts,
    start=2,
):
    tax_sheet.set_value(
        f"A{index}",
        amount,
    )

    tax_sheet.set_formula(
        f"B{index}",
        f"=A{index}*$E$1",
    )

for row in range(2, 5):
    amount = tax_sheet.get_value(
        f"A{row}"
    )

    tax = amount * tax_sheet.get_value(
        "E1"
    )

    print(
        f"Row {row}: Amount={amount}, "
        f"Formula = A{row}*$E$1, "
        f"Tax={tax}"
    )

print(
    "\n$E$1 remains fixed when the formula is copied."
)


# =============================================================================
# SECTION 14: MIXED REFERENCES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 14: MIXED REFERENCES")
print("=" * 80)

mixed_reference_examples = [
    "A1",
    "$A1",
    "A$1",
    "$A$1",
]

for example in mixed_reference_examples:
    reference = parse_cell_reference(
        example
    )

    copied = copy_cell_reference(
        reference,
        row_offset=2,
        column_offset=3,
    )

    print(
        f"{reference:<5} copied +2 rows and +3 columns -> "
        f"{copied}"
    )

print(
    """
Interpretation:

A1:
    Both row and column move.

$A1:
    Column A remains fixed.
    Row moves.

A$1:
    Column moves.
    Row 1 remains fixed.

$A$1:
    Neither row nor column moves.
"""
)


# =============================================================================
# SECTION 15: NAMED RANGES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 15: NAMED RANGES")
print("=" * 80)

workbook.define_named_range(
    name="SalesRevenue",
    worksheet_name="Sales",
    range_reference="D2:D4",
)

workbook.define_named_range(
    name="TaxRate",
    worksheet_name="TaxCalculation",
    range_reference="E1",
)

sales_revenue_values = (
    workbook.get_named_range_values(
        "SalesRevenue"
    )
)

tax_rate_values = (
    workbook.get_named_range_values(
        "TaxRate"
    )
)

print(
    "Named range SalesRevenue:"
)

print(
    sales_revenue_values
)

print(
    "Named range TaxRate:"
)

print(
    tax_rate_values
)

print(
    """
Named ranges improve readability.

Less descriptive:
    =SUM(D2:D100)

More descriptive:
    =SUM(SalesRevenue)

A meaningful name can make a workbook easier to maintain.
"""
)


# =============================================================================
# SECTION 16: EXCEL ERROR VALUES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 16: COMMON EXCEL ERRORS")
print("=" * 80)

error_examples = {
    "#DIV/0!": (
        "Division by zero or division by an empty value."
    ),
    "#VALUE!": (
        "An operation received an incompatible value type."
    ),
    "#REF!": (
        "A formula contains an invalid cell reference."
    ),
    "#NAME?": (
        "Excel does not recognize a function, name, or reference."
    ),
    "#N/A": (
        "A value is unavailable, often from a lookup."
    ),
    "#NUM!": (
        "A formula contains an invalid numeric calculation."
    ),
    "#SPILL!": (
        "A dynamic array cannot place results because cells are occupied."
    ),
}

for error_code, meaning in error_examples.items():
    print(
        f"{error_code:<10} {meaning}"
    )

print(
    "\nDivision-by-zero demonstration:"
)

sales_sheet.set_value(
    "F1",
    100
)

sales_sheet.set_value(
    "G1",
    0
)

sales_sheet.set_formula(
    "H1",
    "=F1/G1"
)

print(
    f"Formula {sales_sheet.get_cell('H1').formula} "
    f"returns {sales_sheet.get_value('H1')}"
)


# =============================================================================
# SECTION 17: COPYING FORMULAS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 17: COPYING FORMULAS")
print("=" * 80)

def adjust_formula_references(
    formula: str,
    row_offset: int,
    column_offset: int,
) -> str:
    """
    Adjust cell references inside a formula.

    This simulates the basic behavior of copying formulas.

    Example:

        =A1+$B$1

    Copied one row down:

        =A2+$B$1
    """

    if not formula.startswith("="):
        raise ValueError(
            "Formula must begin with '='."
        )

    reference_pattern = re.compile(
        r"\$?[A-Za-z]{1,3}\$?[1-9][0-9]*"
    )

    def replace(match: re.Match) -> str:
        reference_text = match.group(0)

        reference = parse_cell_reference(
            reference_text
        )

        copied_reference = copy_cell_reference(
            reference,
            row_offset,
            column_offset,
        )

        return str(copied_reference)

    return reference_pattern.sub(
        replace,
        formula,
    )


original_formula = "=B2*C2+$F$1"

for row_offset in range(0, 4):
    adjusted_formula = adjust_formula_references(
        original_formula,
        row_offset=row_offset,
        column_offset=0,
    )

    print(
        f"Offset {row_offset}: "
        f"{adjusted_formula}"
    )


# =============================================================================
# SECTION 18: COMMON FORMULA OPERATORS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 18: FORMULA OPERATORS")
print("=" * 80)

operators = {
    "+": "Addition",
    "-": "Subtraction",
    "*": "Multiplication",
    "/": "Division",
    "^": "Exponentiation in Excel",
    "&": "Text concatenation",
    "=": "Equal to",
    ">": "Greater than",
    "<": "Less than",
    ">=": "Greater than or equal to",
    "<=": "Less than or equal to",
    "<>": "Not equal to",
}

for operator, meaning in operators.items():
    print(
        f"{operator:<4} {meaning}"
    )


# =============================================================================
# SECTION 19: DATA TYPES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 19: EXCEL DATA TYPES")
print("=" * 80)

data_types = {
    "Number": (
        "Used for arithmetic and quantitative calculations."
    ),
    "Text": (
        "Character data such as names, descriptions, and labels."
    ),
    "Date/Time": (
        "Stored internally as numeric serial values in spreadsheet systems."
    ),
    "Boolean": (
        "TRUE or FALSE."
    ),
    "Formula": (
        "Expression that calculates a result."
    ),
    "Error": (
        "A special value indicating a calculation or reference problem."
    ),
    "Blank": (
        "A cell containing no value."
    ),
}

for data_type, explanation in data_types.items():
    print(
        f"{data_type:<12} {explanation}"
    )


# =============================================================================
# SECTION 20: BASIC DATA VALIDATION CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 20: DATA VALIDATION")
print("=" * 80)

def validate_numeric_range(
    value: Any,
    minimum: float,
    maximum: float,
) -> bool:
    """
    Simulate a basic Excel data validation rule.

    Rule:
        Input must be numeric.
        Input must be between minimum and maximum.
    """

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return minimum <= value <= maximum


test_values = [
    50,
    0,
    101,
    "50",
    None,
    -10,
]

for value in test_values:
    is_valid = validate_numeric_range(
        value,
        minimum=1,
        maximum=100,
    )

    print(
        f"Value={value!r:<6} "
        f"Valid percentage input: {is_valid}"
    )


# =============================================================================
# SECTION 21: PRACTICAL EXAMPLE - STUDENT MARKS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 21: PRACTICAL EXAMPLE - STUDENT MARKS")
print("=" * 80)

marks_sheet = workbook.add_worksheet(
    "StudentMarks"
)

headers = [
    "Student",
    "Mathematics",
    "Science",
    "English",
    "Total",
    "Average",
]

for index, header in enumerate(
    headers,
    start=1,
):
    coordinate = (
        f"{column_number_to_letter(index)}1"
    )

    marks_sheet.set_value(
        coordinate,
        header,
    )

    marks_sheet.set_format(
        coordinate,
        header_format,
    )


students = [
    ("Aarav", 85, 90, 88),
    ("Meera", 72, 81, 79),
    ("Kabir", 95, 92, 97),
]

for row_number, student_data in enumerate(
    students,
    start=2,
):
    student_name, mathematics, science, english = (
        student_data
    )

    marks_sheet.set_value(
        f"A{row_number}",
        student_name,
    )

    marks_sheet.set_value(
        f"B{row_number}",
        mathematics,
    )

    marks_sheet.set_value(
        f"C{row_number}",
        science,
    )

    marks_sheet.set_value(
        f"D{row_number}",
        english,
    )

    marks_sheet.set_formula(
        f"E{row_number}",
        f"=SUM(B{row_number}:D{row_number})",
    )

    marks_sheet.set_formula(
        f"F{row_number}",
        f"=AVERAGE(B{row_number}:D{row_number})",
    )


for row_number in range(1, 5):
    row_values = []

    for column_number in range(1, 7):
        coordinate = (
            f"{column_number_to_letter(column_number)}"
            f"{row_number}"
        )

        row_values.append(
            marks_sheet.get_value(
                coordinate
            )
        )

    print(row_values)


# =============================================================================
# SECTION 22: COMMON MISTAKES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 22: COMMON EXCEL MISTAKES")
print("=" * 80)

common_mistakes = [
    (
        "Using a relative reference when an absolute reference is required",
        "Example: A tax rate moves unexpectedly when a formula is copied."
    ),
    (
        "Using a hard-coded value inside many formulas",
        "Example: =A2*0.18 repeated throughout a workbook."
    ),
    (
        "Mixing text and numbers unintentionally",
        "A value that looks numeric may be stored as text."
    ),
    (
        "Formatting numbers inconsistently",
        "Currency, percentages, and dates should use appropriate formats."
    ),
    (
        "Typing totals manually",
        "Totals should normally be calculated with formulas."
    ),
    (
        "Deleting rows or columns without checking dependent formulas",
        "This can create invalid references."
    ),
    (
        "Using merged cells excessively",
        "Merged cells can interfere with sorting, filtering, and automation."
    ),
    (
        "Using very large ranges unnecessarily",
        "Formulas that reference entire columns may increase calculation cost."
    ),
    (
        "Overwriting formulas with values",
        "This breaks automatic recalculation."
    ),
]

for number, (mistake, consequence) in enumerate(
    common_mistakes,
    start=1,
):
    print(
        f"{number}. {mistake}"
    )

    print(
        f"   Risk: {consequence}"
    )


# =============================================================================
# SECTION 23: BASIC EXCEL SHORTCUTS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 23: BASIC EXCEL SHORTCUTS")
print("=" * 80)

shortcuts = {
    "Ctrl + N": "Create a new workbook.",
    "Ctrl + O": "Open a workbook.",
    "Ctrl + S": "Save the workbook.",
    "F12": "Save As.",
    "Ctrl + C": "Copy selected cells.",
    "Ctrl + X": "Cut selected cells.",
    "Ctrl + V": "Paste.",
    "Ctrl + Z": "Undo.",
    "Ctrl + Y": "Redo.",
    "Ctrl + A": "Select a region or worksheet context.",
    "Ctrl + B": "Toggle bold formatting.",
    "Ctrl + I": "Toggle italic formatting.",
    "Ctrl + U": "Toggle underline formatting.",
    "F2": "Edit the active cell.",
    "Alt + Enter": "Insert a line break within a cell.",
    "Ctrl + Enter": "Fill selected cells with entered content.",
    "Ctrl + D": "Fill down.",
    "Ctrl + R": "Fill right.",
    "Ctrl + Arrow": "Move to the edge of a contiguous data region.",
    "Ctrl + Shift + Arrow": "Extend selection to the edge of a data region.",
    "Ctrl + Home": "Move to the beginning of the worksheet.",
    "Ctrl + End": "Move to the last used cell area.",
    "Ctrl + Space": "Select the current column.",
    "Shift + Space": "Select the current row.",
    "Ctrl + 1": "Open the Format Cells dialog.",
    "Ctrl + Shift + L": "Toggle filters.",
    "Alt + =": "Insert AutoSum.",
    "Ctrl + `": "Toggle formula display in compatible Excel environments.",
}

for shortcut, description in shortcuts.items():
    print(
        f"{shortcut:<22} {description}"
    )


# =============================================================================
# SECTION 24: PERFORMANCE CONSIDERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 24: PERFORMANCE CONSIDERATIONS")
print("=" * 80)

performance_principles = [
    (
        "Avoid unnecessarily large formulas",
        "Large repeated calculations increase workbook recalculation time."
    ),
    (
        "Use appropriate ranges",
        "A1:A1000 is often more efficient and clearer than an entire column."
    ),
    (
        "Avoid excessive volatile calculations",
        "Functions that recalculate frequently can affect performance."
    ),
    (
        "Avoid unnecessary duplicate calculations",
        "Calculate an intermediate value once when practical."
    ),
    (
        "Keep data structures consistent",
        "Consistent columns improve sorting, filtering, formulas, and analysis."
    ),
    (
        "Use named ranges carefully",
        "They improve readability but should remain understandable and organized."
    ),
]

for principle, explanation in performance_principles:
    print(
        f"\n{principle}"
    )

    print(
        f"  {explanation}"
    )


# =============================================================================
# SECTION 25: SPREADSHEET DESIGN PRINCIPLES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 25: SPREADSHEET DESIGN PRINCIPLES")
print("=" * 80)

design_principles = [
    (
        "Separate inputs from calculations",
        "Keep user-entered values distinguishable from calculated cells."
    ),
    (
        "Use clear labels",
        "Headers should explain what each column contains."
    ),
    (
        "Avoid unexplained constants",
        "Store reusable assumptions such as tax rates in dedicated cells."
    ),
    (
        "Use consistent units",
        "Do not mix rupees, thousands of rupees, and percentages without clear labels."
    ),
    (
        "Prefer formulas to manual calculations",
        "Automatic recalculation reduces repetitive manual work."
    ),
    (
        "Document important assumptions",
        "Business rules should be understandable to future users."
    ),
    (
        "Protect important formulas",
        "Production spreadsheets may restrict accidental modification of calculation cells."
    ),
]

for principle, explanation in design_principles:
    print(
        f"{principle}: {explanation}"
    )


# =============================================================================
# SECTION 26: ADVANCED FUNDAMENTAL CONCEPT - DEPENDENCIES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 26: FORMULA DEPENDENCIES")
print("=" * 80)

print(
    """
Spreadsheet calculations form dependency relationships.

Example:

A1 = 100
B1 = 200
C1 = A1 + B1
D1 = C1 * 10

Dependency chain:

A1 ----\
        -> C1 -> D1
B1 ----/

When A1 changes, C1 and D1 may need recalculation.
"""
)


# =============================================================================
# SECTION 27: PRACTICAL EXAMPLE - SALES REPORT
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 27: PRACTICAL EXAMPLE - SALES REPORT")
print("=" * 80)

report_sheet = workbook.add_worksheet(
    "MonthlyReport"
)

report_headers = [
    "Month",
    "Revenue",
    "Expense",
    "Profit",
    "Profit Margin",
]

for index, header in enumerate(
    report_headers,
    start=1,
):
    coordinate = (
        f"{column_number_to_letter(index)}1"
    )

    report_sheet.set_value(
        coordinate,
        header,
    )

    report_sheet.set_format(
        coordinate,
        header_format,
    )


monthly_data = [
    ("January", 500000, 320000),
    ("February", 620000, 390000),
    ("March", 580000, 360000),
]

for row_number, (
    month,
    revenue,
    expense,
) in enumerate(
    monthly_data,
    start=2,
):
    report_sheet.set_value(
        f"A{row_number}",
        month,
    )

    report_sheet.set_value(
        f"B{row_number}",
        revenue,
    )

    report_sheet.set_value(
        f"C{row_number}",
        expense,
    )

    report_sheet.set_formula(
        f"D{row_number}",
        f"=B{row_number}-C{row_number}",
    )

    # Profit margin is conceptually:
    # Profit / Revenue
    #
    # This simplified formula evaluator supports arithmetic.
    report_sheet.set_formula(
        f"E{row_number}",
        f"=D{row_number}/B{row_number}",
    )


for row_number in range(2, 5):
    month = report_sheet.get_value(
        f"A{row_number}"
    )

    revenue = report_sheet.get_value(
        f"B{row_number}"
    )

    expense = report_sheet.get_value(
        f"C{row_number}"
    )

    profit = report_sheet.get_value(
        f"D{row_number}"
    )

    profit_margin = report_sheet.get_value(
        f"E{row_number}"
    )

    print(
        f"{month:<10} "
        f"Revenue={revenue:<8} "
        f"Expense={expense:<8} "
        f"Profit={profit:<8} "
        f"Margin={profit_margin:.2%}"
    )


# =============================================================================
# SECTION 28: EDGE CASES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 28: EDGE CASES")
print("=" * 80)

edge_cases = [
    (
        "Empty cell in arithmetic",
        "Spreadsheet behavior can treat blanks differently depending on the operation and function."
    ),
    (
        "Division by zero",
        "Produces #DIV/0! in Excel."
    ),
    (
        "Text in numeric ranges",
        "Some functions ignore text while others may return errors."
    ),
    (
        "Circular reference",
        "A formula directly or indirectly depends on itself."
    ),
    (
        "Invalid cell reference",
        "Deleting referenced cells can lead to #REF!."
    ),
    (
        "Incorrect absolute reference",
        "A copied formula may repeatedly use the wrong fixed cell."
    ),
]

for edge_case, explanation in edge_cases:
    print(
        f"\n{edge_case}:"
    )

    print(
        f"  {explanation}"
    )


# =============================================================================
# SECTION 29: CIRCULAR REFERENCE CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 29: CIRCULAR REFERENCES")
print("=" * 80)

print(
    """
Example of a circular reference:

A1 = B1 + 10
B1 = A1 + 20

A1 depends on B1.
B1 depends on A1.

Without a controlled iterative calculation strategy,
the spreadsheet cannot resolve this dependency normally.

Circular references can be accidental or intentional.
Intentional iterative models require careful design because
they can produce unstable or non-converging results.
"""
)


# =============================================================================
# SECTION 30: FORMULA AUDITING CONCEPTS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 30: FORMULA AUDITING")
print("=" * 80)

auditing_concepts = {
    "Precedents": (
        "Cells that provide input to the selected formula."
    ),
    "Dependents": (
        "Cells whose formulas depend on the selected cell."
    ),
    "Error Checking": (
        "Tools and methods used to identify formula problems."
    ),
    "Evaluate Formula": (
        "Step-by-step inspection of formula calculation logic."
    ),
    "Trace Relationships": (
        "Visual inspection of dependencies between cells."
    ),
}

for concept, explanation in auditing_concepts.items():
    print(
        f"{concept:<20} {explanation}"
    )


# =============================================================================
# SECTION 31: TESTING SPREADSHEET LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 31: TESTING SPREADSHEET LOGIC")
print("=" * 80)

def calculate_discounted_price(
    price: float,
    discount_rate: float,
) -> float:
    """
    Example business calculation.

    Preconditions:
        price >= 0
        0 <= discount_rate <= 1
    """

    if price < 0:
        raise ValueError(
            "Price cannot be negative."
        )

    if not 0 <= discount_rate <= 1:
        raise ValueError(
            "Discount rate must be between 0 and 1."
        )

    return price * (
        1 - discount_rate
    )


test_cases = [
    (1000, 0.10, 900),
    (500, 0.00, 500),
    (200, 1.00, 0),
]

for price, discount, expected in test_cases:
    result = calculate_discounted_price(
        price,
        discount,
    )

    assert result == expected

    print(
        f"PASS: price={price}, "
        f"discount={discount:.0%}, "
        f"result={result}"
    )

print(
    """
The same principle applies to spreadsheet models:

1. Define expected inputs.
2. Calculate expected outputs independently.
3. Test boundary values.
4. Test invalid inputs.
5. Check formulas after structural changes.
"""
)


# =============================================================================
# SECTION 32: PRODUCTION SPREADSHEET PRACTICES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 32: PRODUCTION SPREADSHEET PRACTICES")
print("=" * 80)

production_practices = [
    (
        "Version control",
        "Maintain identifiable versions of important business workbooks."
    ),
    (
        "Input validation",
        "Restrict invalid user input where practical."
    ),
    (
        "Formula protection",
        "Reduce accidental modification of critical calculations."
    ),
    (
        "Consistent formatting",
        "Use formatting conventions to distinguish inputs, outputs, and calculations."
    ),
    (
        "Documentation",
        "Explain assumptions, calculation logic, and important data sources."
    ),
    (
        "Error handling",
        "Identify and intentionally manage expected error conditions."
    ),
    (
        "Review process",
        "Critical spreadsheets should be reviewed independently."
    ),
]

for practice, explanation in production_practices:
    print(
        f"{practice:<22} {explanation}"
    )


# =============================================================================
# SECTION 33: SECURITY CONSIDERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 33: SECURITY CONSIDERATIONS")
print("=" * 80)

security_considerations = [
    (
        "Sensitive data",
        "Avoid unnecessary storage of confidential information in shared workbooks."
    ),
    (
        "Access control",
        "Restrict access to sensitive business files."
    ),
    (
        "Workbook protection",
        "Protection can reduce accidental modification but should not be treated as a complete security boundary."
    ),
    (
        "External links",
        "Review external workbook links and data sources."
    ),
    (
        "Macros",
        "Only enable and distribute trusted macro-enabled workbooks."
    ),
    (
        "Formula injection",
        "When importing untrusted text into spreadsheet software, values beginning with formula characters may require careful handling."
    ),
]

for topic, explanation in security_considerations:
    print(
        f"\n{topic}:"
    )

    print(
        f"  {explanation}"
    )


# =============================================================================
# SECTION 34: COMPREHENSIVE REFERENCE TABLE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 34: FUNDAMENTAL CONCEPT REFERENCE")
print("=" * 80)

concept_reference = [
    (
        "Workbook",
        "The complete spreadsheet file containing one or more worksheets.",
    ),
    (
        "Worksheet",
        "A tabular grid inside a workbook.",
    ),
    (
        "Cell",
        "The intersection of a row and column.",
    ),
    (
        "Range",
        "A group of one or more cells.",
    ),
    (
        "Formula",
        "An expression beginning with '=' that calculates a result.",
    ),
    (
        "Relative Reference",
        "Changes when a formula is copied.",
    ),
    (
        "Absolute Reference",
        "Uses '$' to remain fixed when copied.",
    ),
    (
        "Mixed Reference",
        "Fixes either the row or the column.",
    ),
    (
        "Named Range",
        "A meaningful name assigned to a cell or range.",
    ),
    (
        "Formatting",
        "Controls presentation without necessarily changing the stored value.",
    ),
]

for concept, definition in concept_reference:
    print(
        f"{concept:<22} {definition}"
    )


# =============================================================================
# SECTION 35: FINAL INTEGRATED EXAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 35: INTEGRATED EXAMPLE")
print("=" * 80)

integrated_sheet = workbook.add_worksheet(
    "IntegratedExample"
)

integrated_headers = [
    "Item",
    "Units",
    "Unit Price",
    "Gross Amount",
    "Discount",
    "Net Amount",
]

for index, header in enumerate(
    integrated_headers,
    start=1,
):
    coordinate = (
        f"{column_number_to_letter(index)}1"
    )

    integrated_sheet.set_value(
        coordinate,
        header,
    )

    integrated_sheet.set_format(
        coordinate,
        header_format,
    )


integrated_sheet.set_value(
    "H1",
    "Discount Rate"
)

integrated_sheet.set_value(
    "I1",
    0.10,
)

items = [
    ("Course A", 4, 1999),
    ("Course B", 2, 4999),
    ("Course C", 1, 9999),
]

for row_number, (
    item,
    units,
    unit_price,
) in enumerate(
    items,
    start=2,
):
    integrated_sheet.set_value(
        f"A{row_number}",
        item,
    )

    integrated_sheet.set_value(
        f"B{row_number}",
        units,
    )

    integrated_sheet.set_value(
        f"C{row_number}",
        unit_price,
    )

    integrated_sheet.set_formula(
        f"D{row_number}",
        f"=B{row_number}*C{row_number}",
    )

    # The discount rate uses an absolute reference.
    # When copied down, $I$1 remains fixed.
    integrated_sheet.set_formula(
        f"E{row_number}",
        f"=D{row_number}*$I$1",
    )

    integrated_sheet.set_formula(
        f"F{row_number}",
        f"=D{row_number}-E{row_number}",
    )


print(
    "Item                 Units  Unit Price  Gross      Discount   Net"
)

print(
    "-" * 75
)

discount_rate = integrated_sheet.get_value(
    "I1"
)

for row_number in range(2, 5):
    item = integrated_sheet.get_value(
        f"A{row_number}"
    )

    units = integrated_sheet.get_value(
        f"B{row_number}"
    )

    unit_price = integrated_sheet.get_value(
        f"C{row_number}"
    )

    gross = units * unit_price
    discount = gross * discount_rate
    net = gross - discount

    print(
        f"{item:<20} "
        f"{units:<6} "
        f"{unit_price:<11} "
        f"{gross:<10.2f} "
        f"{discount:<10.2f} "
        f"{net:<10.2f}"
    )


print("\n" + "=" * 80)
print("EXCEL FUNDAMENTALS STUDY SCRIPT COMPLETE")
print("=" * 80)

print(
    """
The demonstrated concepts include:

- Workbook and worksheet organization
- Rows, columns, cells, and ranges
- Cell references
- Relative references
- Absolute references
- Mixed references
- Basic formulas and arithmetic
- SUM, AVERAGE, MIN, MAX, and COUNT
- Cell formatting
- Named ranges
- Formula copying behavior
- Common spreadsheet errors
- Data validation concepts
- Formula dependencies
- Circular reference concepts
- Spreadsheet testing
- Performance considerations
- Security considerations
- Production spreadsheet design principles
- Basic Excel shortcuts
"""
)
