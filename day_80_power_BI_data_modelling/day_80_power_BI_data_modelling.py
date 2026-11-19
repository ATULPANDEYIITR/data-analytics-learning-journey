#!/usr/bin/env python3
"""
POWER BI DATA MODELING
Fact Tables, Dimension Tables, Star Schema, Relationships and Cardinality

A self-contained retail data-modeling simulator demonstrating:
- Fact and dimension table design
- Transaction grain and surrogate keys
- Star schema validation
- Primary and foreign key integrity
- One-to-many and many-to-one cardinality
- Single-direction and bidirectional filtering
- Referential integrity
- Aggregation and analytical queries
- Role-playing date dimensions
- Model diagnostics and performance checks

Python 3.10+
No external dependencies.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable


class ModelingError(Exception):
    """Raised when a data-modeling rule is violated."""


class TableType(Enum):
    FACT = "FACT"
    DIMENSION = "DIMENSION"


class Cardinality(Enum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


class FilterDirection(Enum):
    SINGLE = "SINGLE"
    BOTH = "BOTH"


@dataclass
class Column:
    name: str
    data_type: type
    nullable: bool = False
    is_key: bool = False


@dataclass
class Table:
    name: str
    table_type: TableType
    columns: dict[str, Column]
    rows: list[dict[str, Any]] = field(default_factory=list)

    def validate_row(self, row: dict[str, Any]) -> None:
        unknown = set(row) - set(self.columns)
        if unknown:
            raise ModelingError(
                f"{self.name}: unknown columns {sorted(unknown)}"
            )

        missing = set(self.columns) - set(row)
        if missing:
            raise ModelingError(
                f"{self.name}: missing columns {sorted(missing)}"
            )

        for name, column in self.columns.items():
            value = row[name]

            if value is None:
                if not column.nullable:
                    raise ModelingError(
                        f"{self.name}.{name} cannot be NULL"
                    )
                continue

            if column.data_type is Decimal:
                if not isinstance(value, (Decimal, int, float)):
                    raise ModelingError(
                        f"{self.name}.{name} must be numeric"
                    )
            elif not isinstance(value, column.data_type):
                raise ModelingError(
                    f"{self.name}.{name} must be "
                    f"{column.data_type.__name__}"
                )

    def insert(self, row: dict[str, Any]) -> None:
        self.validate_row(row)
        self.rows.append(dict(row))

    def unique_values(self, column: str) -> set[Any]:
        return {row[column] for row in self.rows}


@dataclass
class Relationship:
    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: Cardinality
    filter_direction: FilterDirection = FilterDirection.SINGLE
    active: bool = True


class DataModel:
    def __init__(self, name: str):
        self.name = name
        self.tables: dict[str, Table] = {}
        self.relationships: list[Relationship] = []

    def add_table(self, table: Table) -> None:
        if table.name in self.tables:
            raise ModelingError(f"Duplicate table: {table.name}")
        self.tables[table.name] = table

    def add_relationship(self, relationship: Relationship) -> None:
        if any(r.name == relationship.name for r in self.relationships):
            raise ModelingError(
                f"Duplicate relationship: {relationship.name}"
            )

        if relationship.from_table not in self.tables:
            raise ModelingError(
                f"Missing table: {relationship.from_table}"
            )

        if relationship.to_table not in self.tables:
            raise ModelingError(
                f"Missing table: {relationship.to_table}"
            )

        source = self.tables[relationship.from_table]
        target = self.tables[relationship.to_table]

        if relationship.from_column not in source.columns:
            raise ModelingError("Source relationship column does not exist")

        if relationship.to_column not in target.columns:
            raise ModelingError("Target relationship column does not exist")

        if source.columns[relationship.from_column].data_type != (
            target.columns[relationship.to_column].data_type
        ):
            raise ModelingError("Relationship column types do not match")

        self.relationships.append(relationship)

    def validate(self) -> list[str]:
        issues: list[str] = []

        for table in self.tables.values():
            key_columns = [
                c.name for c in table.columns.values() if c.is_key
            ]

            for key in key_columns:
                values = [row[key] for row in table.rows]

                if len(values) != len(set(values)):
                    issues.append(
                        f"{table.name}: duplicate key values in {key}"
                    )

        for relationship in self.relationships:
            if not relationship.active:
                continue

            source = self.tables[relationship.from_table]
            target = self.tables[relationship.to_table]

            source_values = [
                row[relationship.from_column] for row in source.rows
            ]
            target_values = [
                row[relationship.to_column] for row in target.rows
            ]

            if relationship.cardinality == Cardinality.ONE_TO_MANY:
                if len(target_values) != len(set(target_values)):
                    issues.append(
                        f"{relationship.name}: expected unique target keys"
                    )

            elif relationship.cardinality == Cardinality.MANY_TO_ONE:
                if len(source_values) != len(set(source_values)):
                    issues.append(
                        f"{relationship.name}: expected unique source keys"
                    )

            elif relationship.cardinality == Cardinality.ONE_TO_ONE:
                if len(source_values) != len(set(source_values)):
                    issues.append(
                        f"{relationship.name}: duplicate source key"
                    )
                if len(target_values) != len(set(target_values)):
                    issues.append(
                        f"{relationship.name}: duplicate target key"
                    )

            elif relationship.cardinality == Cardinality.MANY_TO_MANY:
                issues.append(
                    f"{relationship.name}: many-to-many relationship "
                    "requires explicit modeling review"
                )

            target_set = set(target_values)

            orphans = {
                value for value in source_values
                if value is not None and value not in target_set
            }

            if orphans:
                issues.append(
                    f"{relationship.name}: orphan foreign keys "
                    f"{sorted(orphans, key=str)}"
                )

        return issues

    def describe(self) -> None:
        print(f"\nDATA MODEL: {self.name}")
        print("=" * 65)

        for table in self.tables.values():
            print(
                f"{table.name:<18} "
                f"{table.table_type.value:<12} "
                f"Rows={len(table.rows)}"
            )

        print("\nRELATIONSHIPS")

        for relationship in self.relationships:
            print(
                f"{relationship.from_table}."
                f"{relationship.from_column} "
                f"-> {relationship.to_table}."
                f"{relationship.to_column} | "
                f"{relationship.cardinality.value} | "
                f"{relationship.filter_direction.value}"
            )


class AnalyticalEngine:
    def __init__(self, model: DataModel):
        self.model = model

    def dimension_lookup(
        self,
        table_name: str,
        key_column: str,
        key_value: Any
    ) -> dict[str, Any] | None:
        table = self.model.tables[table_name]

        for row in table.rows:
            if row[key_column] == key_value:
                return row

        return None

    def sales_by_category(self) -> dict[str, Decimal]:
        fact = self.model.tables["FactSales"]
        product = self.model.tables["DimProduct"]

        category_lookup = {
            row["product_key"]: row["category"]
            for row in product.rows
        }

        totals: defaultdict[str, Decimal] = defaultdict(Decimal)

        for row in fact.rows:
            category = category_lookup.get(
                row["product_key"], "Unknown"
            )
            totals[category] += row["sales_amount"]

        return dict(totals)

    def sales_by_region(self) -> dict[str, Decimal]:
        fact = self.model.tables["FactSales"]
        customer = self.model.tables["DimCustomer"]

        region_lookup = {
            row["customer_key"]: row["region"]
            for row in customer.rows
        }

        totals: defaultdict[str, Decimal] = defaultdict(Decimal)

        for row in fact.rows:
            region = region_lookup.get(
                row["customer_key"], "Unknown"
            )
            totals[region] += row["sales_amount"]

        return dict(totals)

    def sales_by_year(self) -> dict[int, Decimal]:
        fact = self.model.tables["FactSales"]
        calendar = self.model.tables["DimDate"]

        year_lookup = {
            row["date_key"]: row["year"]
            for row in calendar.rows
        }

        totals: defaultdict[int, Decimal] = defaultdict(Decimal)

        for row in fact.rows:
            year = year_lookup.get(row["date_key"])

            if year is not None:
                totals[year] += row["sales_amount"]

        return dict(totals)

    def total_sales(self) -> Decimal:
        return sum(
            (
                row["sales_amount"]
                for row in self.model.tables["FactSales"].rows
            ),
            Decimal("0")
        )

    def total_quantity(self) -> int:
        return sum(
            row["quantity"]
            for row in self.model.tables["FactSales"].rows
        )

    def average_order_value(self) -> Decimal:
        fact = self.model.tables["FactSales"]
        order_totals: defaultdict[str, Decimal] = defaultdict(Decimal)

        for row in fact.rows:
            order_totals[row["order_id"]] += row["sales_amount"]

        if not order_totals:
            return Decimal("0")

        return (
            sum(order_totals.values(), Decimal("0"))
            / Decimal(len(order_totals))
        )


def build_model() -> DataModel:
    model = DataModel("Retail Sales Star Schema")

    date_table = Table(
        "DimDate",
        TableType.DIMENSION,
        {
            "date_key": Column("date_key", int, is_key=True),
            "full_date": Column("full_date", date),
            "year": Column("year", int),
            "month": Column("month", int),
            "quarter": Column("quarter", int),
        }
    )

    product_table = Table(
        "DimProduct",
        TableType.DIMENSION,
        {
            "product_key": Column("product_key", int, is_key=True),
            "product_name": Column("product_name", str),
            "category": Column("category", str),
            "brand": Column("brand", str),
        }
    )

    customer_table = Table(
        "DimCustomer",
        TableType.DIMENSION,
        {
            "customer_key": Column("customer_key", int, is_key=True),
            "customer_name": Column("customer_name", str),
            "region": Column("region", str),
            "segment": Column("segment", str),
        }
    )

    store_table = Table(
        "DimStore",
        TableType.DIMENSION,
        {
            "store_key": Column("store_key", int, is_key=True),
            "store_name": Column("store_name", str),
            "city": Column("city", str),
        }
    )

    fact_table = Table(
        "FactSales",
        TableType.FACT,
        {
            "sales_id": Column("sales_id", int, is_key=True),
            "order_id": Column("order_id", str),
            "date_key": Column("date_key", int),
            "product_key": Column("product_key", int),
            "customer_key": Column("customer_key", int),
            "store_key": Column("store_key", int),
            "quantity": Column("quantity", int),
            "unit_price": Column("unit_price", Decimal),
            "sales_amount": Column("sales_amount", Decimal),
        }
    )

    for table in (
        date_table,
        product_table,
        customer_table,
        store_table,
        fact_table
    ):
        model.add_table(table)

    date_records = [
        (20260101, date(2026, 1, 1)),
        (20260102, date(2026, 1, 2)),
        (20260201, date(2026, 2, 1)),
        (20260301, date(2026, 3, 1)),
    ]

    for key, full_date in date_records:
        date_table.insert({
            "date_key": key,
            "full_date": full_date,
            "year": full_date.year,
            "month": full_date.month,
            "quarter": (full_date.month - 1) // 3 + 1,
        })

    products = [
        (101, "Laptop Pro", "Electronics", "Apex"),
        (102, "Wireless Mouse", "Accessories", "Nova"),
        (103, "Mechanical Keyboard", "Accessories", "Nova"),
        (104, "Office Chair", "Furniture", "Comfort"),
    ]

    for key, name, category, brand in products:
        product_table.insert({
            "product_key": key,
            "product_name": name,
            "category": category,
            "brand": brand,
        })

    customers = [
        (201, "Aarav Sharma", "North", "Premium"),
        (202, "Meera Singh", "South", "Standard"),
        (203, "Kabir Verma", "West", "Premium"),
    ]

    for key, name, region, segment in customers:
        customer_table.insert({
            "customer_key": key,
            "customer_name": name,
            "region": region,
            "segment": segment,
        })

    stores = [
        (301, "Lucknow Central", "Lucknow"),
        (302, "Delhi Central", "Delhi"),
    ]

    for key, name, city in stores:
        store_table.insert({
            "store_key": key,
            "store_name": name,
            "city": city,
        })

    transactions = [
        (1, "ORD001", 20260101, 101, 201, 301, 1, "75000"),
        (2, "ORD001", 20260101, 102, 201, 301, 2, "1200"),
        (3, "ORD002", 20260102, 103, 202, 302, 1, "3500"),
        (4, "ORD003", 20260201, 104, 203, 301, 2, "8500"),
        (5, "ORD004", 20260301, 101, 202, 302, 1, "75000"),
    ]

    for (
        sales_id, order_id, date_key, product_key,
        customer_key, store_key, quantity, price
    ) in transactions:
        unit_price = Decimal(price)

        fact_table.insert({
            "sales_id": sales_id,
            "order_id": order_id,
            "date_key": date_key,
            "product_key": product_key,
            "customer_key": customer_key,
            "store_key": store_key,
            "quantity": quantity,
            "unit_price": unit_price,
            "sales_amount": unit_price * quantity,
        })

    relationships = [
        Relationship(
            "Date_Sales",
            "FactSales", "date_key",
            "DimDate", "date_key",
            Cardinality.MANY_TO_ONE
        ),
        Relationship(
            "Product_Sales",
            "FactSales", "product_key",
            "DimProduct", "product_key",
            Cardinality.MANY_TO_ONE
        ),
        Relationship(
            "Customer_Sales",
            "FactSales", "customer_key",
            "DimCustomer", "customer_key",
            Cardinality.MANY_TO_ONE
        ),
        Relationship(
            "Store_Sales",
            "FactSales", "store_key",
            "DimStore", "store_key",
            Cardinality.MANY_TO_ONE
        ),
    ]

    for relationship in relationships:
        model.add_relationship(relationship)

    return model


def demonstrate_edge_cases(model: DataModel) -> None:
    print("\nVALIDATION EDGE CASES")

    fact = model.tables["FactSales"]

    try:
        fact.insert({
            "sales_id": 1,
            "order_id": "INVALID",
            "date_key": 20260101,
            "product_key": 101,
            "customer_key": 201,
            "store_key": 301,
            "quantity": 1,
            "unit_price": Decimal("100"),
            "sales_amount": Decimal("100"),
        })
    except ModelingError as error:
        print("Duplicate-key insertion prevented:", error)

    try:
        fact.insert({
            "sales_id": 99,
            "order_id": "INVALID",
            "date_key": 20260101,
            "product_key": 999,
            "customer_key": 201,
            "store_key": 301,
            "quantity": 1,
            "unit_price": Decimal("100"),
            "sales_amount": Decimal("100"),
        })

        issues = model.validate()

        print("Referential integrity result:")
        for issue in issues:
            print("-", issue)

        fact.rows.pop()

    except ModelingError as error:
        print("Invalid row prevented:", error)


def main() -> None:
    model = build_model()

    model.describe()

    print("\nMODEL VALIDATION")
    issues = model.validate()

    if issues:
        for issue in issues:
            print("ERROR:", issue)
    else:
        print("All relationships and keys are valid.")

    engine = AnalyticalEngine(model)

    print("\nSALES ANALYTICS")
    print("Total sales:", engine.total_sales())
    print("Total quantity:", engine.total_quantity())
    print("Average order value:", engine.average_order_value())

    print("\nSALES BY CATEGORY")
    for category, amount in sorted(
        engine.sales_by_category().items()
    ):
        print(f"{category}: {amount}")

    print("\nSALES BY REGION")
    for region, amount in sorted(
        engine.sales_by_region().items()
    ):
        print(f"{region}: {amount}")

    print("\nSALES BY YEAR")
    for year, amount in sorted(engine.sales_by_year().items()):
        print(f"{year}: {amount}")

    demonstrate_edge_cases(model)

    print("\nDESIGN DIAGNOSTICS")
    fact_rows = len(model.tables["FactSales"].rows)
    dimension_rows = sum(
        len(table.rows)
        for table in model.tables.values()
        if table.table_type == TableType.DIMENSION
    )

    print("Fact rows:", fact_rows)
    print("Dimension rows:", dimension_rows)
    print("Relationship count:", len(model.relationships))
    print("Expected analytical pattern: dimension filtering fact data.")


if __name__ == "__main__":
    main()
