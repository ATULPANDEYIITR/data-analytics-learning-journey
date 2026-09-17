"""
Advanced Excel: Dynamic Arrays, FILTER, SORT, UNIQUE, SEQUENCE, LET, and LAMBDA
===============================================================================

This standalone study script teaches the conceptual and algorithmic foundations
behind modern Excel dynamic-array formulas.

The script does not require Excel or third-party Python packages. It models
spreadsheet-style tables and implements Python equivalents of important
operations so that the behavior of the Excel functions can be observed
directly.

Excel concepts demonstrated:

    Dynamic arrays
    Spill behavior
    FILTER
    SORT
    UNIQUE
    SEQUENCE
    LET
    LAMBDA
    Composition of dynamic-array functions
    Boolean filtering
    Multi-column sorting
    Error and empty-result handling
    Reusable custom functions
    Performance considerations
    Common spreadsheet design mistakes

Important distinction:
Python implementations below demonstrate the underlying computational ideas.
They are not replacements for Excel's formula engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence
from collections import Counter
from functools import reduce
import math
import statistics


# =============================================================================
# 1. BEGINNER FOUNDATIONS
# =============================================================================

print("=" * 78)
print("ADVANCED EXCEL CONCEPT STUDY")
print("=" * 78)


def explain(title: str, text: str) -> None:
    """Print a compact educational explanation."""
    print(f"\n{title}")
    print("-" * len(title))
    print(text)


explain(
    "Dynamic arrays",
    """
A traditional spreadsheet formula often returned one value per cell.
Modern Excel can return an array of values from one formula.

The resulting values can automatically occupy neighboring cells. This is
called spilling.

For example, the Excel formula:

    =SEQUENCE(5)

conceptually produces:

    1
    2
    3
    4
    5

The important idea is that the formula exists in one cell while its result
occupies several cells.
""",
)


# =============================================================================
# 2. BASIC ARRAY REPRESENTATION
# =============================================================================

numbers = [10, 20, 30, 40, 50]

print("\nPython equivalent of an array:", numbers)
print("Number of elements:", len(numbers))
print("First element:", numbers[0])
print("Last element:", numbers[-1])


def spill_array(values: Sequence[Any]) -> list[Any]:
    """
    Simulate the values produced by a dynamic-array formula.

    Excel performs additional worksheet-level work such as checking whether
    the intended spill range is blocked. This simple function models only the
    resulting array.
    """
    return list(values)


print("\nSimulated spilled result:", spill_array(numbers))


# =============================================================================
# 3. SEQUENCE
# =============================================================================

explain(
    "SEQUENCE",
    """
Excel syntax:

    =SEQUENCE(rows, [columns], [start], [step])

It generates a predictable numeric array.

Examples:

    =SEQUENCE(5)
    =SEQUENCE(3, 2)
    =SEQUENCE(4, 1, 10, 5)
    =SEQUENCE(2, 3, 100, 10)

The optional arguments control dimensions, starting value, and increment.
""",
)


def sequence(
    rows: int,
    columns: int = 1,
    start: float = 1,
    step: float = 1,
) -> list[list[float]]:
    """Python equivalent of Excel SEQUENCE."""
    if rows < 0 or columns < 0:
        raise ValueError("rows and columns cannot be negative")

    result: list[list[float]] = []
    value = start

    for _ in range(rows):
        row = []
        for _ in range(columns):
            row.append(value)
            value += step
        result.append(row)

    return result


print("SEQUENCE(5):")
for row in sequence(5):
    print(row)

print("\nSEQUENCE(3, 2):")
for row in sequence(3, 2):
    print(row)

print("\nSEQUENCE(3, 2, 10, 5):")
for row in sequence(3, 2, 10, 5):
    print(row)


def flatten(matrix: Sequence[Sequence[Any]]) -> list[Any]:
    """Flatten a rectangular or ragged matrix."""
    return [value for row in matrix for value in row]


# =============================================================================
# 4. FILTER
# =============================================================================

explain(
    "FILTER",
    """
Excel syntax:

    =FILTER(array, include, [if_empty])

FILTER returns only rows or values satisfying a Boolean condition.

Example:

    =FILTER(A2:D100, D2:D100="East", "No results")

The include argument is effectively a Boolean mask:

    TRUE
    FALSE
    TRUE
    FALSE

The TRUE positions are retained.

FILTER is especially powerful when its result is combined with other
dynamic-array functions.
""",
)


def excel_filter(
    values: Sequence[Any],
    include: Sequence[bool],
    if_empty: Any = None,
) -> list[Any]:
    """
    Python equivalent of one-dimensional FILTER.

    Excel requires the include array to align with the filtered dimension.
    """
    if len(values) != len(include):
        raise ValueError("array and include must have the same length")

    result = [value for value, keep in zip(values, include) if bool(keep)]

    if not result:
        return [] if if_empty is None else [if_empty]

    return result


scores = [45, 82, 91, 58, 76, 94]
passed = excel_filter(scores, [score >= 70 for score in scores])

print("Scores:", scores)
print("Scores >= 70:", passed)


# =============================================================================
# 5. FILTERING TABLE ROWS
# =============================================================================

@dataclass(frozen=True)
class Employee:
    employee_id: int
    name: str
    department: str
    location: str
    salary: float
    performance: float


employees = [
    Employee(101, "Asha", "Technology", "Delhi", 90000, 91),
    Employee(102, "Ravi", "Finance", "Mumbai", 82000, 84),
    Employee(103, "Meera", "Technology", "Bengaluru", 105000, 96),
    Employee(104, "Arjun", "Operations", "Lucknow", 72000, 78),
    Employee(105, "Neha", "Finance", "Delhi", 88000, 89),
    Employee(106, "Kabir", "Technology", "Mumbai", 97000, 87),
    Employee(107, "Isha", "Operations", "Bengaluru", 76000, 82),
]

technology_employees = [
    employee
    for employee in employees
    if employee.department == "Technology"
]

print("\nTechnology employees:")
for employee in technology_employees:
    print(employee)


def filter_rows(
    rows: Iterable[Any],
    predicate: Callable[[Any], bool],
) -> list[Any]:
    """Generic FILTER-style operation for records."""
    return [row for row in rows if predicate(row)]


high_performers = filter_rows(
    employees,
    lambda employee: employee.performance >= 90,
)

print("\nEmployees with performance >= 90:")
for employee in high_performers:
    print(employee.name, employee.performance)


# =============================================================================
# 6. BOOLEAN LOGIC IN FILTER
# =============================================================================

explain(
    "Boolean logic",
    """
Excel FILTER conditions frequently combine multiple tests.

AND-like logic:

    =FILTER(A2:D100, (B2:B100="Technology")*(D2:D100>90000))

OR-like logic:

    =FILTER(A2:D100, (B2:B100="Technology")+(B2:B100="Finance"))

In Excel's array calculations, multiplication can represent AND because
TRUE/FALSE values behave numerically as 1/0 in this context.

Addition can represent OR when the resulting condition is tested as nonzero.

The exact formula should be designed carefully when conditions can overlap.
""",
)


technology_high_salary = filter_rows(
    employees,
    lambda employee: (
        employee.department == "Technology"
        and employee.salary > 90000
    ),
)

print("Technology employees earning > 90,000:")
for employee in technology_high_salary:
    print(employee.name, employee.salary)


finance_or_operations = filter_rows(
    employees,
    lambda employee: employee.department in {"Finance", "Operations"},
)

print("\nFinance OR Operations:")
for employee in finance_or_operations:
    print(employee.name, employee.department)


# =============================================================================
# 7. SORT
# =============================================================================

explain(
    "SORT",
    """
Excel syntax:

    =SORT(array, [sort_index], [sort_order], [by_col])

Typical usage:

    =SORT(A2:D100, 4, -1)

sort_order:
    1  = ascending
   -1  = descending

SORT returns a new dynamic array and does not require manually rearranging
the source data.

SORTBY is a related function that sorts an array using one or more separate
sort ranges. It is often preferable when sorting records by calculated
criteria.
""",
)


def excel_sort(
    values: Sequence[Any],
    key: Callable[[Any], Any] | None = None,
    reverse: bool = False,
) -> list[Any]:
    """Generic SORT-style operation."""
    return sorted(values, key=key, reverse=reverse)


employees_by_salary = excel_sort(
    employees,
    key=lambda employee: employee.salary,
    reverse=True,
)

print("Employees sorted by salary descending:")
for employee in employees_by_salary:
    print(employee.name, employee.salary)


employees_by_performance = excel_sort(
    employees,
    key=lambda employee: employee.performance,
    reverse=True,
)

print("\nEmployees sorted by performance descending:")
for employee in employees_by_performance:
    print(employee.name, employee.performance)


# =============================================================================
# 8. SORT WITH MULTIPLE CRITERIA
# =============================================================================

explain(
    "Multiple sort criteria",
    """
When several records have the same primary sort value, a secondary key can
provide deterministic ordering.

A common Excel approach is SORTBY:

    =SORTBY(A2:D100, D2:D100, -1, C2:C100, 1)

This means:

    1. sort by column D descending
    2. break ties using column C ascending

Python's sorted() can model the same idea by using a tuple of keys.
""",
)


multi_sorted = sorted(
    employees,
    key=lambda employee: (
        -employee.performance,
        employee.department,
        employee.name,
    ),
)

print("Performance descending, then department, then name:")
for employee in multi_sorted:
    print(
        employee.name,
        employee.performance,
        employee.department,
    )


# =============================================================================
# 9. UNIQUE
# =============================================================================

explain(
    "UNIQUE",
    """
Excel syntax:

    =UNIQUE(array, [by_col], [exactly_once])

UNIQUE returns distinct values.

Examples:

    =UNIQUE(B2:B100)

For records, UNIQUE can operate across rows or columns depending on the
shape and arguments.

The exactly_once argument changes the meaning:

    FALSE or omitted:
        return values appearing one or more times, but only once each.

    TRUE:
        return only values that occur exactly once.
""",
)


def excel_unique(values: Iterable[Any]) -> list[Any]:
    """Preserve first-occurrence order while removing duplicates."""
    seen: set[Any] = set()
    result = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


locations = [employee.location for employee in employees]

print("Locations:", locations)
print("UNIQUE locations:", excel_unique(locations))


def unique_exactly_once(values: Iterable[Any]) -> list[Any]:
    """Model UNIQUE(..., exactly_once=TRUE)."""
    values_list = list(values)
    counts = Counter(values_list)

    return [
        value
        for value in values_list
        if counts[value] == 1
    ]


print(
    "Locations appearing exactly once:",
    unique_exactly_once(locations),
)


# =============================================================================
# 10. DYNAMIC ARRAY COMPOSITION
# =============================================================================

explain(
    "Function composition",
    """
The real power of dynamic arrays comes from composition.

For example:

    =SORT(UNIQUE(FILTER(B2:B100, C2:C100="Technology")))

The evaluation can be understood from the inside outward:

    FILTER(...)
        ↓
    UNIQUE(...)
        ↓
    SORT(...)

This produces a dynamic list of unique Technology values in sorted order.

Dynamic arrays allow one formula to become a small data-processing pipeline.
""",
)


technology_locations = excel_filter(
    locations,
    [employee.department == "Technology" for employee in employees],
)

unique_technology_locations = excel_unique(technology_locations)
sorted_technology_locations = excel_sort(unique_technology_locations)

print("Unique Technology locations:", sorted_technology_locations)


# =============================================================================
# 11. LET
# =============================================================================

explain(
    "LET",
    """
Excel syntax:

    =LET(name1, value1, calculation)

LET assigns names to intermediate expressions.

Without LET, a complex formula may repeat the same calculation several times.

Conceptual example:

    =LET(
        revenue, B2:B100,
        cost, C2:C100,
        profit, revenue-cost,
        FILTER(profit, profit>0)
    )

Benefits include:

    - readability
    - reduced repeated calculation
    - easier maintenance
    - clearer logical structure

Names are scoped to the LET expression.
""",
)


def calculate_profit_rows(
    revenues: Sequence[float],
    costs: Sequence[float],
) -> list[float]:
    """
    Python equivalent of using LET to name intermediate arrays.
    """
    if len(revenues) != len(costs):
        raise ValueError("revenue and cost arrays must have equal length")

    profit = [
        revenue - cost
        for revenue, cost in zip(revenues, costs)
    ]

    profitable = [
        value
        for value in profit
        if value > 0
    ]

    return profitable


revenues = [100, 250, 300, 80, 500]
costs = [60, 270, 200, 100, 350]

print("Profitable results:", calculate_profit_rows(revenues, costs))


# =============================================================================
# 12. A MORE COMPLETE LET-STYLE PIPELINE
# =============================================================================

@dataclass(frozen=True)
class Sale:
    transaction_id: int
    product: str
    region: str
    units: int
    unit_price: float
    cost_per_unit: float


sales = [
    Sale(1, "Laptop", "North", 4, 85000, 65000),
    Sale(2, "Monitor", "West", 10, 18000, 12000),
    Sale(3, "Laptop", "West", 3, 85000, 65000),
    Sale(4, "Keyboard", "North", 20, 3500, 2100),
    Sale(5, "Monitor", "South", 7, 18000, 12000),
    Sale(6, "Laptop", "North", 2, 85000, 65000),
    Sale(7, "Keyboard", "West", 14, 3500, 2100),
]


def profitable_sales_pipeline(
    sales_data: Sequence[Sale],
    minimum_profit: float,
) -> list[tuple[str, float, float]]:
    """
    Model a LET-style pipeline:

        filtered sales
            -> calculate revenue
            -> calculate profit
            -> keep profitable rows
            -> sort by profit

    Intermediate variables make the data flow explicit.
    """
    eligible_sales = [
        sale
        for sale in sales_data
        if sale.units > 0
    ]

    calculated = [
        (
            sale.product,
            sale.units * sale.unit_price,
            sale.units * (sale.unit_price - sale.cost_per_unit),
        )
        for sale in eligible_sales
    ]

    profitable = [
        record
        for record in calculated
        if record[2] >= minimum_profit
    ]

    return sorted(
        profitable,
        key=lambda record: record[2],
        reverse=True,
    )


print("\nProfitable sales pipeline:")
for record in profitable_sales_pipeline(sales, 10000):
    print(record)


# =============================================================================
# 13. LAMBDA
# =============================================================================

explain(
    "LAMBDA",
    """
Excel syntax:

    =LAMBDA(parameter1, parameter2, calculation)

LAMBDA creates reusable custom functions without traditional VBA.

Example concept:

    =LAMBDA(x, x*1.18)

After assigning that function a name such as PRICE_WITH_TAX, it can be
called repeatedly:

    =PRICE_WITH_TAX(A2)

LAMBDA becomes particularly useful when paired with MAP, REDUCE, SCAN,
BYROW, BYCOL, MAKEARRAY, or other dynamic-array functions.
""",
)


def make_lambda(
    function: Callable[..., Any],
) -> Callable[..., Any]:
    """
    A small Python analogy for a named Excel LAMBDA.

    Python functions are already first-class values, so the language naturally
    supports this pattern.
    """
    return function


add_tax = make_lambda(lambda price, rate: price * (1 + rate))

print("Price with 18% tax:", add_tax(1000, 0.18))


def normalize_text(value: str) -> str:
    """
    Example reusable transformation.

    Excel equivalent concept:

        =LAMBDA(text, UPPER(TRIM(text)))
    """
    return " ".join(value.strip().upper().split())


clean_text = make_lambda(normalize_text)

for raw in ["  hello  ", "Excel   Lambda", "  dynamic arrays "]:
    print("Normalized:", clean_text(raw))


# =============================================================================
# 14. LAMBDA FOR BUSINESS CALCULATIONS
# =============================================================================

def margin(revenue: float, cost: float) -> float:
    """Reusable profit-margin function."""
    if revenue == 0:
        raise ZeroDivisionError("revenue cannot be zero")
    return (revenue - cost) / revenue


profit_margin = make_lambda(margin)

print("\nMargin examples:")
for revenue, cost in [(1000, 600), (2500, 1800), (500, 500)]:
    print(
        f"Revenue={revenue}, Cost={cost}, "
        f"Margin={profit_margin(revenue, cost):.2%}"
    )


# =============================================================================
# 15. LAMBDA RECURSION
# =============================================================================

explain(
    "Recursive LAMBDA",
    """
Excel LAMBDA can be recursive when a named LAMBDA refers to itself.

Recursion is useful for some hierarchical or repeated calculations, but it
can make formulas harder to understand and can introduce calculation-depth
or performance problems.

The following Python function demonstrates the underlying idea with factorial.
""",
)


def factorial(n: int) -> int:
    """Recursive example corresponding to a recursive custom function."""
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("factorial is undefined for negative integers")
    if n in (0, 1):
        return 1
    return n * factorial(n - 1)


for value in [0, 1, 5, 8]:
    print(f"{value}! =", factorial(value))


# =============================================================================
# 16. ADVANCED COMPOSITION
# =============================================================================

explain(
    "Advanced dynamic-array pipeline",
    """
A practical modern formula may combine:

    LET
      ↓
    FILTER
      ↓
    computed columns
      ↓
    UNIQUE
      ↓
    SORT

The conceptual structure is similar to a functional data pipeline.
Each operation transforms an array into another array.
""",
)


def advanced_product_analysis(
    sales_data: Sequence[Sale],
    region: str,
    minimum_units: int,
) -> list[tuple[str, int, float]]:
    """
    Model:

        LET(
            filtered, FILTER(...),
            products, UNIQUE(...),
            ...
        )

    Returns product, total units, and revenue for the selected region.
    """
    filtered = [
        sale
        for sale in sales_data
        if sale.region == region
        and sale.units >= minimum_units
    ]

    products = excel_unique(
        sale.product
        for sale in filtered
    )

    results = []

    for product in products:
        matching = [
            sale
            for sale in filtered
            if sale.product == product
        ]

        total_units = sum(sale.units for sale in matching)
        revenue = sum(
            sale.units * sale.unit_price
            for sale in matching
        )

        results.append((product, total_units, revenue))

    return sorted(
        results,
        key=lambda row: row[2],
        reverse=True,
    )


print("\nAdvanced product analysis for North:")
for row in advanced_product_analysis(sales, "North", 1):
    print(row)


# =============================================================================
# 17. EMPTY FILTER RESULTS
# =============================================================================

explain(
    "Empty results and error behavior",
    """
FILTER must account for the possibility that no records satisfy the
condition.

Excel can use:

    =FILTER(A2:D100, condition, "No matching records")

Without an appropriate fallback, users may encounter #CALC! when the
filtered result is empty.

A production workbook should decide whether an empty result should display:

    - a message
    - a blank
    - zero
    - a controlled error
    - an alternative calculation
""",
)


no_matching_sales = excel_filter(
    sales,
    [sale.region == "East" for sale in sales],
)

print("No matching sales:", no_matching_sales)


# =============================================================================
# 18. SPILL ERRORS AS A CONCEPT
# =============================================================================

explain(
    "Spill behavior",
    """
A dynamic-array formula needs enough free worksheet space for its result.

If another value occupies a cell that the array needs, Excel can return
#SPILL!.

Typical causes include:

    - a value in the intended spill range
    - merged cells
    - insufficient worksheet space
    - an array formula placed inside an incompatible structure

A robust spreadsheet design keeps dynamic output regions clear.
""",
)


@dataclass
class SpillArea:
    """Simple simulation of a worksheet spill range."""

    occupied: set[tuple[int, int]]

    def can_spill(self, start_row: int, start_col: int, rows: int, columns: int) -> bool:
        """Check whether a rectangular output area is free."""
        for row in range(start_row, start_row + rows):
            for col in range(start_col, start_col + columns):
                if (row, col) in self.occupied:
                    return False
        return True


worksheet = SpillArea(occupied={(3, 1)})

print(
    "Can spill 2x2 at (1,1):",
    worksheet.can_spill(1, 1, 2, 2),
)

print(
    "Can spill 3x2 at (1,1):",
    worksheet.can_spill(1, 1, 3, 2),
)


# =============================================================================
# 19. PERFORMANCE
# =============================================================================

explain(
    "Performance considerations",
    """
Dynamic arrays are powerful, but large formulas can become expensive.

Potential performance issues include:

    - repeatedly scanning very large ranges
    - repeating identical calculations
    - volatile functions
    - deeply nested formulas
    - unnecessary full-column references
    - expensive recursive LAMBDAs
    - excessive recalculation dependencies

LET can improve performance when it allows an expensive expression to be
calculated once and reused.

Using bounded ranges or Excel Tables can also reduce unnecessary work.
""",
)


def repeated_scan(data: Sequence[int], threshold: int) -> list[int]:
    """A simple linear scan: O(n)."""
    return [value for value in data if value > threshold]


large_data = list(range(1_000_000))

# Demonstration of the algorithmic model, not a benchmark.
sample = repeated_scan(large_data, 999_990)
print("Number of values above 999,990:", len(sample))


# =============================================================================
# 20. COMPLEXITY OF COMMON OPERATIONS
# =============================================================================

complexity = {
    "SEQUENCE generation": "O(n) for n output cells",
    "FILTER": "O(n) for one pass over n records",
    "UNIQUE": "approximately O(n) with hash-based tracking",
    "SORT": "typically O(n log n)",
    "LET": "depends on expressions inside LET",
    "LAMBDA": "depends on its body and invocation count",
}

print("\nTypical computational complexity:")
for operation, complexity_description in complexity.items():
    print(f"{operation}: {complexity_description}")


# =============================================================================
# 21. EDGE CASES
# =============================================================================

explain(
    "Important edge cases",
    """
Important spreadsheet cases include:

    - empty source ranges
    - no FILTER matches
    - duplicate values
    - exactly-once UNIQUE logic
    - blank cells
    - zero values
    - negative values
    - text mixed with numbers
    - inconsistent range dimensions
    - blocked spill ranges
    - errors inside source data
    - invalid sort indexes
    - division by zero
    - recursive functions that do not terminate
""",
)


def safe_margin(revenue: float, cost: float) -> float | None:
    """Return None instead of failing for zero revenue."""
    if revenue == 0:
        return None
    return (revenue - cost) / revenue


edge_cases = [
    (0, 100),
    (100, 100),
    (-100, 50),
    (100, -50),
]

for revenue, cost in edge_cases:
    print(
        f"Revenue={revenue:>5}, Cost={cost:>5}, "
        f"Margin={safe_margin(revenue, cost)}"
    )


# =============================================================================
# 22. VALIDATION
# =============================================================================

def validate_parallel_arrays(*arrays: Sequence[Any]) -> None:
    """Ensure arrays intended to work row-by-row have equal lengths."""
    if not arrays:
        return

    expected_length = len(arrays[0])

    for index, array in enumerate(arrays[1:], start=2):
        if len(array) != expected_length:
            raise ValueError(
                f"Array {index} has length {len(array)}; "
                f"expected {expected_length}"
            )


try:
    validate_parallel_arrays([1, 2, 3], ["A", "B"])
except ValueError as error:
    print("\nValidation error:", error)


# =============================================================================
# 23. TESTING
# =============================================================================

def test_sequence() -> None:
    assert sequence(3) == [[1], [2], [3]]
    assert sequence(2, 2, 10, 10) == [[10, 20], [30, 40]]


def test_filter() -> None:
    assert excel_filter([1, 2, 3], [True, False, True]) == [1, 3]


def test_unique() -> None:
    assert excel_unique(["A", "B", "A", "C", "B"]) == ["A", "B", "C"]


def test_sort() -> None:
    assert excel_sort([3, 1, 2]) == [1, 2, 3]
    assert excel_sort([3, 1, 2], reverse=True) == [3, 2, 1]


def test_lambda() -> None:
    assert add_tax(100, 0.10) == 110


def run_tests() -> None:
    """Minimal built-in test suite."""
    tests = [
        test_sequence,
        test_filter,
        test_unique,
        test_sort,
        test_lambda,
    ]

    for test in tests:
        test()

    print("\nAll educational tests passed.")


run_tests()


# =============================================================================
# 24. ADVANCED STATISTICAL EXAMPLE
# =============================================================================

explain(
    "Combining dynamic-array ideas with statistics",
    """
Dynamic arrays are useful when an analysis needs to produce a changing list
of records and then calculate statistics over that list.

The following example filters employee performance values and calculates
descriptive statistics on the resulting dynamic set.
""",
)


def performance_statistics(
    employees_data: Sequence[Employee],
    department: str,
) -> dict[str, float]:
    """Calculate statistics for one department."""
    values = [
        employee.performance
        for employee in employees_data
        if employee.department == department
    ]

    if not values:
        return {}

    return {
        "count": float(len(values)),
        "minimum": min(values),
        "maximum": max(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
    }


for department in excel_unique(
    employee.department for employee in employees
):
    print(
        department,
        performance_statistics(employees, department),
    )


# =============================================================================
# 25. CUSTOM LAMBDA LIBRARY
# =============================================================================

class LambdaLibrary:
    """
    A Python analogy for a collection of named reusable Excel LAMBDAs.

    Excel users can create named LAMBDA functions in Name Manager.
    This class demonstrates the same organizational idea.
    """

    def __init__(self) -> None:
        self.functions: dict[str, Callable[..., Any]] = {}

    def register(
        self,
        name: str,
        function: Callable[..., Any],
    ) -> None:
        if not name:
            raise ValueError("function name cannot be empty")
        if not callable(function):
            raise TypeError("function must be callable")
        self.functions[name] = function

    def call(self, name: str, *args: Any) -> Any:
        if name not in self.functions:
            raise KeyError(f"Unknown function: {name}")
        return self.functions[name](*args)


library = LambdaLibrary()

library.register(
    "DISCOUNT_PRICE",
    lambda price, discount: price * (1 - discount),
)

library.register(
    "GROSS_PROFIT",
    lambda revenue, cost: revenue - cost,
)

print(
    "\nCustom Lambda library:",
    library.call("DISCOUNT_PRICE", 1000, 0.15),
    library.call("GROSS_PROFIT", 1000, 650),
)


# =============================================================================
# 26. DESIGN PRINCIPLES
# =============================================================================

explain(
    "Practical design principles",
    """
For production spreadsheets:

    1. Keep raw data separate from calculation areas.
    2. Prefer Excel Tables for structured datasets.
    3. Use clear column names.
    4. Use LET when a complex expression is reused.
    5. Use LAMBDA for genuinely reusable business logic.
    6. Keep FILTER conditions readable.
    7. Handle empty results explicitly.
    8. Avoid unnecessary full-column calculations.
    9. Test formulas against duplicate and missing data.
    10. Protect critical formulas and document business assumptions.
    11. Keep spill areas free from manually entered values.
    12. Avoid excessive formula nesting when a simpler structure exists.
""",
)


# =============================================================================
# 27. CONCEPTUAL FORMULA CATALOG
# =============================================================================

formula_catalog = {
    "SEQUENCE": "=SEQUENCE(10)",
    "SEQUENCE matrix": "=SEQUENCE(5,3,1,1)",
    "FILTER": '=FILTER(A2:D100,D2:D100="East","No results")',
    "SORT": "=SORT(A2:D100,4,-1)",
    "UNIQUE": "=UNIQUE(B2:B100)",
    "UNIQUE exactly once": "=UNIQUE(B2:B100,,TRUE)",
    "FILTER + SORT": '=SORT(FILTER(A2:D100,D2:D100="East"))',
    "FILTER + UNIQUE + SORT":
        '=SORT(UNIQUE(FILTER(B2:B100,D2:D100="East")))',
    "LET":
        '=LET(revenue,B2:B100,cost,C2:C100,profit,revenue-cost,FILTER(profit,profit>0))',
    "LAMBDA":
        '=LAMBDA(price,rate,price*(1+rate))',
}

print("\nFormula catalog:")
for name, formula in formula_catalog.items():
    print(f"{name:24} {formula}")


# =============================================================================
# 28. FINAL INTEGRATED EXAMPLE
# =============================================================================

def integrated_analysis(
    sales_data: Sequence[Sale],
    target_region: str,
) -> list[dict[str, Any]]:
    """
    Full Python model of a modern Excel analytical formula.

    Logical sequence:

        filter
        -> calculate columns
        -> group
        -> unique products
        -> sort

    This corresponds to the kind of workflow that could be expressed through
    FILTER, LET, UNIQUE, SORT, and LAMBDA-based helper functions.
    """
    filtered = [
        sale
        for sale in sales_data
        if sale.region == target_region
    ]

    products = excel_unique(
        sale.product for sale in filtered
    )

    output = []

    for product in products:
        product_sales = [
            sale
            for sale in filtered
            if sale.product == product
        ]

        units = sum(sale.units for sale in product_sales)
        revenue = sum(
            sale.units * sale.unit_price
            for sale in product_sales
        )
        cost = sum(
            sale.units * sale.cost_per_unit
            for sale in product_sales
        )
        profit = revenue - cost

        output.append(
            {
                "product": product,
                "units": units,
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "margin": safe_margin(revenue, cost),
            }
        )

    return sorted(
        output,
        key=lambda record: record["profit"],
        reverse=True,
    )


print("\nIntegrated analysis:")
for record in integrated_analysis(sales, "West"):
    print(record)


# =============================================================================
# 29. QUICK REFERENCE
# =============================================================================

print("\n" + "=" * 78)
print("QUICK REFERENCE")
print("=" * 78)

quick_reference = [
    ("Dynamic array", "One formula can return multiple cells."),
    ("Spill", "Automatic placement of array results into neighboring cells."),
    ("FILTER", "Returns values satisfying a Boolean condition."),
    ("SORT", "Returns values in a specified order."),
    ("UNIQUE", "Returns distinct values or exactly-once values."),
    ("SEQUENCE", "Generates a numeric array."),
    ("LET", "Names intermediate calculations inside a formula."),
    ("LAMBDA", "Creates reusable custom spreadsheet functions."),
    ("Composition", "Combines array functions into data-processing pipelines."),
    ("#SPILL!", "Indicates that the intended spill range cannot be populated."),
    ("#CALC!", "Can occur when FILTER has no results without a fallback."),
]

for concept, meaning in quick_reference:
    print(f"{concept:18} {meaning}")


print("\nStudy script completed successfully.")
