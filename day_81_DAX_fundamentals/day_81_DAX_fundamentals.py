from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Callable, Iterable, Any
from collections import defaultdict
import json


# ============================================================
# DAX FUNDAMENTALS: EVALUATION ENGINE SIMULATION
# ============================================================
# Demonstrates:
# - Measures
# - Calculated columns
# - Calculated tables
# - DAX-like syntax and functions
# - Row context and filter context
# - Context transition
# - CALCULATE, FILTER, ALL, VALUES, SUMX, RELATED
# - Relationships and aggregation
#
# This is a Python educational simulation of selected DAX
# semantics, not a replacement for the Power BI DAX engine.
# ============================================================


@dataclass(frozen=True)
class Product:
    product_id: int
    product_name: str
    category: str
    unit_price: Decimal


@dataclass(frozen=True)
class Sale:
    sale_id: int
    product_id: int
    sale_date: date
    quantity: int
    unit_cost: Decimal


@dataclass
class EvaluationContext:
    filters: dict[str, set[Any]]
    row: dict[str, Any] | None = None

    def copy(self) -> EvaluationContext:
        return EvaluationContext(
            filters={key: set(value) for key, value in self.filters.items()},
            row=dict(self.row) if self.row else None
        )


class DAXError(Exception):
    pass


class DAXModel:
    def __init__(
        self,
        products: list[Product],
        sales: list[Sale]
    ):
        self.products = products
        self.sales = sales

        self.product_by_id = {
            product.product_id: product for product in products
        }

        self._validate_relationships()

        self.measures: dict[str, Callable] = {
            "Total Sales": self.total_sales,
            "Total Quantity": self.total_quantity,
            "Total Cost": self.total_cost,
            "Total Profit": self.total_profit,
            "Average Selling Price": self.average_selling_price,
            "Profit Margin": self.profit_margin,
            "Sales Count": self.sales_count,
        }

        self.calculated_columns = self.create_calculated_columns()
        self.calculated_tables = self.create_calculated_tables()

    def _validate_relationships(self):
        product_ids = set(self.product_by_id)

        if len(product_ids) != len(self.products):
            raise DAXError("Duplicate product identifiers.")

        sale_ids = [sale.sale_id for sale in self.sales]

        if len(sale_ids) != len(set(sale_ids)):
            raise DAXError("Duplicate sale identifiers.")

        for sale in self.sales:
            if sale.product_id not in product_ids:
                raise DAXError(
                    f"Sale {sale.sale_id} references an unknown product."
                )

            if sale.quantity < 0:
                raise DAXError("Quantity cannot be negative.")

            if sale.unit_cost < 0:
                raise DAXError("Unit cost cannot be negative.")

    # --------------------------------------------------------
    # Filter context
    # --------------------------------------------------------

    def rows_in_context(
        self,
        context: EvaluationContext
    ) -> list[Sale]:

        result = []

        for sale in self.sales:
            product = self.product_by_id[sale.product_id]

            values = {
                "Sales.SaleID": sale.sale_id,
                "Sales.ProductID": sale.product_id,
                "Sales.Date": sale.sale_date,
                "Sales.Quantity": sale.quantity,
                "Sales.UnitCost": sale.unit_cost,
                "Product.ProductID": product.product_id,
                "Product.Name": product.product_name,
                "Product.Category": product.category,
                "Product.UnitPrice": product.unit_price,
            }

            if all(
                values.get(column) in allowed
                for column, allowed in context.filters.items()
            ):
                result.append(sale)

        return result

    def filter_context(
        self,
        column: str,
        values: Iterable[Any]
    ) -> EvaluationContext:

        return EvaluationContext({
            column: set(values)
        })

    # --------------------------------------------------------
    # Measures
    # --------------------------------------------------------

    def total_sales(self, context: EvaluationContext) -> Decimal:
        return sum(
            (
                self.product_by_id[sale.product_id].unit_price
                * sale.quantity
                for sale in self.rows_in_context(context)
            ),
            Decimal("0")
        )

    def total_quantity(self, context: EvaluationContext) -> int:
        return sum(
            sale.quantity
            for sale in self.rows_in_context(context)
        )

    def total_cost(self, context: EvaluationContext) -> Decimal:
        return sum(
            (
                sale.unit_cost * sale.quantity
                for sale in self.rows_in_context(context)
            ),
            Decimal("0")
        )

    def total_profit(self, context: EvaluationContext) -> Decimal:
        return self.total_sales(context) - self.total_cost(context)

    def average_selling_price(
        self,
        context: EvaluationContext
    ) -> Decimal | None:

        quantity = self.total_quantity(context)

        if quantity == 0:
            return None

        return self.total_sales(context) / quantity

    def profit_margin(self, context: EvaluationContext) -> Decimal | None:
        sales = self.total_sales(context)

        if sales == 0:
            return None

        return self.total_profit(context) / sales * 100

    def sales_count(self, context: EvaluationContext) -> int:
        return len(self.rows_in_context(context))

    # --------------------------------------------------------
    # CALCULATE and context transition
    # --------------------------------------------------------

    def calculate(
        self,
        measure: Callable,
        context: EvaluationContext,
        filters: dict[str, set[Any]] | None = None,
        remove_filters: set[str] | None = None
    ):

        new_context = context.copy()

        # ALL-like behavior: remove selected filters.
        for column in remove_filters or set():
            new_context.filters.pop(column, None)

        # CALCULATE replaces existing filters on the
        # specified columns.
        for column, values in (filters or {}).items():
            new_context.filters[column] = set(values)

        # Context transition: convert row-context values
        # into filter-context values.
        if context.row:
            for column, value in context.row.items():
                new_context.filters[column] = {value}

        return measure(new_context)

    # --------------------------------------------------------
    # FILTER and SUMX
    # --------------------------------------------------------

    def filter_sales(
        self,
        context: EvaluationContext,
        predicate: Callable[[Sale, Product], bool]
    ) -> list[Sale]:

        return [
            sale
            for sale in self.rows_in_context(context)
            if predicate(sale, self.product_by_id[sale.product_id])
        ]

    def sumx(
        self,
        rows: Iterable[Sale],
        expression: Callable[[Sale], Decimal]
    ) -> Decimal:

        return sum(
            (expression(row) for row in rows),
            Decimal("0")
        )

    # --------------------------------------------------------
    # Calculated columns
    # --------------------------------------------------------

    def create_calculated_columns(self):
        columns = []

        for sale in self.sales:
            product = self.product_by_id[sale.product_id]

            # Calculated columns are evaluated row by row.
            columns.append({
                "SaleID": sale.sale_id,
                "Revenue": product.unit_price * sale.quantity,
                "Cost": sale.unit_cost * sale.quantity,
                "Profit": (
                    product.unit_price - sale.unit_cost
                ) * sale.quantity,
                "ProfitCategory": (
                    "High"
                    if product.unit_price > sale.unit_cost * Decimal("1.5")
                    else "Standard"
                ),
            })

        return columns

    # --------------------------------------------------------
    # Calculated tables
    # --------------------------------------------------------

    def create_calculated_tables(self):
        categories = sorted({
            product.category for product in self.products
        })

        return {
            "CategorySummary": [
                {
                    "Category": category,
                    "ProductCount": sum(
                        1 for product in self.products
                        if product.category == category
                    )
                }
                for category in categories
            ],

            "ProductList": [
                {
                    "ProductID": product.product_id,
                    "ProductName": product.product_name,
                    "Category": product.category
                }
                for product in self.products
            ]
        }

    # --------------------------------------------------------
    # VALUES and DISTINCTCOUNT
    # --------------------------------------------------------

    def values(
        self,
        column: str,
        context: EvaluationContext
    ) -> set[Any]:

        values = set()

        for sale in self.rows_in_context(context):
            product = self.product_by_id[sale.product_id]

            mapping = {
                "Product.Category": product.category,
                "Product.Name": product.product_name,
                "Sales.Date": sale.sale_date,
                "Sales.ProductID": sale.product_id,
            }

            if column in mapping:
                values.add(mapping[column])

        return values

    def distinct_count(
        self,
        column: str,
        context: EvaluationContext
    ) -> int:
        return len(self.values(column, context))

    # --------------------------------------------------------
    # Reporting
    # --------------------------------------------------------

    def category_report(self):
        report = []

        for category in sorted({
            product.category for product in self.products
        }):
            context = self.filter_context(
                "Product.Category",
                [category]
            )

            report.append({
                "category": category,
                "sales": self.total_sales(context),
                "quantity": self.total_quantity(context),
                "profit": self.total_profit(context),
                "margin": self.profit_margin(context),
                "transactions": self.sales_count(context)
            })

        return report


def money(value):
    if value is None:
        return None
    return round(value, 2)


def run_tests(model: DAXModel):
    all_context = EvaluationContext({})

    assert model.total_quantity(all_context) == 39
    assert model.total_sales(all_context) == Decimal("4995")
    assert model.total_cost(all_context) == Decimal("2840")
    assert model.total_profit(all_context) == Decimal("2155")

    electronics = model.filter_context(
        "Product.Category",
        ["Electronics"]
    )

    assert model.total_quantity(electronics) == 15
    assert model.total_sales(electronics) == Decimal("3000")

    assert model.calculate(
        model.total_sales,
        electronics,
        remove_filters={"Product.Category"}
    ) == Decimal("4995")

    assert model.distinct_count(
        "Product.Category",
        all_context
    ) == 3

    assert len(model.calculated_columns) == len(model.sales)

    assert len(
        model.calculated_tables["ProductList"]
    ) == len(model.products)

    # Division by zero must not produce an invalid result.
    empty_context = model.filter_context(
        "Sales.ProductID",
        [999]
    )

    assert model.profit_margin(empty_context) is None

    # SUMX evaluates an expression for every filtered row.
    filtered = model.filter_sales(
        all_context,
        lambda sale, product: product.category == "Electronics"
    )

    assert model.sumx(
        filtered,
        lambda sale: (
            model.product_by_id[sale.product_id].unit_price
            * sale.quantity
        )
    ) == Decimal("3000")


def main():
    products = [
        Product(1, "Laptop", "Electronics", Decimal("1000")),
        Product(2, "Phone", "Electronics", Decimal("500")),
        Product(3, "Desk", "Furniture", Decimal("300")),
        Product(4, "Chair", "Furniture", Decimal("200")),
        Product(5, "Notebook", "Stationery", Decimal("50")),
    ]

    sales = [
        Sale(101, 1, date(2026, 1, 10), 2, Decimal("700")),
        Sale(102, 2, date(2026, 1, 11), 4, Decimal("300")),
        Sale(103, 3, date(2026, 1, 12), 3, Decimal("180")),
        Sale(104, 4, date(2026, 1, 13), 5, Decimal("120")),
        Sale(105, 5, date(2026, 1, 14), 10, Decimal("20")),
        Sale(106, 1, date(2026, 2, 10), 1, Decimal("700")),
        Sale(107, 2, date(2026, 2, 11), 2, Decimal("300")),
        Sale(108, 3, date(2026, 2, 12), 4, Decimal("180")),
        Sale(109, 4, date(2026, 2, 13), 3, Decimal("120")),
        Sale(110, 5, date(2026, 2, 14), 5, Decimal("20")),
    ]

    model = DAXModel(products, sales)
    run_tests(model)

    context = EvaluationContext({})

    print("=" * 65)
    print("DAX FUNDAMENTALS: SALES ANALYTICS")
    print("=" * 65)

    print("\nMEASURES")
    for name, measure in model.measures.items():
        print(f"{name}: {measure(context)}")

    print("\nCATEGORY REPORT")
    for item in model.category_report():
        print(
            f"{item['category']:<15}"
            f" Sales={money(item['sales'])}"
            f" Quantity={item['quantity']}"
            f" Profit={money(item['profit'])}"
            f" Margin={money(item['margin'])}%"
        )

    print("\nCALCULATED COLUMNS")
    for row in model.calculated_columns[:3]:
        print(row)

    print("\nCALCULATED TABLES")
    print(json.dumps(
        model.calculated_tables,
        indent=2,
        default=str
    ))

    print("\nFILTER CONTEXT EXAMPLE")
    electronics = model.filter_context(
        "Product.Category",
        ["Electronics"]
    )
    print("Electronics sales:", model.total_sales(electronics))

    print("\nCALCULATE WITH ALL-LIKE FILTER REMOVAL")
    print(
        "All-category sales:",
        model.calculate(
            model.total_sales,
            electronics,
            remove_filters={"Product.Category"}
        )
    )

    print("\nSUMX EXAMPLE")
    print(
        "Total revenue:",
        model.sumx(
            model.sales,
            lambda sale: (
                model.product_by_id[sale.product_id].unit_price
                * sale.quantity
            )
        )
    )

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
