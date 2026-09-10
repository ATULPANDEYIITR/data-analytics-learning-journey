"""
Excel Lookup Functions
======================

A self-contained study script covering:

- VLOOKUP
- HLOOKUP
- XLOOKUP
- INDEX
- MATCH
- XMATCH
- Exact and approximate matching
- Lookup errors and error handling
- Left lookups and two-way lookups
- Wildcards
- Duplicate matches
- Sorted versus unsorted lookup data
- Approximate-match boundary behavior
- Dynamic lookup patterns
- Multiple-criteria lookups
- Performance and maintainability considerations
- Practical Excel-oriented implementations

The examples use Python data structures to model spreadsheet tables and
reproduce the important logic behind Excel lookup functions.

This file requires only Python's standard library.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional
import math
import random
import statistics
import time


# =============================================================================
# 1. FUNDAMENTALS: WHAT IS A LOOKUP?
# =============================================================================

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    """Print a readable subsection heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def print_result(label: str, value: Any) -> None:
    """Print a named result."""
    print(f"{label}: {value}")


section("1. Lookup fundamentals")

# A lookup operation has three essential ideas:
#
# 1. lookup_value:
#    The value we want to find.
#
# 2. lookup_array/table:
#    The data in which we search.
#
# 3. return_array/column:
#    The data from which we retrieve the corresponding result.
#
# Example:
#
# Employee ID | Employee | Department | Salary
# ------------+----------+------------+-------
# E101        | Anika    | Finance    | 72000
# E102        | Rahul    | Sales      | 68000
# E103        | Priya    | IT         | 85000
#
# Searching for E102 is the lookup.
# Returning Rahul is retrieving the corresponding value.

employees = [
    ["E101", "Anika", "Finance", 72000],
    ["E102", "Rahul", "Sales", 68000],
    ["E103", "Priya", "IT", 85000],
    ["E104", "Karan", "HR", 64000],
]

print_result("Employee table", employees)
print_result("Lookup value", "E102")


# =============================================================================
# 2. EXCEL-LIKE ERROR TYPES
# =============================================================================

section("2. Lookup errors")

# Excel lookup functions can produce different kinds of errors.
#
# Common errors include:
#
# #N/A
#   The lookup value cannot be found.
#
# #VALUE!
#   An argument has an invalid type or shape.
#
# #REF!
#   A formula refers to an invalid reference.
#
# #NAME?
#   Excel does not recognize a function or name.
#
# #SPILL!
#   A dynamic-array result cannot occupy the required cells.
#
# #NUM!
#   A numeric calculation or argument is invalid.
#
# For educational purposes, custom Python exceptions model the most important
# lookup-related failures.

class ExcelLookupError(Exception):
    """Base class for lookup-related errors."""


class ExcelNAError(ExcelLookupError):
    """Equivalent conceptually to Excel's #N/A."""


class ExcelValueError(ExcelLookupError):
    """Equivalent conceptually to Excel's #VALUE!."""


class ExcelRefError(ExcelLookupError):
    """Equivalent conceptually to Excel's #REF!."""


NA = ExcelNAError


def ifna(value_function: Callable[[], Any], fallback: Any) -> Any:
    """
    Simulate Excel IFNA.

    IFNA replaces only a #N/A-type error and allows other errors to propagate.
    """
    try:
        return value_function()
    except ExcelNAError:
        return fallback


def iferror(value_function: Callable[[], Any], fallback: Any) -> Any:
    """
    Simulate Excel IFERROR.

    IFERROR catches lookup errors represented by ExcelLookupError.
    """
    try:
        return value_function()
    except ExcelLookupError:
        return fallback


print_result(
    "IFNA missing lookup",
    ifna(lambda: (_ for _ in ()).throw(ExcelNAError()), "Not found"),
)

print_result(
    "IFERROR missing lookup",
    iferror(lambda: (_ for _ in ()).throw(ExcelValueError()), "Invalid value"),
)


# =============================================================================
# 3. EXACT MATCHING
# =============================================================================

section("3. Exact matching")

def exact_equal(a: Any, b: Any) -> bool:
    """
    Compare two lookup values.

    Excel comparisons have spreadsheet-specific type and coercion rules.
    This educational implementation intentionally keeps the comparison
    explicit and predictable.
    """
    return a == b


def exact_match_position(
    lookup_value: Any,
    lookup_array: Iterable[Any],
) -> int:
    """
    Return the zero-based position of the first exact match.

    Raises ExcelNAError when the value does not exist.
    """
    for position, value in enumerate(lookup_array):
        if exact_equal(value, lookup_value):
            return position
    raise ExcelNAError(f"'{lookup_value}' was not found")


print_result(
    "Position of E103",
    exact_match_position("E103", [row[0] for row in employees]),
)

print_result(
    "Missing lookup",
    ifna(
        lambda: exact_match_position("E999", [row[0] for row in employees]),
        "Not found",
    ),
)


# =============================================================================
# 4. MATCH
# =============================================================================

section("4. MATCH")

# Excel MATCH has the conceptual form:
#
# MATCH(lookup_value, lookup_array, match_type)
#
# match_type:
#   0   exact match
#   1   exact or next smaller value; lookup array must be ascending
#  -1   exact or next larger value; lookup array must be descending
#
# MATCH returns a POSITION, not the actual return value.
#
# Excel positions are 1-based.
# Python indexes are 0-based.
#
# This distinction is essential when translating between spreadsheet logic
# and programming logic.


def excel_match(
    lookup_value: Any,
    lookup_array: list[Any],
    match_type: int = 1,
) -> int:
    """
    Educational implementation of Excel MATCH.

    Returns a 1-based position, matching Excel's convention.
    """
    if match_type not in (0, 1, -1):
        raise ExcelValueError("match_type must be 0, 1, or -1")

    if not lookup_array:
        raise ExcelNAError("Empty lookup array")

    if match_type == 0:
        for index, value in enumerate(lookup_array):
            if value == lookup_value:
                return index + 1
        raise ExcelNAError(f"'{lookup_value}' was not found")

    if match_type == 1:
        # Exact match or largest value <= lookup_value.
        best_position: Optional[int] = None

        for index, value in enumerate(lookup_array):
            try:
                if value <= lookup_value:
                    best_position = index + 1
                else:
                    # For ascending data, once we exceed the target,
                    # later values cannot be valid candidates.
                    break
            except TypeError as exc:
                raise ExcelValueError(
                    "Approximate MATCH requires comparable values"
                ) from exc

        if best_position is None:
            raise ExcelNAError(
                "No value is less than or equal to the lookup value"
            )

        return best_position

    # match_type == -1
    # Exact match or smallest value >= lookup_value in descending data.
    best_position = None

    for index, value in enumerate(lookup_array):
        try:
            if value >= lookup_value:
                best_position = index + 1
            else:
                break
        except TypeError as exc:
            raise ExcelValueError(
                "Approximate MATCH requires comparable values"
            ) from exc

    if best_position is None:
        raise ExcelNAError(
            "No value is greater than or equal to the lookup value"
        )

    return best_position


product_codes = ["P101", "P102", "P103", "P104"]

print_result(
    "MATCH exact P103",
    excel_match("P103", product_codes, 0),
)

print_result(
    "MATCH missing P999",
    ifna(
        lambda: excel_match("P999", product_codes, 0),
        "Not found",
    ),
)


# =============================================================================
# 5. INDEX
# =============================================================================

section("5. INDEX")

# INDEX returns a value at a specified position.
#
# In Excel:
#
# INDEX(array, row_num)
#
# or for a two-dimensional range:
#
# INDEX(array, row_num, column_num)
#
# INDEX is powerful because it separates:
#
#   "Where is the value?"
#
# from:
#
#   "What value should be returned?"
#
# This separation makes INDEX + MATCH flexible.


def excel_index(
    array: list[list[Any]] | list[Any],
    row_num: int,
    column_num: Optional[int] = None,
) -> Any:
    """
    Educational implementation of INDEX using 1-based positions.
    """
    if row_num < 1:
        raise ExcelValueError("row_num must be at least 1")

    if isinstance(array, list) and (
        not array or not isinstance(array[0], list)
    ):
        if row_num > len(array):
            raise ExcelRefError("INDEX row is outside the array")
        if column_num is not None:
            raise ExcelValueError(
                "column_num is not valid for a one-dimensional array"
            )
        return array[row_num - 1]

    if row_num > len(array):
        raise ExcelRefError("INDEX row is outside the array")

    row = array[row_num - 1]

    if column_num is None:
        return row

    if column_num < 1 or column_num > len(row):
        raise ExcelRefError("INDEX column is outside the array")

    return row[column_num - 1]


print_result(
    "INDEX row 2",
    excel_index(employees, 2),
)

print_result(
    "INDEX row 3, column 2",
    excel_index(employees, 3, 2),
)


# =============================================================================
# 6. INDEX + MATCH
# =============================================================================

section("6. INDEX + MATCH")

# A classic Excel formula is conceptually:
#
# =INDEX(C2:C5, MATCH("E103", A2:A5, 0))
#
# MATCH finds the row.
# INDEX returns the value from the return range at that row.
#
# Unlike VLOOKUP, this pattern does not require the return column to be
# to the right of the lookup column.


def index_match(
    lookup_value: Any,
    lookup_array: list[Any],
    return_array: list[Any],
) -> Any:
    """Perform an exact INDEX + MATCH lookup."""
    if len(lookup_array) != len(return_array):
        raise ExcelValueError(
            "lookup_array and return_array must have equal lengths"
        )

    position = excel_match(lookup_value, lookup_array, 0)
    return excel_index(return_array, position)


employee_ids = [row[0] for row in employees]
employee_names = [row[1] for row in employees]
employee_departments = [row[2] for row in employees]

print_result(
    "INDEX + MATCH E104 -> department",
    index_match("E104", employee_ids, employee_departments),
)


# =============================================================================
# 7. VLOOKUP
# =============================================================================

section("7. VLOOKUP")

# VLOOKUP means Vertical Lookup.
#
# Conceptual Excel syntax:
#
# VLOOKUP(lookup_value, table_array, col_index_num, [range_lookup])
#
# The lookup value must be searched in the first column of table_array.
#
# range_lookup:
#   FALSE or 0 -> exact match
#   TRUE or 1  -> approximate match
#
# VLOOKUP returns the first matching row.


def excel_vlookup(
    lookup_value: Any,
    table_array: list[list[Any]],
    col_index_num: int,
    range_lookup: bool = False,
) -> Any:
    """
    Educational VLOOKUP implementation.

    Exact mode scans from top to bottom.

    Approximate mode implements the standard ascending-data concept:
    return the last row whose first-column value is <= lookup_value.
    """
    if not table_array:
        raise ExcelNAError("VLOOKUP table is empty")

    if col_index_num < 1:
        raise ExcelValueError("col_index_num must be at least 1")

    for row in table_array:
        if col_index_num > len(row):
            raise ExcelRefError("col_index_num exceeds table width")

    if not range_lookup:
        for row in table_array:
            if row[0] == lookup_value:
                return row[col_index_num - 1]
        raise ExcelNAError(f"'{lookup_value}' was not found")

    best_row: Optional[list[Any]] = None

    for row in table_array:
        try:
            if row[0] <= lookup_value:
                best_row = row
            else:
                break
        except TypeError as exc:
            raise ExcelValueError(
                "Approximate VLOOKUP requires compatible values"
            ) from exc

    if best_row is None:
        raise ExcelNAError(
            f"No approximate VLOOKUP match exists for '{lookup_value}'"
        )

    return best_row[col_index_num - 1]


print_result(
    "VLOOKUP E102 -> name",
    excel_vlookup("E102", employees, 2, False),
)

print_result(
    "VLOOKUP E103 -> salary",
    excel_vlookup("E103", employees, 4, False),
)


# =============================================================================
# 8. VLOOKUP APPROXIMATE MATCH
# =============================================================================

section("8. VLOOKUP approximate matching")

# Approximate matching is useful for ranges such as:
#
# Score | Grade
# 0     | F
# 40    | D
# 50    | C
# 60    | B
# 75    | A
# 90    | A+
#
# For score 82, the correct boundary is 75, so the result is A.
#
# The lookup column must be sorted ascending for this pattern.

grade_table = [
    [0, "F"],
    [40, "D"],
    [50, "C"],
    [60, "B"],
    [75, "A"],
    [90, "A+"],
]

for score in [35, 40, 49, 67, 82, 95]:
    grade = ifna(
        lambda score=score: excel_vlookup(
            score,
            grade_table,
            2,
            True,
        ),
        "Below minimum boundary",
    )
    print_result(f"Score {score}", grade)


# =============================================================================
# 9. APPROXIMATE MATCH BOUNDARIES
# =============================================================================

section("9. Approximate match boundary behavior")

# Approximate lookup usually answers:
#
# "What is the largest boundary that does not exceed my value?"
#
# It does not mean:
#
# "Find the numerically closest value."
#
# Example:
#
# Boundaries = 0, 40, 50, 60, 75, 90
# Lookup     = 74
#
# The answer is the 60 boundary, not 75, because 75 exceeds 74.

boundary_values = [0, 40, 50, 60, 75, 90]

for value in [0, 39, 40, 74, 75, 89, 90]:
    position = excel_match(value, boundary_values, 1)
    boundary = excel_index(boundary_values, position)
    print_result(
        f"Approximate MATCH for {value}",
        f"position={position}, boundary={boundary}",
    )


# =============================================================================
# 10. HLOOKUP
# =============================================================================

section("10. HLOOKUP")

# HLOOKUP means Horizontal Lookup.
#
# Conceptual syntax:
#
# HLOOKUP(lookup_value, table_array, row_index_num, [range_lookup])
#
# HLOOKUP searches across the first row and returns a value from a specified
# row in the same column.


sales_by_quarter = [
    ["Quarter", "Q1", "Q2", "Q3", "Q4"],
    ["Revenue", 120000, 135000, 148000, 162000],
    ["Profit", 18000, 22000, 27000, 31000],
]


def excel_hlookup(
    lookup_value: Any,
    table_array: list[list[Any]],
    row_index_num: int,
    range_lookup: bool = False,
) -> Any:
    """Educational HLOOKUP implementation."""
    if not table_array:
        raise ExcelNAError("HLOOKUP table is empty")

    if row_index_num < 1 or row_index_num > len(table_array):
        raise ExcelRefError("row_index_num is outside the table")

    header = table_array[0]

    if not range_lookup:
        for column_index, value in enumerate(header):
            if value == lookup_value:
                return table_array[row_index_num - 1][column_index]
        raise ExcelNAError(f"'{lookup_value}' was not found")

    best_column: Optional[int] = None

    for column_index, value in enumerate(header):
        try:
            if value <= lookup_value:
                best_column = column_index
            else:
                break
        except TypeError as exc:
            raise ExcelValueError(
                "Approximate HLOOKUP requires comparable values"
            ) from exc

    if best_column is None:
        raise ExcelNAError(
            f"No approximate HLOOKUP match for '{lookup_value}'"
        )

    return table_array[row_index_num - 1][best_column]


print_result(
    "HLOOKUP Q3 -> revenue",
    excel_hlookup("Q3", sales_by_quarter, 2, False),
)

print_result(
    "HLOOKUP Q4 -> profit",
    excel_hlookup("Q4", sales_by_quarter, 3, False),
)


# =============================================================================
# 11. XLOOKUP
# =============================================================================

section("11. XLOOKUP")

# XLOOKUP is designed to address many limitations of VLOOKUP and HLOOKUP.
#
# Conceptual syntax:
#
# XLOOKUP(
#     lookup_value,
#     lookup_array,
#     return_array,
#     [if_not_found],
#     [match_mode],
#     [search_mode]
# )
#
# Important match_mode values:
#
# 0   Exact match
# -1  Exact match or next smaller item
# 1   Exact match or next larger item
# 2   Wildcard match
#
# Important search_mode values:
#
# 1   First-to-last
# -1  Last-to-first
#
# XLOOKUP can perform left lookups because lookup_array and return_array are
# independent.


def wildcard_match(pattern: str, text: str) -> bool:
    """
    Implement a small Excel-style wildcard matcher.

    * = any number of characters
    ? = exactly one character
    ~ = escape the next wildcard character

    Matching is case-insensitive for this educational implementation.
    """
    pattern = pattern.lower()
    text = text.lower()

    def match(pi: int, ti: int) -> bool:
        while pi < len(pattern):
            character = pattern[pi]

            if character == "~":
                pi += 1
                if pi >= len(pattern):
                    return ti == len(text)
                if ti >= len(text) or pattern[pi] != text[ti]:
                    return False
                pi += 1
                ti += 1
                continue

            if character == "*":
                pi += 1
                if pi == len(pattern):
                    return True

                for next_text_index in range(ti, len(text) + 1):
                    if match(pi, next_text_index):
                        return True

                return False

            if character == "?":
                if ti >= len(text):
                    return False
                pi += 1
                ti += 1
                continue

            if ti >= len(text) or character != text[ti]:
                return False

            pi += 1
            ti += 1

        return ti == len(text)

    return match(0, 0)


def excel_xlookup(
    lookup_value: Any,
    lookup_array: list[Any],
    return_array: list[Any],
    if_not_found: Any = None,
    match_mode: int = 0,
    search_mode: int = 1,
) -> Any:
    """
    Educational XLOOKUP implementation.

    Supported match modes:
        0  exact
       -1  exact or next smaller
        1  exact or next larger
        2  wildcard

    Supported search modes:
        1   first-to-last
       -1   last-to-first
    """
    if len(lookup_array) != len(return_array):
        raise ExcelValueError(
            "lookup_array and return_array must have equal lengths"
        )

    if match_mode not in (0, -1, 1, 2):
        raise ExcelValueError("Unsupported match_mode")

    if search_mode not in (1, -1):
        raise ExcelValueError("Unsupported search_mode")

    indexes = range(len(lookup_array))
    if search_mode == -1:
        indexes = reversed(range(len(lookup_array)))

    # Exact and wildcard matching.
    if match_mode in (0, 2):
        for index in indexes:
            candidate = lookup_array[index]

            if match_mode == 0:
                matched = candidate == lookup_value
            else:
                matched = (
                    isinstance(candidate, str)
                    and isinstance(lookup_value, str)
                    and wildcard_match(lookup_value, candidate)
                )

            if matched:
                return return_array[index]

        if if_not_found is not None:
            return if_not_found

        raise ExcelNAError(f"'{lookup_value}' was not found")

    # Approximate matching.
    # For a simple educational implementation, we evaluate candidates
    # explicitly rather than relying on a sorted binary-search algorithm.
    candidates: list[tuple[Any, int]] = []

    for index, candidate in enumerate(lookup_array):
        try:
            if match_mode == -1 and candidate <= lookup_value:
                candidates.append((candidate, index))
            elif match_mode == 1 and candidate >= lookup_value:
                candidates.append((candidate, index))
        except TypeError as exc:
            raise ExcelValueError(
                "Approximate XLOOKUP requires comparable values"
            ) from exc

    if not candidates:
        if if_not_found is not None:
            return if_not_found
        raise ExcelNAError(f"No approximate match for '{lookup_value}'")

    if match_mode == -1:
        best_value = max(item[0] for item in candidates)
    else:
        best_value = min(item[0] for item in candidates)

    # Respect search direction when duplicates exist.
    candidate_indexes = [
        index for value, index in candidates if value == best_value
    ]

    selected_index = (
        candidate_indexes[0]
        if search_mode == 1
        else candidate_indexes[-1]
    )

    return return_array[selected_index]


print_result(
    "XLOOKUP E103 -> name",
    excel_xlookup("E103", employee_ids, employee_names),
)

print_result(
    "XLOOKUP E103 -> department",
    excel_xlookup("E103", employee_ids, employee_departments),
)

print_result(
    "XLOOKUP missing value",
    excel_xlookup(
        "E999",
        employee_ids,
        employee_names,
        if_not_found="Employee not found",
    ),
)


# =============================================================================
# 12. VLOOKUP VERSUS XLOOKUP
# =============================================================================

section("12. VLOOKUP versus XLOOKUP")

comparison = {
    "Lookup direction": {
        "VLOOKUP": "Normally rightward from first column",
        "XLOOKUP": "Can return left or right",
    },
    "Exact matching": {
        "VLOOKUP": "FALSE",
        "XLOOKUP": "match_mode=0",
    },
    "Approximate matching": {
        "VLOOKUP": "TRUE",
        "XLOOKUP": "match_mode=-1 or 1",
    },
    "Return specification": {
        "VLOOKUP": "Column number",
        "XLOOKUP": "Separate return array",
    },
    "Not-found result": {
        "VLOOKUP": "Usually handled with IFERROR/IFNA",
        "XLOOKUP": "if_not_found argument",
    },
    "Search direction": {
        "VLOOKUP": "Limited",
        "XLOOKUP": "search_mode",
    },
    "Wildcard matching": {
        "VLOOKUP": "Limited through related techniques",
        "XLOOKUP": "match_mode=2",
    },
}

for feature, values in comparison.items():
    print(f"\n{feature}:")
    for function_name, description in values.items():
        print(f"  {function_name}: {description}")


# =============================================================================
# 13. LEFT LOOKUP
# =============================================================================

section("13. Left lookup")

# Consider:
#
# Employee | ID
# Anika    | E101
# Rahul    | E102
# Priya    | E103
#
# If the lookup value is E102 and the desired result is Rahul, VLOOKUP cannot
# naturally perform this because E102 is to the right of the return column.
#
# XLOOKUP and INDEX + MATCH solve this directly.

employee_name_first = employee_names
employee_id_second = employee_ids

print_result(
    "INDEX + MATCH left lookup",
    index_match("E102", employee_id_second, employee_name_first),
)

print_result(
    "XLOOKUP left lookup",
    excel_xlookup("E102", employee_id_second, employee_name_first),
)


# =============================================================================
# 14. XMATCH
# =============================================================================

section("14. XMATCH")

# XMATCH is a modern replacement for many MATCH use cases.
#
# Conceptual syntax:
#
# XMATCH(lookup_value, lookup_array, [match_mode], [search_mode])
#
# It supports:
#
# match_mode:
#   0   exact
#  -1   exact or next smaller
#   1   exact or next larger
#   2   wildcard
#
# search_mode:
#   1   first-to-last
#  -1   last-to-first
#   2   binary search ascending
#  -2   binary search descending
#
# The combination of XMATCH and INDEX can create a flexible lookup system.


def excel_xmatch(
    lookup_value: Any,
    lookup_array: list[Any],
    match_mode: int = 0,
    search_mode: int = 1,
) -> int:
    """Educational XMATCH implementation returning a 1-based position."""
    if match_mode not in (0, -1, 1, 2):
        raise ExcelValueError("Unsupported XMATCH match_mode")

    if search_mode not in (1, -1, 2, -2):
        raise ExcelValueError("Unsupported XMATCH search_mode")

    indexes = list(range(len(lookup_array)))

    if search_mode == -1:
        indexes.reverse()

    if match_mode == 0:
        for index in indexes:
            if lookup_array[index] == lookup_value:
                return index + 1
        raise ExcelNAError(f"'{lookup_value}' was not found")

    if match_mode == 2:
        if not isinstance(lookup_value, str):
            raise ExcelValueError("Wildcard lookup requires a text pattern")

        for index in indexes:
            if (
                isinstance(lookup_array[index], str)
                and wildcard_match(lookup_value, lookup_array[index])
            ):
                return index + 1

        raise ExcelNAError(f"Wildcard '{lookup_value}' was not found")

    candidates: list[tuple[Any, int]] = []

    for index, candidate in enumerate(lookup_array):
        try:
            if match_mode == -1 and candidate <= lookup_value:
                candidates.append((candidate, index))
            elif match_mode == 1 and candidate >= lookup_value:
                candidates.append((candidate, index))
        except TypeError as exc:
            raise ExcelValueError(
                "Approximate XMATCH requires comparable values"
            ) from exc

    if not candidates:
        raise ExcelNAError(f"No approximate match for '{lookup_value}'")

    if match_mode == -1:
        best_value = max(value for value, _ in candidates)
    else:
        best_value = min(value for value, _ in candidates)

    selected = [
        index for value, index in candidates if value == best_value
    ]

    return (selected[0] if search_mode != -1 else selected[-1]) + 1


print_result(
    "XMATCH E103",
    excel_xmatch("E103", employee_ids, 0),
)

print_result(
    "XMATCH last Rahul",
    excel_xmatch(
        "Rahul",
        ["Anika", "Rahul", "Priya", "Rahul"],
        0,
        -1,
    ),
)


# =============================================================================
# 15. XLOOKUP WITH DUPLICATES
# =============================================================================

section("15. Duplicate lookup values")

# Lookup functions may encounter duplicate values.
#
# A first-to-last search returns the first matching record.
# A last-to-first search returns the last matching record.
#
# This distinction matters when data contains multiple transactions for the
# same customer, employee, product, or account.

duplicate_ids = ["C101", "C102", "C101", "C103"]
duplicate_statuses = ["Open", "Closed", "Escalated", "Open"]

print_result(
    "First C101",
    excel_xlookup(
        "C101",
        duplicate_ids,
        duplicate_statuses,
        search_mode=1,
    ),
)

print_result(
    "Last C101",
    excel_xlookup(
        "C101",
        duplicate_ids,
        duplicate_statuses,
        search_mode=-1,
    ),
)


# =============================================================================
# 16. WILDCARD LOOKUPS
# =============================================================================

section("16. Wildcard lookups")

# Excel wildcard symbols:
#
# *  matches zero or more characters
# ?  matches exactly one character
# ~  escapes a wildcard
#
# Example:
#
# "Rah*" matches Rahul, Rahi, Rakesh only if the prefix is Rah.
# "A?ika" matches Anika but not Aabika.
#
# Wildcards are useful when the lookup value is partially known.

names = ["Anika", "Anil", "Rahul", "Rakesh", "Priya", "Priyanka"]
departments = ["Finance", "IT", "Sales", "Sales", "IT", "HR"]

print_result(
    "Wildcard Rah*",
    excel_xlookup(
        "Rah*",
        names,
        departments,
        if_not_found="No matching name",
        match_mode=2,
    ),
)

print_result(
    "Wildcard Pri*",
    excel_xlookup(
        "Pri*",
        names,
        departments,
        if_not_found="No matching name",
        match_mode=2,
    ),
)


# =============================================================================
# 17. TWO-WAY LOOKUP
# =============================================================================

section("17. Two-way lookup")

# A two-way lookup finds:
#
#   1. the correct row
#   2. the correct column
#
# Example:
#
#             Jan   Feb   Mar
# Product A   100   120   130
# Product B   200   220   240
#
# We can ask:
#
# "What is Product B's February value?"
#
# In Excel, INDEX + MATCH + MATCH is a classic solution:
#
# =INDEX(data,
#        MATCH(row_key, row_headers, 0),
#        MATCH(column_key, column_headers, 0))


monthly_sales = [
    ["Product", "Jan", "Feb", "Mar"],
    ["Product A", 100, 120, 130],
    ["Product B", 200, 220, 240],
    ["Product C", 300, 320, 350],
]

row_headers = [row[0] for row in monthly_sales[1:]]
column_headers = monthly_sales[0][1:]
data_matrix = [row[1:] for row in monthly_sales[1:]]


def two_way_index_match(
    row_value: Any,
    column_value: Any,
    row_headers: list[Any],
    column_headers: list[Any],
    data_matrix: list[list[Any]],
) -> Any:
    """Perform an INDEX + MATCH + MATCH two-dimensional lookup."""
    row_position = excel_match(row_value, row_headers, 0)
    column_position = excel_match(column_value, column_headers, 0)

    return excel_index(
        data_matrix,
        row_position,
        column_position,
    )


print_result(
    "Product B / Feb",
    two_way_index_match(
        "Product B",
        "Feb",
        row_headers,
        column_headers,
        data_matrix,
    ),
)


# =============================================================================
# 18. TWO-WAY XLOOKUP
# =============================================================================

section("18. Two-way XLOOKUP")

# XLOOKUP can also be nested:
#
# XLOOKUP(
#     column_name,
#     column_headers,
#     XLOOKUP(row_name, row_headers, data)
# )
#
# This separates row selection and column selection.

def xlookup_two_way(
    row_value: Any,
    column_value: Any,
    row_headers: list[Any],
    column_headers: list[Any],
    data_matrix: list[list[Any]],
) -> Any:
    """Perform a two-dimensional lookup using XLOOKUP concepts."""
    selected_row = excel_xlookup(
        row_value,
        row_headers,
        data_matrix,
    )

    return excel_xlookup(
        column_value,
        column_headers,
        selected_row,
    )


print_result(
    "Product C / Mar",
    xlookup_two_way(
        "Product C",
        "Mar",
        row_headers,
        column_headers,
        data_matrix,
    ),
)


# =============================================================================
# 19. MULTIPLE-CRITERIA LOOKUPS
# =============================================================================

section("19. Multiple-criteria lookups")

# Real datasets often require more than one condition.
#
# Example:
#
# Employee | Department | City | Salary
#
# A lookup might require:
#
# Department = IT
# City       = Delhi
#
# One common Excel approach is to create a Boolean condition for every row:
#
# (Department="IT") * (City="Delhi")
#
# The row where both conditions are TRUE becomes the matching row.
#
# Another practical method is a helper key such as:
#
# IT|Delhi
#
# Then a standard lookup can search for that combined key.

employee_records = [
    {
        "employee": "Anika",
        "department": "Finance",
        "city": "Mumbai",
        "salary": 72000,
    },
    {
        "employee": "Rahul",
        "department": "IT",
        "city": "Delhi",
        "salary": 85000,
    },
    {
        "employee": "Priya",
        "department": "IT",
        "city": "Mumbai",
        "salary": 88000,
    },
    {
        "employee": "Karan",
        "department": "HR",
        "city": "Delhi",
        "salary": 64000,
    },
]


def multiple_criteria_lookup(
    records: list[dict[str, Any]],
    criteria: dict[str, Any],
    return_field: str,
) -> Any:
    """Return the first record satisfying all supplied criteria."""
    for record in records:
        if all(record.get(key) == value for key, value in criteria.items()):
            if return_field not in record:
                raise ExcelRefError(
                    f"Return field '{return_field}' does not exist"
                )
            return record[return_field]

    raise ExcelNAError("No record satisfies all criteria")


print_result(
    "IT + Delhi salary",
    multiple_criteria_lookup(
        employee_records,
        {"department": "IT", "city": "Delhi"},
        "salary",
    ),
)


# =============================================================================
# 20. HELPER-KEY LOOKUP
# =============================================================================

section("20. Helper-key lookup")

# Helper keys are often useful in spreadsheet design because they simplify
# formulas and can make formulas easier to inspect.

helper_keys = [
    f"{record['department']}|{record['city']}"
    for record in employee_records
]
helper_values = [record["salary"] for record in employee_records]

print_result(
    "Helper key IT|Delhi",
    excel_xlookup(
        "IT|Delhi",
        helper_keys,
        helper_values,
        if_not_found="No matching employee",
    ),
)


# =============================================================================
# 21. EXACT VERSUS APPROXIMATE MATCHING
# =============================================================================

section("21. Exact versus approximate matching")

exact_example = ["A", "B", "C", "D"]

print_result(
    "Exact match B",
    excel_match("B", exact_example, 0),
)

numeric_boundaries = [100, 200, 300, 400]

for amount in [99, 100, 150, 250, 399, 400, 450]:
    try:
        position = excel_match(amount, numeric_boundaries, 1)
        boundary = excel_index(numeric_boundaries, position)
        print_result(
            f"Approximate match {amount}",
            f"boundary={boundary}",
        )
    except ExcelLookupError as error:
        print_result(
            f"Approximate match {amount}",
            f"error={error}",
        )


# =============================================================================
# 22. WHY SORTING MATTERS
# =============================================================================

section("22. Why sorting matters")

# Approximate lookup is fundamentally a boundary-selection operation.
#
# Ascending:
#
# 0, 40, 50, 60, 75, 90
#
# Correct.
#
# Unsorted:
#
# 0, 75, 40, 90, 50, 60
#
# An approximate lookup algorithm that assumes ascending order can return an
# incorrect result.
#
# Therefore:
#
# Exact match:
#   Sorting is generally unnecessary.
#
# Approximate match:
#   Sorting requirements depend on the specific function/mode.
#   Follow the function's documented ordering requirement.
#
# This is one of the most important practical rules in lookup work.

sorted_boundaries = [0, 40, 50, 60, 75, 90]
unsorted_boundaries = [0, 75, 40, 90, 50, 60]

print_result(
    "Sorted approximate lookup for 82",
    excel_match(82, sorted_boundaries, 1),
)

print_result(
    "Unsorted data demonstrates why approximate matching is dangerous",
    excel_match(82, unsorted_boundaries, 1),
)


# =============================================================================
# 23. ERROR HANDLING PATTERNS
# =============================================================================

section("23. Error handling patterns")

# A lookup formula should distinguish:
#
# "The record does not exist"
#
# from:
#
# "The formula or data structure is invalid."
#
# IFNA is preferable when only a missing lookup should be replaced.
#
# IFERROR is broader and catches many different errors.

def lookup_salary(employee_id: str) -> float:
    return index_match(
        employee_id,
        employee_ids,
        [row[3] for row in employees],
    )


print_result(
    "IFNA with missing employee",
    ifna(
        lambda: lookup_salary("E999"),
        "Employee not found",
    ),
)

print_result(
    "IFERROR with invalid operation",
    iferror(
        lambda: excel_index(employees, 99, 2),
        "Lookup/reference error",
    ),
)


# =============================================================================
# 24. ERROR DIAGNOSTICS
# =============================================================================

section("24. Error diagnostics")

def diagnose_lookup_error(
    lookup_value: Any,
    lookup_array: list[Any],
) -> str:
    """
    Explain why an exact lookup failed.

    Diagnostic logic:
    1. Empty lookup array
    2. Exact value exists
    3. Potential type mismatch
    4. Genuine missing value
    """
    if not lookup_array:
        return "The lookup array is empty."

    if lookup_value in lookup_array:
        return "The value exists and should match exactly."

    same_text = [
        value
        for value in lookup_array
        if str(value).strip().lower() == str(lookup_value).strip().lower()
    ]

    if same_text:
        return (
            "A text-normalization issue may exist, such as case, "
            "whitespace, or representation differences."
        )

    return "The lookup value is not present."


print_result(
    "Diagnostic E999",
    diagnose_lookup_error("E999", employee_ids),
)

print_result(
    "Diagnostic E103 ",
    diagnose_lookup_error("E103 ", employee_ids),
)


# =============================================================================
# 25. TEXT NORMALIZATION
# =============================================================================

section("25. Text normalization")

# Spreadsheet lookup failures frequently arise from inconsistent text:
#
# "E103"
# " E103"
# "E103 "
#
# These may look identical visually but can behave differently depending on
# the formula and data type.
#
# CLEAN and TRIM are commonly used spreadsheet concepts for cleaning data.
#
# Python equivalents can be demonstrated explicitly.

def normalize_text(value: Any) -> str:
    """Basic normalization similar to spreadsheet data-cleaning patterns."""
    return str(value).strip().lower()


def normalized_lookup(
    lookup_value: str,
    lookup_array: list[str],
    return_array: list[Any],
) -> Any:
    """Lookup after normalizing both lookup and source values."""
    normalized_target = normalize_text(lookup_value)

    for value, result in zip(lookup_array, return_array):
        if normalize_text(value) == normalized_target:
            return result

    raise ExcelNAError(f"'{lookup_value}' was not found")


messy_ids = ["E101", " E102", "E103 ", "E104"]
messy_names = ["Anika", "Rahul", "Priya", "Karan"]

print_result(
    "Normalized lookup of ' E102 '",
    normalized_lookup(" E102 ", messy_ids, messy_names),
)


# =============================================================================
# 26. NUMBERS STORED AS TEXT
# =============================================================================

section("26. Numbers stored as text")

# A classic spreadsheet problem:
#
# Numeric 100
#
# versus:
#
# Text "100"
#
# They can appear visually identical but represent different types.
#
# Robust spreadsheet models should keep identifiers and numeric measures in
# consistent data types.

numeric_values = [100, 200, 300]
text_values = ["100", "200", "300"]

print_result(
    "Exact numeric 200",
    excel_match(200, numeric_values, 0),
)

print_result(
    "Exact text '200'",
    excel_match("200", text_values, 0),
)

print_result(
    "Numeric 200 against text values",
    ifna(
        lambda: excel_match(200, text_values, 0),
        "No exact match because the representations differ",
    ),
)


# =============================================================================
# 27. CASE SENSITIVITY
# =============================================================================

section("27. Case sensitivity")

# Standard Excel lookup comparisons are generally not case-sensitive.
#
# A case-sensitive comparison can be built separately when the business rule
# requires it.
#
# Example:
#
# "abc" and "ABC"
#
# Standard lookup:
#   generally treated as the same text.
#
# Case-sensitive custom logic:
#   treated as different strings.

def case_insensitive_lookup(
    lookup_value: str,
    lookup_array: list[str],
) -> int:
    """Return 1-based position using case-insensitive matching."""
    target = lookup_value.lower()

    for index, value in enumerate(lookup_array):
        if value.lower() == target:
            return index + 1

    raise ExcelNAError("Value not found")


def case_sensitive_lookup(
    lookup_value: str,
    lookup_array: list[str],
) -> int:
    """Return 1-based position using case-sensitive matching."""
    for index, value in enumerate(lookup_array):
        if value == lookup_value:
            return index + 1

    raise ExcelNAError("Value not found")


case_data = ["ABC", "abc", "Abc"]

print_result(
    "Case-insensitive abc",
    case_insensitive_lookup("abc", case_data),
)

print_result(
    "Case-sensitive abc",
    case_sensitive_lookup("abc", case_data),
)


# =============================================================================
# 28. SEARCHING FROM LAST TO FIRST
# =============================================================================

section("28. First match versus last match")

transaction_ids = ["T001", "T002", "T001", "T003", "T001"]
transaction_values = [100, 200, 350, 400, 500]

print_result(
    "First T001",
    excel_xlookup(
        "T001",
        transaction_ids,
        transaction_values,
        search_mode=1,
    ),
)

print_result(
    "Last T001",
    excel_xlookup(
        "T001",
        transaction_ids,
        transaction_values,
        search_mode=-1,
    ),
)


# =============================================================================
# 29. APPROXIMATE MATCH: NEXT SMALLER
# =============================================================================

section("29. Exact or next smaller")

tax_brackets = [
    [0, 0.00],
    [250000, 0.05],
    [500000, 0.10],
    [1000000, 0.20],
    [1500000, 0.30],
]

income = 780000

tax_rate = excel_xlookup(
    income,
    [row[0] for row in tax_brackets],
    [row[1] for row in tax_brackets],
    match_mode=-1,
)

print_result(
    f"Applicable rate boundary for income {income}",
    tax_rate,
)


# =============================================================================
# 30. APPROXIMATE MATCH: NEXT LARGER
# =============================================================================

section("30. Exact or next larger")

delivery_limits = [10, 25, 50, 100]
shipping_classes = ["Small", "Medium", "Large", "Freight"]

package_weight = 37

shipping_class = excel_xlookup(
    package_weight,
    delivery_limits,
    shipping_classes,
    match_mode=1,
)

print_result(
    f"Next larger shipping limit for {package_weight}",
    shipping_class,
)


# =============================================================================
# 31. SORTED LOOKUP DATA STRUCTURE
# =============================================================================

section("31. Sorted lookup data")

# For very large datasets, binary search can be dramatically faster than
# scanning every row.
#
# Complexity:
#
# Linear search:
#   O(n)
#
# Binary search:
#   O(log n)
#
# The trade-off is that binary search requires correctly sorted data.
#
# XMATCH and XLOOKUP provide binary-search modes in modern Excel, represented
# conceptually here with Python's bisect module.

def binary_exact_match(
    lookup_value: Any,
    lookup_array: list[Any],
) -> int:
    """Return a 1-based exact position using binary search."""
    position = bisect_left(lookup_array, lookup_value)

    if (
        position >= len(lookup_array)
        or lookup_array[position] != lookup_value
    ):
        raise ExcelNAError(f"'{lookup_value}' was not found")

    return position + 1


large_sorted_values = list(range(0, 1_000_000, 2))

print_result(
    "Binary exact lookup position",
    binary_exact_match(888888, large_sorted_values),
)


# =============================================================================
# 32. BINARY APPROXIMATE LOOKUP
# =============================================================================

section("32. Binary approximate lookup")

def binary_next_smaller(
    lookup_value: int | float,
    sorted_values: list[int | float],
) -> int | float:
    """
    Return the largest sorted value <= lookup_value.

    This is the algorithmic equivalent of an approximate lookup boundary.
    """
    position = bisect_right(sorted_values, lookup_value) - 1

    if position < 0:
        raise ExcelNAError(
            "No value is less than or equal to the lookup value"
        )

    return sorted_values[position]


for value in [0, 1, 7, 8, 999999]:
    print_result(
        f"Binary next-smaller lookup for {value}",
        binary_next_smaller(value, large_sorted_values),
    )


# =============================================================================
# 33. PERFORMANCE COMPARISON
# =============================================================================

section("33. Performance comparison")

# This demonstration compares a simple linear search with binary search.
#
# Exact runtime depends on hardware and Python implementation, so the values
# are illustrative rather than universal benchmarks.

def linear_search(
    lookup_value: int,
    values: list[int],
) -> int:
    """Return zero-based position using linear search."""
    for index, value in enumerate(values):
        if value == lookup_value:
            return index
    raise ExcelNAError("Value not found")


performance_data = list(range(0, 2_000_000, 2))
performance_target = 1_999_998

start = time.perf_counter()
linear_search(performance_target, performance_data)
linear_time = time.perf_counter() - start

start = time.perf_counter()
binary_exact_match(performance_target, performance_data)
binary_time = time.perf_counter() - start

print_result("Linear search time", f"{linear_time:.6f} seconds")
print_result("Binary search time", f"{binary_time:.6f} seconds")


# =============================================================================
# 34. VLOOKUP COLUMN-INDEX FRAGILITY
# =============================================================================

section("34. VLOOKUP column-index fragility")

# VLOOKUP uses a numeric column index:
#
# VLOOKUP(A2, A:D, 4, FALSE)
#
# If a new column is inserted into the table, the intended return column may
# change relative to the hard-coded index.
#
# XLOOKUP identifies the return range directly, which generally makes the
# formula easier to maintain.

original_table = [
    ["ID", "Name", "Department", "Salary"],
    ["E101", "Anika", "Finance", 72000],
    ["E102", "Rahul", "Sales", 68000],
]

modified_table = [
    ["ID", "Name", "Department", "Location", "Salary"],
    ["E101", "Anika", "Finance", "Mumbai", 72000],
    ["E102", "Rahul", "Sales", "Delhi", 68000],
]

print_result(
    "Original VLOOKUP salary column index",
    excel_vlookup("E102", original_table[1:], 4, False),
)

print_result(
    "Modified table correct salary index",
    excel_vlookup("E102", modified_table[1:], 5, False),
)

print_result(
    "XLOOKUP salary after inserted column",
    excel_xlookup(
        "E102",
        [row[0] for row in modified_table[1:]],
        [row[4] for row in modified_table[1:]],
    ),
)


# =============================================================================
# 35. LOOKUP VALUES WITH BLANKS
# =============================================================================

section("35. Blank lookup values")

blank_data = ["A", "", "C"]
blank_results = [10, 20, 30]

print_result(
    "Lookup blank",
    excel_xlookup(
        "",
        blank_data,
        blank_results,
        if_not_found="Blank not found",
    ),
)

# In production spreadsheets, decide explicitly whether blank values are
# legitimate keys or should be rejected.


# =============================================================================
# 36. ZERO AS A VALID RESULT
# =============================================================================

section("36. Zero is a valid result")

# A common mistake is to interpret a returned zero as a failed lookup.
#
# A lookup result of 0 is valid if the source cell contains zero.
#
# The correct test is whether the lookup itself succeeded, not whether the
# returned value is truthy.

zero_ids = ["A", "B", "C"]
zero_values = [100, 0, 300]

result = excel_xlookup(
    "B",
    zero_ids,
    zero_values,
)

print_result("Lookup result for B", result)
print_result("Lookup succeeded", True)


# =============================================================================
# 37. RETURNING MULTIPLE MATCHES
# =============================================================================

section("37. Multiple matches")

# XLOOKUP returns one matching result.
#
# If all matching records are required, Excel's FILTER function is usually a
# more appropriate tool than a single-result lookup.
#
# This script demonstrates the underlying selection concept.

def filter_matches(
    lookup_value: Any,
    lookup_array: list[Any],
    return_array: list[Any],
) -> list[Any]:
    """Return every matching result."""
    if len(lookup_array) != len(return_array):
        raise ExcelValueError("Arrays must have equal lengths")

    return [
        result
        for value, result in zip(lookup_array, return_array)
        if value == lookup_value
    ]


all_t001_values = filter_matches(
    "T001",
    transaction_ids,
    transaction_values,
)

print_result(
    "All T001 transaction values",
    all_t001_values,
)


# =============================================================================
# 38. LOOKUP TABLE DESIGN
# =============================================================================

section("38. Lookup table design principles")

# Good lookup tables generally have:
#
# 1. A clearly defined key.
# 2. Consistent data types.
# 3. One record per unique key when uniqueness is expected.
# 4. No accidental duplicates.
# 5. No merged cells in the data area.
# 6. Consistent headers.
# 7. Appropriate sorting for approximate lookup.
# 8. No unnecessary hidden transformations.
#
# The quality of the lookup formula cannot compensate for poorly structured
# source data.

@dataclass
class LookupTable:
    """Simple representation of a lookup table with a declared key."""

    key_name: str
    rows: list[dict[str, Any]]

    def validate_unique_keys(self) -> list[Any]:
        """Return duplicate key values."""
        seen: set[Any] = set()
        duplicates: set[Any] = set()

        for row in self.rows:
            key = row.get(self.key_name)

            if key in seen:
                duplicates.add(key)

            seen.add(key)

        return sorted(duplicates, key=str)


quality_table = LookupTable(
    key_name="id",
    rows=[
        {"id": "E101", "name": "Anika"},
        {"id": "E102", "name": "Rahul"},
        {"id": "E103", "name": "Priya"},
    ],
)

print_result(
    "Duplicate keys in quality table",
    quality_table.validate_unique_keys(),
)


# =============================================================================
# 39. DUPLICATE-KEY DETECTION
# =============================================================================

section("39. Duplicate-key detection")

duplicate_key_table = LookupTable(
    key_name="id",
    rows=[
        {"id": "E101", "name": "Anika"},
        {"id": "E102", "name": "Rahul"},
        {"id": "E101", "name": "Anika Updated"},
    ],
)

print_result(
    "Duplicate keys",
    duplicate_key_table.validate_unique_keys(),
)


# =============================================================================
# 40. LOOKUP WITH STRUCTURED RECORDS
# =============================================================================

section("40. Lookup using structured records")

def record_lookup(
    lookup_value: Any,
    records: list[dict[str, Any]],
    key_field: str,
    return_field: str,
) -> Any:
    """Perform an exact lookup against dictionary-like records."""
    for record in records:
        if key_field not in record:
            raise ExcelRefError(
                f"Key field '{key_field}' does not exist"
            )

        if record[key_field] == lookup_value:
            if return_field not in record:
                raise ExcelRefError(
                    f"Return field '{return_field}' does not exist"
                )
            return record[return_field]

    raise ExcelNAError(f"'{lookup_value}' was not found")


print_result(
    "Structured lookup",
    record_lookup(
        "E103",
        employee_records=[
            {
                "id": "E101",
                "name": "Anika",
                "department": "Finance",
            },
            {
                "id": "E102",
                "name": "Rahul",
                "department": "Sales",
            },
            {
                "id": "E103",
                "name": "Priya",
                "department": "IT",
            },
        ],
        key_field="id",
        return_field="name",
    ),
)


# =============================================================================
# 41. LOOKUP CHAINING
# =============================================================================

section("41. Lookup chaining")

# Sometimes one lookup supplies the key for another lookup.
#
# Example:
#
# Employee ID -> Department Code -> Department Name
#
# This can be useful but excessive chaining increases formula complexity and
# makes data lineage harder to understand.

employee_to_department_code = {
    "E101": "FIN",
    "E102": "SAL",
    "E103": "IT",
}

department_names = {
    "FIN": "Finance",
    "SAL": "Sales",
    "IT": "Information Technology",
}

employee_id = "E103"
department_code = employee_to_department_code[employee_id]
department_name = department_names[department_code]

print_result(
    "Chained lookup result",
    department_name,
)


# =============================================================================
# 42. LOOKUP WITH CALCULATED RETURN VALUES
# =============================================================================

section("42. Lookup with calculated return values")

# A lookup does not always have to return raw data.
#
# The returned value can be used in another calculation.
#
# Example:
#
# Product -> Unit price
# Quantity -> supplied separately
# Total = looked-up price * quantity

product_ids = ["P101", "P102", "P103"]
product_prices = [125.0, 250.0, 400.0]

ordered_product = "P102"
quantity = 6

unit_price = excel_xlookup(
    ordered_product,
    product_ids,
    product_prices,
)

total = unit_price * quantity

print_result("Unit price", unit_price)
print_result("Quantity", quantity)
print_result("Order total", total)


# =============================================================================
# 43. LOOKUP AND DATA VALIDATION
# =============================================================================

section("43. Lookup and validation")

def validated_lookup(
    lookup_value: Any,
    lookup_array: list[Any],
    return_array: list[Any],
) -> Any:
    """
    Perform a lookup after validating array shape and lookup input.
    """
    if lookup_value is None:
        raise ExcelValueError("Lookup value cannot be None")

    if len(lookup_array) != len(return_array):
        raise ExcelValueError(
            "Lookup and return arrays must have the same length"
        )

    if not lookup_array:
        raise ExcelValueError("Lookup array cannot be empty")

    return excel_xlookup(
        lookup_value,
        lookup_array,
        return_array,
    )


print_result(
    "Validated lookup",
    validated_lookup("P103", product_ids, product_prices),
)


# =============================================================================
# 44. APPROXIMATE LOOKUP WITH NEGATIVE VALUES
# =============================================================================

section("44. Approximate matching with negative values")

temperature_boundaries = [
    [-20, "Very Cold"],
    [0, "Cold"],
    [15, "Mild"],
    [25, "Warm"],
    [35, "Hot"],
]

for temperature in [-30, -20, -5, 10, 20, 30, 40]:
    result = ifna(
        lambda temperature=temperature: excel_xlookup(
            temperature,
            [row[0] for row in temperature_boundaries],
            [row[1] for row in temperature_boundaries],
            match_mode=-1,
        ),
        "Below minimum range",
    )

    print_result(
        f"Temperature {temperature}",
        result,
    )


# =============================================================================
# 45. APPROXIMATE MATCH WITH DECIMALS
# =============================================================================

section("45. Approximate matching with decimal boundaries")

commission_table = [
    [0.00, 0.01],
    [10000.00, 0.02],
    [50000.00, 0.03],
    [100000.00, 0.05],
]

sales_value = 72000.50

commission_rate = excel_xlookup(
    sales_value,
    [row[0] for row in commission_table],
    [row[1] for row in commission_table],
    match_mode=-1,
)

print_result(
    "Commission rate",
    commission_rate,
)

print_result(
    "Commission amount",
    sales_value * commission_rate,
)


# =============================================================================
# 46. MATCH TYPE COMPARISON
# =============================================================================

section("46. MATCH type comparison")

match_array = [10, 20, 30, 40, 50]

test_value = 35

for match_type in [0, 1, -1]:
    try:
        position = excel_match(
            test_value,
            match_array,
            match_type,
        )

        print_result(
            f"MATCH type {match_type}",
            f"position={position}, value={excel_index(match_array, position)}",
        )
    except ExcelLookupError as error:
        print_result(
            f"MATCH type {match_type}",
            f"error={error}",
        )


# =============================================================================
# 47. XLOOKUP MATCH MODE COMPARISON
# =============================================================================

section("47. XLOOKUP match-mode comparison")

lookup_boundaries = [10, 20, 30, 40, 50]

for mode in [0, -1, 1]:
    try:
        result = excel_xlookup(
            35,
            lookup_boundaries,
            lookup_boundaries,
            if_not_found="Not found",
            match_mode=mode,
        )

        print_result(
            f"XLOOKUP match_mode={mode}",
            result,
        )
    except ExcelLookupError as error:
        print_result(
            f"XLOOKUP match_mode={mode}",
            f"error={error}",
        )


# =============================================================================
# 48. LOOKUP ERRORS CAUSED BY ARRAY SIZE MISMATCH
# =============================================================================

section("48. Array-size mismatch")

try:
    excel_xlookup(
        "A",
        ["A", "B", "C"],
        [10, 20],
    )
except ExcelLookupError as error:
    print_result(
        "Mismatched lookup/return arrays",
        f"{type(error).__name__}: {error}",
    )


# =============================================================================
# 49. LOOKUP ERRORS CAUSED BY INVALID INDEX
# =============================================================================

section("49. Invalid INDEX references")

for row_number, column_number in [
    (0, 1),
    (99, 1),
    (1, 99),
]:
    try:
        value = excel_index(
            employees,
            row_number,
            column_number,
        )
        print_result(
            f"INDEX({row_number}, {column_number})",
            value,
        )
    except ExcelLookupError as error:
        print_result(
            f"INDEX({row_number}, {column_number})",
            f"{type(error).__name__}: {error}",
        )


# =============================================================================
# 50. COMMON MISTAKE: OMITTING EXACT MATCH
# =============================================================================

section("50. Common mistake: omitting exact-match intent")

# A frequent source of spreadsheet errors is using approximate matching when
# an identifier lookup requires exact matching.
#
# Employee IDs, invoice numbers, account numbers, SKU codes, and transaction
# IDs normally require exact matching.

identifier_table = [
    ["1001", "Customer A"],
    ["1002", "Customer B"],
    ["1003", "Customer C"],
]

identifier = "1002"

correct = excel_vlookup(
    identifier,
    identifier_table,
    2,
    False,
)

print_result(
    "Correct identifier lookup",
    correct,
)

print_result(
    "Rule",
    "Use exact matching for identifiers unless approximate behavior is explicitly intended.",
)


# =============================================================================
# 51. COMMON MISTAKE: WRONG APPROXIMATE SORT ORDER
# =============================================================================

section("51. Common mistake: wrong approximate sort order")

# An approximate lookup based on ascending boundaries should not be fed
# arbitrary unsorted data.

correct_boundaries = [0, 50, 100, 150, 200]
incorrect_boundaries = [100, 0, 200, 50, 150]

print_result(
    "Correctly sorted boundaries",
    correct_boundaries,
)

print_result(
    "Incorrectly sorted boundaries",
    incorrect_boundaries,
)


# =============================================================================
# 52. COMMON MISTAKE: USING THE WRONG VLOOKUP COLUMN NUMBER
# =============================================================================

section("52. Common mistake: incorrect VLOOKUP column number")

try:
    result = excel_vlookup(
        "E102",
        employees,
        5,
        False,
    )
    print_result("Result", result)
except ExcelLookupError as error:
    print_result(
        "Incorrect column index",
        f"{type(error).__name__}: {error}",
    )


# =============================================================================
# 53. COMMON MISTAKE: DUPLICATE KEYS
# =============================================================================

section("53. Common mistake: assuming keys are unique")

duplicate_lookup_ids = ["A", "B", "A"]
duplicate_lookup_values = ["First A", "B", "Second A"]

print_result(
    "First matching A",
    excel_xlookup(
        "A",
        duplicate_lookup_ids,
        duplicate_lookup_values,
    ),
)

print_result(
    "Last matching A",
    excel_xlookup(
        "A",
        duplicate_lookup_ids,
        duplicate_lookup_values,
        search_mode=-1,
    ),
)

print_result(
    "All matching A",
    filter_matches(
        "A",
        duplicate_lookup_ids,
        duplicate_lookup_values,
    ),
)


# =============================================================================
# 54. VLOOKUP WITH HORIZONTAL DATA
# =============================================================================

section("54. Choosing the appropriate lookup orientation")

# Vertical tables:
#
# VLOOKUP / XLOOKUP / INDEX + MATCH
#
# Horizontal tables:
#
# HLOOKUP / XLOOKUP / INDEX + MATCH
#
# In modern spreadsheet design, XLOOKUP often reduces the need to choose
# between VLOOKUP and HLOOKUP because lookup and return arrays can be supplied
# independently.

print_result(
    "Vertical lookup",
    excel_xlookup(
        "E101",
        employee_ids,
        employee_names,
    ),
)

print_result(
    "Horizontal lookup",
    excel_xlookup(
        "Q2",
        sales_by_quarter[0],
        sales_by_quarter[1],
    ),
)


# =============================================================================
# 55. INDEX + XMATCH
# =============================================================================

section("55. INDEX + XMATCH")

# INDEX + XMATCH is a modern flexible alternative to INDEX + MATCH.
#
# Conceptually:
#
# =INDEX(return_range, XMATCH(lookup_value, lookup_range, 0))
#
# XMATCH provides additional matching and search modes.

def index_xmatch(
    lookup_value: Any,
    lookup_array: list[Any],
    return_array: list[Any],
    match_mode: int = 0,
    search_mode: int = 1,
) -> Any:
    """Perform INDEX + XMATCH."""
    if len(lookup_array) != len(return_array):
        raise ExcelValueError("Array sizes must match")

    position = excel_xmatch(
        lookup_value,
        lookup_array,
        match_mode,
        search_mode,
    )

    return excel_index(
        return_array,
        position,
    )


print_result(
    "INDEX + XMATCH",
    index_xmatch(
        "E104",
        employee_ids,
        employee_departments,
    ),
)


# =============================================================================
# 56. TWO-WAY INDEX + XMATCH
# =============================================================================

section("56. Two-way INDEX + XMATCH")

def two_way_index_xmatch(
    row_value: Any,
    column_value: Any,
    row_headers: list[Any],
    column_headers: list[Any],
    data_matrix: list[list[Any]],
) -> Any:
    """Two-dimensional lookup using INDEX + XMATCH."""
    row_position = excel_xmatch(
        row_value,
        row_headers,
        0,
    )

    column_position = excel_xmatch(
        column_value,
        column_headers,
        0,
    )

    return excel_index(
        data_matrix,
        row_position,
        column_position,
    )


print_result(
    "Product A / Mar",
    two_way_index_xmatch(
        "Product A",
        "Mar",
        row_headers,
        column_headers,
        data_matrix,
    ),
)


# =============================================================================
# 57. SEARCH MODE AND DUPLICATES
# =============================================================================

section("57. Search mode and duplicates")

duplicate_products = ["P101", "P102", "P101", "P103", "P101"]
duplicate_prices = [100, 200, 125, 300, 150]

first_price = excel_xlookup(
    "P101",
    duplicate_products,
    duplicate_prices,
    search_mode=1,
)

last_price = excel_xlookup(
    "P101",
    duplicate_products,
    duplicate_prices,
    search_mode=-1,
)

print_result("First P101 price", first_price)
print_result("Last P101 price", last_price)


# =============================================================================
# 58. LOOKUP WITH BOOLEAN VALUES
# =============================================================================

section("58. Lookup with Boolean values")

boolean_keys = [True, False, True]
boolean_results = ["First true", "False result", "Second true"]

print_result(
    "First TRUE",
    excel_xlookup(
        True,
        boolean_keys,
        boolean_results,
    ),
)

print_result(
    "Last TRUE",
    excel_xlookup(
        True,
        boolean_keys,
        boolean_results,
        search_mode=-1,
    ),
)


# =============================================================================
# 59. LOOKUP WITH DATES
# =============================================================================

section("59. Lookup with dates")

from datetime import date

date_boundaries = [
    [date(2026, 1, 1), "Q1"],
    [date(2026, 4, 1), "Q2"],
    [date(2026, 7, 1), "Q3"],
    [date(2026, 10, 1), "Q4"],
]

transaction_date = date(2026, 8, 15)

quarter = excel_xlookup(
    transaction_date,
    [row[0] for row in date_boundaries],
    [row[1] for row in date_boundaries],
    match_mode=-1,
)

print_result(
    f"Quarter for {transaction_date}",
    quarter,
)


# =============================================================================
# 60. LOOKUP WITH TIME-LIKE NUMBERS
# =============================================================================

section("60. Time and numeric lookup boundaries")

# Spreadsheet times are commonly represented internally as fractions of a day.
#
# 12:00 PM = 0.5
#
# This example uses fractions to illustrate the underlying boundary concept.

time_boundaries = [
    [0.00, "Night"],
    [0.25, "Morning"],
    [0.50, "Afternoon"],
    [0.75, "Evening"],
]

current_time_fraction = 0.63

time_period = excel_xlookup(
    current_time_fraction,
    [row[0] for row in time_boundaries],
    [row[1] for row in time_boundaries],
    match_mode=-1,
)

print_result(
    "Time period",
    time_period,
)


# =============================================================================
# 61. LOOKUP TABLE FOR BUSINESS METRICS
# =============================================================================

section("61. Business metric lookup")

risk_bands = [
    [0.00, "Low"],
    [0.25, "Moderate"],
    [0.50, "High"],
    [0.75, "Very High"],
]

portfolio_risk = 0.61

risk_band = excel_xlookup(
    portfolio_risk,
    [row[0] for row in risk_bands],
    [row[1] for row in risk_bands],
    match_mode=-1,
)

print_result(
    "Portfolio risk band",
    risk_band,
)


# =============================================================================
# 62. LOOKUP WITH PRODUCT CATEGORIES
# =============================================================================

section("62. Product category lookup")

product_catalog = [
    ["P001", "Laptop", "Electronics", 65000],
    ["P002", "Chair", "Furniture", 8500],
    ["P003", "Phone", "Electronics", 42000],
    ["P004", "Desk", "Furniture", 15000],
]

catalog_ids = [row[0] for row in product_catalog]
catalog_names = [row[1] for row in product_catalog]
catalog_categories = [row[2] for row in product_catalog]
catalog_prices = [row[3] for row in product_catalog]

requested_id = "P003"

print_result(
    "Product name",
    excel_xlookup(requested_id, catalog_ids, catalog_names),
)

print_result(
    "Product category",
    excel_xlookup(requested_id, catalog_ids, catalog_categories),
)

print_result(
    "Product price",
    excel_xlookup(requested_id, catalog_ids, catalog_prices),
)


# =============================================================================
# 63. FORMULA SELECTION LOGIC
# =============================================================================

section("63. Selecting a lookup function")

def choose_lookup_pattern(
    needs_left_lookup: bool,
    needs_horizontal_lookup: bool,
    needs_approximate_match: bool,
    needs_last_match: bool,
    modern_excel_available: bool,
) -> str:
    """
    Provide a conceptual function-selection recommendation.

    This is a teaching aid, not an Excel formula generator.
    """
    if modern_excel_available:
        if needs_last_match:
            return "XLOOKUP with search_mode=-1"
        if needs_approximate_match:
            return "XLOOKUP with the appropriate match_mode"
        return "XLOOKUP"

    if needs_horizontal_lookup:
        return "HLOOKUP or INDEX + MATCH"

    if needs_left_lookup:
        return "INDEX + MATCH"

    if needs_approximate_match:
        return "VLOOKUP/HLOOKUP with correctly sorted data"

    return "VLOOKUP with exact matching"


print_result(
    "Modern Excel, left lookup",
    choose_lookup_pattern(
        needs_left_lookup=True,
        needs_horizontal_lookup=False,
        needs_approximate_match=False,
        needs_last_match=False,
        modern_excel_available=True,
    ),
)

print_result(
    "Legacy-compatible left lookup",
    choose_lookup_pattern(
        needs_left_lookup=True,
        needs_horizontal_lookup=False,
        needs_approximate_match=False,
        needs_last_match=False,
        modern_excel_available=False,
    ),
)


# =============================================================================
# 64. LOOKUP FUNCTION DECISION TABLE
# =============================================================================

section("64. Lookup decision table")

decision_table = [
    ("Simple vertical exact lookup", "XLOOKUP"),
    ("Simple vertical lookup in older Excel", "VLOOKUP"),
    ("Horizontal lookup in older Excel", "HLOOKUP"),
    ("Position of a value", "MATCH or XMATCH"),
    ("Return value by position", "INDEX"),
    ("Flexible two-way lookup", "INDEX + XMATCH"),
    ("Approximate boundary lookup", "XLOOKUP / MATCH / VLOOKUP"),
    ("Return the last matching record", "XLOOKUP search_mode=-1"),
    ("Multiple matching records", "FILTER-style approach"),
]

for requirement, preferred_pattern in decision_table:
    print(f"{requirement:<45} -> {preferred_pattern}")


# =============================================================================
# 65. FORMULA CONCEPTS AS STRINGS
# =============================================================================

section("65. Common Excel formula patterns")

formula_patterns = {
    "Exact VLOOKUP":
        '=VLOOKUP(A2,$A$2:$D$100,4,FALSE)',
    "Approximate VLOOKUP":
        '=VLOOKUP(A2,$A$2:$B$10,2,TRUE)',
    "Exact HLOOKUP":
        '=HLOOKUP(B1,$B$1:$F$4,4,FALSE)',
    "INDEX + MATCH":
        '=INDEX($C$2:$C$100,MATCH(A2,$A$2:$A$100,0))',
    "XLOOKUP":
        '=XLOOKUP(A2,$A$2:$A$100,$C$2:$C$100,"Not found")',
    "XLOOKUP approximate smaller":
        '=XLOOKUP(A2,$A$2:$A$100,$C$2:$C$100,"Not found",-1)',
    "XMATCH":
        '=XMATCH(A2,$A$2:$A$100,0)',
    "INDEX + XMATCH":
        '=INDEX($C$2:$C$100,XMATCH(A2,$A$2:$A$100,0))',
    "Two-way INDEX + XMATCH":
        '=INDEX($B$2:$F$100,XMATCH(A2,$A$2:$A$100,0),XMATCH(B1,$B$1:$F$1,0))',
}

for description, formula in formula_patterns.items():
    print(f"{description}: {formula}")


# =============================================================================
# 66. ABSOLUTE REFERENCES
# =============================================================================

section("66. Absolute and relative references")

# Excel formulas often use:
#
# A2       relative reference
# $A$2     absolute reference
# A$2      fixed row
# $A2      fixed column
#
# Lookup tables copied down a worksheet commonly need absolute references so
# that the source table does not shift unexpectedly.

reference_examples = [
    "A2",
    "$A$2",
    "A$2",
    "$A2",
]

for reference in reference_examples:
    print_result(
        f"Reference {reference}",
        "Use depends on whether row and/or column movement is intended.",
    )


# =============================================================================
# 67. TABLE-BASED LOOKUPS
# =============================================================================

section("67. Structured table concepts")

# Excel Tables provide structured references.
#
# Instead of:
#
# $A$2:$D$1000
#
# a table might expose names such as:
#
# Employees[Employee ID]
# Employees[Department]
#
# The major advantage is that the table can expand as records are added.

structured_formula = (
    '=XLOOKUP([@[Employee ID]],'
    'Employees[Employee ID],'
    'Employees[Department],'
    '"Not found")'
)

print_result(
    "Structured XLOOKUP concept",
    structured_formula,
)


# =============================================================================
# 68. PERFORMANCE: REPEATED LOOKUPS
# =============================================================================

section("68. Performance: repeated lookups")

# A workbook containing thousands of repeated lookup formulas can become
# computationally expensive.
#
# Practical optimization principles:
#
# - Keep lookup ranges reasonably sized.
# - Avoid unnecessarily repeated expensive calculations.
# - Use Excel Tables and clear ranges.
# - Use binary-search modes only when the required ordering guarantees are
#   satisfied.
# - Consider Power Query or data-model approaches for large transformation
#   workloads.
# - Avoid volatile functions around lookup logic unless necessary.
#
# The following simulation illustrates caching.

lookup_cache: dict[str, Any] = {}


def cached_employee_lookup(employee_id: str) -> Any:
    """Cache repeated employee lookups."""
    if employee_id not in lookup_cache:
        lookup_cache[employee_id] = excel_xlookup(
            employee_id,
            employee_ids,
            employee_names,
        )

    return lookup_cache[employee_id]


for identifier in ["E101", "E102", "E101", "E103", "E101"]:
    print_result(
        f"Cached lookup {identifier}",
        cached_employee_lookup(identifier),
    )

print_result(
    "Number of cached values",
    len(lookup_cache),
)


# =============================================================================
# 69. PERFORMANCE: EXACT LOOKUP VERSUS INDEXED DICTIONARY
# =============================================================================

section("69. Performance concept: indexed lookup")

# Excel is not Python, but the underlying computational idea is useful:
#
# Repeated linear scans can be expensive.
# An index can make repeated retrieval much faster.
#
# In spreadsheet systems, Excel Tables, optimized formulas, Power Query,
# database indexes, and data models address related problems.

employee_index = {
    row[0]: row[1]
    for row in employees
}

print_result(
    "Indexed employee lookup",
    employee_index.get("E103"),
)


# =============================================================================
# 70. SECURITY AND DATA-INTEGRITY CONSIDERATIONS
# =============================================================================

section("70. Security and data integrity considerations")

# Lookup functions do not inherently provide data security.
#
# A lookup can expose whatever data the formula can access.
#
# Important controls include:
#
# - Restricting access to sensitive worksheets/workbooks.
# - Protecting formulas when appropriate.
# - Avoiding accidental exposure of confidential columns.
# - Validating imported data.
# - Preventing duplicate or malformed identifiers.
# - Auditing lookup sources.
# - Avoiding reliance on hidden columns as a security mechanism.
#
# Worksheet hiding is not equivalent to strong access control.
#
# Data integrity is particularly important when lookups determine:
#
# - salaries
# - prices
# - account balances
# - customer classifications
# - tax rates
# - risk categories
# - financial calculations
#
# A wrong lookup can produce a plausible-looking but materially incorrect
# result.

sensitive_fields = [
    "salary",
    "bank_account",
    "tax_identifier",
    "customer_credit_limit",
]

print_result(
    "Sensitive fields require controlled access",
    sensitive_fields,
)


# =============================================================================
# 71. AUDITABILITY
# =============================================================================

section("71. Auditability")

# A good lookup formula should be understandable by another analyst.
#
# Prefer:
#
# - clearly named tables
# - explicit return ranges
# - exact-match intent
# - meaningful error messages
# - consistent data types
# - documented assumptions
#
# Avoid:
#
# - unexplained hard-coded column numbers
# - hidden helper logic
# - ambiguous approximate matches
# - excessively nested formulas
# - inconsistent source ranges

audit_checklist = [
    "Is the lookup key clearly defined?",
    "Is exact or approximate matching intentional?",
    "Are duplicate keys expected?",
    "Is the source data correctly sorted when required?",
    "Are lookup and return ranges aligned?",
    "Is the not-found behavior explicit?",
    "Are source values stored consistently?",
]

for item in audit_checklist:
    print(f"[ ] {item}")


# =============================================================================
# 72. UNIT TESTS FOR LOOKUP LOGIC
# =============================================================================

section("72. Unit testing lookup logic")

def assert_equal(
    actual: Any,
    expected: Any,
    test_name: str,
) -> None:
    """Simple assertion helper for educational tests."""
    if actual != expected:
        raise AssertionError(
            f"{test_name}: expected {expected!r}, got {actual!r}"
        )

    print(f"PASS: {test_name}")


assert_equal(
    excel_xlookup(
        "E101",
        employee_ids,
        employee_names,
    ),
    "Anika",
    "XLOOKUP exact match",
)

assert_equal(
    index_match(
        "E102",
        employee_ids,
        employee_departments,
    ),
    "Sales",
    "INDEX + MATCH",
)

assert_equal(
    excel_vlookup(
        "E103",
        employees,
        4,
        False,
    ),
    85000,
    "VLOOKUP exact salary",
)

assert_equal(
    excel_hlookup(
        "Q2",
        sales_by_quarter,
        2,
        False,
    ),
    135000,
    "HLOOKUP exact revenue",
)

assert_equal(
    excel_match(
        82,
        boundary_values,
        1,
    ),
    5,
    "MATCH approximate boundary",
)


# =============================================================================
# 73. EDGE-CASE TESTS
# =============================================================================

section("73. Edge-case tests")

edge_cases = [
    ("Missing exact value", lambda: excel_xlookup(
        "missing",
        ["A", "B"],
        [1, 2],
    )),
    ("Empty lookup array", lambda: excel_xlookup(
        "A",
        [],
        [],
    )),
    ("Array length mismatch", lambda: excel_xlookup(
        "A",
        ["A"],
        [],
    )),
    ("Invalid MATCH type", lambda: excel_match(
        "A",
        ["A"],
        99,
    )),
    ("Invalid INDEX row", lambda: excel_index(
        ["A", "B"],
        0,
    )),
]

for description, operation in edge_cases:
    try:
        result = operation()
        print_result(description, f"unexpected success: {result}")
    except ExcelLookupError as error:
        print_result(
            description,
            f"correctly raised {type(error).__name__}",
        )


# =============================================================================
# 74. PROPERTY-STYLE RANDOMIZED CHECK
# =============================================================================

section("74. Randomized lookup validation")

# A simple randomized check verifies that exact XLOOKUP and INDEX + MATCH
# return the same first matching result for unique keys.

random.seed(42)

random_keys = [
    f"K{index:04d}"
    for index in random.sample(range(10000), 100)
]

random_values = [
    random.randint(1, 100000)
    for _ in random_keys
]

for key, expected_value in zip(random_keys, random_values):
    xlookup_value = excel_xlookup(
        key,
        random_keys,
        random_values,
    )

    index_match_value = index_match(
        key,
        random_keys,
        random_values,
    )

    assert_equal(
        xlookup_value,
        expected_value,
        f"XLOOKUP randomized key {key}",
    )

    assert_equal(
        index_match_value,
        expected_value,
        f"INDEX + MATCH randomized key {key}",
    )


# =============================================================================
# 75. PRACTICAL EMPLOYEE LOOKUP DEMONSTRATION
# =============================================================================

section("75. Practical employee lookup")

employee_directory = [
    ["E201", "Aarav", "Finance", "Mumbai", 72000],
    ["E202", "Meera", "IT", "Delhi", 91000],
    ["E203", "Kabir", "Sales", "Pune", 68000],
    ["E204", "Isha", "HR", "Bengaluru", 76000],
]

directory_ids = [row[0] for row in employee_directory]

for employee_id in ["E201", "E202", "E999"]:
    employee_name = excel_xlookup(
        employee_id,
        directory_ids,
        [row[1] for row in employee_directory],
        if_not_found="Employee ID not found",
    )

    department = excel_xlookup(
        employee_id,
        directory_ids,
        [row[2] for row in employee_directory],
        if_not_found="Department unavailable",
    )

    city = excel_xlookup(
        employee_id,
        directory_ids,
        [row[3] for row in employee_directory],
        if_not_found="City unavailable",
    )

    print_result(
        employee_id,
        {
            "name": employee_name,
            "department": department,
            "city": city,
        },
    )


# =============================================================================
# 76. PRACTICAL FINANCIAL THRESHOLD LOOKUP
# =============================================================================

section("76. Practical financial threshold lookup")

credit_score_bands = [
    [300, "Poor"],
    [580, "Fair"],
    [670, "Good"],
    [740, "Very Good"],
    [800, "Excellent"],
]

for credit_score in [550, 600, 700, 760, 820]:
    band = excel_xlookup(
        credit_score,
        [row[0] for row in credit_score_bands],
        [row[1] for row in credit_score_bands],
        if_not_found="Below supported range",
        match_mode=-1,
    )

    print_result(
        f"Credit score {credit_score}",
        band,
    )


# =============================================================================
# 77. PRACTICAL COMMISSION LOOKUP
# =============================================================================

section("77. Practical commission lookup")

commission_bands = [
    [0, 0.00],
    [100000, 0.01],
    [250000, 0.02],
    [500000, 0.03],
    [1000000, 0.05],
]

sales_values = [50000, 175000, 300000, 700000, 1500000]

for sales in sales_values:
    rate = excel_xlookup(
        sales,
        [row[0] for row in commission_bands],
        [row[1] for row in commission_bands],
        match_mode=-1,
    )

    commission = sales * rate

    print_result(
        f"Sales {sales}",
        {
            "rate": rate,
            "commission": commission,
        },
    )


# =============================================================================
# 78. PRACTICAL DATE BAND LOOKUP
# =============================================================================

section("78. Practical date-band lookup")

financial_year_boundaries = [
    [date(2024, 4, 1), "FY2024-25"],
    [date(2025, 4, 1), "FY2025-26"],
    [date(2026, 4, 1), "FY2026-27"],
    [date(2027, 4, 1), "FY2027-28"],
]

sample_dates = [
    date(2025, 3, 31),
    date(2025, 4, 1),
    date(2026, 2, 15),
    date(2026, 9, 10),
]

for sample_date in sample_dates:
    financial_year = excel_xlookup(
        sample_date,
        [row[0] for row in financial_year_boundaries],
        [row[1] for row in financial_year_boundaries],
        match_mode=-1,
    )

    print_result(
        str(sample_date),
        financial_year,
    )


# =============================================================================
# 79. COMPARING FORMULA MAINTAINABILITY
# =============================================================================

section("79. Formula maintainability")

maintenance_examples = {
    "VLOOKUP":
        "Depends on a column number and first-column lookup arrangement.",
    "HLOOKUP":
        "Depends on a row number and first-row lookup arrangement.",
    "INDEX + MATCH":
        "Separates lookup position from return range.",
    "INDEX + XMATCH":
        "Adds flexible match and search modes.",
    "XLOOKUP":
        "Separates lookup and return arrays and supports explicit not-found behavior.",
}

for function_name, explanation in maintenance_examples.items():
    print(f"{function_name}: {explanation}")


# =============================================================================
# 80. FORMULA DESIGN PRINCIPLES
# =============================================================================

section("80. Formula design principles")

design_principles = [
    "Use exact matching for identifiers unless approximate behavior is required.",
    "Use approximate matching for explicit boundary tables.",
    "Keep approximate lookup boundaries correctly ordered.",
    "Keep lookup and return arrays aligned.",
    "Validate duplicate keys when uniqueness is expected.",
    "Use XLOOKUP when modern Excel is available and its features fit the task.",
    "Use INDEX + MATCH or INDEX + XMATCH when position-based flexibility is useful.",
    "Use IFNA when only a missing lookup should be converted to a fallback.",
    "Use IFERROR only when broad error suppression is intentional.",
    "Avoid hard-coded lookup ranges when structured tables can provide safer references.",
    "Document the meaning of lookup boundaries.",
    "Treat lookup results as business-critical data when they feed financial or operational decisions.",
]

for number, principle in enumerate(design_principles, start=1):
    print(f"{number}. {principle}")


# =============================================================================
# 81. COMPREHENSIVE DEMONSTRATION
# =============================================================================

section("81. Comprehensive lookup demonstration")

orders = [
    ["O1001", "P101", 2],
    ["O1002", "P102", 5],
    ["O1003", "P103", 1],
    ["O1004", "P101", 4],
]

order_product_ids = [row[1] for row in orders]
order_quantities = [row[2] for row in orders]

for order_id, product_id, quantity in orders:
    price = excel_xlookup(
        product_id,
        product_ids,
        product_prices,
        if_not_found=None,
    )

    product_name = excel_xlookup(
        product_id,
        product_ids,
        product_ids,
    )

    order_total = price * quantity

    print_result(
        order_id,
        {
            "product": product_name,
            "quantity": quantity,
            "unit_price": price,
            "total": order_total,
        },
    )


# =============================================================================
# 82. LIMITATIONS OF LOOKUP FUNCTIONS
# =============================================================================

section("82. Limitations")

limitations = [
    "A lookup formula does not automatically fix bad source data.",
    "Duplicate keys can make a single-result lookup ambiguous.",
    "Approximate matching can produce incorrect results when boundaries are improperly ordered.",
    "Large numbers of complex formulas can affect workbook calculation performance.",
    "Hard-coded references can become fragile when workbook structures change.",
    "Lookup functions are not substitutes for relational database design.",
    "A lookup formula does not provide access control or data security.",
    "Suppressing all errors can hide genuine data-quality or formula defects.",
    "Wildcard searches can return unexpected records when patterns are too broad.",
]

for limitation in limitations:
    print(f"- {limitation}")


# =============================================================================
# 83. FINAL PRACTICAL RULES
# =============================================================================

section("83. Practical rules")

rules = [
    ("VLOOKUP", "Use when the lookup key is in the first column and a straightforward vertical lookup is sufficient."),
    ("HLOOKUP", "Use for horizontal layouts, especially legacy workbooks."),
    ("XLOOKUP", "Use for flexible modern lookups with explicit lookup and return arrays."),
    ("INDEX", "Use to return a value at a known position."),
    ("MATCH", "Use to find a position using classic matching behavior."),
    ("XMATCH", "Use when modern matching and search modes are useful."),
    ("Exact matching", "Use for identifiers, codes, IDs, names when an exact record is intended."),
    ("Approximate matching", "Use for thresholds, grades, rates, bands, ranges, and boundary tables."),
    ("IFNA", "Use when a missing lookup is the specific error you want to handle."),
    ("IFERROR", "Use when several formula errors should intentionally share one fallback."),
]

for concept, rule in rules:
    print(f"{concept:<24}: {rule}")


# =============================================================================
# 84. END-TO-END EXAMPLE
# =============================================================================

section("84. End-to-end example")

# Business requirement:
#
# Given a customer's purchase amount:
# 1. Determine the applicable discount band.
# 2. Return the discount percentage.
# 3. Calculate the discount amount.
# 4. Calculate the final payable amount.
#
# This combines exact data lookup and approximate boundary lookup.

discount_bands = [
    [0, 0.00],
    [10000, 0.02],
    [25000, 0.05],
    [50000, 0.08],
    [100000, 0.12],
]

purchase_amounts = [7500, 15000, 32000, 80000, 125000]

for purchase_amount in purchase_amounts:
    discount_rate = excel_xlookup(
        purchase_amount,
        [row[0] for row in discount_bands],
        [row[1] for row in discount_bands],
        match_mode=-1,
    )

    discount_amount = purchase_amount * discount_rate
    final_amount = purchase_amount - discount_amount

    print_result(
        f"Purchase {purchase_amount}",
        {
            "discount_rate": discount_rate,
            "discount_amount": round(discount_amount, 2),
            "final_amount": round(final_amount, 2),
        },
    )


# =============================================================================
# 85. SCRIPT COMPLETION
# =============================================================================

section("85. Completed study demonstrations")

print(
    "The script has demonstrated VLOOKUP, HLOOKUP, XLOOKUP, INDEX, MATCH, "
    "XMATCH, exact and approximate matching, lookup errors, wildcard and "
    "duplicate handling, two-way lookups, multiple criteria, data validation, "
    "performance concepts, and practical lookup design."
)
