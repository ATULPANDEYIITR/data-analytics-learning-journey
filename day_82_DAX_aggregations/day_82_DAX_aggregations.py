"""
DAX AGGREGATIONS: SUM, AVERAGE, COUNT, DISTINCTCOUNT, CALCULATE, FILTER

A self-contained analytical engine simulating fundamental DAX aggregation
and filter-context behavior using Python.

Scenario:
A retail organization analyzes sales transactions across products,
regions, customers, and reporting periods.

Run:
    python dax_aggregations.py
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from collections import defaultdict
from typing import Callable, Iterable, Optional, Any
from enum import Enum


class DaxError(Exception):
    """Base exception for analytical operations."""


class InvalidColumnError(DaxError):
    pass


class InvalidFilterError(DaxError):
    pass


class AggregationError(DaxError):
    pass


class DataType(Enum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    TEXT = "text"


@dataclass(frozen=True)
class SalesRecord:
    transaction_id: int
    order_date: date
    customer_id: Optional[int]
    product_id: int
    region: str
    category: str
    quantity: Optional[int]
    unit_price: Optional[Decimal]
    revenue: Optional[Decimal]
    status: str

    def __post_init__(self):
        if self.transaction_id <= 0:
            raise ValueError("Transaction ID must be positive.")

        if self.quantity is not None and self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        if self.revenue is not None and self.revenue < 0:
            raise ValueError("Revenue cannot be negative.")


class FilterOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    IN = "in"


@dataclass(frozen=True)
class FilterCondition:
    column: str
    operator: FilterOperator
    value: Any

    def evaluate(self, record: SalesRecord) -> bool:
        actual = getattr(record, self.column)

        if actual is None:
            return False

        if self.operator == FilterOperator.EQUALS:
            return actual == self.value

        if self.operator == FilterOperator.NOT_EQUALS:
            return actual != self.value

        if self.operator == FilterOperator.GREATER_THAN:
            return actual > self.value

        if self.operator == FilterOperator.GREATER_OR_EQUAL:
            return actual >= self.value

        if self.operator == FilterOperator.LESS_THAN:
            return actual < self.value

        if self.operator == FilterOperator.LESS_OR_EQUAL:
            return actual <= self.value

        if self.operator == FilterOperator.IN:
            return actual in self.value

        raise InvalidFilterError("Unsupported filter operator.")


class FilterContext:
    """
    Represents the current analytical filter context.

    Filters are evaluated together using AND semantics.
    """

    def __init__(self, conditions=None):
        self.conditions = tuple(conditions or [])

    def apply(self, records):
        result = []

        for record in records:
            if all(condition.evaluate(record)
                   for condition in self.conditions):
                result.append(record)

        return result

    def add(self, *conditions):
        return FilterContext(self.conditions + tuple(conditions))

    def replace_column(self, column, condition):
        remaining = [
            existing
            for existing in self.conditions
            if existing.column != column
        ]

        return FilterContext(remaining + [condition])


class SalesModel:
    """
    In-memory analytical model.

    The model validates columns, supports filtering, and exposes
    DAX-inspired aggregation operations.
    """

    VALID_COLUMNS = {
        field.name
        for field in SalesRecord.__dataclass_fields__.values()
    }

    NUMERIC_COLUMNS = {
        "transaction_id",
        "product_id",
        "quantity",
        "unit_price",
        "revenue"
    }

    def __init__(self, records: Iterable[SalesRecord]):
        self.records = list(records)

        self._validate_records()

    def _validate_records(self):
        transaction_ids = set()

        for record in self.records:
            if record.transaction_id in transaction_ids:
                raise ValueError(
                    f"Duplicate transaction: {record.transaction_id}"
                )

            transaction_ids.add(record.transaction_id)

    def validate_column(self, column):
        if column not in self.VALID_COLUMNS:
            raise InvalidColumnError(
                f"Unknown column: {column}"
            )

    def evaluate(self, context=None):
        context = context or FilterContext()
        return context.apply(self.records)

    def sum(self, column, context=None):
        """
        SUM ignores blank values.

        Returns zero when no nonblank numeric values exist.
        """
        self.validate_column(column)

        if column not in self.NUMERIC_COLUMNS:
            raise AggregationError("SUM requires a numeric column.")

        values = [
            getattr(record, column)
            for record in self.evaluate(context)
            if getattr(record, column) is not None
        ]

        return sum(values, Decimal("0"))

    def average(self, column, context=None):
        """
        AVERAGE ignores blank values.

        Returns None when no nonblank values exist.
        """
        self.validate_column(column)

        if column not in self.NUMERIC_COLUMNS:
            raise AggregationError(
                "AVERAGE requires a numeric column."
            )

        values = [
            getattr(record, column)
            for record in self.evaluate(context)
            if getattr(record, column) is not None
        ]

        if not values:
            return None

        return sum(values, Decimal("0")) / len(values)

    def count(self, column, context=None):
        """
        COUNT counts nonblank numeric values.

        Text values are not counted.
        """
        self.validate_column(column)

        if column not in self.NUMERIC_COLUMNS:
            raise AggregationError(
                "COUNT requires a numeric column."
            )

        return sum(
            1
            for record in self.evaluate(context)
            if getattr(record, column) is not None
        )

    def distinct_count(self, column, context=None):
        """
        DISTINCTCOUNT counts distinct values, including BLANK
        when a blank value exists.

        Python None represents DAX BLANK.
        """
        self.validate_column(column)

        values = {
            getattr(record, column)
            for record in self.evaluate(context)
        }

        return len(values)

    def filter(self, context=None, *conditions):
        """
        FILTER returns rows satisfying a Boolean predicate.

        This implementation also supports composing a new
        filter context.
        """
        context = context or FilterContext()
        filtered_context = context.add(*conditions)

        return self.evaluate(filtered_context)

    def calculate(self, expression, *filters, context=None,
                  replace_columns=None):
        """
        CALCULATE evaluates an expression under modified
        filter context.

        Filters on columns specified in replace_columns
        replace existing filters on those columns.

        Other filters remain active.
        """
        current = context or FilterContext()

        replace_columns = set(replace_columns or [])

        for condition in filters:
            self.validate_column(condition.column)

            if condition.column in replace_columns:
                current = current.replace_column(
                    condition.column,
                    condition
                )
            else:
                current = current.add(condition)

        return expression(current)

    def calculate_sum(self, column, *filters, context=None,
                      replace_columns=None):
        return self.calculate(
            lambda ctx: self.sum(column, ctx),
            *filters,
            context=context,
            replace_columns=replace_columns
        )


def money(value):
    if value is None:
        return "BLANK"

    return f"{Decimal(value):,.2f}"


def build_sample_data():
    return SalesModel([
        SalesRecord(
            1001, date(2026, 1, 5), 101, 1,
            "North", "Electronics", 2,
            Decimal("500.00"), Decimal("1000.00"), "Completed"
        ),
        SalesRecord(
            1002, date(2026, 1, 8), 102, 2,
            "South", "Furniture", 1,
            Decimal("800.00"), Decimal("800.00"), "Completed"
        ),
        SalesRecord(
            1003, date(2026, 1, 12), 101, 3,
            "North", "Electronics", 3,
            Decimal("200.00"), Decimal("600.00"), "Completed"
        ),
        SalesRecord(
            1004, date(2026, 2, 2), 103, 4,
            "East", "Furniture", 2,
            Decimal("350.00"), Decimal("700.00"), "Pending"
        ),
        SalesRecord(
            1005, date(2026, 2, 9), 104, 5,
            "West", "Clothing", 5,
            Decimal("100.00"), Decimal("500.00"), "Completed"
        ),
        SalesRecord(
            1006, date(2026, 2, 15), 102, 6,
            "South", "Electronics", 1,
            Decimal("1200.00"), Decimal("1200.00"), "Completed"
        ),
        SalesRecord(
            1007, date(2026, 3, 1), 105, 7,
            "North", "Clothing", 4,
            Decimal("150.00"), Decimal("600.00"), "Cancelled"
        ),
        SalesRecord(
            1008, date(2026, 3, 5), 103, 8,
            "East", "Electronics", 2,
            Decimal("450.00"), Decimal("900.00"), "Completed"
        ),
        SalesRecord(
            1009, date(2026, 3, 12), None, 9,
            "West", "Furniture", None,
            Decimal("250.00"), None, "Pending"
        ),
        SalesRecord(
            1010, date(2026, 3, 18), 106, 10,
            "North", "Electronics", 1,
            Decimal("300.00"), Decimal("300.00"), "Completed"
        ),
    ])


def run_demonstration():
    model = build_sample_data()

    print("=" * 65)
    print("DAX AGGREGATION AND FILTER CONTEXT SIMULATION")
    print("=" * 65)

    # SUM
    total_sales = model.sum("revenue")
    print("\n1. SUM")
    print("Total revenue:", money(total_sales))

    # AVERAGE
    average_sales = model.average("revenue")
    print("\n2. AVERAGE")
    print("Average transaction revenue:", money(average_sales))

    # COUNT
    quantity_count = model.count("quantity")
    print("\n3. COUNT")
    print("Nonblank quantity values:", quantity_count)

    # DISTINCTCOUNT
    customer_count = model.distinct_count("customer_id")
    print("\n4. DISTINCTCOUNT")
    print("Distinct customers including BLANK:", customer_count)

    # FILTER
    print("\n5. FILTER")

    north_filter = FilterCondition(
        "region",
        FilterOperator.EQUALS,
        "North"
    )

    north_records = model.filter(None, north_filter)

    print("North region transactions:", len(north_records))
    print(
        "North region revenue:",
        money(model.sum("revenue", FilterContext([north_filter])))
    )

    # Multiple filters use AND semantics.
    electronics_filter = FilterCondition(
        "category",
        FilterOperator.EQUALS,
        "Electronics"
    )

    completed_filter = FilterCondition(
        "status",
        FilterOperator.EQUALS,
        "Completed"
    )

    combined_context = FilterContext([
        electronics_filter,
        completed_filter
    ])

    print("\n6. MULTIPLE FILTER CONDITIONS")
    print(
        "Completed electronics revenue:",
        money(model.sum("revenue", combined_context))
    )

    # CALCULATE
    print("\n7. CALCULATE")

    calculate_result = model.calculate_sum(
        "revenue",
        FilterCondition(
            "region",
            FilterOperator.EQUALS,
            "South"
        )
    )

    print("Revenue for South:", money(calculate_result))

    # Existing filter replacement.
    print("\n8. CALCULATE FILTER REPLACEMENT")

    existing_context = FilterContext([
        FilterCondition(
            "region",
            FilterOperator.EQUALS,
            "North"
        )
    ])

    replaced_result = model.calculate_sum(
        "revenue",
        FilterCondition(
            "region",
            FilterOperator.EQUALS,
            "South"
        ),
        context=existing_context,
        replace_columns={"region"}
    )

    print("Replaced North with South:", money(replaced_result))

    # Existing filter preservation.
    print("\n9. FILTER CONTEXT PRESERVATION")

    preserved_result = model.calculate_sum(
        "revenue",
        FilterCondition(
            "category",
            FilterOperator.EQUALS,
            "Electronics"
        ),
        context=existing_context
    )

    print(
        "North electronics revenue:",
        money(preserved_result)
    )

    # Empty-context edge case.
    print("\n10. EMPTY FILTER RESULT")

    empty_context = FilterContext([
        FilterCondition(
            "region",
            FilterOperator.EQUALS,
            "Antarctica"
        )
    ])

    print("SUM:", money(model.sum("revenue", empty_context)))
    print("AVERAGE:", money(model.average("revenue", empty_context)))
    print("COUNT:", model.count("revenue", empty_context))
    print(
        "DISTINCTCOUNT:",
        model.distinct_count("customer_id", empty_context)
    )

    # Additional business analysis.
    print("\n11. REGIONAL REVENUE")

    regional_revenue = defaultdict(Decimal)

    for record in model.records:
        if record.revenue is not None:
            regional_revenue[record.region] += record.revenue

    for region, revenue in sorted(regional_revenue.items()):
        print(f"{region:10} {money(revenue)}")

    # Assertions validate important behavior.
    assert model.sum("revenue") == Decimal("6600.00")
    assert model.count("revenue") == 9
    assert model.distinct_count("customer_id") == 7
    assert model.average("revenue") == Decimal("6600") / 9

    assert model.sum(
        "revenue",
        FilterContext([north_filter])
    ) == Decimal("2500.00")

    print("\nAll validation assertions passed.")


if __name__ == "__main__":
    try:
        run_demonstration()
    except (DaxError, ValueError, TypeError) as error:
        print(f"Execution error: {error}")
        raise
