"""
Excel Conditional Analysis
==========================

Topic:
COUNTIF, COUNTIFS, SUMIF, SUMIFS, AVERAGEIF, AVERAGEIFS,
logical conditions, nested formulas, edge cases, and practical analysis.

This is a standalone Python study script that models the logic behind
important Excel conditional-analysis functions.

The goal is not to reproduce Excel internally, but to make the underlying
logic explicit and executable in Python.

The examples progress from basic single-condition analysis to multiple
conditions, logical combinations, nested calculations, validation,
performance considerations, and production-style reporting.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isclose
from statistics import mean
from typing import Any, Callable, Iterable, Sequence


# ============================================================================
# 1. FOUNDATIONAL IDEA: CONDITIONAL ANALYSIS
# ============================================================================

print("=" * 80)
print("EXCEL CONDITIONAL ANALYSIS WITH PYTHON")
print("=" * 80)

print(
    """
Conditional analysis means:
1. Examine data.
2. Test whether each row satisfies a condition.
3. Include only matching rows.
4. Perform an aggregation such as count, sum, or average.

Excel functions such as COUNTIF, SUMIF, and AVERAGEIF automate this pattern.

For example:

    COUNTIF(B2:B20, "East")

means:

    Count how many cells in B2:B20 contain "East".

The Python equivalent can be expressed as:

    sum(1 for value in regions if value == "East")

The Python implementation below makes the same reasoning explicit.
"""
)


# ============================================================================
# 2. SAMPLE DATASET
# ============================================================================

employees = [
    {
        "employee": "Aarav",
        "department": "Sales",
        "region": "North",
        "performance": 88,
        "sales": 125000,
        "experience": 5,
        "status": "Active",
    },
    {
        "employee": "Diya",
        "department": "Sales",
        "region": "South",
        "performance": 76,
        "sales": 98000,
        "experience": 3,
        "status": "Active",
    },
    {
        "employee": "Kabir",
        "department": "Finance",
        "region": "North",
        "performance": 92,
        "sales": 150000,
        "experience": 7,
        "status": "Active",
    },
    {
        "employee": "Anaya",
        "department": "HR",
        "region": "West",
        "performance": 81,
        "sales": 72000,
        "experience": 4,
        "status": "Active",
    },
    {
        "employee": "Vihaan",
        "department": "Sales",
        "region": "North",
        "performance": 95,
        "sales": 175000,
        "experience": 8,
        "status": "Active",
    },
    {
        "employee": "Ishita",
        "department": "Finance",
        "region": "East",
        "performance": 69,
        "sales": 65000,
        "experience": 2,
        "status": "Inactive",
    },
    {
        "employee": "Reyansh",
        "department": "IT",
        "region": "South",
        "performance": 87,
        "sales": 110000,
        "experience": 6,
        "status": "Active",
    },
    {
        "employee": "Myra",
        "department": "Sales",
        "region": "West",
        "performance": 73,
        "sales": 89000,
        "experience": 3,
        "status": "Active",
    },
    {
        "employee": "Arjun",
        "department": "IT",
        "region": "North",
        "performance": 91,
        "sales": 135000,
        "experience": 9,
        "status": "Active",
    },
    {
        "employee": "Sara",
        "department": "HR",
        "region": "East",
        "performance": 84,
        "sales": 79000,
        "experience": 5,
        "status": "Active",
    },
]


def print_rows(rows: Iterable[dict[str, Any]]) -> None:
    """Print records in a simple readable format."""
    for row in rows:
        print(
            f"{row['employee']:8} | "
            f"{row['department']:8} | "
            f"{row['region']:5} | "
            f"Performance={row['performance']:3} | "
            f"Sales={row['sales']:7,.0f} | "
            f"Experience={row['experience']:2} | "
            f"Status={row['status']}"
        )


print("\nSAMPLE DATA")
print("-" * 80)
print_rows(employees)


# ============================================================================
# 3. EXCEL RANGE CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("EXCEL RANGE CONCEPT")
print("=" * 80)

print(
    """
An Excel range is a group of cells.

For example:

    B2:B20

could contain department names.

A conditional function usually works with:
- a criteria range
- a criterion
- and sometimes a sum/average range
- additional criteria ranges for multi-condition functions

Conceptually:

    condition -> select rows -> aggregate selected values
"""
)

departments = [row["department"] for row in employees]
sales_values = [row["sales"] for row in employees]
performance_values = [row["performance"] for row in employees]

print("Departments:", departments)
print("Sales:", sales_values)


# ============================================================================
# 4. BASIC LOGICAL OPERATORS
# ============================================================================

print("\n" + "=" * 80)
print("LOGICAL OPERATORS")
print("=" * 80)

print(
    """
Common logical comparisons:

    =       equal
    <>      not equal
    >       greater than
    <       less than
    >=      greater than or equal to
    <=      less than or equal to

Python uses:

    ==      equal
    !=      not equal
    >       greater than
    <       less than
    >=      greater than or equal to
    <=      less than or equal to

Excel:

    A2="Sales"

Python:

    department == "Sales"
"""
)

example_performance = 88

print("88 = 88:", example_performance == 88)
print("88 > 80:", example_performance > 80)
print("88 >= 90:", example_performance >= 90)
print("88 <> 90 in Excel equivalent:", example_performance != 90)


# ============================================================================
# 5. COUNTIF
# ============================================================================

print("\n" + "=" * 80)
print("COUNTIF")
print("=" * 80)

print(
    """
Excel syntax:

    COUNTIF(range, criteria)

Purpose:
Count cells satisfying one condition.

Example:

    =COUNTIF(B2:B20,"Sales")

This counts the number of Sales records.
"""
)


def countif(values: Iterable[Any], criterion: Any) -> int:
    """
    Python model of basic Excel COUNTIF behavior.

    This implementation supports:
    - exact text matching
    - exact numeric matching
    - comparison criteria such as >80
    - >=, <=, <>, <, >
    """
    return sum(1 for value in values if matches_criterion(value, criterion))


def matches_criterion(value: Any, criterion: Any) -> bool:
    """Evaluate one Excel-like criterion against one value."""
    if criterion is None:
        return value is None

    if not isinstance(criterion, str):
        return value == criterion

    operators = [">=", "<=", "<>", ">", "<", "="]

    for operator in operators:
        if criterion.startswith(operator):
            operand_text = criterion[len(operator):].strip()
            operand = convert_criterion_operand(operand_text)

            try:
                if operator == "=":
                    return value == operand
                if operator == "<>":
                    return value != operand
                if operator == ">":
                    return value > operand
                if operator == "<":
                    return value < operand
                if operator == ">=":
                    return value >= operand
                if operator == "<=":
                    return value <= operand
            except TypeError:
                return False

    return value == criterion


def convert_criterion_operand(text: str) -> Any:
    """Convert a textual criterion operand into a useful Python value."""
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


sales_count = countif(departments, "Sales")
high_performance_count = countif(performance_values, ">=90")

print("Sales employees:", sales_count)
print("Employees with performance >= 90:", high_performance_count)


# ============================================================================
# 6. COUNTIF WITH OTHER CONDITIONS
# ============================================================================

print("\nCOUNTIF EXAMPLES")
print("-" * 80)

print("Finance employees:", countif(departments, "Finance"))
print("IT employees:", countif(departments, "IT"))
print("Performance > 80:", countif(performance_values, ">80"))
print("Performance <= 75:", countif(performance_values, "<=75"))
print("Performance not equal to 88:", countif(performance_values, "<>88"))


# ============================================================================
# 7. COUNTIF WITH WILDCARD CONCEPTS
# ============================================================================

print("\n" + "=" * 80)
print("COUNTIF WILDCARDS")
print("=" * 80)

print(
    """
Excel COUNTIF also supports wildcard criteria:

    *       matches any number of characters
    ?       matches exactly one character
    ~       escapes a wildcard

Examples:

    =COUNTIF(A2:A20,"A*")
    =COUNTIF(A2:A20,"?iya")

The function below adds simple wildcard support.
"""
)

import re


def wildcard_to_regex(pattern: str) -> str:
    """Convert Excel-style * and ? wildcards into a regular expression."""
    regex = ""
    for character in pattern:
        if character == "*":
            regex += ".*"
        elif character == "?":
            regex += "."
        elif character == "~":
            # A literal ~ is unusual here; preserve it when no wildcard follows.
            regex += "~"
        else:
            regex += re.escape(character)
    return "^" + regex + "$"


def matches_text_or_wildcard(value: Any, criterion: Any) -> bool:
    """Match text criteria with optional Excel-style wildcards."""
    if not isinstance(value, str) or not isinstance(criterion, str):
        return matches_criterion(value, criterion)

    if "*" in criterion or "?" in criterion:
        return re.match(wildcard_to_regex(criterion), value, re.IGNORECASE) is not None

    return value.lower() == criterion.lower()


def countif_with_wildcards(values: Iterable[Any], criterion: Any) -> int:
    return sum(
        1 for value in values if matches_text_or_wildcard(value, criterion)
    )


employee_names = [row["employee"] for row in employees]

print("Names starting with A:", countif_with_wildcards(employee_names, "A*"))
print("Names ending with a:", countif_with_wildcards(employee_names, "*a"))
print("Names with four characters:", countif_with_wildcards(employee_names, "????"))


# ============================================================================
# 8. COUNTIFS
# ============================================================================

print("\n" + "=" * 80)
print("COUNTIFS")
print("=" * 80)

print(
    """
Excel syntax:

    COUNTIFS(criteria_range1, criteria1,
             criteria_range2, criteria2,
             ...)

COUNTIFS applies AND logic.

Example:

    =COUNTIFS(B2:B20,"Sales",C2:C20,"North")

Meaning:

    Department = Sales
    AND
    Region = North

Only rows satisfying every criterion are counted.
"""
)


def countifs(
    ranges_and_criteria: Sequence[tuple[Sequence[Any], Any]]
) -> int:
    """Count rows satisfying every supplied condition."""
    if not ranges_and_criteria:
        return 0

    length = len(ranges_and_criteria[0][0])

    if any(len(values) != length for values, _ in ranges_and_criteria):
        raise ValueError("All COUNTIFS ranges must have the same length.")

    count = 0

    for index in range(length):
        if all(
            matches_criterion(values[index], criterion)
            for values, criterion in ranges_and_criteria
        ):
            count += 1

    return count


sales_north = countifs(
    [
        (departments, "Sales"),
        ([row["region"] for row in employees], "North"),
    ]
)

sales_north_high_performance = countifs(
    [
        (departments, "Sales"),
        ([row["region"] for row in employees], "North"),
        (performance_values, ">=90"),
    ]
)

print("Sales employees in North:", sales_north)
print("Sales + North + performance >= 90:", sales_north_high_performance)


# ============================================================================
# 9. AND LOGIC
# ============================================================================

print("\n" + "=" * 80)
print("AND LOGIC")
print("=" * 80)

print(
    """
AND means every condition must be true.

Excel:

    =AND(B2="Sales",C2="North",D2>=90)

Python:

    department == "Sales" and region == "North" and performance >= 90
"""
)


def is_high_value_sales_employee(row: dict[str, Any]) -> bool:
    """A row-level AND condition."""
    return (
        row["department"] == "Sales"
        and row["region"] == "North"
        and row["performance"] >= 90
    )


matching_rows = [
    row for row in employees if is_high_value_sales_employee(row)
]

print("Rows satisfying all three conditions:")
print_rows(matching_rows)


# ============================================================================
# 10. OR LOGIC
# ============================================================================

print("\n" + "=" * 80)
print("OR LOGIC")
print("=" * 80)

print(
    """
OR means at least one condition must be true.

Excel:

    =OR(B2="Sales",B2="Finance")

Python:

    department == "Sales" or department == "Finance"

COUNTIFS naturally represents AND conditions, not arbitrary OR conditions.

For OR conditions, common Excel techniques include:
- adding separate COUNTIF results
- using SUM with multiple COUNTIF results
- using FILTER with OR logic
- using SUMPRODUCT for more complex logic
"""
)


sales_or_finance = sum(
    1
    for row in employees
    if row["department"] == "Sales" or row["department"] == "Finance"
)

print("Sales OR Finance employees:", sales_or_finance)


# ============================================================================
# 11. AVOIDING DOUBLE COUNTING WITH OR CONDITIONS
# ============================================================================

print("\n" + "=" * 80)
print("OR CONDITIONS AND DOUBLE COUNTING")
print("=" * 80)

print(
    """
When categories are mutually exclusive, adding separate counts is safe.

For example:

    Sales + Finance

works because one row cannot simultaneously have both departments.

With overlapping conditions, simple addition can double-count.

For sets A and B:

    |A OR B| = |A| + |B| - |A AND B|

This is the inclusion-exclusion principle.
"""
)

north_count = countif([row["region"] for row in employees], "North")
high_performance_count = countif(performance_values, ">=90")
north_and_high = countifs(
    [
        ([row["region"] for row in employees], "North"),
        (performance_values, ">=90"),
    ]
)

north_or_high = north_count + high_performance_count - north_and_high

print("North:", north_count)
print("Performance >= 90:", high_performance_count)
print("North AND performance >= 90:", north_and_high)
print("North OR performance >= 90:", north_or_high)


# ============================================================================
# 12. SUMIF
# ============================================================================

print("\n" + "=" * 80)
print("SUMIF")
print("=" * 80)

print(
    """
Excel syntax:

    SUMIF(range, criteria, [sum_range])

Purpose:
Add values corresponding to rows that satisfy one condition.

Example:

    =SUMIF(B2:B20,"Sales",E2:E20)

This means:

    Find rows where department = Sales.
    Add the corresponding sales values.
"""
)


def sumif(
    criteria_range: Sequence[Any],
    criterion: Any,
    sum_range: Sequence[float],
) -> float:
    """Python model of Excel SUMIF."""
    if len(criteria_range) != len(sum_range):
        raise ValueError("criteria_range and sum_range must have equal length.")

    total = 0.0

    for criterion_value, sum_value in zip(criteria_range, sum_range):
        if matches_criterion(criterion_value, criterion):
            if isinstance(sum_value, (int, float)) and not isinstance(sum_value, bool):
                total += sum_value

    return total


sales_total = sumif(departments, "Sales", sales_values)
finance_total = sumif(departments, "Finance", sales_values)

print("Sales total:", f"{sales_total:,.2f}")
print("Finance total:", f"{finance_total:,.2f}")


# ============================================================================
# 13. SUMIF WITH NUMERIC CRITERIA
# ============================================================================

print("\nSUMIF WITH NUMERIC CONDITIONS")
print("-" * 80)

sales_above_100k = sumif(
    sales_values,
    ">100000",
    sales_values,
)

performance_sum_for_high_scores = sumif(
    performance_values,
    ">=90",
    sales_values,
)

print("Sales values greater than 100,000:", f"{sales_above_100k:,.2f}")
print(
    "Sales generated by employees with performance >= 90:",
    f"{performance_sum_for_high_scores:,.2f}",
)


# ============================================================================
# 14. SUMIFS
# ============================================================================

print("\n" + "=" * 80)
print("SUMIFS")
print("=" * 80)

print(
    """
Excel syntax:

    SUMIFS(sum_range,
           criteria_range1, criteria1,
           criteria_range2, criteria2,
           ...)

Important difference:

    SUMIF  -> one condition
    SUMIFS -> multiple conditions

Example:

    =SUMIFS(E2:E20,
            B2:B20,"Sales",
            C2:C20,"North",
            D2:D20,">=90")
"""
)


def sumifs(
    sum_range: Sequence[float],
    ranges_and_criteria: Sequence[tuple[Sequence[Any], Any]],
) -> float:
    """Python model of Excel SUMIFS."""
    if any(len(values) != len(sum_range) for values, _ in ranges_and_criteria):
        raise ValueError("All SUMIFS ranges must have the same length.")

    total = 0.0

    for index, value_to_sum in enumerate(sum_range):
        row_matches = all(
            matches_criterion(values[index], criterion)
            for values, criterion in ranges_and_criteria
        )

        if row_matches and isinstance(value_to_sum, (int, float)):
            total += value_to_sum

    return total


sales_north_total = sumifs(
    sales_values,
    [
        (departments, "Sales"),
        ([row["region"] for row in employees], "North"),
    ],
)

sales_north_high_total = sumifs(
    sales_values,
    [
        (departments, "Sales"),
        ([row["region"] for row in employees], "North"),
        (performance_values, ">=90"),
    ],
)

print("Sales in North:", f"{sales_north_total:,.2f}")
print(
    "Sales in North with performance >= 90:",
    f"{sales_north_high_total:,.2f}",
)


# ============================================================================
# 15. AVERAGEIF
# ============================================================================

print("\n" + "=" * 80)
print("AVERAGEIF")
print("=" * 80)

print(
    """
Excel syntax:

    AVERAGEIF(range, criteria, [average_range])

Purpose:
Average values associated with one condition.

Example:

    =AVERAGEIF(B2:B20,"Sales",D2:D20)

This calculates average performance for Sales employees.
"""
)


def averageif(
    criteria_range: Sequence[Any],
    criterion: Any,
    average_range: Sequence[float],
) -> float:
    """Python model of Excel AVERAGEIF."""
    if len(criteria_range) != len(average_range):
        raise ValueError("Ranges must have equal length.")

    matching_values = [
        value
        for criterion_value, value in zip(criteria_range, average_range)
        if matches_criterion(criterion_value, criterion)
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]

    if not matching_values:
        raise ZeroDivisionError("AVERAGEIF has no numeric matching values.")

    return sum(matching_values) / len(matching_values)


sales_average_performance = averageif(
    departments,
    "Sales",
    performance_values,
)

print("Average Sales performance:", f"{sales_average_performance:.2f}")


# ============================================================================
# 16. AVERAGEIFS
# ============================================================================

print("\n" + "=" * 80)
print("AVERAGEIFS")
print("=" * 80)

print(
    """
Excel syntax:

    AVERAGEIFS(average_range,
               criteria_range1, criteria1,
               criteria_range2, criteria2,
               ...)

It calculates an average after applying multiple AND conditions.
"""
)


def averageifs(
    average_range: Sequence[float],
    ranges_and_criteria: Sequence[tuple[Sequence[Any], Any]],
) -> float:
    """Python model of Excel AVERAGEIFS."""
    if any(len(values) != len(average_range) for values, _ in ranges_and_criteria):
        raise ValueError("All AVERAGEIFS ranges must have the same length.")

    matching_values = []

    for index, value_to_average in enumerate(average_range):
        if all(
            matches_criterion(values[index], criterion)
            for values, criterion in ranges_and_criteria
        ):
            if isinstance(value_to_average, (int, float)) and not isinstance(
                value_to_average, bool
            ):
                matching_values.append(value_to_average)

    if not matching_values:
        raise ZeroDivisionError("AVERAGEIFS has no numeric matching values.")

    return sum(matching_values) / len(matching_values)


sales_north_average = averageifs(
    performance_values,
    [
        (departments, "Sales"),
        ([row["region"] for row in employees], "North"),
    ],
)

print("Average performance for Sales + North:", f"{sales_north_average:.2f}")


# ============================================================================
# 17. COMPARING THE SIX CORE FUNCTIONS
# ============================================================================

print("\n" + "=" * 80)
print("SIX CORE CONDITIONAL FUNCTIONS")
print("=" * 80)

print(
    """
COUNTIF
    Counts cells matching one condition.

COUNTIFS
    Counts rows matching multiple conditions.

SUMIF
    Adds values matching one condition.

SUMIFS
    Adds values matching multiple conditions.

AVERAGEIF
    Averages values matching one condition.

AVERAGEIFS
    Averages values matching multiple conditions.

A useful mental model is:

    COUNT -> How many?
    SUM   -> How much total?
    AVERAGE -> What is the mean?

IF  -> one condition
IFS -> multiple conditions
"""
)


# ============================================================================
# 18. CONDITION SELECTION
# ============================================================================

print("\n" + "=" * 80)
print("CONDITION SELECTION")
print("=" * 80)


def select_rows(
    rows: Iterable[dict[str, Any]],
    condition: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Return rows satisfying a supplied logical condition."""
    return [row for row in rows if condition(row)]


high_performers = select_rows(
    employees,
    lambda row: row["performance"] >= 90,
)

print("High performers:")
print_rows(high_performers)


# ============================================================================
# 19. COMBINING AND, OR, AND NOT
# ============================================================================

print("\n" + "=" * 80)
print("COMBINING LOGICAL CONDITIONS")
print("=" * 80)


def complex_condition(row: dict[str, Any]) -> bool:
    """
    Example:

        department is Sales
        AND
        (performance >= 85 OR sales >= 150000)
        AND
        status is not Inactive
    """
    return (
        row["department"] == "Sales"
        and (
            row["performance"] >= 85
            or row["sales"] >= 150000
        )
        and row["status"] != "Inactive"
    )


complex_matches = select_rows(employees, complex_condition)

print("Rows matching complex condition:")
print_rows(complex_matches)


# ============================================================================
# 20. NESTED LOGICAL CONDITIONS
# ============================================================================

print("\n" + "=" * 80)
print("NESTED LOGICAL CONDITIONS")
print("=" * 80)

print(
    """
Nested logic means that one logical expression contains another.

Example:

    =IF(
        AND(
            B2="Sales",
            OR(D2>=90,E2>=150000)
        ),
        "Priority",
        "Normal"
    )

The evaluation structure is:

    IF
     |
     +-- AND
          |
          +-- department = Sales
          |
          +-- OR
               |
               +-- performance >= 90
               +-- sales >= 150000
"""
)


def priority_label(row: dict[str, Any]) -> str:
    """Equivalent of a nested IF/AND/OR decision."""
    if (
        row["department"] == "Sales"
        and (
            row["performance"] >= 90
            or row["sales"] >= 150000
        )
    ):
        return "Priority"

    return "Normal"


for row in employees:
    print(row["employee"], "->", priority_label(row))


# ============================================================================
# 21. NESTED IF DECISION TREE
# ============================================================================

print("\n" + "=" * 80)
print("NESTED IF DECISION TREE")
print("=" * 80)

print(
    """
A nested IF can classify numerical values.

Example:

    =IF(D2>=90,"Excellent",
        IF(D2>=80,"Good",
            IF(D2>=70,"Average","Needs Improvement")))

The ordering matters.

The highest threshold should generally be evaluated first.
"""
)


def performance_category(score: float) -> str:
    """Classify performance using ordered thresholds."""
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Good"
    if score >= 70:
        return "Average"
    return "Needs Improvement"


for row in employees:
    print(
        f"{row['employee']:8} | "
        f"{row['performance']:3} | "
        f"{performance_category(row['performance'])}"
    )


# ============================================================================
# 22. NESTED FORMULAS AND CONDITIONAL AGGREGATION
# ============================================================================

print("\n" + "=" * 80)
print("NESTED CONDITIONAL AGGREGATION")
print("=" * 80)

print(
    """
A formula can use the result of one calculation as the input to another.

For example, a report might first determine:

    Sales employees with performance >= 90

and then calculate:

    total sales
    average performance
    employee count

The Python equivalent is to create one filtered population and then
perform multiple aggregations on it.
"""
)

priority_sales = select_rows(
    employees,
    lambda row: (
        row["department"] == "Sales"
        and row["performance"] >= 90
    ),
)

priority_sales_total = sum(row["sales"] for row in priority_sales)
priority_sales_average = mean(
    row["performance"] for row in priority_sales
) if priority_sales else None

print("Priority Sales employees:", len(priority_sales))
print("Priority Sales revenue:", f"{priority_sales_total:,.2f}")
print(
    "Priority Sales average performance:",
    f"{priority_sales_average:.2f}" if priority_sales_average else "N/A",
)


# ============================================================================
# 23. DATE CONDITIONS
# ============================================================================

print("\n" + "=" * 80)
print("DATE-BASED CONDITIONS")
print("=" * 80)

print(
    """
COUNTIFS, SUMIFS, and AVERAGEIFS can also work with dates.

Typical Excel examples:

    =COUNTIF(A2:A100,">=01/01/2026")

    =SUMIFS(E2:E100,A2:A100,">="&DATE(2026,1,1))

The comparison operator and date value are often combined with &.

Python represents dates explicitly using datetime.date.
"""
)

transactions = [
    {"date": date(2026, 1, 5), "region": "North", "amount": 50000},
    {"date": date(2026, 2, 12), "region": "South", "amount": 75000},
    {"date": date(2026, 3, 18), "region": "North", "amount": 92000},
    {"date": date(2026, 4, 22), "region": "West", "amount": 65000},
    {"date": date(2026, 5, 9), "region": "North", "amount": 110000},
]

cutoff_date = date(2026, 3, 1)

transactions_after_cutoff = [
    transaction
    for transaction in transactions
    if transaction["date"] >= cutoff_date
]

print("Transactions on or after March 1, 2026:")
for transaction in transactions_after_cutoff:
    print(transaction)


# ============================================================================
# 24. TEXT CONDITIONS
# ============================================================================

print("\n" + "=" * 80)
print("TEXT CONDITIONS")
print("=" * 80)

print(
    """
Text criteria are frequently used for:
- department
- region
- status
- product category
- customer segment

Examples:

    =COUNTIF(B2:B100,"Sales")
    =COUNTIF(F2:F100,"Active")
    =SUMIF(C2:C100,"North",E2:E100)

Case sensitivity is an important practical issue.

Standard Excel COUNTIF-style comparisons are generally not case-sensitive.
The custom Python examples above can be made explicitly case-insensitive
for text matching.
"""
)

statuses = [row["status"] for row in employees]

print("Active:", countif(statuses, "Active"))
print("Inactive:", countif(statuses, "Inactive"))


# ============================================================================
# 25. BLANK AND NON-BLANK CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("BLANK AND NON-BLANK CONDITIONS")
print("=" * 80)

print(
    """
Excel uses criteria such as:

    =COUNTIF(A2:A20,"")
    =COUNTIF(A2:A20,"<>")

The first is commonly used to identify blank cells.
The second is commonly used to identify non-blank cells.

Blank handling deserves care because empty strings, truly empty cells,
spaces, zeros, and errors are not conceptually identical.
"""
)

sample_values = ["North", "", "South", None, " ", "East", 0]

blank_values = [
    value for value in sample_values
    if value == "" or value is None
]

non_blank_values = [
    value for value in sample_values
    if value != "" and value is not None
]

print("Blank-like values:", blank_values)
print("Non-blank values:", non_blank_values)


# ============================================================================
# 26. ERRORS AND AVERAGEIFS
# ============================================================================

print("\n" + "=" * 80)
print("NO MATCHING ROWS")
print("=" * 80)

print(
    """
A COUNTIF with no matches normally returns 0.

A SUMIF with no matches normally returns 0.

An AVERAGEIF/AVERAGEIFS operation with no numeric matching values
cannot produce a meaningful arithmetic average.

In Excel, this situation commonly results in #DIV/0!.

Production formulas often handle this explicitly:

    =IFERROR(AVERAGEIF(...),0)

or

    =IFERROR(AVERAGEIFS(...),"No data")
"""
)

try:
    averageif(
        departments,
        "Legal",
        performance_values,
    )
except ZeroDivisionError as error:
    print("Handled no-match average:", error)


# ============================================================================
# 27. IFERROR-STYLE HANDLING
# ============================================================================

print("\n" + "=" * 80)
print("ERROR HANDLING")
print("=" * 80)


def safe_averageif(
    criteria_range: Sequence[Any],
    criterion: Any,
    average_range: Sequence[float],
    default: Any = 0,
) -> Any:
    """Return a default value instead of failing when no values match."""
    try:
        return averageif(criteria_range, criterion, average_range)
    except ZeroDivisionError:
        return default


print(
    "Average Legal performance:",
    safe_averageif(
        departments,
        "Legal",
        performance_values,
        default="No matching data",
    ),
)


# ============================================================================
# 28. RANGE SIZE VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("RANGE SIZE VALIDATION")
print("=" * 80)

print(
    """
Excel conditional aggregation is sensitive to range alignment.

For example:

    =SUMIFS(E2:E20,B2:B20,"Sales")

works because all ranges cover corresponding rows.

Conceptually incorrect range alignment can produce wrong results.

A robust implementation validates equal lengths.
"""
)

try:
    sumif(
        ["Sales", "Finance"],
        "Sales",
        [100],
    )
except ValueError as error:
    print("Validation error:", error)


# ============================================================================
# 29. REAL-WORLD SALES ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("REAL-WORLD SALES ANALYSIS")
print("=" * 80)

print(
    """
A practical report may ask:

1. How many Sales employees are there?
2. How much revenue did Sales generate?
3. What is Sales' average performance?
4. How many Sales employees in North exceeded 90?
5. What revenue did those employees generate?
6. What percentage of Sales employees are high performers?
"""
)

sales_rows = [
    row for row in employees
    if row["department"] == "Sales"
]

sales_employee_count = len(sales_rows)
sales_revenue = sum(row["sales"] for row in sales_rows)
sales_average = (
    mean(row["performance"] for row in sales_rows)
    if sales_rows
    else 0
)

sales_north_high_rows = [
    row
    for row in sales_rows
    if row["region"] == "North"
    and row["performance"] >= 90
]

sales_north_high_count = len(sales_north_high_rows)
sales_north_high_revenue = sum(
    row["sales"] for row in sales_north_high_rows
)

high_performer_percentage = (
    sales_north_high_count / sales_employee_count * 100
    if sales_employee_count
    else 0
)

print("Sales employee count:", sales_employee_count)
print("Sales revenue:", f"{sales_revenue:,.2f}")
print("Sales average performance:", f"{sales_average:.2f}")
print("Sales + North + performance >= 90:", sales_north_high_count)
print(
    "Revenue from Sales + North + performance >= 90:",
    f"{sales_north_high_revenue:,.2f}",
)
print(
    "Percentage of Sales employees meeting condition:",
    f"{high_performer_percentage:.2f}%",
)


# ============================================================================
# 30. CONDITIONAL KPI TABLE
# ============================================================================

print("\n" + "=" * 80)
print("CONDITIONAL KPI TABLE")
print("=" * 80)


def department_kpi(department: str) -> dict[str, Any]:
    """Build conditional metrics for one department."""
    rows = [
        row for row in employees
        if row["department"] == department
    ]

    revenue = sum(row["sales"] for row in rows)
    average_performance = (
        mean(row["performance"] for row in rows)
        if rows
        else None
    )

    high_performers = [
        row for row in rows
        if row["performance"] >= 90
    ]

    return {
        "department": department,
        "employees": len(rows),
        "revenue": revenue,
        "average_performance": average_performance,
        "high_performers": len(high_performers),
    }


for department in sorted({row["department"] for row in employees}):
    kpi = department_kpi(department)
    average_display = (
        f"{kpi['average_performance']:.2f}"
        if kpi["average_performance"] is not None
        else "N/A"
    )

    print(
        f"{kpi['department']:8} | "
        f"Employees={kpi['employees']:2} | "
        f"Revenue={kpi['revenue']:9,.0f} | "
        f"Avg Performance={average_display:>6} | "
        f"High Performers={kpi['high_performers']:2}"
    )


# ============================================================================
# 31. MULTIPLE CONDITIONS WITH DIFFERENT OPERATORS
# ============================================================================

print("\n" + "=" * 80)
print("MULTIPLE OPERATORS")
print("=" * 80)

print(
    """
Criteria do not need to use the same comparison operator.

For example:

    Department = Sales
    AND
    Performance >= 80
    AND
    Sales < 150000
    AND
    Experience <> 3

This can be represented in Excel with:

    =COUNTIFS(
        B2:B20,"Sales",
        D2:D20,">=80",
        E2:E20,"<150000",
        F2:F20,"<>3"
    )
"""
)

mixed_condition_count = countifs(
    [
        (departments, "Sales"),
        (performance_values, ">=80"),
        (sales_values, "<150000"),
        ([row["experience"] for row in employees], "<>3"),
    ]
)

print("Mixed-condition count:", mixed_condition_count)


# ============================================================================
# 32. CONDITIONAL RATIO
# ============================================================================

print("\n" + "=" * 80)
print("CONDITIONAL RATIO")
print("=" * 80)

print(
    """
A common analytical pattern is:

    matching records / total records

For example:

    high performers / all employees

This converts a COUNTIFS result into a rate or percentage.
"""
)

total_employees = len(employees)
high_performers = countif(performance_values, ">=90")

high_performer_rate = (
    high_performers / total_employees
    if total_employees
    else 0
)

print("High performer count:", high_performers)
print("High performer rate:", f"{high_performer_rate:.2%}")


# ============================================================================
# 33. CONDITIONAL SUM AS A PERCENTAGE OF TOTAL
# ============================================================================

print("\n" + "=" * 80)
print("CONDITIONAL SUM PERCENTAGE")
print("=" * 80)

total_sales = sum(sales_values)

north_sales = sumif(
    [row["region"] for row in employees],
    "North",
    sales_values,
)

north_sales_share = north_sales / total_sales if total_sales else 0

print("Total sales:", f"{total_sales:,.2f}")
print("North sales:", f"{north_sales:,.2f}")
print("North share:", f"{north_sales_share:.2%}")


# ============================================================================
# 34. CONDITIONAL AVERAGE VS GLOBAL AVERAGE
# ============================================================================

print("\n" + "=" * 80)
print("CONDITIONAL AVERAGE VS GLOBAL AVERAGE")
print("=" * 80)

global_average_performance = mean(performance_values)
sales_average_performance = averageif(
    departments,
    "Sales",
    performance_values,
)

print("Global average:", f"{global_average_performance:.2f}")
print("Sales average:", f"{sales_average_performance:.2f}")
print(
    "Difference:",
    f"{sales_average_performance - global_average_performance:.2f}",
)


# ============================================================================
# 35. WEIGHTED VS UNWEIGHTED CONDITIONAL AVERAGE
# ============================================================================

print("\n" + "=" * 80)
print("AVERAGE VS WEIGHTED AVERAGE")
print("=" * 80)

print(
    """
AVERAGEIF calculates an arithmetic mean.

If every record should have equal importance:

    average = sum(values) / count(values)

A weighted average is different.

For example, when performance scores represent percentages but sales
amounts represent business impact, weighting performance by sales
may produce a different business metric.

The two calculations answer different questions.
"""
)


def weighted_average(
    values: Sequence[float],
    weights: Sequence[float],
) -> float:
    """Calculate a weighted arithmetic average."""
    if len(values) != len(weights):
        raise ValueError("Values and weights must have equal lengths.")

    total_weight = sum(weights)

    if total_weight == 0:
        raise ZeroDivisionError("Total weight cannot be zero.")

    return sum(
        value * weight
        for value, weight in zip(values, weights)
    ) / total_weight


sales_weighted_performance = weighted_average(
    performance_values,
    sales_values,
)

print("Simple average performance:", f"{global_average_performance:.2f}")
print("Sales-weighted performance:", f"{sales_weighted_performance:.2f}")


# ============================================================================
# 36. CUSTOM CONDITION ENGINE
# ============================================================================

print("\n" + "=" * 80)
print("CUSTOM CONDITION ENGINE")
print("=" * 80)

print(
    """
For advanced analysis, it is useful to separate:

    data
    condition
    aggregation

This makes the same data usable with many different business rules.
"""


def conditional_count(
    rows: Iterable[dict[str, Any]],
    condition: Callable[[dict[str, Any]], bool],
) -> int:
    return sum(1 for row in rows if condition(row))


def conditional_sum(
    rows: Iterable[dict[str, Any]],
    condition: Callable[[dict[str, Any]], bool],
    value_selector: Callable[[dict[str, Any]], float],
) -> float:
    return sum(
        value_selector(row)
        for row in rows
        if condition(row)
    )


def conditional_average(
    rows: Iterable[dict[str, Any]],
    condition: Callable[[dict[str, Any]], bool],
    value_selector: Callable[[dict[str, Any]], float],
) -> float:
    values = [
        value_selector(row)
        for row in rows
        if condition(row)
    ]

    if not values:
        raise ZeroDivisionError("No values satisfy the condition.")

    return sum(values) / len(values)


condition = lambda row: (
    row["region"] == "North"
    and row["sales"] >= 100000
)

print(
    "Count:",
    conditional_count(employees, condition),
)

print(
    "Sales total:",
    f"{conditional_sum(employees, condition, lambda row: row['sales']):,.2f}",
)

print(
    "Average performance:",
    f"{conditional_average(employees, condition, lambda row: row['performance']):.2f}",
)


# ============================================================================
# 37. EXCEL FORMULA CONSTRUCTION
# ============================================================================

print("\n" + "=" * 80)
print("CONSTRUCTING EXCEL FORMULAS")
print("=" * 80)

print(
    """
Conditional formulas are often constructed from cell references.

Example:

    =COUNTIFS(
        B2:B100,$H$2,
        C2:C100,$H$3,
        D2:D100,">="&$H$4
    )

Here:

    $H$2 -> department criterion
    $H$3 -> region criterion
    $H$4 -> performance threshold

Absolute references are useful when copying formulas across a report.
"""
)


def excel_countifs_formula(
    criteria: Sequence[tuple[str, str]]
) -> str:
    """Generate a readable COUNTIFS formula."""
    arguments = []

    for cell_range, criterion in criteria:
        arguments.append(f"{cell_range},{criterion}")

    return "=COUNTIFS(" + ",".join(arguments) + ")"


formula = excel_countifs_formula(
    [
        ("B2:B100", '"Sales"'),
        ("C2:C100", '"North"'),
        ("D2:D100", '">=90"'),
    ]
)

print(formula)


# ============================================================================
# 38. RELATIVE AND ABSOLUTE REFERENCES
# ============================================================================

print("\n" + "=" * 80)
print("RELATIVE AND ABSOLUTE REFERENCES")
print("=" * 80)

print(
    """
Excel references:

    A1       relative column and relative row
    $A$1     absolute column and absolute row
    A$1      relative column, absolute row
    $A1      absolute column, relative row

When conditional formulas are copied, reference behavior determines
whether the criteria range moves or stays fixed.

Example:

    =COUNTIF($B$2:$B$100,H2)

The criteria range stays fixed while H2 can change to H3, H4, and so on.
"""
)


# ============================================================================
# 39. COMMON FORMULA DESIGN MISTAKES
# ============================================================================

print("\n" + "=" * 80)
print("COMMON MISTAKES")
print("=" * 80)

mistakes = [
    (
        "Using SUMIF when several conditions are required",
        "Use SUMIFS when the logic requires multiple AND conditions.",
    ),
    (
        "Mismatched range sizes",
        "Keep criteria ranges and aggregation ranges aligned.",
    ),
    (
        "Forgetting quotes around text criteria",
        'Use "Sales", not Sales, inside a formula.',
    ),
    (
        "Incorrect comparison syntax",
        'Use ">=90" as the criterion text.',
    ),
    (
        "Ignoring empty results",
        "Protect averages and divisions against zero matching rows.",
    ),
    (
        "Using OR logic as if it were AND logic",
        "COUNTIFS combines criteria using AND semantics.",
    ),
    (
        "Double-counting overlapping OR groups",
        "Use inclusion-exclusion or a row-level OR test.",
    ),
    (
        "Incorrectly assuming case sensitivity",
        "Standard COUNTIF-style text comparisons are generally case-insensitive.",
    ),
    (
        "Ignoring errors in source data",
        "Clean or explicitly handle errors before aggregation.",
    ),
    (
        "Building excessively nested formulas",
        "Separate complicated logic into helper columns or structured calculations.",
    ),
]

for mistake, correction in mistakes:
    print(f"- {mistake}")
    print(f"  Correction: {correction}")


# ============================================================================
# 40. EDGE CASES
# ============================================================================

print("\n" + "=" * 80)
print("EDGE CASES")
print("=" * 80)

edge_case_data = [
    10,
    20,
    0,
    -5,
    None,
    "10",
    "",
]

print("Data:", edge_case_data)

print(">=10:", countif(edge_case_data, ">=10"))
print("=0:", countif(edge_case_data, 0))
print("<0:", countif(edge_case_data, "<0"))
print("Blank:", countif(edge_case_data, ""))


# ============================================================================
# 41. DATA TYPE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("DATA TYPE CONSIDERATIONS")
print("=" * 80)

print(
    """
Conditional analysis depends heavily on consistent data types.

Potential problems include:

    10000
    "10000"

These may look similar to a human but can behave differently in
calculations.

Other problematic values include:

    "₹10000"
    "10%"
    "  Sales "
    "sales"
    blank cells
    error values
    dates stored as text

A strong spreadsheet design separates:
- display formatting
- underlying value
- business meaning
"""
)


# ============================================================================
# 42. DATA CLEANING BEFORE CONDITIONAL ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("DATA CLEANING")
print("=" * 80)


def normalize_department(value: Any) -> str:
    """Normalize department text before conditional analysis."""
    if value is None:
        return ""

    return str(value).strip().lower()


messy_departments = [
    "Sales",
    " sales ",
    "SALES",
    "Finance",
    None,
]

normalized = [
    normalize_department(value)
    for value in messy_departments
]

print("Original:", messy_departments)
print("Normalized:", normalized)

normalized_sales_count = sum(
    value == "sales"
    for value in normalized
)

print("Normalized Sales count:", normalized_sales_count)


# ============================================================================
# 43. PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("PERFORMANCE CONSIDERATIONS")
print("=" * 80)

print(
    """
Conditional formulas can become expensive in very large workbooks.

Potential performance issues include:
- millions of cells
- many repeated COUNTIFS/SUMIFS calculations
- volatile formulas
- unnecessary full-column references
- repeated complex criteria
- duplicated calculations across dashboards

Good design principles include:
- use appropriate ranges
- avoid unnecessary full-column references when practical
- calculate reusable values once
- use Excel Tables and structured references where appropriate
- consider PivotTables for large aggregation workloads
- reduce repeated nested formulas
- keep source data normalized

In Python, repeatedly scanning a list is O(n) for one conditional operation.
Multiple independent scans can therefore approach O(k*n), where k is
the number of separate conditions or metrics.
"""
)

# Demonstrate that each aggregation scans the data.
print("COUNTIF Sales:", countif(departments, "Sales"))
print("SUMIF Sales:", sumif(departments, "Sales", sales_values))
print(
    "AVERAGEIF Sales:",
    f"{averageif(departments, 'Sales', performance_values):.2f}",
)


# ============================================================================
# 44. SINGLE-PASS MULTI-METRIC ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("SINGLE-PASS MULTI-METRIC ANALYSIS")
print("=" * 80)

print(
    """
When many related metrics are required, one row-by-row pass can calculate
several metrics at once.

This is a useful programming concept even though Excel's formula engine
uses its own calculation model.
"""
)


def calculate_sales_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    """Calculate several Sales metrics in one pass."""
    count = 0
    total = 0.0
    performance_total = 0.0
    high_performer_count = 0

    for row in rows:
        if row["department"] != "Sales":
            continue

        count += 1
        total += row["sales"]
        performance_total += row["performance"]

        if row["performance"] >= 90:
            high_performer_count += 1

    return {
        "count": count,
        "total_sales": total,
        "average_performance": (
            performance_total / count if count else 0
        ),
        "high_performer_count": high_performer_count,
    }


metrics = calculate_sales_metrics(employees)

for key, value in metrics.items():
    print(f"{key}: {value}")


# ============================================================================
# 45. CONDITIONAL REPORTING FUNCTION
# ============================================================================

print("\n" + "=" * 80)
print("CONDITIONAL REPORTING")
print("=" * 80)


@dataclass
class ConditionalReport:
    """Container for a small conditional-analysis report."""

    department: str
    employee_count: int
    total_sales: float
    average_performance: float
    high_performer_count: int
    high_performer_rate: float


def build_department_report(
    rows: Sequence[dict[str, Any]],
    department: str,
) -> ConditionalReport:
    """Create a reusable department-level conditional report."""
    matching = [
        row for row in rows
        if row["department"] == department
    ]

    count = len(matching)
    total_sales = sum(row["sales"] for row in matching)
    average_performance = (
        mean(row["performance"] for row in matching)
        if matching
        else 0
    )
    high_count = sum(
        row["performance"] >= 90
        for row in matching
    )
    high_rate = high_count / count if count else 0

    return ConditionalReport(
        department=department,
        employee_count=count,
        total_sales=total_sales,
        average_performance=average_performance,
        high_performer_count=high_count,
        high_performer_rate=high_rate,
    )


report = build_department_report(employees, "Sales")

print(report)


# ============================================================================
# 46. VALIDATING RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("RESULT VALIDATION")
print("=" * 80)

print(
    """
Spreadsheet analysis should be validated.

Useful validation techniques include:
- manually checking a small subset
- comparing COUNTIF against a filtered row count
- checking that SUMIFS does not exceed the relevant total
- checking that an average lies within the possible range
- testing empty-result cases
- testing boundary values
"""
)

manual_sales_rows = [
    row for row in employees
    if row["department"] == "Sales"
]

formula_count = countif(departments, "Sales")
manual_count = len(manual_sales_rows)

assert formula_count == manual_count

formula_sales_sum = sumif(
    departments,
    "Sales",
    sales_values,
)

manual_sales_sum = sum(
    row["sales"]
    for row in manual_sales_rows
)

assert isclose(formula_sales_sum, manual_sales_sum)

print("COUNTIF validation: PASSED")
print("SUMIF validation: PASSED")


# ============================================================================
# 47. BOUNDARY TESTING
# ============================================================================

print("\n" + "=" * 80)
print("BOUNDARY TESTING")
print("=" * 80)

boundary_values = [69, 70, 79, 80, 89, 90, 91]

print("Values:", boundary_values)
print(">=90:", countif(boundary_values, ">=90"))
print(">90:", countif(boundary_values, ">90"))
print(">=80:", countif(boundary_values, ">=80"))
print("<80:", countif(boundary_values, "<80"))


# ============================================================================
# 48. UNIT TESTS
# ============================================================================

print("\n" + "=" * 80)
print("UNIT TESTS")
print("=" * 80)


def run_tests() -> None:
    """Run core correctness tests."""
    assert countif([1, 2, 2, 3], 2) == 2
    assert countif([1, 2, 3, 4], ">=3") == 2
    assert countif(["Sales", "Finance", "Sales"], "Sales") == 2

    assert sumif(
        ["A", "B", "A"],
        "A",
        [10, 20, 30],
    ) == 40

    assert averageif(
        ["A", "A", "B"],
        "A",
        [10, 20, 100],
    ) == 15

    assert countifs(
        [
            (["A", "A", "B"], "A"),
            ([10, 20, 30], ">=20"),
        ]
    ) == 1

    assert sumifs(
        [10, 20, 30],
        [
            (["A", "A", "B"], "A"),
            ([10, 20, 30], ">=20"),
        ],
    ) == 20

    assert averageifs(
        [10, 20, 30],
        [
            (["A", "A", "B"], "A"),
            ([10, 20, 30], ">=20"),
        ],
    ) == 20

    assert countif_with_wildcards(
        ["Aarav", "Anaya", "Kabir"],
        "A*",
    ) == 2

    try:
        sumif(["A"], "A", [10, 20])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected range mismatch error.")

    try:
        averageif(["A"], "B", [10])
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("Expected no-match average error.")


run_tests()

print("All unit tests passed.")


# ============================================================================
# 49. ADVANCED CONDITION COMPOSITION
# ============================================================================

print("\n" + "=" * 80)
print("ADVANCED CONDITION COMPOSITION")
print("=" * 80)


def and_conditions(
    *conditions: Callable[[dict[str, Any]], bool],
) -> Callable[[dict[str, Any]], bool]:
    """Compose multiple row conditions using AND."""
    return lambda row: all(condition(row) for condition in conditions)


def or_conditions(
    *conditions: Callable[[dict[str, Any]], bool],
) -> Callable[[dict[str, Any]], bool]:
    """Compose multiple row conditions using OR."""
    return lambda row: any(condition(row) for condition in conditions)


def not_condition(
    condition: Callable[[dict[str, Any]], bool],
) -> Callable[[dict[str, Any]], bool]:
    """Negate a row condition."""
    return lambda row: not condition(row)


is_sales = lambda row: row["department"] == "Sales"
is_north = lambda row: row["region"] == "North"
is_high_performance = lambda row: row["performance"] >= 90
is_active = lambda row: row["status"] == "Active"

combined = and_conditions(
    is_sales,
    is_north,
    is_high_performance,
    is_active,
)

advanced_rows = select_rows(employees, combined)

print("Sales + North + high performance + active:")
print_rows(advanced_rows)

sales_or_finance_condition = or_conditions(
    lambda row: row["department"] == "Sales",
    lambda row: row["department"] == "Finance",
)

sales_or_finance_rows = select_rows(
    employees,
    sales_or_finance_condition,
)

print("\nSales OR Finance:")
print_rows(sales_or_finance_rows)

not_active_rows = select_rows(
    employees,
    not_condition(is_active),
)

print("\nNot active:")
print_rows(not_active_rows)


# ============================================================================
# 50. CONDITIONAL ANALYSIS AS SET OPERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("CONDITIONAL ANALYSIS AS SET OPERATIONS")
print("=" * 80)

print(
    """
Many spreadsheet conditions can be understood as set operations.

AND:
    intersection

OR:
    union

NOT:
    complement

For example:

    Sales AND North

is the intersection of:

    Sales employees
    North employees

This perspective is useful when designing complicated analytical logic.
"""
)

sales_names = {
    row["employee"]
    for row in employees
    if row["department"] == "Sales"
}

north_names = {
    row["employee"]
    for row in employees
    if row["region"] == "North"
}

print("Sales set:", sales_names)
print("North set:", north_names)
print("Sales AND North:", sales_names & north_names)
print("Sales OR North:", sales_names | north_names)


# ============================================================================
# 51. FORMULA CHOICE DECISION GUIDE
# ============================================================================

print("\n" + "=" * 80)
print("FORMULA CHOICE DECISION GUIDE")
print("=" * 80)

print(
    """
Use COUNTIF when:
    You need a count based on one condition.

Use COUNTIFS when:
    You need a count based on multiple AND conditions.

Use SUMIF when:
    You need a total based on one condition.

Use SUMIFS when:
    You need a total based on multiple AND conditions.

Use AVERAGEIF when:
    You need a mean based on one condition.

Use AVERAGEIFS when:
    You need a mean based on multiple AND conditions.

Use IF when:
    You need to return different values depending on one logical test.

Use nested IF or other logical structures when:
    Multiple decision levels are required.

Use AND when:
    Every condition must be true.

Use OR when:
    At least one condition must be true.

Use NOT when:
    A condition must be reversed.
"""
)


# ============================================================================
# 52. BUSINESS CASE: PERFORMANCE SEGMENTATION
# ============================================================================

print("\n" + "=" * 80)
print("BUSINESS CASE: PERFORMANCE SEGMENTATION")
print("=" * 80)


def segment_employee(row: dict[str, Any]) -> str:
    """
    Multi-level segmentation:

    Excellent:
        performance >= 90 AND sales >= 100000

    Strong:
        performance >= 80 AND sales >= 80000

    Developing:
        performance >= 70

    Needs Attention:
        everything else
    """
    if row["performance"] >= 90 and row["sales"] >= 100000:
        return "Excellent"

    if row["performance"] >= 80 and row["sales"] >= 80000:
        return "Strong"

    if row["performance"] >= 70:
        return "Developing"

    return "Needs Attention"


for row in employees:
    print(
        f"{row['employee']:8} -> "
        f"{segment_employee(row)}"
    )


# ============================================================================
# 53. BUSINESS CASE: ELIGIBILITY RULE
# ============================================================================

print("\n" + "=" * 80)
print("BUSINESS CASE: ELIGIBILITY RULE")
print("=" * 80)

print(
    """
A real business rule may be:

Eligible if:
    Active
    AND experience >= 5
    AND (
        performance >= 85
        OR sales >= 120000
    )
"""
)


def is_eligible_for_bonus(row: dict[str, Any]) -> bool:
    return (
        row["status"] == "Active"
        and row["experience"] >= 5
        and (
            row["performance"] >= 85
            or row["sales"] >= 120000
        )
    )


eligible_employees = select_rows(
    employees,
    is_eligible_for_bonus,
)

print("Bonus-eligible employees:")
print_rows(eligible_employees)


# ============================================================================
# 54. BUSINESS CASE: CONDITIONAL PAYOUT
# ============================================================================

print("\n" + "=" * 80)
print("BUSINESS CASE: CONDITIONAL PAYOUT")
print("=" * 80)

print(
    """
Conditional analysis can feed another calculation.

For example:

    if eligible:
        bonus = sales * 5%
    else:
        bonus = 0
"""
)


def calculate_bonus(row: dict[str, Any]) -> float:
    if is_eligible_for_bonus(row):
        return row["sales"] * 0.05

    return 0.0


total_bonus = sum(
    calculate_bonus(row)
    for row in employees
)

for row in employees:
    print(
        f"{row['employee']:8} | "
        f"Eligible={is_eligible_for_bonus(row)!s:5} | "
        f"Bonus={calculate_bonus(row):,.2f}"
    )

print("Total bonus liability:", f"{total_bonus:,.2f}")


# ============================================================================
# 55. NESTED FORMULAS: PRACTICAL DESIGN ALTERNATIVE
# ============================================================================

print("\n" + "=" * 80)
print("NESTED FORMULA DESIGN")
print("=" * 80)

print(
    """
Deeply nested formulas can become difficult to audit.

A formula such as:

    =IF(A2="Sales",
        IF(B2>=90,"A",
            IF(B2>=80,"B","C")),
        IF(A2="Finance","F","Other"))

works, but complexity increases quickly.

A helper column can make the logic more transparent.

The Python equivalent is to isolate business rules in named functions.
"""
)


def grade_employee(row: dict[str, Any]) -> str:
    """A named rule is easier to inspect than deeply nested logic."""
    if row["department"] == "Sales":
        if row["performance"] >= 90:
            return "A"
        if row["performance"] >= 80:
            return "B"
        return "C"

    if row["department"] == "Finance":
        return "F"

    return "Other"


for row in employees:
    print(row["employee"], "->", grade_employee(row))


# ============================================================================
# 56. SECURITY AND DATA INTEGRITY CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("SECURITY AND DATA INTEGRITY")
print("=" * 80)

print(
    """
Conditional formulas are normally not a security mechanism.

Important considerations include:

1. Formula results depend on source data integrity.
2. A hidden row is not necessarily excluded from a calculation.
3. Worksheet protection does not automatically make data trustworthy.
4. External links and imported data can introduce unexpected values.
5. User-editable criteria cells should be validated.
6. Business-critical calculations should have independent checks.
7. Sensitive spreadsheets should use appropriate access controls.

For financial or operational reporting, formula correctness and source-data
governance are separate concerns.
"""
)


# ============================================================================
# 57. AUDITABLE ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("AUDITABLE ANALYSIS")
print("=" * 80)

print(
    """
A good conditional-analysis model should make the following visible:

    Source data
        |
        v
    Criteria
        |
        v
    Matching records
        |
        v
    Aggregation
        |
        v
    KPI

Auditability improves when:
- criteria are stored in clearly labeled cells
- formulas use consistent ranges
- helper columns expose important intermediate logic
- assumptions are separated from calculations
- boundary cases are tested
"""
)


# ============================================================================
# 58. PRODUCTION-STYLE VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("PRODUCTION-STYLE VALIDATION")
print("=" * 80)


def validate_dataset(rows: Sequence[dict[str, Any]]) -> list[str]:
    """Validate fields needed for conditional business analysis."""
    errors: list[str] = []

    required_fields = {
        "employee",
        "department",
        "region",
        "performance",
        "sales",
        "experience",
        "status",
    }

    for index, row in enumerate(rows, start=1):
        missing = required_fields - row.keys()

        if missing:
            errors.append(
                f"Row {index}: missing fields {sorted(missing)}"
            )
            continue

        if not isinstance(row["performance"], (int, float)):
            errors.append(
                f"Row {index}: performance must be numeric."
            )

        if not isinstance(row["sales"], (int, float)):
            errors.append(
                f"Row {index}: sales must be numeric."
            )

        if row["performance"] < 0 or row["performance"] > 100:
            errors.append(
                f"Row {index}: performance outside 0-100 range."
            )

        if row["sales"] < 0:
            errors.append(
                f"Row {index}: sales cannot be negative."
            )

    return errors


validation_errors = validate_dataset(employees)

if validation_errors:
    print("Validation errors:")
    for error in validation_errors:
        print(error)
else:
    print("Dataset validation: PASSED")


# ============================================================================
# 59. PERFORMANCE-SAFE FILTERING
# ============================================================================

print("\n" + "=" * 80)
print("PERFORMANCE-SAFE FILTERING")
print("=" * 80)

print(
    """
For large datasets, it is often useful to:
- avoid repeatedly extracting the same columns
- store reusable filtered populations
- combine related calculations into one pass
- avoid unnecessary transformations

For example, if five KPIs all depend on Sales employees, filtering Sales
once can be simpler and faster than independently scanning the entire
dataset five times.
"""
)

sales_population = [
    row for row in employees
    if row["department"] == "Sales"
]

sales_high_performers = [
    row for row in sales_population
    if row["performance"] >= 90
]

print("Sales population:", len(sales_population))
print("Sales high performers:", len(sales_high_performers))


# ============================================================================
# 60. CONDITIONAL AGGREGATION WITH GENERATORS
# ============================================================================

print("\n" + "=" * 80)
print("GENERATOR-BASED CONDITIONAL AGGREGATION")
print("=" * 80)

print(
    """
Generators can avoid constructing temporary lists when only an aggregate
is required.

For example:

    sum(row["sales"] for row in employees if condition(row))

This is memory-efficient because values are processed lazily.
"""
)

north_total_generator = sum(
    row["sales"]
    for row in employees
    if row["region"] == "North"
)

north_count_generator = sum(
    1
    for row in employees
    if row["region"] == "North"
)

print("North total sales:", f"{north_total_generator:,.2f}")
print("North employee count:", north_count_generator)


# ============================================================================
# 61. COMPARISON TABLE
# ============================================================================

print("\n" + "=" * 80)
print("FUNCTION COMPARISON")
print("=" * 80)

comparison = [
    ("COUNTIF", "1", "Count", "One condition"),
    ("COUNTIFS", "Many", "Count", "Multiple AND conditions"),
    ("SUMIF", "1", "Sum", "One condition"),
    ("SUMIFS", "Many", "Sum", "Multiple AND conditions"),
    ("AVERAGEIF", "1", "Average", "One condition"),
    ("AVERAGEIFS", "Many", "Average", "Multiple AND conditions"),
]

print(f"{'Function':12} | {'Conditions':10} | {'Operation':10} | Purpose")
print("-" * 75)

for function, conditions, operation, purpose in comparison:
    print(
        f"{function:12} | "
        f"{conditions:10} | "
        f"{operation:10} | "
        f"{purpose}"
    )


# ============================================================================
# 62. FINAL INTEGRATED ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("FINAL INTEGRATED ANALYSIS")
print("=" * 80)

print(
    """
Integrated example:

Identify active Sales employees in North with:
    performance >= 85
    AND sales >= 100000

Then calculate:
    count
    total sales
    average performance
    average experience
    percentage of all employees
"""
)

integrated_condition = (
    lambda row: (
        row["status"] == "Active"
        and row["department"] == "Sales"
        and row["region"] == "North"
        and row["performance"] >= 85
        and row["sales"] >= 100000
    )
)

integrated_rows = select_rows(
    employees,
    integrated_condition,
)

integrated_count = len(integrated_rows)
integrated_total_sales = sum(
    row["sales"] for row in integrated_rows
)

integrated_average_performance = (
    mean(row["performance"] for row in integrated_rows)
    if integrated_rows
    else 0
)

integrated_average_experience = (
    mean(row["experience"] for row in integrated_rows)
    if integrated_rows
    else 0
)

integrated_percentage = (
    integrated_count / len(employees) * 100
    if employees
    else 0
)

print("Matching employees:")
print_rows(integrated_rows)

print("\nIntegrated metrics:")
print("Count:", integrated_count)
print("Total sales:", f"{integrated_total_sales:,.2f}")
print(
    "Average performance:",
    f"{integrated_average_performance:.2f}",
)
print(
    "Average experience:",
    f"{integrated_average_experience:.2f}",
)
print(
    "Percentage of all employees:",
    f"{integrated_percentage:.2f}%",
)


# ============================================================================
# 63. KEY FORMULA PATTERNS
# ============================================================================

print("\n" + "=" * 80)
print("KEY EXCEL FORMULA PATTERNS")
print("=" * 80)

formula_patterns = {
    "Count one condition":
        '=COUNTIF(B2:B100,"Sales")',

    "Count multiple conditions":
        '=COUNTIFS(B2:B100,"Sales",C2:C100,"North")',

    "Sum one condition":
        '=SUMIF(B2:B100,"Sales",E2:E100)',

    "Sum multiple conditions":
        '=SUMIFS(E2:E100,B2:B100,"Sales",C2:C100,"North")',

    "Average one condition":
        '=AVERAGEIF(B2:B100,"Sales",D2:D100)',

    "Average multiple conditions":
        '=AVERAGEIFS(D2:D100,B2:B100,"Sales",C2:C100,"North")',

    "Greater than":
        '=COUNTIF(D2:D100,">80")',

    "Greater than or equal":
        '=COUNTIF(D2:D100,">=80")',

    "Less than":
        '=COUNTIF(D2:D100,"<80")',

    "Not equal":
        '=COUNTIF(B2:B100,"<>Sales")',

    "AND":
        '=AND(B2="Sales",D2>=90)',

    "OR":
        '=OR(B2="Sales",B2="Finance")',

    "NOT":
        '=NOT(B2="Inactive")',

    "Nested IF":
        '=IF(D2>=90,"Excellent",IF(D2>=80,"Good","Needs Improvement"))',
}

for description, formula in formula_patterns.items():
    print(f"{description:30} -> {formula}")


# ============================================================================
# 64. STUDY CHECKLIST
# ============================================================================

print("\n" + "=" * 80)
print("STUDY CHECKLIST")
print("=" * 80)

checklist = [
    "Understand Excel ranges and criteria.",
    "Understand COUNTIF.",
    "Understand COUNTIFS.",
    "Understand SUMIF.",
    "Understand SUMIFS.",
    "Understand AVERAGEIF.",
    "Understand AVERAGEIFS.",
    "Use comparison operators correctly.",
    "Understand AND logic.",
    "Understand OR logic.",
    "Understand NOT logic.",
    "Understand nested IF logic.",
    "Handle empty results.",
    "Validate range alignment.",
    "Handle text and numeric data correctly.",
    "Understand wildcard criteria.",
    "Handle dates as criteria.",
    "Test boundary conditions.",
    "Avoid double counting with OR logic.",
    "Design auditable formulas.",
    "Consider performance for large datasets.",
    "Validate business-critical calculations.",
]

for index, item in enumerate(checklist, start=1):
    print(f"{index:2}. {item}")


# ============================================================================
# 65. END-TO-END ASSERTIONS
# ============================================================================

print("\n" + "=" * 80)
print("END-TO-END ASSERTIONS")
print("=" * 80)

assert sales_count == 4
assert sales_total == 487000
assert sales_north == 2
assert sales_north_high_total == 175000
assert high_performers == 3
assert north_count == 4
assert north_and_high == 2

print("Core COUNTIF/COUNTIFS assertions: PASSED")
print("Core SUMIF/SUMIFS assertions: PASSED")
print("Logical-condition assertions: PASSED")
print("The complete conditional-analysis study script executed successfully.")
