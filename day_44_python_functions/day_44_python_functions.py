"""
Python Functions: From Fundamentals to Advanced Patterns

This executable module demonstrates function definitions, positional and
keyword parameters, default values, return semantics, scope, lambda functions,
higher-order functions, closures, decorators, recursion, generators, and
practical function testing.

Run with Python 3.10 or later:
    python python_functions.py
"""

from __future__ import annotations

from collections import Counter
from functools import wraps, reduce
from time import perf_counter
from typing import Callable, Iterable, TypeVar


T = TypeVar("T")
R = TypeVar("R")


# Function definition, parameters, and return values


def calculate_invoice(
    unit_price: float,
    quantity: int,
    *,
    discount_rate: float = 0.0,
    tax_rate: float = 0.0,
) -> dict[str, float]:
    """Calculate an invoice using keyword-only discount and tax parameters."""
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative.")
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    if not 0 <= discount_rate <= 1:
        raise ValueError("Discount rate must be between 0 and 1.")
    if not 0 <= tax_rate <= 1:
        raise ValueError("Tax rate must be between 0 and 1.")

    subtotal = unit_price * quantity
    discount = subtotal * discount_rate
    taxable_amount = subtotal - discount
    tax = taxable_amount * tax_rate

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "tax": round(tax, 2),
        "total": round(taxable_amount + tax, 2),
    }


def describe_employee(
    employee_id: int,
    department: str,
    role: str = "Associate",
) -> str:
    """Combine required and optional parameters into a descriptive result."""
    if employee_id <= 0:
        raise ValueError("Employee ID must be positive.")
    if not department.strip() or not role.strip():
        raise ValueError("Department and role cannot be empty.")

    return f"Employee {employee_id}: {role} in {department}"


def summarize_scores(*scores: float, label: str = "Assessment") -> dict:
    """Accept a variable number of positional scores."""
    if not scores:
        return {"label": label, "count": 0, "average": None, "highest": None}

    if any(not 0 <= score <= 100 for score in scores):
        raise ValueError("Every score must be between 0 and 100.")

    return {
        "label": label,
        "count": len(scores),
        "average": round(sum(scores) / len(scores), 2),
        "highest": max(scores),
    }


def build_employee_record(**attributes: object) -> dict[str, object]:
    """Collect arbitrary keyword arguments into a new dictionary."""
    allowed_fields = {"name", "department", "email", "job_title"}
    unknown_fields = set(attributes) - allowed_fields

    if unknown_fields:
        raise ValueError(f"Unsupported fields: {sorted(unknown_fields)}")

    if not attributes.get("name"):
        raise ValueError("An employee name is required.")

    return dict(attributes)


# Returning values, multiple results, and early exits


def classify_transaction(amount: float) -> tuple[str, float]:
    """Return a category and normalized amount."""
    if amount < 0:
        return "refund", abs(amount)
    if amount == 0:
        return "zero-value", 0.0
    if amount >= 100_000:
        return "high-value", amount
    return "standard", amount


def find_employee(
    employees: Iterable[dict[str, object]],
    employee_id: int,
) -> dict[str, object] | None:
    """Return the first matching employee, or None when absent."""
    for employee in employees:
        if employee.get("id") == employee_id:
            return employee

    # Reaching the end without a return produces None explicitly here.
    return None


def demonstrate_return_semantics() -> None:
    """Show why printing and returning are different operations."""

    def print_only(value: int) -> None:
        print(f"Printed value: {value}")

    def return_value(value: int) -> int:
        return value * 2

    printed_result = print_only(7)
    calculated_result = return_value(7)

    print("Print-only function returns:", printed_result)
    print("Value-returning function returns:", calculated_result)


# Mutable defaults: avoid sharing state between calls


def add_tag_safely(
    tag: str,
    tags: list[str] | None = None,
) -> list[str]:
    """Create a fresh list when no list is supplied."""
    if tags is None:
        tags = []

    tags.append(tag)
    return tags


# Scope: local, global, and nonlocal variables


tax_rate = 0.18


def calculate_tax(amount: float) -> float:
    """Read a module-level name without modifying global state."""
    if amount < 0:
        raise ValueError("Amount cannot be negative.")
    return amount * tax_rate


def make_sequence_counter(start: int = 0) -> Callable[[], int]:
    """
    Create a closure that retains its own state.

    The nonlocal declaration permits reassignment of the enclosing variable.
    """
    current = start

    def next_value() -> int:
        nonlocal current
        current += 1
        return current

    return next_value


def make_scoped_greeting(prefix: str) -> Callable[[str], str]:
    """Demonstrate a closure that retains a value from its enclosing scope."""
    def greet(name: str) -> str:
        return f"{prefix}, {name.strip()}!"

    return greet


# Lambda functions and sorting records


def demonstrate_lambdas() -> None:
    """Use short anonymous functions where a named function is unnecessary."""
    products = [
        {"name": "Keyboard", "price": 2499.0, "stock": 12},
        {"name": "Monitor", "price": 14999.0, "stock": 5},
        {"name": "Mouse", "price": 799.0, "stock": 30},
    ]

    by_price = sorted(products, key=lambda product: product["price"])
    by_stock = sorted(products, key=lambda product: product["stock"])

    print("Products by price:", [p["name"] for p in by_price])
    print("Products by stock:", [p["name"] for p in by_stock])

    square = lambda number: number * number
    print("Square of 12:", square(12))

    # Lambdas are expressions, not replacements for every named function.
    # Use def when logic needs documentation, validation, or several statements.


# Higher-order functions: functions passed to or returned from functions


def apply_discount(
    price: float,
    discount_function: Callable[[float], float],
) -> float:
    """Accept behavior as an argument rather than hard-coding a discount."""
    if price < 0:
        raise ValueError("Price cannot be negative.")

    discounted_price = discount_function(price)
    if not 0 <= discounted_price <= price:
        raise ValueError("Discount function returned an invalid price.")

    return round(discounted_price, 2)


def percentage_discount(rate: float) -> Callable[[float], float]:
    """Return a function configured with a particular discount rate."""
    if not 0 <= rate <= 1:
        raise ValueError("Rate must be between 0 and 1.")

    return lambda price: price * (1 - rate)


def compose(
    first: Callable[[T], R],
    second: Callable[[R], T],
) -> Callable[[T], T]:
    """
    Compose two compatible transformations.

    For this compact example, both transformations have the same input/output
    type. The second transformation receives the first one's result.
    """
    return lambda value: second(first(value))


def normalize_department(value: str) -> str:
    return value.strip().casefold()


def display_department(value: str) -> str:
    return value.replace("-", " ").title()


# Built-in higher-order operations and comprehensions


def analyze_sales(
    sales: list[dict[str, object]],
) -> dict[str, object]:
    """Filter, transform, aggregate, and rank a realistic sales dataset."""
    valid_sales: list[dict[str, object]] = []

    for sale in sales:
        amount = sale.get("amount")
        region = sale.get("region")

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise ValueError("Each sale must have a numeric amount.")
        if amount < 0:
            raise ValueError("Sale amounts cannot be negative.")
        if not isinstance(region, str) or not region.strip():
            raise ValueError("Each sale must have a region.")

        valid_sales.append(sale)

    large_sales = list(
        filter(lambda sale: float(sale["amount"]) >= 10_000, valid_sales)
    )

    amounts = list(map(lambda sale: float(sale["amount"]), valid_sales))
    total = reduce(lambda left, right: left + right, amounts, 0.0)

    regional_totals: Counter[str] = Counter()
    for sale in valid_sales:
        region = str(sale["region"]).strip()
        regional_totals[region] += float(sale["amount"])

    return {
        "sale_count": len(valid_sales),
        "large_sale_count": len(large_sales),
        "total_revenue": round(total, 2),
        "average_sale": round(total / len(amounts), 2) if amounts else 0.0,
        "regional_totals": dict(regional_totals.most_common()),
    }


# Decorators: higher-order functions that wrap callable behavior


def log_call(function: Callable[..., R]) -> Callable[..., R]:
    """Log function calls while preserving metadata and return values."""

    @wraps(function)
    def wrapper(*args: object, **kwargs: object) -> R:
        print(f"Calling {function.__name__}")
        return function(*args, **kwargs)

    return wrapper


def measure_execution(
    function: Callable[..., R],
) -> Callable[..., R]:
    """Measure elapsed wall-clock time without changing the result."""

    @wraps(function)
    def wrapper(*args: object, **kwargs: object) -> R:
        started = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = perf_counter() - started
            print(f"{function.__name__} took {elapsed:.6f} seconds")

    return wrapper


@log_call
@measure_execution
def calculate_batch_total(values: Iterable[float]) -> float:
    """Aggregate a batch of validated non-negative values."""
    total = 0.0

    for value in values:
        if value < 0:
            raise ValueError("Batch values cannot be negative.")
        total += value

    return round(total, 2)


# Recursion and iteration


def factorial_recursive(number: int) -> int:
    """Calculate a factorial recursively, with explicit input validation."""
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("Factorial input must be an integer.")
    if number < 0:
        raise ValueError("Factorial is undefined for negative integers.")
    if number > 900:
        raise ValueError("Input exceeds the safe demonstration recursion limit.")

    if number <= 1:
        return 1

    return number * factorial_recursive(number - 1)


def factorial_iterative(number: int) -> int:
    """Avoid recursive call-stack growth for larger factorial inputs."""
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("Factorial input must be an integer.")
    if number < 0:
        raise ValueError("Factorial is undefined for negative integers.")

    result = 1
    for factor in range(2, number + 1):
        result *= factor

    return result


# Generators provide lazy results rather than allocating a full collection.


def running_totals(values: Iterable[float]) -> Iterable[float]:
    """Yield cumulative totals as input values are consumed."""
    total = 0.0

    for value in values:
        total += value
        yield total


# Callable-based validation and reusable function contracts


def validate_positive_amount(amount: float) -> float:
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    return amount


def execute_validated(
    amount: float,
    validator: Callable[[float], float],
    operation: Callable[[float], float],
) -> float:
    """Separate input validation from the business operation."""
    valid_amount = validator(amount)
    return operation(valid_amount)


def test_function_behavior() -> None:
    """Run lightweight assertions without third-party testing libraries."""
    invoice = calculate_invoice(
        100.0,
        3,
        discount_rate=0.10,
        tax_rate=0.18,
    )
    assert invoice == {
        "subtotal": 300.0,
        "discount": 30.0,
        "tax": 48.6,
        "total": 318.6,
    }

    assert describe_employee(42, "Engineering") == (
        "Employee 42: Associate in Engineering"
    )
    assert summarize_scores(80, 90, label="Python")["average"] == 85.0
    assert summarize_scores()["average"] is None
    assert classify_transaction(-250) == ("refund", 250)
    assert add_tag_safely("urgent") == ["urgent"]
    assert add_tag_safely("normal") == ["normal"]
    assert factorial_recursive(5) == factorial_iterative(5) == 120
    assert list(running_totals([2, 3, 5])) == [2.0, 5.0, 10.0]

    try:
        calculate_invoice(-1, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative unit prices must be rejected.")

    try:
        summarize_scores(120)
    except ValueError:
        pass
    else:
        raise AssertionError("Out-of-range scores must be rejected.")

    print("All function tests passed.")


def main() -> None:
    print("Function parameters and return values")
    print(
        calculate_invoice(
            1250,
            4,
            discount_rate=0.05,
            tax_rate=0.18,
        )
    )
    print(describe_employee(1042, "Cybersecurity", "Engineer"))
    print(summarize_scores(88, 92, 76, label="Technical assessment"))

    print("\nFlexible keyword parameters")
    print(
        build_employee_record(
            name="Riya Sharma",
            department="Operations",
            job_title="Analyst",
        )
    )

    print("\nReturn semantics")
    demonstrate_return_semantics()

    print("\nScope and closures")
    first_counter = make_sequence_counter(10)
    second_counter = make_sequence_counter(100)
    print(first_counter(), first_counter(), second_counter())
    formal_greeting = make_scoped_greeting("Good morning")
    print(formal_greeting("Riya"))

    print("\nLambda functions")
    demonstrate_lambdas()

    print("\nHigher-order functions")
    ten_percent_off = percentage_discount(0.10)
    print("Discounted price:", apply_discount(2500, ten_percent_off))

    normalize_then_display = compose(
        normalize_department,
        display_department,
    )
    print(normalize_then_display("  CYBERSECURITY-OPERATIONS "))

    print("\nSales analytics")
    sales = [
        {"region": "North", "amount": 15_000},
        {"region": "South", "amount": 8_500},
        {"region": "North", "amount": 12_000},
        {"region": "West", "amount": 25_000},
    ]
    print(analyze_sales(sales))

    print("\nDecorators")
    print(calculate_batch_total([1200, 3500, 750]))

    print("\nRecursion and iteration")
    print("Recursive factorial:", factorial_recursive(8))
    print("Iterative factorial:", factorial_iterative(20))

    print("\nLazy generator")
    for cumulative in running_totals([1500, 2250, 800]):
        print("Cumulative amount:", cumulative)

    print("\nComposable validation")
    result = execute_validated(
        5000,
        validate_positive_amount,
        lambda amount: amount * 1.18,
    )
    print("Validated amount including tax:", round(result, 2))

    print("\nTesting")
    test_function_behavior()


if __name__ == "__main__":
    main()
