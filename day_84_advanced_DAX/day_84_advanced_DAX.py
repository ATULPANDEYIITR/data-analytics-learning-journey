from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable, Iterable, Any
from collections import defaultdict
from copy import deepcopy


# ============================================================
# ADVANCED DAX CONCEPTS
# Context Transition | Row Context | Filter Context
# Variables | Iterators
#
# Python simulation of fundamental DAX evaluation semantics.
# ============================================================


# -----------------------------
# 1. Sample analytical dataset
# -----------------------------

SALES = [
    {"SaleID": 1, "ProductID": 101, "Category": "Electronics",
     "Region": "North", "Quantity": 2, "UnitPrice": 500, "Cost": 350},
    {"SaleID": 2, "ProductID": 102, "Category": "Electronics",
     "Region": "South", "Quantity": 1, "UnitPrice": 800, "Cost": 600},
    {"SaleID": 3, "ProductID": 103, "Category": "Furniture",
     "Region": "North", "Quantity": 3, "UnitPrice": 200, "Cost": 120},
    {"SaleID": 4, "ProductID": 101, "Category": "Electronics",
     "Region": "West", "Quantity": 1, "UnitPrice": 500, "Cost": 350},
    {"SaleID": 5, "ProductID": 104, "Category": "Furniture",
     "Region": "South", "Quantity": 4, "UnitPrice": 150, "Cost": 90},
    {"SaleID": 6, "ProductID": 105, "Category": "Clothing",
     "Region": "North", "Quantity": 5, "UnitPrice": 80, "Cost": 40},
]

PRODUCTS = [
    {"ProductID": 101, "ProductName": "Laptop", "Category": "Electronics"},
    {"ProductID": 102, "ProductName": "Monitor", "Category": "Electronics"},
    {"ProductID": 103, "ProductName": "Desk", "Category": "Furniture"},
    {"ProductID": 104, "ProductName": "Chair", "Category": "Furniture"},
    {"ProductID": 105, "ProductName": "Shirt", "Category": "Clothing"},
]


# -----------------------------
# 2. Domain exceptions
# -----------------------------

class DaxEvaluationError(Exception):
    """Base exception for evaluation errors."""


class InvalidContextError(DaxEvaluationError):
    pass


class MissingColumnError(DaxEvaluationError):
    pass


# -----------------------------
# 3. Evaluation context
# -----------------------------

@dataclass
class EvaluationContext:
    """
    Filter context contains restrictions on model columns.

    Row context contains the current row being evaluated.
    Multiple row contexts support nested iterators.
    """

    filters: dict[str, set[Any]] = field(default_factory=dict)
    row_contexts: list[dict[str, Any]] = field(default_factory=list)

    def clone(self) -> EvaluationContext:
        return EvaluationContext(
            filters=deepcopy(self.filters),
            row_contexts=deepcopy(self.row_contexts)
        )

    def push_row(self, row: dict[str, Any]) -> None:
        self.row_contexts.append(row)

    def pop_row(self) -> None:
        if not self.row_contexts:
            raise InvalidContextError("No active row context.")
        self.row_contexts.pop()

    def current_row(self) -> dict[str, Any]:
        if not self.row_contexts:
            raise InvalidContextError("No active row context.")
        return self.row_contexts[-1]

    def transition(self) -> None:
        """
        Simulate CALCULATE context transition.

        Values from the active row contexts become filters.
        Existing filters are intersected with transitioned values.
        """
        for row in self.row_contexts:
            for column, value in row.items():
                if column in self.filters:
                    self.filters[column].intersection_update({value})
                else:
                    self.filters[column] = {value}


# -----------------------------
# 4. Analytical model
# -----------------------------

class DataModel:

    def __init__(self):
        self.tables = {
            "Sales": SALES,
            "Products": PRODUCTS
        }

    def rows(self, table: str) -> list[dict[str, Any]]:
        if table not in self.tables:
            raise DaxEvaluationError(f"Unknown table: {table}")
        return self.tables[table]

    def validate_column(self, table: str, column: str) -> None:
        rows = self.rows(table)
        if rows and column not in rows[0]:
            raise MissingColumnError(f"{table}[{column}] does not exist.")

    def apply_filters(
        self,
        table: str,
        context: EvaluationContext
    ) -> list[dict[str, Any]]:
        """
        Apply filters to a table.

        This simplified model uses same-table filters.
        Cross-table filtering is implemented through explicit
        relationship propagation in related_rows().
        """
        rows = self.rows(table)

        for column, allowed_values in context.filters.items():
            if column not in rows[0]:
                continue

            rows = [
                row for row in rows
                if row[column] in allowed_values
            ]

        return rows

    def related_rows(
        self,
        table: str,
        context: EvaluationContext
    ) -> list[dict[str, Any]]:
        """
        Demonstrate one-to-many relationship propagation:
        Products filters propagate to Sales through ProductID.
        """
        rows = self.rows(table)

        product_filters = {
            key: values
            for key, values in context.filters.items()
            if key in PRODUCTS[0]
        }

        if table == "Sales" and product_filters:
            matching_products = self.apply_filters(
                "Products",
                EvaluationContext(filters=product_filters)
            )
            product_ids = {
                product["ProductID"] for product in matching_products
            }
            rows = [
                sale for sale in rows
                if sale["ProductID"] in product_ids
            ]

        sales_filters = {
            key: values
            for key, values in context.filters.items()
            if key in SALES[0]
        }

        for column, allowed in sales_filters.items():
            rows = [row for row in rows if row[column] in allowed]

        return rows


MODEL = DataModel()


# -----------------------------
# 5. Basic aggregation measures
# -----------------------------

def sales_amount(context: EvaluationContext) -> Decimal:
    total = sum(
        (
            Decimal(str(row["Quantity"]))
            * Decimal(str(row["UnitPrice"]))
            for row in MODEL.related_rows("Sales", context)
        ),
        Decimal("0")
    )
    return total


def total_cost(context: EvaluationContext) -> Decimal:
    return sum(
        (
            Decimal(str(row["Quantity"]))
            * Decimal(str(row["Cost"]))
            for row in MODEL.related_rows("Sales", context)
        ),
        Decimal("0")
    )


def total_profit(context: EvaluationContext) -> Decimal:
    return sales_amount(context) - total_cost(context)


# -----------------------------
# 6. FILTER iterator
# -----------------------------

def filter_table(
    table: str,
    context: EvaluationContext,
    predicate: Callable[[dict[str, Any]], bool]
) -> list[dict[str, Any]]:
    """
    FILTER evaluates a Boolean condition for each row.
    Each iteration establishes a row context.
    """
    result = []

    for row in MODEL.related_rows(table, context):
        child = context.clone()
        child.push_row(row)

        try:
            if predicate(child.current_row()):
                result.append(row)
        finally:
            child.pop_row()

    return result


# -----------------------------
# 7. SUMX iterator
# -----------------------------

def sumx(
    table: str,
    context: EvaluationContext,
    expression: Callable[[EvaluationContext], Decimal]
) -> Decimal:
    """
    SUMX evaluates an expression separately for every row.

    Row context alone does not automatically filter a measure.
    The expression must explicitly perform context transition
    when required.
    """
    total = Decimal("0")

    for row in MODEL.related_rows(table, context):
        child = context.clone()
        child.push_row(row)

        try:
            value = expression(child)
            if value is not None:
                total += Decimal(str(value))
        finally:
            child.pop_row()

    return total


# -----------------------------
# 8. CALCULATE
# -----------------------------

def calculate(
    expression: Callable[[EvaluationContext], Decimal],
    context: EvaluationContext,
    filters: dict[str, set[Any]] | None = None
) -> Decimal:
    """
    CALCULATE modifies filter context.

    Order:
    1. Copy the existing context.
    2. Perform context transition.
    3. Apply explicit filter arguments.
    4. Evaluate the expression.
    """
    modified = context.clone()
    modified.transition()

    if filters:
        for column, values in filters.items():
            if not isinstance(values, set):
                raise InvalidContextError(
                    f"Filter for {column} must be a set."
                )

            if column in modified.filters:
                modified.filters[column].intersection_update(values)
            else:
                modified.filters[column] = set(values)

    return expression(modified)


# -----------------------------
# 9. ADDCOLUMNS
# -----------------------------

def add_columns(
    table: str,
    context: EvaluationContext,
    expressions: dict[
        str, Callable[[EvaluationContext], Any]
    ]
) -> list[dict[str, Any]]:
    """
    ADDCOLUMNS creates calculated columns in a virtual table.

    Expressions receive row context. Explicit CALCULATE is
    needed when a measure must be evaluated for that row.
    """
    result = []

    for row in MODEL.related_rows(table, context):
        child = context.clone()
        child.push_row(row)

        try:
            new_row = dict(row)

            for name, expression in expressions.items():
                new_row[name] = expression(child)

            result.append(new_row)
        finally:
            child.pop_row()

    return result


# -----------------------------
# 10. Variables and evaluation
# -----------------------------

def profit_margin(context: EvaluationContext) -> Decimal:
    """
    Variables store evaluated values within a measure.

    A zero denominator returns zero rather than raising
    a division error.
    """
    revenue = sales_amount(context)
    cost = total_cost(context)
    profit = revenue - cost

    return (
        profit / revenue
        if revenue != 0
        else Decimal("0")
    )


def regional_sales(context: EvaluationContext) -> dict[str, Decimal]:
    """
    Evaluate sales independently for each region.
    """
    regions = {
        row["Region"]
        for row in MODEL.rows("Sales")
    }

    return {
        region: calculate(
            sales_amount,
            context,
            {"Region": {region}}
        )
        for region in sorted(regions)
    }


# -----------------------------
# 11. Demonstration
# -----------------------------

def run_examples() -> None:
    base = EvaluationContext()

    print("\nADVANCED DAX SEMANTIC SIMULATION")
    print("=" * 55)

    # Filter context
    north = calculate(
        sales_amount,
        base,
        {"Region": {"North"}}
    )
    print("North sales:", north)

    # Multiple filters
    electronics_north = calculate(
        sales_amount,
        base,
        {
            "Region": {"North"},
            "Category": {"Electronics"}
        }
    )
    print("North electronics sales:", electronics_north)

    # Row context
    def current_row_revenue(context: EvaluationContext):
        row = context.current_row()
        return Decimal(str(row["Quantity"] * row["UnitPrice"]))

    print(
        "SUMX row-context revenue:",
        sumx("Sales", base, current_row_revenue)
    )

    # Context transition
    def measure_for_current_row(context: EvaluationContext):
        return calculate(sales_amount, context)

    transitioned_total = sumx(
        "Sales",
        base,
        measure_for_current_row
    )
    print("SUMX with context transition:", transitioned_total)

    # FILTER
    high_value_sales = filter_table(
        "Sales",
        base,
        lambda row: row["Quantity"] * row["UnitPrice"] >= 500
    )
    print("High-value transaction count:", len(high_value_sales))

    # ADDCOLUMNS
    product_analysis = add_columns(
        "Products",
        base,
        {
            "ProductSales": lambda ctx: calculate(
                sales_amount,
                ctx
            )
        }
    )

    print("\nPRODUCT SALES")
    for product in product_analysis:
        print(
            product["ProductName"],
            product["ProductSales"]
        )

    # Variables
    print("\nPROFITABILITY")
    print("Revenue:", sales_amount(base))
    print("Cost:", total_cost(base))
    print("Profit:", total_profit(base))
    print("Profit margin:", round(profit_margin(base) * 100, 2), "%")

    # Regional evaluation
    print("\nREGIONAL SALES")
    for region, amount in regional_sales(base).items():
        print(region, amount)

    # Nested row contexts
    print("\nNESTED ITERATOR EXAMPLE")

    def nested_evaluation(context: EvaluationContext):
        outer_row = context.current_row()
        nested = context.clone()
        nested.push_row({
            "Region": outer_row["Region"]
        })

        try:
            return calculate(sales_amount, nested)
        finally:
            nested.pop_row()

    nested_total = sumx("Sales", base, nested_evaluation)
    print("Nested context result:", nested_total)

    # Edge case: division by zero
    empty_context = EvaluationContext(
        filters={"Region": {"Nonexistent"}}
    )
    print("Empty-context margin:", profit_margin(empty_context))


# -----------------------------
# 12. Automated validation
# -----------------------------

def run_tests() -> None:
    context = EvaluationContext()

    assert sales_amount(context) == Decimal("3350")
    assert total_cost(context) == Decimal("2190")
    assert total_profit(context) == Decimal("1160")

    assert calculate(
        sales_amount,
        context,
        {"Region": {"North"}}
    ) == Decimal("1900")

    assert calculate(
        sales_amount,
        context,
        {"Category": {"Electronics"}}
    ) == Decimal("1800")

    assert sumx(
        "Sales",
        context,
        lambda ctx: Decimal(
            str(
                ctx.current_row()["Quantity"]
                * ctx.current_row()["UnitPrice"]
            )
        )
    ) == Decimal("3350")

    assert sumx(
        "Sales",
        context,
        lambda ctx: calculate(sales_amount, ctx)
    ) == Decimal("3350")

    assert profit_margin(context) == (
        Decimal("1160") / Decimal("3350")
    )

    assert profit_margin(
        EvaluationContext(filters={"Region": {"Unknown"}})
    ) == Decimal("0")

    # Context transition must not mutate the original context.
    child = context.clone()
    child.push_row({"Region": "North"})
    transitioned = child.clone()
    transitioned.transition()

    assert transitioned.filters["Region"] == {"North"}
    assert context.filters == {}

    # Invalid column handling
    try:
        MODEL.validate_column("Sales", "UnknownColumn")
    except MissingColumnError:
        pass
    else:
        raise AssertionError("Invalid column was accepted.")

    print("\nAll Python tests passed.")


if __name__ == "__main__":
    run_examples()
    run_tests()
