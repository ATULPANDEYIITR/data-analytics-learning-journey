"""
Python for Analytics: Syntax, Variables, Data Types, Operators, Expressions,
Input/Output, Data Validation, and Practical Analytical Calculations.

Run with:
    python python_for_analytics.py

The program uses only the Python standard library and runs without external
packages. It progresses from basic expressions to reusable analytics functions,
data-quality checks, summary statistics, and CSV reporting.
"""

from __future__ import annotations

import csv
import io
import json
import math
import statistics
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable


def print_heading(title: str) -> None:
    """Print a readable heading for an executable demonstration."""
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def demonstrate_variables_and_types() -> dict[str, Any]:
    """Show how analytics values are represented by Python data types."""
    print_heading("Variables and data types")

    department = "Operations"
    employee_count = 48
    monthly_budget = 275000.50
    automation_enabled = True
    missing_measurement = None

    # Integers represent counts, floats represent approximate measurements,
    # strings identify categories, and None explicitly represents missing data.
    measurements = [12.5, 13.0, 11.8, 14.2]
    departments = {"Operations", "Finance", "Technology"}
    employee = {
        "employee_id": "E104",
        "department": department,
        "active": automation_enabled,
    }

    values = {
        "department": department,
        "employee_count": employee_count,
        "monthly_budget": monthly_budget,
        "automation_enabled": automation_enabled,
        "missing_measurement": missing_measurement,
        "measurements": measurements,
        "departments": departments,
        "employee": employee,
    }

    for name, value in values.items():
        print(f"{name:24} value={value!r}, type={type(value).__name__}")

    print(f"Budget per employee: {monthly_budget / employee_count:.2f}")
    print(f"Unique departments: {len(departments)}")

    return values


def demonstrate_operators() -> None:
    """Demonstrate operators commonly used in analytical expressions."""
    print_heading("Operators and expressions")

    revenue = 850000
    operating_cost = 612500
    previous_revenue = 790000
    units_sold = 1250

    profit = revenue - operating_cost
    profit_margin = profit / revenue * 100
    revenue_growth = (revenue - previous_revenue) / previous_revenue * 100
    average_price = revenue / units_sold

    print(f"Profit: {profit}")
    print(f"Profit margin: {profit_margin:.2f}%")
    print(f"Revenue growth: {revenue_growth:.2f}%")
    print(f"Average revenue per unit: {average_price:.2f}")
    print(f"Floor division: {17 // 5}")
    print(f"Remainder: {17 % 5}")
    print(f"Exponentiation: {2 ** 8}")
    print(f"Comparison: revenue > operating_cost is {revenue > operating_cost}")
    print(f"Logical condition: {revenue > 0 and operating_cost >= 0}")
    print(f"Membership: 'Operations' in ['Operations', 'Finance']")

    # Parentheses make calculation order explicit and easier to audit.
    adjusted_profit = revenue - (operating_cost + 15000)
    print(f"Profit after additional costs: {adjusted_profit}")

    # Division by zero must be checked before calculating ratios.
    denominator = 0
    safe_ratio = revenue / denominator if denominator != 0 else None
    print(f"Ratio with a zero denominator: {safe_ratio}")


def parse_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a value into a finite Decimal suitable for financial work."""
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a numeric value")

    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty")

    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is not a valid number: {value!r}") from exc

    if not number.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return number


def calculate_financial_metrics(
    revenue: Any,
    cost: Any,
    previous_revenue: Any,
) -> dict[str, Decimal | None]:
    """Calculate validated financial metrics with decimal arithmetic."""
    revenue_value = parse_decimal(revenue, "revenue")
    cost_value = parse_decimal(cost, "cost")
    previous_value = parse_decimal(previous_revenue, "previous_revenue")

    if revenue_value < 0 or cost_value < 0 or previous_value < 0:
        raise ValueError("Revenue and costs cannot be negative")

    profit = revenue_value - cost_value
    margin = (
        profit / revenue_value * Decimal("100")
        if revenue_value != 0
        else None
    )
    growth = (
        (revenue_value - previous_value) / previous_value * Decimal("100")
        if previous_value != 0
        else None
    )

    return {
        "revenue": revenue_value,
        "cost": cost_value,
        "profit": profit,
        "profit_margin_percent": margin,
        "revenue_growth_percent": growth,
    }


def demonstrate_numeric_precision() -> None:
    """Contrast approximate floating-point arithmetic with Decimal."""
    print_heading("Numeric precision and financial calculations")

    print(f"Float calculation: 0.1 + 0.2 = {0.1 + 0.2!r}")
    exact_amount = Decimal("0.10") + Decimal("0.20")
    print(f"Decimal calculation: {exact_amount}")

    metrics = calculate_financial_metrics("125000.00", "92500.00", "110000.00")

    for name, value in metrics.items():
        if value is None:
            print(f"{name}: unavailable because its denominator is zero")
        else:
            print(f"{name}: {value}")

    rounded_profit = metrics["profit"].quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    print(f"Profit rounded to two decimal places: {rounded_profit}")

    # Financial calculations should construct Decimal values from strings,
    # not from floats whose binary approximation is already present.
    try:
        calculate_financial_metrics("100", "110", "0")
    except ValueError as exc:
        print(f"Validation example: {exc}")


def safe_percentage_change(old_value: float, new_value: float) -> float | None:
    """Return percentage change or None when the baseline is zero."""
    if not math.isfinite(old_value) or not math.isfinite(new_value):
        raise ValueError("Measurements must be finite")
    if old_value < 0 or new_value < 0:
        raise ValueError("Measurements cannot be negative")
    if old_value == 0:
        return None
    return (new_value - old_value) / old_value * 100


def summarize_measurements(values: Iterable[Any]) -> dict[str, float | int | None]:
    """Produce descriptive statistics after validating numeric observations."""
    cleaned: list[float] = []

    for position, raw_value in enumerate(values):
        if raw_value is None or isinstance(raw_value, bool):
            continue

        try:
            value = float(raw_value)
        except (TypeError, ValueError, OverflowError):
            continue

        # NaN and infinities are not valid observations for these statistics.
        if math.isfinite(value):
            cleaned.append(value)

    if not cleaned:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "population_standard_deviation": None,
        }

    return {
        "count": len(cleaned),
        "mean": statistics.fmean(cleaned),
        "median": statistics.median(cleaned),
        "minimum": min(cleaned),
        "maximum": max(cleaned),
        "population_standard_deviation": statistics.pstdev(cleaned),
    }


def demonstrate_data_processing() -> None:
    """Use basic data structures to calculate operational performance."""
    print_heading("Analytics with lists, dictionaries, and missing values")

    daily_orders: list[int | None] = [120, 135, 0, 148, None, 162, 155]
    valid_orders = [value for value in daily_orders if value is not None]

    print(f"Daily order records: {daily_orders}")
    print(f"Observed days: {len(valid_orders)}")
    print(f"Total orders on observed days: {sum(valid_orders)}")
    print(f"Average orders on observed days: {statistics.mean(valid_orders):.2f}")
    print(f"Days with no orders: {sum(value == 0 for value in valid_orders)}")
    print(f"Days with missing order counts: {daily_orders.count(None)}")

    # A missing value is not equivalent to zero. Excluding missing records
    # preserves the distinction between no activity and unknown activity.
    summary = summarize_measurements(daily_orders)
    print(f"Descriptive statistics: {summary}")

    revenue_by_region = {
        "North": 425000.0,
        "South": 387500.0,
        "East": 298000.0,
        "West": 412000.0,
    }

    total_revenue = sum(revenue_by_region.values())
    print(f"Total regional revenue: {total_revenue:.2f}")

    for region, revenue in sorted(
        revenue_by_region.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        share = revenue / total_revenue * 100 if total_revenue else 0
        print(f"{region:8} revenue={revenue:10.2f}, share={share:6.2f}%")

    categories = ["Hardware", "Software", "Hardware", "Services", "Software"]
    print(f"Category frequencies: {dict(Counter(categories))}")


def analyze_sales_records(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate transaction records and aggregate accepted sales."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_transaction_ids: set[str] = set()

    required_fields = {"transaction_id", "region", "quantity", "unit_price"}

    for record in records:
        errors: list[str] = []

        if not isinstance(record, dict):
            rejected.append({"record": repr(record), "errors": ["Record must be a dictionary"]})
            continue

        missing_fields = required_fields - record.keys()
        if missing_fields:
            errors.append(f"Missing fields: {', '.join(sorted(missing_fields))}")

        transaction_id = str(record.get("transaction_id", "")).strip()
        region = str(record.get("region", "")).strip()

        if not transaction_id:
            errors.append("transaction_id cannot be empty")
        elif transaction_id in seen_transaction_ids:
            errors.append(f"Duplicate transaction_id: {transaction_id}")
        else:
            # Reserve an ID only after all record checks pass.
            pass

        quantity: int | None = None
        try:
            raw_quantity = record.get("quantity")
            if isinstance(raw_quantity, bool):
                raise ValueError
            quantity = int(raw_quantity)
            if str(raw_quantity).strip() != str(quantity) or quantity <= 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            errors.append("quantity must be a positive whole number")

        unit_price: Decimal | None = None
        try:
            unit_price = parse_decimal(record.get("unit_price"), "unit_price")
            if unit_price < 0:
                errors.append("unit_price cannot be negative")
        except ValueError as exc:
            errors.append(str(exc))

        if not region:
            errors.append("region cannot be empty")

        if errors:
            rejected.append({"record": record, "errors": errors})
            continue

        assert quantity is not None and unit_price is not None
        seen_transaction_ids.add(transaction_id)
        accepted.append(
            {
                "transaction_id": transaction_id,
                "region": region,
                "quantity": quantity,
                "unit_price": unit_price,
                "sales_amount": unit_price * quantity,
            }
        )

    totals: dict[str, Decimal] = {}
    for record in accepted:
        region = record["region"]
        totals[region] = totals.get(region, Decimal("0")) + record["sales_amount"]

    return {
        "accepted": accepted,
        "rejected": rejected,
        "regional_sales": totals,
        "total_sales": sum(totals.values(), Decimal("0")),
    }


def demonstrate_validation_and_aggregation() -> dict[str, Any]:
    """Show record validation, duplicate detection, and grouped aggregation."""
    print_heading("Transaction validation and grouped analytics")

    records = [
        {
            "transaction_id": "TX-1001",
            "region": "North",
            "quantity": 12,
            "unit_price": "1499.50",
        },
        {
            "transaction_id": "TX-1002",
            "region": "South",
            "quantity": 8,
            "unit_price": "2200.00",
        },
        {
            "transaction_id": "TX-1003",
            "region": "North",
            "quantity": 5,
            "unit_price": "999.00",
        },
        {
            "transaction_id": "TX-1002",
            "region": "East",
            "quantity": 3,
            "unit_price": "750.00",
        },
        {
            "transaction_id": "TX-1004",
            "region": "West",
            "quantity": -2,
            "unit_price": "100.00",
        },
        {
            "transaction_id": "TX-1005",
            "region": "East",
            "quantity": 4,
            "unit_price": "invalid",
        },
    ]

    result = analyze_sales_records(records)

    print(f"Accepted records: {len(result['accepted'])}")
    print(f"Rejected records: {len(result['rejected'])}")
    print(f"Total sales: {result['total_sales']:.2f}")

    for region, total in sorted(result["regional_sales"].items()):
        print(f"{region:8} {total:.2f}")

    for rejected in result["rejected"]:
        print(f"Rejected record: {rejected['record']}")
        for error in rejected["errors"]:
            print(f"  - {error}")

    return result


def demonstrate_input_output() -> None:
    """Demonstrate safe input parsing and structured output without prompts."""
    print_heading("Input, output, and serialization")

    raw_input = "  12500.75  "
    parsed_amount = parse_decimal(raw_input, "amount")
    print(f"Raw input: {raw_input!r}")
    print(f"Parsed amount: {parsed_amount}")

    report = {
        "report_name": "Monthly Operations",
        "period": "2026-09",
        "orders_processed": 4850,
        "error_rate_percent": 1.24,
        "regions": ["North", "South", "East", "West"],
    }

    # JSON is useful for exchanging structured analytics results with APIs
    # and other applications. Decimal values need explicit serialization.
    report["sample_financial_value"] = str(parsed_amount)
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    print(serialized)

    restored = json.loads(serialized)
    print(f"Restored report period: {restored['period']}")

    # A fixed sample makes the script deterministic in automated environments.
    # Interactive programs should wrap input() in parsing and exception handling.
    simulated_user_input = "42"
    try:
        user_value = int(simulated_user_input)
        print(f"Validated whole-number input: {user_value}")
    except ValueError:
        print("Input must be a whole number.")


def build_csv_report(result: dict[str, Any]) -> str:
    """Create a CSV report in memory so it can be inspected or saved."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=["region", "sales_amount", "share_percent"],
    )
    writer.writeheader()

    total = result["total_sales"]
    for region, amount in sorted(result["regional_sales"].items()):
        share = amount / total * Decimal("100") if total else Decimal("0")
        writer.writerow(
            {
                "region": region,
                "sales_amount": f"{amount:.2f}",
                "share_percent": f"{share:.2f}",
            }
        )

    return buffer.getvalue()


def demonstrate_csv_reporting(result: dict[str, Any]) -> None:
    """Generate a portable tabular report and read it back."""
    print_heading("CSV output and round-trip validation")

    csv_text = build_csv_report(result)
    print(csv_text, end="")

    # Reading the generated content verifies the column structure and values.
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    print(f"Report rows: {len(rows)}")

    for row in rows:
        assert set(row) == {"region", "sales_amount", "share_percent"}
        assert Decimal(row["sales_amount"]) >= 0


def run_edge_case_checks() -> None:
    """Exercise boundary conditions and demonstrate expected failures."""
    print_heading("Edge cases and executable checks")

    assert summarize_measurements([])["count"] == 0
    assert summarize_measurements([None, "bad", float("nan")])["count"] == 0
    assert summarize_measurements([2, 4, 6])["mean"] == 4.0
    assert safe_percentage_change(100, 125) == 25.0
    assert safe_percentage_change(0, 125) is None

    try:
        parse_decimal("NaN", "amount")
    except ValueError as exc:
        print(f"Non-finite input rejected: {exc}")
    else:
        raise AssertionError("NaN should have been rejected")

    try:
        calculate_financial_metrics("-1", "0", "10")
    except ValueError as exc:
        print(f"Negative revenue rejected: {exc}")
    else:
        raise AssertionError("Negative revenue should have been rejected")

    try:
        safe_percentage_change(float("inf"), 100)
    except ValueError as exc:
        print(f"Infinite measurement rejected: {exc}")
    else:
        raise AssertionError("Infinite measurements should have been rejected")

    print("All edge-case assertions passed.")


def main() -> None:
    """Run the analytics demonstrations in a logical learning sequence."""
    demonstrate_variables_and_types()
    demonstrate_operators()
    demonstrate_numeric_precision()
    demonstrate_data_processing()
    transaction_result = demonstrate_validation_and_aggregation()
    demonstrate_input_output()
    demonstrate_csv_reporting(transaction_result)
    run_edge_case_checks()


if __name__ == "__main__":
    main()
