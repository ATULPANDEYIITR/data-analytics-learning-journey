#!/usr/bin/env python3
"""
POWER BI INTRODUCTION
Business Intelligence Concepts, Data Modeling, Reporting and Dashboard Simulation

A self-contained simulation of a Business Intelligence workflow:
1. Load and validate business data.
2. Transform transactional records.
3. Build a star schema.
4. Calculate business measures.
5. Apply filters and aggregations.
6. Generate report pages and dashboard KPIs.
7. Simulate refresh operations and data-quality failures.
8. Export analytical results to CSV and JSON.

Python 3.10+
No external dependencies.
"""

from __future__ import annotations

import csv
import json
import logging
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("power_bi_simulation")


# ============================================================
# 1. DOMAIN ENUMS
# ============================================================

class RefreshStatus(Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ReportType(Enum):
    SALES = "sales"
    CUSTOMER = "customer"
    PRODUCT = "product"
    FINANCIAL = "financial"


class FilterOperator(Enum):
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"


# ============================================================
# 2. DATA MODELS
# ============================================================

@dataclass(frozen=True)
class Customer:
    customer_id: int
    customer_name: str
    region: str
    segment: str


@dataclass(frozen=True)
class Product:
    product_id: int
    product_name: str
    category: str
    unit_cost: float


@dataclass(frozen=True)
class SalesTransaction:
    transaction_id: int
    customer_id: int
    product_id: int
    transaction_date: date
    quantity: int
    unit_price: float

    @property
    def revenue(self) -> float:
        return self.quantity * self.unit_price

    @property
    def cost(self) -> float:
        return self.quantity


@dataclass
class DataQualityReport:
    total_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BusinessFilter:
    field_name: str
    operator: FilterOperator
    value: Any


# ============================================================
# 3. SAMPLE BUSINESS DATA
# ============================================================

def create_sample_data():
    customers = [
        Customer(1, "Aarav Sharma", "North", "Enterprise"),
        Customer(2, "Meera Verma", "South", "Consumer"),
        Customer(3, "Rohan Gupta", "East", "Enterprise"),
        Customer(4, "Ananya Singh", "West", "Consumer"),
        Customer(5, "Kabir Patel", "North", "Small Business"),
    ]

    products = [
        Product(101, "Laptop", "Electronics", 45000),
        Product(102, "Monitor", "Electronics", 12000),
        Product(103, "Office Chair", "Furniture", 5000),
        Product(104, "Desk", "Furniture", 8000),
        Product(105, "Keyboard", "Accessories", 1000),
    ]

    transactions = [
        SalesTransaction(1001, 1, 101, date(2026, 1, 10), 2, 65000),
        SalesTransaction(1002, 2, 102, date(2026, 1, 15), 3, 18000),
        SalesTransaction(1003, 3, 103, date(2026, 2, 5), 5, 8500),
        SalesTransaction(1004, 4, 104, date(2026, 2, 12), 2, 12000),
        SalesTransaction(1005, 1, 105, date(2026, 3, 1), 10, 1800),
        SalesTransaction(1006, 5, 101, date(2026, 3, 15), 1, 68000),
        SalesTransaction(1007, 3, 102, date(2026, 4, 2), 4, 17500),
        SalesTransaction(1008, 2, 103, date(2026, 4, 8), 3, 9000),
        SalesTransaction(1009, 4, 105, date(2026, 5, 10), 15, 1600),
        SalesTransaction(1010, 5, 104, date(2026, 5, 18), 3, 12500),
    ]

    return customers, products, transactions


# ============================================================
# 4. DATA VALIDATION AND TRANSFORMATION
# ============================================================

class DataValidationError(Exception):
    pass


class DataTransformer:

    @staticmethod
    def validate(
        customers: list[Customer],
        products: list[Product],
        transactions: list[SalesTransaction],
    ) -> DataQualityReport:

        report = DataQualityReport(total_records=len(transactions))

        customer_ids = {c.customer_id for c in customers}
        product_ids = {p.product_id for p in products}

        if len(customer_ids) != len(customers):
            raise DataValidationError("Duplicate customer identifiers.")

        if len(product_ids) != len(products):
            raise DataValidationError("Duplicate product identifiers.")

        for transaction in transactions:
            errors = []

            if transaction.transaction_id <= 0:
                errors.append("Invalid transaction identifier")

            if transaction.customer_id not in customer_ids:
                errors.append("Unknown customer")

            if transaction.product_id not in product_ids:
                errors.append("Unknown product")

            if transaction.quantity <= 0:
                errors.append("Quantity must be positive")

            if transaction.unit_price < 0:
                errors.append("Unit price cannot be negative")

            if errors:
                report.rejected_records += 1
                report.errors.append(
                    f"Transaction {transaction.transaction_id}: "
                    + ", ".join(errors)
                )
            else:
                report.valid_records += 1

        return report

    @staticmethod
    def transform(
        customers: list[Customer],
        products: list[Product],
        transactions: list[SalesTransaction],
    ) -> list[dict[str, Any]]:

        customer_lookup = {c.customer_id: c for c in customers}
        product_lookup = {p.product_id: p for p in products}

        transformed = []

        for transaction in transactions:
            customer = customer_lookup.get(transaction.customer_id)
            product = product_lookup.get(transaction.product_id)

            if customer is None or product is None:
                continue

            if transaction.quantity <= 0 or transaction.unit_price < 0:
                continue

            revenue = transaction.revenue
            cost = transaction.quantity * product.unit_cost

            transformed.append({
                "transaction_id": transaction.transaction_id,
                "date": transaction.transaction_date.isoformat(),
                "year": transaction.transaction_date.year,
                "month": transaction.transaction_date.month,
                "customer_id": customer.customer_id,
                "customer_name": customer.customer_name,
                "region": customer.region,
                "segment": customer.segment,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "quantity": transaction.quantity,
                "unit_price": transaction.unit_price,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "profit": round(revenue - cost, 2),
            })

        return transformed


# ============================================================
# 5. STAR SCHEMA SIMULATION
# ============================================================

class StarSchema:

    def __init__(self, records: list[dict[str, Any]]):
        self.fact_sales = records

        self.dim_customer = {
            r["customer_id"]: {
                "customer_id": r["customer_id"],
                "customer_name": r["customer_name"],
                "region": r["region"],
                "segment": r["segment"],
            }
            for r in records
        }

        self.dim_product = {
            r["product_id"]: {
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "category": r["category"],
            }
            for r in records
        }

        self.dim_date = {
            r["date"]: {
                "date": r["date"],
                "year": r["year"],
                "month": r["month"],
            }
            for r in records
        }

    def describe(self):
        return {
            "fact_table": "fact_sales",
            "fact_rows": len(self.fact_sales),
            "dimension_tables": {
                "dim_customer": len(self.dim_customer),
                "dim_product": len(self.dim_product),
                "dim_date": len(self.dim_date),
            },
        }


# ============================================================
# 6. DAX-STYLE BUSINESS MEASURES
# ============================================================

class Measures:

    @staticmethod
    def total_sales(records):
        return round(sum(r["revenue"] for r in records), 2)

    @staticmethod
    def total_cost(records):
        return round(sum(r["cost"] for r in records), 2)

    @staticmethod
    def total_profit(records):
        return round(sum(r["profit"] for r in records), 2)

    @staticmethod
    def total_quantity(records):
        return sum(r["quantity"] for r in records)

    @staticmethod
    def transaction_count(records):
        return len(records)

    @staticmethod
    def average_order_value(records):
        count = len(records)
        if not count:
            return 0.0
        return round(
            Measures.total_sales(records) / count,
            2
        )

    @staticmethod
    def profit_margin(records):
        revenue = Measures.total_sales(records)

        if revenue == 0:
            return 0.0

        return round(
            Measures.total_profit(records) / revenue * 100,
            2
        )

    @staticmethod
    def distinct_customers(records):
        return len({r["customer_id"] for r in records})


# ============================================================
# 7. FILTER CONTEXT AND REPORT ENGINE
# ============================================================

class ReportEngine:

    def __init__(self, records):
        self.records = records

    @staticmethod
    def matches(record, business_filter: BusinessFilter):

        actual = record.get(business_filter.field_name)
        expected = business_filter.value

        if actual is None:
            return False

        if business_filter.operator == FilterOperator.EQUALS:
            return actual == expected

        if business_filter.operator == FilterOperator.GREATER_THAN:
            return actual > expected

        if business_filter.operator == FilterOperator.LESS_THAN:
            return actual < expected

        if business_filter.operator == FilterOperator.CONTAINS:
            return str(expected).lower() in str(actual).lower()

        raise ValueError("Unsupported filter operator.")

    def apply_filters(self, filters: list[BusinessFilter]):
        records = self.records

        for business_filter in filters:
            records = [
                record for record in records
                if self.matches(record, business_filter)
            ]

        return records

    def group_by(self, records, dimension, measure="revenue"):

        groups = defaultdict(float)

        for record in records:
            groups[record[dimension]] += record[measure]

        return {
            key: round(value, 2)
            for key, value in sorted(groups.items())
        }

    def build_report(self, report_type: ReportType):

        if report_type == ReportType.SALES:
            dimension = "region"
        elif report_type == ReportType.CUSTOMER:
            dimension = "customer_name"
        elif report_type == ReportType.PRODUCT:
            dimension = "product_name"
        elif report_type == ReportType.FINANCIAL:
            dimension = "category"
        else:
            raise ValueError("Unsupported report type.")

        return {
            "report_type": report_type.value,
            "generated_at": datetime.now().isoformat(),
            "total_revenue": Measures.total_sales(self.records),
            "total_profit": Measures.total_profit(self.records),
            "profit_margin": Measures.profit_margin(self.records),
            "dimension": dimension,
            "visualization_data": self.group_by(
                self.records, dimension
            ),
        }


# ============================================================
# 8. DASHBOARD KPI MANAGEMENT
# ============================================================

@dataclass
class KPI:
    name: str
    value: float
    unit: str
    description: str


class Dashboard:

    def __init__(self, records):
        self.records = records
        self.kpis: list[KPI] = []

    def calculate(self):

        self.kpis = [
            KPI(
                "Total Revenue",
                Measures.total_sales(self.records),
                "INR",
                "Total recognized sales value",
            ),
            KPI(
                "Total Profit",
                Measures.total_profit(self.records),
                "INR",
                "Revenue minus calculated product cost",
            ),
            KPI(
                "Profit Margin",
                Measures.profit_margin(self.records),
                "%",
                "Profit divided by revenue",
            ),
            KPI(
                "Orders",
                Measures.transaction_count(self.records),
                "count",
                "Number of sales transactions",
            ),
            KPI(
                "Customers",
                Measures.distinct_customers(self.records),
                "count",
                "Unique customers represented in sales",
            ),
        ]

        return self.kpis

    def display(self):

        if not self.kpis:
            self.calculate()

        print("\n" + "=" * 65)
        print("POWER BI STYLE EXECUTIVE DASHBOARD")
        print("=" * 65)

        for kpi in self.kpis:
            print(
                f"{kpi.name:20} "
                f"{kpi.value:>15,.2f} {kpi.unit}"
            )

        print("=" * 65)


# ============================================================
# 9. DATA REFRESH SIMULATION
# ============================================================

class RefreshManager:

    def __init__(self):
        self.status = RefreshStatus.NOT_STARTED
        self.last_refresh: Optional[datetime] = None
        self.error: Optional[str] = None

    def refresh(self, operation):

        if self.status == RefreshStatus.RUNNING:
            raise RuntimeError("Refresh already running.")

        self.status = RefreshStatus.RUNNING
        self.error = None

        try:
            result = operation()
            self.status = RefreshStatus.SUCCEEDED
            self.last_refresh = datetime.now()
            logger.info("Data refresh completed successfully.")
            return result

        except Exception as exc:
            self.status = RefreshStatus.FAILED
            self.error = str(exc)
            logger.exception("Data refresh failed.")
            raise

    def get_status(self):

        return {
            "status": self.status.value,
            "last_refresh": (
                self.last_refresh.isoformat()
                if self.last_refresh else None
            ),
            "error": self.error,
        }


# ============================================================
# 10. EXPORT AND FILE HANDLING
# ============================================================

def export_json(data, filename):

    path = Path(filename)

    path.write_text(
        json.dumps(data, indent=4, default=str),
        encoding="utf-8",
    )

    logger.info("JSON exported to %s", path.resolve())


def export_csv(records, filename):

    if not records:
        raise ValueError("Cannot export an empty dataset.")

    path = Path(filename)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys()),
        )
        writer.writeheader()
        writer.writerows(records)

    logger.info("CSV exported to %s", path.resolve())


# ============================================================
# 11. BUSINESS INTELLIGENCE ANALYTICS
# ============================================================

def monthly_sales_analysis(records):

    monthly = defaultdict(float)

    for record in records:
        key = (record["year"], record["month"])
        monthly[key] += record["revenue"]

    result = []

    previous = None

    for (year, month), revenue in sorted(monthly.items()):

        growth = None

        if previous is not None and previous != 0:
            growth = round(
                (revenue - previous) / previous * 100,
                2,
            )

        result.append({
            "year": year,
            "month": month,
            "revenue": round(revenue, 2),
            "growth_percent": growth,
        })

        previous = revenue

    return result


def identify_top_products(records, limit=3):

    totals = defaultdict(float)

    for record in records:
        totals[record["product_name"]] += record["revenue"]

    return sorted(
        totals.items(),
        key=lambda item: (-item[1], item[0]),
    )[:limit]


def calculate_statistical_metrics(records):

    values = [r["revenue"] for r in records]

    if not values:
        return {
            "mean": 0,
            "median": 0,
            "standard_deviation": 0,
        }

    return {
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "standard_deviation": round(
            statistics.pstdev(values), 2
        ),
    }


# ============================================================
# 12. MAIN APPLICATION
# ============================================================

def main():

    print("\nPOWER BI INTRODUCTION")
    print("Business Intelligence Architecture Simulation")
    print("-" * 65)

    customers, products, transactions = create_sample_data()

    quality = DataTransformer.validate(
        customers, products, transactions
    )

    print("\nDATA QUALITY")
    print(asdict(quality))

    if quality.rejected_records:
        raise DataValidationError(
            "Data quality validation failed."
        )

    refresh_manager = RefreshManager()

    def pipeline():

        transformed = DataTransformer.transform(
            customers, products, transactions
        )

        if not transformed:
            raise ValueError("No valid records available.")

        return transformed

    records = refresh_manager.refresh(pipeline)

    print("\nREFRESH STATUS")
    print(refresh_manager.get_status())

    schema = StarSchema(records)

    print("\nDATA MODEL")
    print(json.dumps(schema.describe(), indent=4))

    dashboard = Dashboard(records)
    dashboard.calculate()
    dashboard.display()

    report_engine = ReportEngine(records)

    print("\nSALES REPORT")
    sales_report = report_engine.build_report(
        ReportType.SALES
    )
    print(json.dumps(sales_report, indent=4))

    print("\nPRODUCT REPORT")
    product_report = report_engine.build_report(
        ReportType.PRODUCT
    )
    print(json.dumps(product_report, indent=4))

    print("\nFILTERED ANALYSIS: NORTH REGION")

    north_records = report_engine.apply_filters([
        BusinessFilter(
            "region",
            FilterOperator.EQUALS,
            "North",
        )
    ])

    print({
        "revenue": Measures.total_sales(north_records),
        "profit": Measures.total_profit(north_records),
        "transactions": Measures.transaction_count(
            north_records
        ),
    })

    print("\nMONTHLY SALES")
    print(json.dumps(
        monthly_sales_analysis(records),
        indent=4,
    ))

    print("\nTOP PRODUCTS")
    print(identify_top_products(records))

    print("\nSTATISTICAL METRICS")
    print(calculate_statistical_metrics(records))

    export_json(
        sales_report,
        "power_bi_sales_report.json",
    )

    export_csv(
        records,
        "power_bi_fact_sales.csv",
    )

    # Edge case: zero-valued revenue must not cause division by zero.
    assert Measures.profit_margin([]) == 0.0
    assert Measures.average_order_value([]) == 0.0

    # Business rule: every transaction must reference a known entity.
    assert len(records) == quality.valid_records

    # Revenue reconciliation.
    assert abs(
        Measures.total_sales(records)
        - sum(r["revenue"] for r in records)
    ) < 0.01

    print("\nALL VALIDATION ASSERTIONS PASSED.")
    print("BI simulation completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except (DataValidationError, ValueError, RuntimeError) as error:
        logger.error("Application stopped: %s", error)
        raise SystemExit(1)
