"""
EXCEL FORMULAS: FUNDAMENTALS TO ADVANCED PRACTICE
=================================================

Topic:
SUM, AVERAGE, MIN, MAX, COUNT, COUNTA, ROUND, IF, IFS, AND, OR, NOT

This standalone Python study script models important Excel formula concepts
using Python so that the logic can be executed, inspected, compared, and tested.

The examples progress from:
1. Spreadsheet fundamentals
2. Aggregation formulas
3. Counting formulas
4. Rounding
5. Conditional logic
6. Combining logical functions
7. Nested and progressively complex formulas
8. Error and edge-case behavior
9. Practical business examples
10. Formula design, debugging, performance, and production considerations

Important:
Excel and Python are different languages. The functions below intentionally
model common Excel behavior rather than pretending that Python syntax is Excel
syntax. Excel formula examples are shown in comments and strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from math import isnan
from typing import Any, Iterable, Sequence


# =============================================================================
# 1. SPREADSHEET FUNDAMENTALS
# =============================================================================

"""
An Excel worksheet is organized into:
- Workbooks
- Worksheets
- Rows
- Columns
- Cells
- Cell references
- Ranges

Examples of Excel references:
    A1       -> column A, row 1
    B5       -> column B, row 5
    A1:A10   -> vertical range
    A1:D10   -> rectangular range

A formula normally begins with "=".

Examples:
    =SUM(B2:B10)
    =AVERAGE(C2:C10)
    =IF(D2>=50,"Pass","Fail")

Excel formulas can use:
- Constants: =10+5
- Cell references: =A1+B1
- Ranges: =SUM(A1:A10)
- Functions: =SUM(A1:A10)
- Operators: =A1*B1
- Logical expressions: =A1>=50

The Python examples below represent spreadsheet cells as ordinary values.
"""

sales = [1200, 1500, 1800, 900, 2100]

print("=" * 80)
print("EXCEL FORMULAS: FUNDAMENTALS")
print("=" * 80)

print("\nExample data:")
print(sales)

print("\nEquivalent Excel formula:")
print("=SUM(B2:B6)")


# =============================================================================
# 2. RANGE AND VALUE NORMALIZATION
# =============================================================================

def flatten_values(values: Any) -> list[Any]:
    """
    Flatten nested Python lists/tuples into a single list.

    This makes demonstrations such as:
        excel_sum([10, 20], [30, 40])
    possible.

    Excel ranges are naturally two-dimensional, while the educational examples
    here use Python sequences for simplicity.
    """
    result: list[Any] = []

    if isinstance(values, (list, tuple)):
        for item in values:
            result.extend(flatten_values(item))
    else:
        result.append(values)

    return result


def is_excel_number(value: Any) -> bool:
    """
    Approximate the numeric values accepted by the formulas in this lesson.

    bool is deliberately excluded because Python treats True and False as
    integers, while spreadsheet logic distinguishes Boolean values from
    ordinary numeric cells in many formula contexts.
    """
    return (
        isinstance(value, (int, float, Decimal))
        and not isinstance(value, bool)
        and not (isinstance(value, float) and isnan(value))
    )


def numeric_values(values: Any) -> list[int | float | Decimal]:
    """Return numeric values from a sequence."""
    return [value for value in flatten_values(values) if is_excel_number(value)]


# =============================================================================
# 3. SUM
# =============================================================================

def excel_sum(*values: Any) -> int | float | Decimal:
    """
    Educational model of Excel SUM.

    Excel:
        =SUM(A1:A5)
        =SUM(A1:A5,C1:C5)
        =SUM(10,20,30)

    Important ideas:
    - SUM adds numeric values.
    - Multiple arguments can be supplied.
    - Text encountered inside a referenced range is generally ignored.
    - Boolean behavior depends on whether the Boolean is directly supplied or
      comes from a reference. This educational implementation intentionally
      keeps the model simple and ignores Boolean values.
    """
    numbers = numeric_values(values)

    if not numbers:
        return 0

    total = numbers[0]
    for number in numbers[1:]:
        total += number

    return total


print("\n" + "-" * 80)
print("SUM")
print("-" * 80)

monthly_sales = [10000, 12000, 9500, 11000, 13000]

print("Monthly sales:", monthly_sales)
print("Python result:", excel_sum(monthly_sales))
print("Excel formula: =SUM(B2:B6)")

print("\nMultiple ranges:")
north_region = [100, 200, 300]
south_region = [150, 250, 350]

print("Excel formula: =SUM(B2:B4,D2:D4)")
print("Python result:", excel_sum(north_region, south_region))

mixed_values = [100, "N/A", 200, None, 300]
print("\nMixed values:", mixed_values)
print("SUM-style result:", excel_sum(mixed_values))


# =============================================================================
# 4. AVERAGE
# =============================================================================

def excel_average(*values: Any) -> float:
    """
    Educational model of Excel AVERAGE.

    Excel:
        =AVERAGE(B2:B6)

    AVERAGE calculates:
        sum of numeric values / count of numeric values

    Text and blank-like values are ignored in the simplified range model.
    """
    numbers = numeric_values(values)

    if not numbers:
        raise ValueError("AVERAGE requires at least one numeric value.")

    return float(sum(numbers) / len(numbers))


print("\n" + "-" * 80)
print("AVERAGE")
print("-" * 80)

marks = [78, 85, 91, 66, 80]

print("Marks:", marks)
print("Python result:", excel_average(marks))
print("Excel formula: =AVERAGE(B2:B6)")

print("\nAVERAGE relationship:")
print("SUM =", excel_sum(marks))
print("COUNT =", len(numeric_values(marks)))
print("SUM / COUNT =", excel_sum(marks) / len(numeric_values(marks)))

try:
    print(excel_average(["N/A", None]))
except ValueError as error:
    print("Empty numeric set:", error)


# =============================================================================
# 5. MIN
# =============================================================================

def excel_min(*values: Any) -> int | float | Decimal:
    """
    Educational model of Excel MIN.

    Excel:
        =MIN(B2:B10)

    MIN returns the smallest numeric value.
    """
    numbers = numeric_values(values)

    if not numbers:
        raise ValueError("MIN requires at least one numeric value.")

    return min(numbers)


print("\n" + "-" * 80)
print("MIN")
print("-" * 80)

temperatures = [32, 28, 35, 25, 31]

print("Temperatures:", temperatures)
print("Minimum:", excel_min(temperatures))
print("Excel formula: =MIN(B2:B6)")


# =============================================================================
# 6. MAX
# =============================================================================

def excel_max(*values: Any) -> int | float | Decimal:
    """
    Educational model of Excel MAX.

    Excel:
        =MAX(B2:B10)

    MAX returns the largest numeric value.
    """
    numbers = numeric_values(values)

    if not numbers:
        raise ValueError("MAX requires at least one numeric value.")

    return max(numbers)


print("\n" + "-" * 80)
print("MAX")
print("-" * 80)

temperatures = [32, 28, 35, 25, 31]

print("Temperatures:", temperatures)
print("Maximum:", excel_max(temperatures))
print("Excel formula: =MAX(B2:B6)")


# =============================================================================
# 7. COUNT
# =============================================================================

def excel_count(*values: Any) -> int:
    """
    Educational model of Excel COUNT.

    Excel:
        =COUNT(A1:A10)

    COUNT counts numeric values.

    It does not count:
    - Text
    - Blank cells
    - Ordinary logical values in referenced cells
    """
    return len(numeric_values(values))


print("\n" + "-" * 80)
print("COUNT")
print("-" * 80)

employee_data = [101, "Rahul", 45000, None, 55000, "Pending", 62000]

print("Data:", employee_data)
print("COUNT-style result:", excel_count(employee_data))
print("Excel formula: =COUNT(A2:A8)")


# =============================================================================
# 8. COUNTA
# =============================================================================

def excel_counta(*values: Any) -> int:
    """
    Educational model of Excel COUNTA.

    Excel:
        =COUNTA(A1:A10)

    COUNTA counts non-empty values.

    It can count:
    - Numbers
    - Text
    - TRUE/FALSE
    - Error values
    - Other non-empty cell contents

    A truly empty cell is not counted.
    """
    flattened = flatten_values(values)
    return sum(value is not None for value in flattened)


print("\n" + "-" * 80)
print("COUNTA")
print("-" * 80)

survey_responses = [
    "Yes",
    "No",
    None,
    "Yes",
    42,
    False,
    "",
]

print("Data:", survey_responses)
print("COUNTA-style result:", excel_counta(survey_responses))
print("Excel formula: =COUNTA(A2:A8)")

print("\nCOUNT versus COUNTA:")
print("COUNT :", excel_count(survey_responses))
print("COUNTA:", excel_counta(survey_responses))

print(
    "\nImportant Excel distinction: an empty-looking formula result such as "
    '="" is not necessarily equivalent to a genuinely empty cell for every '
    "counting operation."
)


# =============================================================================
# 9. ROUND
# =============================================================================

def excel_round(number: float | int | Decimal, digits: int = 0) -> int | float:
    """
    Educational model of Excel ROUND using decimal arithmetic.

    Excel:
        =ROUND(A1,2)
        =ROUND(A1,0)
        =ROUND(A1,-1)

    Positive digits:
        ROUND(123.456, 2) -> 123.46

    Zero digits:
        ROUND(123.456, 0) -> 123

    Negative digits:
        ROUND(123.456, -1) -> 120

    Decimal ROUND_HALF_UP is used because spreadsheet-style decimal rounding
    is easier to reason about than Python's built-in banker's rounding.
    """
    try:
        decimal_number = Decimal(str(number))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("ROUND requires a numeric value.") from error

    if digits >= 0:
        quantizer = Decimal("1").scaleb(-digits)
    else:
        quantizer = Decimal("1").scaleb(-digits)

    rounded = decimal_number.quantize(quantizer, rounding=ROUND_HALF_UP)

    if digits == 0:
        return int(rounded)

    return float(rounded)


print("\n" + "-" * 80)
print("ROUND")
print("-" * 80)

amount = 1234.56789

print("Original:", amount)
print("2 decimals:", excel_round(amount, 2))
print("0 decimals:", excel_round(amount, 0))
print("-1 digit:", excel_round(amount, -1))

print("\nExcel formulas:")
print("=ROUND(A1,2)")
print("=ROUND(A1,0)")
print("=ROUND(A1,-1)")

print("\nImportant:")
print("ROUND(2.675, 2) in Python's normal float arithmetic can expose")
print("binary floating-point behavior. Decimal arithmetic is useful when")
print("teaching financial and decimal rounding concepts.")


# =============================================================================
# 10. IF
# =============================================================================

def excel_if(
    condition: bool,
    value_if_true: Any,
    value_if_false: Any,
) -> Any:
    """
    Educational model of Excel IF.

    Excel:
        =IF(B2>=50,"Pass","Fail")

    IF has three conceptual parts:
        IF(condition, value_if_true, value_if_false)
    """
    return value_if_true if condition else value_if_false


print("\n" + "-" * 80)
print("IF")
print("-" * 80)

score = 72

result = excel_if(score >= 50, "Pass", "Fail")

print("Score:", score)
print("Result:", result)
print('Excel formula: =IF(B2>=50,"Pass","Fail")')


# =============================================================================
# 11. IF WITH NUMERIC RESULTS
# =============================================================================

sales_amount = 125000
target = 100000

bonus = excel_if(sales_amount >= target, 10000, 0)

print("\nNumeric IF result:")
print("Sales:", sales_amount)
print("Target:", target)
print("Bonus:", bonus)
print("Excel formula: =IF(B2>=C2,10000,0)")


# =============================================================================
# 12. IF WITH TEXT
# =============================================================================

attendance_percentage = 91

attendance_status = excel_if(
    attendance_percentage >= 75,
    "Eligible",
    "Not Eligible",
)

print("\nText classification:")
print("Attendance:", attendance_percentage)
print("Status:", attendance_status)
print('Excel formula: =IF(B2>=75,"Eligible","Not Eligible")')


# =============================================================================
# 13. IFS
# =============================================================================

def excel_ifs(*condition_result_pairs: tuple[bool, Any]) -> Any:
    """
    Educational model of Excel IFS.

    Excel:
        =IFS(
            B2>=90,"A",
            B2>=80,"B",
            B2>=70,"C",
            B2>=60,"D",
            TRUE,"F"
        )

    IFS evaluates conditions from left to right and returns the result
    associated with the first TRUE condition.

    Unlike IF, IFS does not require a traditional third argument for a default
    branch. A final TRUE condition is commonly used as a fallback.
    """
    for condition, result in condition_result_pairs:
        if condition:
            return result

    raise ValueError("IFS found no TRUE condition.")


print("\n" + "-" * 80)
print("IFS")
print("-" * 80)

score = 87

grade = excel_ifs(
    (score >= 90, "A"),
    (score >= 80, "B"),
    (score >= 70, "C"),
    (score >= 60, "D"),
    (True, "F"),
)

print("Score:", score)
print("Grade:", grade)

print("\nExcel equivalent:")
print(
    '=IFS(B2>=90,"A",B2>=80,"B",B2>=70,"C",'
    'B2>=60,"D",TRUE,"F")'
)

print("\nCondition order matters:")
score = 95

bad_order = excel_ifs(
    (score >= 60, "D"),
    (score >= 80, "B"),
    (score >= 90, "A"),
)

correct_order = excel_ifs(
    (score >= 90, "A"),
    (score >= 80, "B"),
    (score >= 60, "D"),
)

print("Bad ordering:", bad_order)
print("Correct ordering:", correct_order)


# =============================================================================
# 14. AND
# =============================================================================

def excel_and(*conditions: Any) -> bool:
    """
    Educational model of Excel AND.

    Excel:
        =AND(B2>=50,C2>=75)

    AND returns TRUE only when every supplied condition is TRUE.

    Important spreadsheet idea:
        AND = all requirements must be satisfied.
    """
    if not conditions:
        return True

    return all(bool(condition) for condition in conditions)


print("\n" + "-" * 80)
print("AND")
print("-" * 80)

score = 82
attendance = 88

eligible = excel_and(
    score >= 50,
    attendance >= 75,
)

print("Score:", score)
print("Attendance:", attendance)
print("Eligible:", eligible)
print("Excel formula: =AND(B2>=50,C2>=75)")


# =============================================================================
# 15. OR
# =============================================================================

def excel_or(*conditions: Any) -> bool:
    """
    Educational model of Excel OR.

    Excel:
        =OR(B2="Manager",B2="Director")

    OR returns TRUE when at least one condition is TRUE.

    Important spreadsheet idea:
        OR = any acceptable requirement can be satisfied.
    """
    if not conditions:
        return False

    return any(bool(condition) for condition in conditions)


print("\n" + "-" * 80)
print("OR")
print("-" * 80)

department = "Finance"
role = "Analyst"

has_priority_access = excel_or(
    department == "IT",
    role == "Manager",
)

print("Department:", department)
print("Role:", role)
print("Priority access:", has_priority_access)
print('Excel formula: =OR(B2="IT",C2="Manager")')


# =============================================================================
# 16. NOT
# =============================================================================

def excel_not(condition: Any) -> bool:
    """
    Educational model of Excel NOT.

    Excel:
        =NOT(B2="Closed")

    NOT reverses TRUE to FALSE and FALSE to TRUE.
    """
    return not bool(condition)


print("\n" + "-" * 80)
print("NOT")
print("-" * 80)

status = "Open"

is_not_closed = excel_not(status == "Closed")

print("Status:", status)
print("Not closed:", is_not_closed)
print('Excel formula: =NOT(B2="Closed")')


# =============================================================================
# 17. COMBINING IF + AND
# =============================================================================

print("\n" + "-" * 80)
print("IF + AND")
print("-" * 80)

score = 78
attendance = 82

passed = excel_if(
    excel_and(score >= 50, attendance >= 75),
    "Pass",
    "Fail",
)

print("Score:", score)
print("Attendance:", attendance)
print("Result:", passed)

print(
    'Excel formula: =IF(AND(B2>=50,C2>=75),"Pass","Fail")'
)


# =============================================================================
# 18. COMBINING IF + OR
# =============================================================================

print("\n" + "-" * 80)
print("IF + OR")
print("-" * 80)

role = "Manager"
department = "Sales"

special_access = excel_if(
    excel_or(role == "Manager", department == "Security"),
    "Allowed",
    "Denied",
)

print("Role:", role)
print("Department:", department)
print("Access:", special_access)

print(
    'Excel formula: =IF(OR(B2="Manager",C2="Security"),"Allowed","Denied")'
)


# =============================================================================
# 19. IF + NOT
# =============================================================================

print("\n" + "-" * 80)
print("IF + NOT")
print("-" * 80)

account_status = "Active"

message = excel_if(
    excel_not(account_status == "Suspended"),
    "Account can operate",
    "Account blocked",
)

print("Status:", account_status)
print("Message:", message)

print(
    'Excel formula: =IF(NOT(B2="Suspended"),'
    '"Account can operate","Account blocked")'
)


# =============================================================================
# 20. AND + OR + NOT TOGETHER
# =============================================================================

print("\n" + "-" * 80)
print("COMBINED LOGIC")
print("-" * 80)

age = 28
has_experience = True
has_degree = True
is_blacklisted = False

eligible = excel_and(
    age >= 21,
    excel_or(has_experience, has_degree),
    excel_not(is_blacklisted),
)

print("Age:", age)
print("Experience:", has_experience)
print("Degree:", has_degree)
print("Blacklisted:", is_blacklisted)
print("Eligible:", eligible)

print(
    "Excel formula concept:"
)
print(
    "=AND(B2>=21,OR(C2=TRUE,D2=TRUE),NOT(E2=TRUE))"
)


# =============================================================================
# 21. NESTED IF
# =============================================================================

def nested_grade(score: float) -> str:
    """
    Python representation of a nested IF decision tree.

    Equivalent Excel concept:
        =IF(B2>=90,"A",
            IF(B2>=80,"B",
                IF(B2>=70,"C",
                    IF(B2>=60,"D","F")
                )
            )
        )

    IFS is often easier to read when there are many independent thresholds.
    """
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


print("\n" + "-" * 80)
print("NESTED IF")
print("-" * 80)

for test_score in [95, 84, 73, 61, 42]:
    print(test_score, "->", nested_grade(test_score))


# =============================================================================
# 22. WHEN TO USE IF VERSUS IFS
# =============================================================================

print("\n" + "-" * 80)
print("IF VERSUS IFS")
print("-" * 80)

print(
    """
IF is especially suitable for:
- One binary decision
- A simple TRUE/FALSE classification
- A small number of nested conditions

IFS is especially suitable for:
- Several mutually exclusive categories
- Threshold-based grading
- Multi-level classifications
- Replacing deeply nested IF expressions

Example:
    =IF(B2>=50,"Pass","Fail")

Compared with:
    =IFS(B2>=90,"A",B2>=80,"B",B2>=70,"C",TRUE,"F")
"""
)


# =============================================================================
# 23. PRACTICAL SALES ANALYSIS
# =============================================================================

print("\n" + "-" * 80)
print("PRACTICAL SALES ANALYSIS")
print("-" * 80)

sales_data = [12500, 18000, 14250, 9800, 22000, 16500]

total_sales = excel_sum(sales_data)
average_sales = excel_average(sales_data)
minimum_sales = excel_min(sales_data)
maximum_sales = excel_max(sales_data)
sales_count = excel_count(sales_data)

print("Sales:", sales_data)
print("Total:", total_sales)
print("Average:", excel_round(average_sales, 2))
print("Minimum:", minimum_sales)
print("Maximum:", maximum_sales)
print("Number of observations:", sales_count)

print("\nExcel formulas:")
print("=SUM(B2:B7)")
print("=AVERAGE(B2:B7)")
print("=MIN(B2:B7)")
print("=MAX(B2:B7)")
print("=COUNT(B2:B7)")


# =============================================================================
# 24. PRACTICAL EMPLOYEE PERFORMANCE ANALYSIS
# =============================================================================

@dataclass
class Employee:
    """Simple representation of an employee record."""

    name: str
    sales: float
    attendance: float
    rating: float
    active: bool


employees = [
    Employee("Asha", 125000, 96, 4.8, True),
    Employee("Bharat", 85000, 91, 4.1, True),
    Employee("Charu", 150000, 88, 4.7, True),
    Employee("Dev", 60000, 72, 3.2, False),
    Employee("Esha", 110000, 95, 4.4, True),
]

print("\n" + "-" * 80)
print("EMPLOYEE PERFORMANCE ANALYSIS")
print("-" * 80)

for employee in employees:
    eligible_for_bonus = excel_and(
        employee.sales >= 100000,
        employee.attendance >= 90,
        employee.rating >= 4.0,
        employee.active,
    )

    performance_band = excel_ifs(
        (employee.sales >= 140000, "Exceptional"),
        (employee.sales >= 100000, "Strong"),
        (employee.sales >= 75000, "Developing"),
        (True, "Needs Improvement"),
    )

    print(
        employee.name,
        "| Bonus:", eligible_for_bonus,
        "| Performance:", performance_band,
    )

print(
    "\nExcel formula concept for bonus:"
)
print(
    '=IF(AND(B2>=100000,C2>=90,D2>=4,E2=TRUE),'
    '"Eligible","Not Eligible")'
)


# =============================================================================
# 25. PRACTICAL STUDENT RESULT SYSTEM
# =============================================================================

@dataclass
class Student:
    """Student performance record."""

    name: str
    mathematics: float
    science: float
    english: float
    attendance: float


students = [
    Student("Anil", 88, 91, 84, 92),
    Student("Bhavna", 72, 68, 75, 81),
    Student("Chetan", 45, 62, 58, 79),
    Student("Divya", 95, 94, 96, 97),
]

print("\n" + "-" * 80)
print("STUDENT RESULT SYSTEM")
print("-" * 80)

for student in students:
    subject_average = excel_average(
        student.mathematics,
        student.science,
        student.english,
    )

    all_subjects_pass = excel_and(
        student.mathematics >= 40,
        student.science >= 40,
        student.english >= 40,
    )

    attendance_eligible = student.attendance >= 75

    final_status = excel_if(
        excel_and(all_subjects_pass, attendance_eligible),
        "Pass",
        "Fail",
    )

    grade = excel_ifs(
        (subject_average >= 90, "A+"),
        (subject_average >= 80, "A"),
        (subject_average >= 70, "B"),
        (subject_average >= 60, "C"),
        (subject_average >= 50, "D"),
        (True, "F"),
    )

    print(
        f"{student.name}: average={excel_round(subject_average, 2)}, "
        f"grade={grade}, status={final_status}"
    )


# =============================================================================
# 26. EDGE CASES: SUM
# =============================================================================

print("\n" + "-" * 80)
print("EDGE CASES")
print("-" * 80)

print("\nSUM with no numeric values:")
print(excel_sum(["A", None, "B"]))

print("\nCOUNT with text and blanks:")
print(excel_count(["100", 100, None, "200", 200]))

print("\nCOUNTA with text, numbers, blanks, and Boolean:")
print(excel_counta(["100", 100, None, "200", 200, True, False]))


# =============================================================================
# 27. EDGE CASES: AVERAGE, MIN, MAX
# =============================================================================

def safe_average(values: Sequence[Any]) -> float | None:
    """
    Safe wrapper for AVERAGE.

    A worksheet design should explicitly decide what happens when no numeric
    observations exist instead of allowing an unhandled calculation error.
    """
    numbers = numeric_values(values)

    if not numbers:
        return None

    return excel_average(numbers)


def safe_min(values: Sequence[Any]) -> int | float | Decimal | None:
    """Safe wrapper for MIN."""
    numbers = numeric_values(values)
    return min(numbers) if numbers else None


def safe_max(values: Sequence[Any]) -> int | float | Decimal | None:
    """Safe wrapper for MAX."""
    numbers = numeric_values(values)
    return max(numbers) if numbers else None


empty_dataset: list[Any] = []

print("\nEmpty dataset:")
print("AVERAGE:", safe_average(empty_dataset))
print("MIN:", safe_min(empty_dataset))
print("MAX:", safe_max(empty_dataset))


# =============================================================================
# 28. EDGE CASES: ROUND
# =============================================================================

print("\nROUND edge cases:")

rounding_examples = [
    (12.345, 2),
    (12.344, 2),
    (12.5, 0),
    (13.5, 0),
    (1234.0, -2),
    (1250.0, -2),
]

for number, digits in rounding_examples:
    print(
        f"ROUND({number}, {digits}) -> "
        f"{excel_round(number, digits)}"
    )


# =============================================================================
# 29. LOGICAL TRUTH TABLES
# =============================================================================

print("\n" + "-" * 80)
print("LOGICAL TRUTH TABLES")
print("-" * 80)

print("\nA     B     AND    OR")
for a in [False, True]:
    for b in [False, True]:
        print(
            f"{str(a):5} {str(b):5} "
            f"{str(excel_and(a, b)):6} "
            f"{str(excel_or(a, b)):5}"
        )

print("\nA     NOT(A)")
for a in [False, True]:
    print(f"{str(a):5} {str(excel_not(a))}")


# =============================================================================
# 30. BOOLEAN ALGEBRA INTERPRETATION
# =============================================================================

print("\n" + "-" * 80)
print("BOOLEAN LOGIC")
print("-" * 80)

print(
    """
AND:
    TRUE only when every requirement is true.

OR:
    TRUE when at least one requirement is true.

NOT:
    Reverses a logical result.

Common translation:
    AND -> all conditions required
    OR  -> any condition acceptable
    NOT -> exclude or reverse a condition

Example business rule:
    A customer receives a discount when:
        order >= 5000
        AND customer is active
        AND customer is not blocked

Conceptual Excel formula:
    =IF(
        AND(
            B2>=5000,
            C2="Active",
            NOT(D2="Blocked")
        ),
        "Discount",
        "No Discount"
    )
"""
)


# =============================================================================
# 31. COMBINING AGGREGATION WITH LOGIC
# =============================================================================

print("\n" + "-" * 80)
print("AGGREGATION + LOGIC")
print("-" * 80)

quarterly_sales = [125000, 145000, 98000, 160000]

total = excel_sum(quarterly_sales)
average = excel_average(quarterly_sales)
best_quarter = excel_max(quarterly_sales)
worst_quarter = excel_min(quarterly_sales)

target = 500000

target_status = excel_if(
    total >= target,
    "Target Achieved",
    "Target Missed",
)

print("Quarterly sales:", quarterly_sales)
print("Total:", total)
print("Average:", excel_round(average, 2))
print("Best quarter:", best_quarter)
print("Worst quarter:", worst_quarter)
print("Target status:", target_status)

print("\nExcel concepts:")
print("=SUM(B2:E2)")
print("=AVERAGE(B2:E2)")
print("=MAX(B2:E2)")
print("=MIN(B2:E2)")
print('=IF(SUM(B2:E2)>=500000,"Target Achieved","Target Missed")')


# =============================================================================
# 32. VALIDATING DATA BEFORE CALCULATION
# =============================================================================

def validate_numeric_dataset(
    values: Sequence[Any],
    minimum_allowed: float | None = None,
    maximum_allowed: float | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate a numeric dataset before applying spreadsheet-style calculations.

    Validation matters because formulas can be mathematically correct while
    the underlying data is invalid.
    """
    errors: list[str] = []

    for index, value in enumerate(values, start=1):
        if not is_excel_number(value):
            errors.append(f"Position {index}: non-numeric value {value!r}")

        if is_excel_number(value):
            if minimum_allowed is not None and value < minimum_allowed:
                errors.append(
                    f"Position {index}: {value} is below {minimum_allowed}"
                )

            if maximum_allowed is not None and value > maximum_allowed:
                errors.append(
                    f"Position {index}: {value} exceeds {maximum_allowed}"
                )

    return not errors, errors


print("\n" + "-" * 80)
print("DATA VALIDATION")
print("-" * 80)

raw_scores = [88, 92, 105, 74, "Missing", -4]

valid, validation_errors = validate_numeric_dataset(
    raw_scores,
    minimum_allowed=0,
    maximum_allowed=100,
)

print("Valid:", valid)

for error in validation_errors:
    print("Error:", error)


# =============================================================================
# 33. SAFE CONDITIONAL CALCULATION
# =============================================================================

def performance_label(
    sales: float,
    attendance: float,
    rating: float,
) -> str:
    """
    More production-oriented business rule.

    Priority:
    1. Invalid values are rejected by validation assumptions.
    2. Strong performance requires all three thresholds.
    3. Good performance requires sales and either attendance or rating.
    4. Otherwise performance is classified as developing.
    """
    if sales < 0 or not 0 <= attendance <= 100 or not 0 <= rating <= 5:
        return "Invalid Data"

    strong = excel_and(
        sales >= 100000,
        attendance >= 90,
        rating >= 4,
    )

    good = excel_and(
        sales >= 80000,
        excel_or(attendance >= 85, rating >= 3.5),
    )

    return excel_ifs(
        (strong, "Strong"),
        (good, "Good"),
        (True, "Developing"),
    )


print("\n" + "-" * 80)
print("COMPLEX BUSINESS RULE")
print("-" * 80)

test_employees = [
    ("Employee A", 125000, 95, 4.7),
    ("Employee B", 90000, 82, 4.0),
    ("Employee C", 50000, 70, 3.1),
    ("Employee D", -100, 110, 8),
]

for name, sales, attendance, rating in test_employees:
    print(
        name,
        "->",
        performance_label(sales, attendance, rating),
    )


# =============================================================================
# 34. COMMON FORMULA MISTAKES
# =============================================================================

print("\n" + "-" * 80)
print("COMMON FORMULA MISTAKES")
print("-" * 80)

print(
    """
1. Forgetting the leading "="
   Correct:
       =SUM(B2:B10)

2. Selecting the wrong range
   Example:
       =SUM(B2:B10)
   may accidentally exclude B11.

3. Using COUNT when COUNTA is required
   COUNT counts numeric values.
   COUNTA counts non-empty values.

4. Dividing by zero conceptually
   AVERAGE requires numeric observations.

5. Incorrect IF nesting
   Complex nested IF formulas can become difficult to maintain.

6. Incorrect IFS order
   Conditions are evaluated from left to right.
   A broad condition placed before a specific condition can prevent the
   specific condition from ever being reached.

7. Confusing AND and OR
   AND means every condition.
   OR means at least one condition.

8. Forgetting NOT reverses a condition
   NOT(TRUE) = FALSE
   NOT(FALSE) = TRUE

9. Rounding too early
   Rounding intermediate values can change final results.
   Keep full precision internally when appropriate and round the final
   presentation value unless business rules explicitly require intermediate
   rounding.

10. Treating formatting as data
    Currency formatting, percentage formatting, and decimal display do not
    necessarily change the underlying numeric value.

11. Ignoring blanks and text
    The behavior of functions depends on whether values are genuinely blank,
    text, numbers, logical values, or errors.

12. Building formulas that are harder to audit than necessary
    A shorter formula is not automatically a better formula.
"""
)


# =============================================================================
# 35. PERFORMANCE CONSIDERATIONS
# =============================================================================

print("\n" + "-" * 80)
print("PERFORMANCE CONSIDERATIONS")
print("-" * 80)

print(
    """
For ordinary spreadsheets, these functions are inexpensive. Performance
becomes important when formulas are copied across very large datasets or
when formulas depend on many other calculations.

Practical considerations:

- Avoid unnecessarily huge ranges.
  Prefer:
      =SUM(B2:B5000)
  over:
      =SUM(B:B)
  when the entire column is not required.

- Avoid repeating expensive calculations.
  If the same logical or aggregation result is needed multiple times, consider
  storing it in a helper cell or using an appropriate structured formula.

- Keep worksheets logically organized.
  Clear input, calculation, and output areas make recalculation dependencies
  easier to understand.

- Use tables and structured references where appropriate.
  They can make formulas easier to maintain when rows are added.

- Avoid excessive nested logic.
  A long nested IF can become difficult to audit and maintain.

- Use IFS when a multi-level decision is naturally expressed as ordered
  conditions.

- Avoid unnecessary rounding operations.
  Rounding every intermediate calculation may add complexity and produce
  different results from calculations performed at full precision.
"""
)


# =============================================================================
# 36. SECURITY AND DATA-INTEGRITY CONSIDERATIONS
# =============================================================================

print("\n" + "-" * 80)
print("SECURITY AND DATA INTEGRITY")
print("-" * 80)

print(
    """
Formula correctness is only one part of spreadsheet reliability.

Important controls include:

- Validate input data before calculations.
- Protect cells containing formulas when appropriate.
- Separate raw inputs from calculated outputs.
- Restrict editing of important calculation cells.
- Use consistent data validation rules.
- Audit formulas in financial and operational workbooks.
- Be careful when importing external data.
- Do not assume a displayed number is trustworthy merely because a formula
  produced it.
- Preserve the distinction between missing, zero, text, and invalid data.
- Document business rules when formulas implement financial, compliance,
  payroll, grading, or eligibility decisions.

A formula can be syntactically valid and still implement the wrong business
rule. Data governance and formula auditing therefore matter as much as syntax.
"""
)


# =============================================================================
# 37. FORMULA AUDITING EXAMPLE
# =============================================================================

@dataclass
class FormulaAudit:
    """Represents a simple audit record for a business rule."""

    formula_name: str
    purpose: str
    inputs: list[str]
    rule: str


audit_records = [
    FormulaAudit(
        formula_name="Total Sales",
        purpose="Calculate total sales",
        inputs=["B2:B13"],
        rule="SUM all numeric sales values",
    ),
    FormulaAudit(
        formula_name="Average Sales",
        purpose="Calculate average sales",
        inputs=["B2:B13"],
        rule="AVERAGE numeric sales values",
    ),
    FormulaAudit(
        formula_name="Bonus Eligibility",
        purpose="Determine whether employee qualifies",
        inputs=["Sales", "Attendance", "Rating"],
        rule="All required thresholds must be satisfied",
    ),
]

print("\n" + "-" * 80)
print("FORMULA AUDIT")
print("-" * 80)

for record in audit_records:
    print(f"\nFormula: {record.formula_name}")
    print(f"Purpose: {record.purpose}")
    print(f"Inputs: {', '.join(record.inputs)}")
    print(f"Rule: {record.rule}")


# =============================================================================
# 38. TESTING FORMULA LOGIC
# =============================================================================

def assert_equal(actual: Any, expected: Any, description: str) -> None:
    """
    Small testing helper.

    Formula logic should be tested with normal cases, boundary values, and
    invalid inputs.
    """
    if actual != expected:
        raise AssertionError(
            f"{description}: expected {expected!r}, got {actual!r}"
        )

    print("PASS:", description)


print("\n" + "-" * 80)
print("FORMULA TESTS")
print("-" * 80)

assert_equal(
    excel_sum([10, 20, 30]),
    60,
    "SUM basic calculation",
)

assert_equal(
    excel_average([10, 20, 30]),
    20.0,
    "AVERAGE basic calculation",
)

assert_equal(
    excel_min([5, 2, 9]),
    2,
    "MIN basic calculation",
)

assert_equal(
    excel_max([5, 2, 9]),
    9,
    "MAX basic calculation",
)

assert_equal(
    excel_count([1, "2", 3, None]),
    2,
    "COUNT ignores text and blanks",
)

assert_equal(
    excel_counta([1, "2", 3, None]),
    3,
    "COUNTA counts non-empty values",
)

assert_equal(
    excel_round(12.345, 2),
    12.35,
    "ROUND to two decimals",
)

assert_equal(
    excel_if(10 > 5, "Yes", "No"),
    "Yes",
    "IF true branch",
)

assert_equal(
    excel_if(10 < 5, "Yes", "No"),
    "No",
    "IF false branch",
)

assert_equal(
    excel_ifs(
        (False, "First"),
        (True, "Second"),
        (True, "Third"),
    ),
    "Second",
    "IFS returns first true condition",
)

assert_equal(
    excel_and(True, True, True),
    True,
    "AND all true",
)

assert_equal(
    excel_and(True, False, True),
    False,
    "AND with false condition",
)

assert_equal(
    excel_or(False, False, True),
    True,
    "OR with one true condition",
)

assert_equal(
    excel_or(False, False, False),
    False,
    "OR all false",
)

assert_equal(
    excel_not(True),
    False,
    "NOT true",
)

assert_equal(
    excel_not(False),
    True,
    "NOT false",
)


# =============================================================================
# 39. BOUNDARY TESTS
# =============================================================================

print("\n" + "-" * 80)
print("BOUNDARY TESTS")
print("-" * 80)

grade_boundaries = [59, 60, 69, 70, 79, 80, 89, 90, 100]

for score in grade_boundaries:
    print(score, "->", nested_grade(score))


print(
    "\nBoundary testing is especially important for formulas containing "
    ">=, >, <=, and < operators."
)


# =============================================================================
# 40. FORMULA DECISION MATRIX
# =============================================================================

print("\n" + "-" * 80)
print("FUNCTION SELECTION GUIDE")
print("-" * 80)

function_guide = {
    "SUM": "Add numeric values.",
    "AVERAGE": "Calculate arithmetic mean of numeric values.",
    "MIN": "Find the smallest numeric value.",
    "MAX": "Find the largest numeric value.",
    "COUNT": "Count numeric values.",
    "COUNTA": "Count non-empty values.",
    "ROUND": "Round a number to a specified number of digits.",
    "IF": "Return one result when a condition is true and another when false.",
    "IFS": "Return the result for the first true condition among multiple rules.",
    "AND": "Require every condition to be true.",
    "OR": "Require at least one condition to be true.",
    "NOT": "Reverse a logical condition.",
}

for function_name, purpose in function_guide.items():
    print(f"{function_name:8} -> {purpose}")


# =============================================================================
# 41. CONCEPTUAL COMPARISONS
# =============================================================================

print("\n" + "-" * 80)
print("IMPORTANT DISTINCTIONS")
print("-" * 80)

print(
    """
SUM vs AVERAGE
--------------
SUM answers:
    "What is the total?"

AVERAGE answers:
    "What is the typical arithmetic value?"

MIN vs MAX
----------
MIN answers:
    "What is the smallest value?"

MAX answers:
    "What is the largest value?"

COUNT vs COUNTA
---------------
COUNT:
    Counts numeric values.

COUNTA:
    Counts non-empty values.

IF vs IFS
---------
IF:
    Best for binary or relatively simple branching.

IFS:
    Best for several ordered conditions.

AND vs OR
---------
AND:
    Every condition must be TRUE.

OR:
    At least one condition must be TRUE.

NOT:
    Reverses the result.

ROUND vs DISPLAY FORMATTING
---------------------------
ROUND changes the calculated numeric result.

Formatting can change how a number is displayed without necessarily changing
its underlying value.

For example, displaying 123.456 as 123.46 is not necessarily the same as
rounding the stored calculation to 123.46.
"""
)


# =============================================================================
# 42. ADVANCED BUSINESS RULE
# =============================================================================

@dataclass
class LoanApplication:
    """Simplified loan application for demonstrating compound logic."""

    applicant_age: int
    monthly_income: float
    credit_score: int
    employment_years: float
    existing_default: bool


def loan_decision(application: LoanApplication) -> str:
    """
    Simplified educational decision engine.

    This is not a real lending model. It demonstrates how Excel-style logical
    formulas can express eligibility rules.

    Rule:
    - Applicant must be at least 21.
    - Income must be at least 50,000.
    - Credit score must be at least 700.
    - Employment must be at least 2 years.
    - Existing default must be false.

    A real financial system would require substantially more controls,
    regulatory logic, explainability, and risk modeling.
    """
    basic_eligibility = excel_and(
        application.applicant_age >= 21,
        application.monthly_income >= 50000,
        application.credit_score >= 700,
        application.employment_years >= 2,
        excel_not(application.existing_default),
    )

    if not basic_eligibility:
        return "Not Eligible"

    return "Eligible"


print("\n" + "-" * 80)
print("ADVANCED COMPOUND LOGIC EXAMPLE")
print("-" * 80)

applications = [
    LoanApplication(32, 85000, 760, 5, False),
    LoanApplication(25, 60000, 680, 3, False),
    LoanApplication(40, 90000, 780, 8, True),
]

for application in applications:
    print(loan_decision(application))

print(
    "\nExcel formula concept:"
)
print(
    '=IF(AND('
    'B2>=21,'
    'C2>=50000,'
    'D2>=700,'
    'E2>=2,'
    'NOT(F2=TRUE)'
    '),"Eligible","Not Eligible")'
)


# =============================================================================
# 43. ADVANCED ROUNDING: FINANCIAL EXAMPLE
# =============================================================================

print("\n" + "-" * 80)
print("FINANCIAL ROUNDING EXAMPLE")
print("-" * 80)

unit_price = Decimal("1999.99")
quantity = 3
tax_rate = Decimal("0.18")

subtotal = unit_price * quantity
tax = subtotal * tax_rate
grand_total = subtotal + tax

print("Unit price:", unit_price)
print("Quantity:", quantity)
print("Subtotal:", subtotal)
print("Tax:", excel_round(tax, 2))
print("Grand total:", excel_round(grand_total, 2))

print("\nExcel formula concepts:")
print("Subtotal: =B2*C2")
print("Tax: =ROUND(B3*D2,2)")
print("Grand total: =ROUND(B3+B4,2)")


# =============================================================================
# 44. HANDLING MISSING VALUES
# =============================================================================

print("\n" + "-" * 80)
print("MISSING VALUES")
print("-" * 80)

inventory = [100, 125, None, 80, None, 150]

print("Inventory:", inventory)
print("SUM:", excel_sum(inventory))
print("AVERAGE:", excel_average(inventory))
print("MIN:", excel_min(inventory))
print("MAX:", excel_max(inventory))
print("COUNT:", excel_count(inventory))
print("COUNTA:", excel_counta(inventory))

print(
    """
When working with real worksheets, determine what a blank means:

- Not entered yet
- Not applicable
- Zero
- Missing
- Unknown

These meanings are not interchangeable.

A blank representing "unknown" should not automatically be converted to zero,
because doing so can distort totals and averages.
"""
)


# =============================================================================
# 45. FORMULA COMPOSITION
# =============================================================================

print("\n" + "-" * 80)
print("FORMULA COMPOSITION")
print("-" * 80)

orders = [1200, 1500, 2200, 700, 3000, 1800]

average_order = excel_average(orders)

large_order_count = excel_count(
    [order if order >= 2000 else None for order in orders]
)

large_order_ratio = large_order_count / excel_count(orders)

classification = excel_ifs(
    (large_order_ratio >= 0.50, "High-value mix"),
    (large_order_ratio >= 0.25, "Moderate-value mix"),
    (True, "Low-value mix"),
)

print("Orders:", orders)
print("Average order:", excel_round(average_order, 2))
print("Orders >= 2000:", large_order_count)
print("Large-order ratio:", excel_round(large_order_ratio * 100, 2), "%")
print("Classification:", classification)

print(
    "\nExcel concept:"
)
print(
    '=COUNT(IF(B2:B7>=2000,B2:B7,""))'
)
print(
    "Note: exact Excel implementation depends on Excel version and formula "
    "design. Modern dynamic-array Excel differs from older array-formula "
    "behavior."
)


# =============================================================================
# 46. LIMITATIONS OF THE PYTHON MODEL
# =============================================================================

print("\n" + "-" * 80)
print("LIMITATIONS OF THIS EDUCATIONAL MODEL")
print("-" * 80)

print(
    """
This script demonstrates formula concepts rather than implementing the entire
Excel calculation engine.

Actual Excel has many additional behaviors involving:

- Cell references
- Absolute and relative references
- Mixed references
- Worksheet references
- Structured table references
- Date serial numbers
- Error values such as #N/A and #DIV/0!
- Text coercion rules
- Array calculations
- Dynamic arrays
- Calculation dependencies
- Volatile functions
- Locale-specific separators
- Number formatting
- Named ranges
- External workbook references

The functions here deliberately focus on the requested formula family:
SUM, AVERAGE, MIN, MAX, COUNT, COUNTA, ROUND, IF, IFS, AND, OR, and NOT.
"""
)


# =============================================================================
# 47. BEST-PRACTICE FORMULA DESIGN
# =============================================================================

print("\n" + "-" * 80)
print("BEST PRACTICES")
print("-" * 80)

print(
    """
1. Make formulas readable.
2. Keep business rules simple where possible.
3. Use consistent ranges.
4. Test boundary conditions.
5. Separate raw data from calculated fields.
6. Validate inputs.
7. Avoid accidental circular logic.
8. Avoid unnecessarily broad ranges.
9. Use absolute references when a threshold must remain fixed.
10. Use parentheses to make logical grouping explicit.
11. Prefer a clear IFS structure over deeply nested IF logic when appropriate.
12. Document important business rules.
13. Check whether blanks, text, zeros, and errors have different meanings.
14. Avoid premature rounding.
15. Audit critical formulas before relying on the workbook operationally.
"""
)


# =============================================================================
# 48. ABSOLUTE, RELATIVE, AND MIXED REFERENCE CONCEPTS
# =============================================================================

print("\n" + "-" * 80)
print("CELL REFERENCE CONCEPTS")
print("-" * 80)

print(
    """
Relative reference:
    A1

When copied, Excel adjusts the reference.

Absolute reference:
    $A$1

When copied, both the column and row remain fixed.

Mixed references:
    $A1
    A$1

Examples:

    =B2*$F$1

If B2 contains a sales value and F1 contains a commission rate, copying the
formula downward changes B2 to B3, B4, and so on, while $F$1 remains fixed.

This is essential when formulas apply a single fixed assumption to many rows.
"""
)


# =============================================================================
# 49. FORMULA ERROR PREVENTION
# =============================================================================

def safe_percentage(part: float, whole: float) -> float | None:
    """
    Prevent division-by-zero in a derived calculation.

    Excel users often handle equivalent situations with IF:

        =IF(B2=0,0,A2/B2)

    or an error-handling function in broader formula designs.
    """
    if whole == 0:
        return None

    return part / whole


print("\n" + "-" * 80)
print("ERROR PREVENTION")
print("-" * 80)

print("80 / 100:", safe_percentage(80, 100))
print("80 / 0:", safe_percentage(80, 0))

print(
    "\nExcel concept:"
)
print(
    '=IF(B2=0,0,A2/B2)'
)


# =============================================================================
# 50. FINAL INTEGRATED EXAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("FINAL INTEGRATED EXAMPLE")
print("=" * 80)

@dataclass
class Product:
    """Product record for an integrated spreadsheet-style analysis."""

    name: str
    sales: list[float]
    target: float
    active: bool


products = [
    Product("Product A", [12000, 15000, 18000], 40000, True),
    Product("Product B", [8000, 9000, 10000], 30000, True),
    Product("Product C", [20000, 21000, 22000], 50000, False),
    Product("Product D", [14000, 17000, 19000], 45000, True),
]


def analyze_product(product: Product) -> dict[str, Any]:
    """
    Integrated use of all requested formula concepts.

    Demonstrates:
    - SUM
    - AVERAGE
    - MIN
    - MAX
    - COUNT
    - COUNTA
    - ROUND
    - IF
    - IFS
    - AND
    - OR
    - NOT
    """
    total = excel_sum(product.sales)
    average = excel_average(product.sales)
    minimum = excel_min(product.sales)
    maximum = excel_max(product.sales)
    observations = excel_count(product.sales)
    populated = excel_counta(product.sales)

    target_ratio = total / product.target if product.target else 0

    target_status = excel_if(
        total >= product.target,
        "Achieved",
        "Missed",
    )

    performance = excel_ifs(
        (target_ratio >= 1.20, "Exceptional"),
        (target_ratio >= 1.00, "Strong"),
        (target_ratio >= 0.80, "Developing"),
        (True, "Needs Attention"),
    )

    operational_status = excel_if(
        excel_and(
            product.active,
            excel_or(
                total >= product.target,
                average >= 15000,
            ),
            excel_not(product.name == "Product C"),
        ),
        "Priority",
        "Standard",
    )

    return {
        "name": product.name,
        "total": total,
        "average": excel_round(average, 2),
        "minimum": minimum,
        "maximum": maximum,
        "count": observations,
        "counta": populated,
        "target_ratio_percent": excel_round(target_ratio * 100, 2),
        "target_status": target_status,
        "performance": performance,
        "operational_status": operational_status,
    }


for product in products:
    result = analyze_product(product)

    print(f"\n{result['name']}")
    print(f"  Total sales: {result['total']}")
    print(f"  Average sales: {result['average']}")
    print(f"  Minimum sale: {result['minimum']}")
    print(f"  Maximum sale: {result['maximum']}")
    print(f"  COUNT: {result['count']}")
    print(f"  COUNTA: {result['counta']}")
    print(f"  Target achievement: {result['target_ratio_percent']}%")
    print(f"  Target status: {result['target_status']}")
    print(f"  Performance: {result['performance']}")
    print(f"  Operational status: {result['operational_status']}")


# =============================================================================
# 51. FORMULA REFERENCE SHEET
# =============================================================================

print("\n" + "=" * 80)
print("EXCEL FORMULA REFERENCE SHEET")
print("=" * 80)

formula_reference = [
    ("SUM", "=SUM(B2:B10)", "Adds numeric values"),
    ("AVERAGE", "=AVERAGE(B2:B10)", "Calculates arithmetic mean"),
    ("MIN", "=MIN(B2:B10)", "Returns smallest numeric value"),
    ("MAX", "=MAX(B2:B10)", "Returns largest numeric value"),
    ("COUNT", "=COUNT(B2:B10)", "Counts numeric values"),
    ("COUNTA", "=COUNTA(B2:B10)", "Counts non-empty cells"),
    ("ROUND", "=ROUND(B2,2)", "Rounds to two decimal places"),
    ("IF", '=IF(B2>=50,"Pass","Fail")', "Two-way conditional decision"),
    ("IFS", '=IFS(B2>=90,"A",B2>=80,"B",TRUE,"F")', "Multiple conditions"),
    ("AND", "=AND(B2>=50,C2>=75)", "All conditions must be TRUE"),
    ("OR", '=OR(B2="Yes",C2="Yes")', "At least one condition TRUE"),
    ("NOT", '=NOT(B2="Closed")', "Reverses logical result"),
]

for function_name, syntax, purpose in formula_reference:
    print(f"{function_name:9} | {syntax:45} | {purpose}")


# =============================================================================
# 52. KEY CONCEPTS CHECK
# =============================================================================

print("\n" + "=" * 80)
print("KNOWLEDGE CHECK")
print("=" * 80)

knowledge_check = [
    "SUM answers a total-value question.",
    "AVERAGE answers an arithmetic-mean question.",
    "MIN finds the smallest numeric value.",
    "MAX finds the largest numeric value.",
    "COUNT counts numeric values.",
    "COUNTA counts non-empty values.",
    "ROUND changes the numeric result to a requested precision.",
    "IF implements a TRUE/FALSE branch.",
    "IFS evaluates conditions from left to right.",
    "AND requires all supplied conditions to be true.",
    "OR requires at least one supplied condition to be true.",
    "NOT reverses a logical result.",
    "Boundary conditions should be tested.",
    "Input quality affects formula reliability.",
]

for number, concept in enumerate(knowledge_check, start=1):
    print(f"{number:02}. {concept}")


# =============================================================================
# 53. SCRIPT COMPLETION
# =============================================================================

print("\n" + "=" * 80)
print("SCRIPT COMPLETED SUCCESSFULLY")
print("=" * 80)

print(
    """
The examples above provide executable demonstrations of the requested Excel
formula family and show how aggregation, counting, rounding, conditional
logic, and Boolean logic can be combined into practical spreadsheet rules.

The most important structural pattern is:

    DATA
      |
      v
    AGGREGATION
      |
      v
    LOGICAL TESTS
      |
      v
    CONDITIONAL RESULT
      |
      v
    VALIDATED BUSINESS OUTPUT

In Excel, these concepts are expressed through cell references and formulas.
In Python, the same logical ideas can be represented with functions, classes,
conditions, and tests.
"""
)
