#!/usr/bin/env python3
"""
Power BI Visualization: Cards, Tables, Matrices, Charts, Maps,
Slicers, Drill-through, and Bookmarks.

A self-contained analytical visualization engine using Python's
standard library. It models a realistic retail sales dashboard,
including filtering, aggregation, visualization specifications,
drill-through, and saved dashboard states.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class VisualizationType(Enum):
    CARD = "card"
    TABLE = "table"
    MATRIX = "matrix"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    MAP = "map"


class Aggregation(Enum):
    SUM = "sum"
    COUNT = "count"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    DISTINCT_COUNT = "distinct_count"


class DashboardError(Exception):
    """Base exception for dashboard operations."""


class ValidationError(DashboardError):
    """Invalid data, filter, or visualization configuration."""


class BookmarkNotFoundError(DashboardError):
    """Requested bookmark does not exist."""


class DrillThroughError(DashboardError):
    """Invalid drill-through operation."""


@dataclass(frozen=True)
class SalesRecord:
    transaction_id: int
    transaction_date: date
    region: str
    city: str
    category: str
    product: str
    salesperson: str
    quantity: int
    unit_price: float
    discount: float

    @property
    def gross_sales(self) -> float:
        return self.quantity * self.unit_price

    @property
    def net_sales(self) -> float:
        return self.gross_sales * (1 - self.discount)

    @property
    def profit(self) -> float:
        return self.net_sales * 0.25


@dataclass
class DashboardBookmark:
    name: str
    filters: dict[str, Any]
    selected_visual: str | None
    description: str


@dataclass
class VisualConfiguration:
    name: str
    visual_type: VisualizationType
    dimensions: list[str]
    measures: dict[str, Aggregation]
    title: str


class SalesDashboard:
    VALID_FIELDS = {
        "transaction_id",
        "transaction_date",
        "region",
        "city",
        "category",
        "product",
        "salesperson",
        "quantity",
        "gross_sales",
        "net_sales",
        "profit",
    }

    def __init__(self, records: list[SalesRecord]):
        if not records:
            raise ValidationError("Dataset cannot be empty.")

        self.records = records
        self.filters: dict[str, Any] = {}
        self.bookmarks: dict[str, DashboardBookmark] = {}
        self.selected_visual: str | None = None

        self.visuals = self._configure_visuals()

    @staticmethod
    def _configure_visuals() -> dict[str, VisualConfiguration]:
        return {
            "sales_card": VisualConfiguration(
                "sales_card",
                VisualizationType.CARD,
                [],
                {"net_sales": Aggregation.SUM},
                "Total Net Sales",
            ),
            "regional_table": VisualConfiguration(
                "regional_table",
                VisualizationType.TABLE,
                ["region", "city"],
                {
                    "net_sales": Aggregation.SUM,
                    "profit": Aggregation.SUM,
                },
                "Regional Sales Details",
            ),
            "category_matrix": VisualConfiguration(
                "category_matrix",
                VisualizationType.MATRIX,
                ["region", "category"],
                {"net_sales": Aggregation.SUM},
                "Regional Category Matrix",
            ),
            "category_chart": VisualConfiguration(
                "category_chart",
                VisualizationType.BAR_CHART,
                ["category"],
                {"net_sales": Aggregation.SUM},
                "Sales by Category",
            ),
            "monthly_chart": VisualConfiguration(
                "monthly_chart",
                VisualizationType.LINE_CHART,
                ["month"],
                {"net_sales": Aggregation.SUM},
                "Monthly Sales Trend",
            ),
            "category_share": VisualConfiguration(
                "category_share",
                VisualizationType.PIE_CHART,
                ["category"],
                {"net_sales": Aggregation.SUM},
                "Category Contribution",
            ),
            "regional_map": VisualConfiguration(
                "regional_map",
                VisualizationType.MAP,
                ["region", "city"],
                {"net_sales": Aggregation.SUM},
                "Sales by Location",
            ),
        }

    @staticmethod
    def sample_data() -> list[SalesRecord]:
        raw = [
            (1, "2026-01-05", "North", "Delhi", "Electronics",
             "Laptop", "Amit", 2, 65000, 0.05),
            (2, "2026-01-12", "North", "Lucknow", "Furniture",
             "Chair", "Neha", 5, 4500, 0.10),
            (3, "2026-02-08", "South", "Bengaluru", "Electronics",
             "Mobile", "Rahul", 4, 30000, 0.08),
            (4, "2026-02-15", "West", "Mumbai", "Clothing",
             "Jacket", "Priya", 8, 2500, 0.05),
            (5, "2026-03-03", "East", "Kolkata", "Furniture",
             "Table", "Amit", 3, 12000, 0.12),
            (6, "2026-03-18", "North", "Delhi", "Clothing",
             "Shirt", "Neha", 10, 1200, 0.02),
            (7, "2026-04-10", "South", "Chennai", "Electronics",
             "Laptop", "Rahul", 1, 70000, 0.04),
            (8, "2026-04-20", "West", "Pune", "Furniture",
             "Chair", "Priya", 6, 5000, 0.07),
            (9, "2026-05-05", "East", "Kolkata", "Electronics",
             "Mobile", "Amit", 3, 28000, 0.06),
            (10, "2026-05-17", "North", "Lucknow", "Clothing",
             "Jacket", "Neha", 4, 3000, 0.03),
            (11, "2026-06-02", "South", "Bengaluru", "Furniture",
             "Table", "Rahul", 2, 15000, 0.10),
            (12, "2026-06-19", "West", "Mumbai", "Electronics",
             "Laptop", "Priya", 2, 62000, 0.05),
        ]

        records = [
            SalesRecord(
                transaction_id=row[0],
                transaction_date=date.fromisoformat(row[1]),
                region=row[2],
                city=row[3],
                category=row[4],
                product=row[5],
                salesperson=row[6],
                quantity=row[7],
                unit_price=row[8],
                discount=row[9],
            )
            for row in raw
        ]

        for record in records:
            if record.quantity <= 0:
                raise ValidationError("Quantity must be positive.")
            if record.unit_price < 0:
                raise ValidationError("Unit price cannot be negative.")
            if not 0 <= record.discount <= 1:
                raise ValidationError("Discount must be between 0 and 1.")

        return records

    @staticmethod
    def _value(record: SalesRecord, field: str) -> Any:
        if field == "month":
            return record.transaction_date.strftime("%Y-%m")
        if not hasattr(record, field):
            raise ValidationError(f"Unknown field: {field}")
        return getattr(record, field)

    def apply_slicer(self, field: str, value: Any) -> None:
        """Apply a single-value slicer selection."""
        if field not in self.VALID_FIELDS:
            raise ValidationError(f"Invalid slicer field: {field}")

        self.filters[field] = value

    def apply_range_slicer(
        self, field: str, minimum: float, maximum: float
    ) -> None:
        if field not in self.VALID_FIELDS:
            raise ValidationError(f"Invalid range field: {field}")
        if minimum > maximum:
            raise ValidationError("Minimum cannot exceed maximum.")

        self.filters[field] = (minimum, maximum)

    def apply_multi_select(self, field: str, values: set[Any]) -> None:
        if field not in self.VALID_FIELDS:
            raise ValidationError(f"Invalid slicer field: {field}")
        if not values:
            raise ValidationError("Multi-select cannot be empty.")

        self.filters[field] = frozenset(values)

    def clear_filters(self) -> None:
        self.filters.clear()

    def filtered_records(self) -> list[SalesRecord]:
        result = []

        for record in self.records:
            matches = True

            for field, condition in self.filters.items():
                actual = self._value(record, field)

                if isinstance(condition, tuple):
                    matches &= condition[0] <= actual <= condition[1]
                elif isinstance(condition, frozenset):
                    matches &= actual in condition
                else:
                    matches &= actual == condition

                if not matches:
                    break

            if matches:
                result.append(record)

        return result

    @staticmethod
    def aggregate(
        records: list[SalesRecord],
        field: str,
        operation: Aggregation,
    ) -> float | int:
        values = [getattr(record, field) for record in records]

        if not values:
            return 0

        if operation == Aggregation.SUM:
            return round(sum(values), 2)
        if operation == Aggregation.COUNT:
            return len(values)
        if operation == Aggregation.AVERAGE:
            return round(statistics.mean(values), 2)
        if operation == Aggregation.MIN:
            return min(values)
        if operation == Aggregation.MAX:
            return max(values)
        if operation == Aggregation.DISTINCT_COUNT:
            return len(set(values))

        raise ValidationError("Unsupported aggregation.")

    def card(self, field: str) -> dict[str, Any]:
        records = self.filtered_records()

        if field not in {"net_sales", "profit", "quantity"}:
            raise ValidationError("Unsupported card measure.")

        return {
            "visual_type": "card",
            "title": f"Total {field.replace('_', ' ').title()}",
            "value": self.aggregate(records, field, Aggregation.SUM),
            "record_count": len(records),
        }

    def table(
        self,
        dimensions: list[str],
        measures: list[str],
    ) -> list[dict[str, Any]]:
        if not dimensions:
            raise ValidationError("At least one table dimension is required.")

        for field in dimensions + measures:
            if field not in self.VALID_FIELDS:
                raise ValidationError(f"Invalid table field: {field}")

        grouped: dict[tuple, list[SalesRecord]] = defaultdict(list)

        for record in self.filtered_records():
            key = tuple(self._value(record, field) for field in dimensions)
            grouped[key].append(record)

        output = []

        for key, rows in sorted(grouped.items(), key=lambda item: str(item[0])):
            result = dict(zip(dimensions, key))

            for measure in measures:
                result[measure] = self.aggregate(
                    rows, measure, Aggregation.SUM
                )

            output.append(result)

        return output

    def matrix(
        self,
        row_field: str,
        column_field: str,
        measure: str,
    ) -> dict[str, Any]:
        for field in (row_field, column_field, measure):
            if field not in self.VALID_FIELDS:
                raise ValidationError(f"Invalid matrix field: {field}")

        cells: dict[tuple, float] = defaultdict(float)
        row_labels = set()
        column_labels = set()

        for record in self.filtered_records():
            row = self._value(record, row_field)
            column = self._value(record, column_field)

            row_labels.add(row)
            column_labels.add(column)
            cells[(row, column)] += getattr(record, measure)

        rows = sorted(row_labels)
        columns = sorted(column_labels)

        matrix_data = []

        for row in rows:
            values = {
                column: round(cells[(row, column)], 2)
                for column in columns
            }
            matrix_data.append({
                row_field: row,
                **values,
                "total": round(sum(values.values()), 2),
            })

        return {
            "row_field": row_field,
            "column_field": column_field,
            "measure": measure,
            "columns": columns,
            "rows": matrix_data,
        }

    def chart(
        self,
        dimension: str,
        measure: str,
        chart_type: VisualizationType,
    ) -> dict[str, Any]:
        if chart_type not in {
            VisualizationType.BAR_CHART,
            VisualizationType.LINE_CHART,
            VisualizationType.PIE_CHART,
        }:
            raise ValidationError("Unsupported chart type.")

        if dimension not in self.VALID_FIELDS | {"month"}:
            raise ValidationError("Invalid chart dimension.")

        if measure not in {"net_sales", "profit", "quantity"}:
            raise ValidationError("Invalid chart measure.")

        grouped: dict[Any, float] = defaultdict(float)

        for record in self.filtered_records():
            grouped[self._value(record, dimension)] += getattr(
                record, measure
            )

        data = [
            {"label": str(key), "value": round(value, 2)}
            for key, value in sorted(
                grouped.items(), key=lambda item: str(item[0])
            )
        ]

        return {
            "visual_type": chart_type.value,
            "dimension": dimension,
            "measure": measure,
            "data": data,
        }

    def map_data(self) -> dict[str, Any]:
        """Return geographic aggregates; coordinates are not fabricated."""
        return {
            "visual_type": "map",
            "location_field": "city",
            "data": self.table(
                ["region", "city"], ["net_sales", "profit"]
            ),
            "geocoding_required": True,
        }

    def drill_through(
        self,
        field: str,
        value: Any,
        target_field: str = "product",
    ) -> list[dict[str, Any]]:
        """Navigate from a summary context to detailed transaction rows."""
        if field not in self.VALID_FIELDS:
            raise DrillThroughError("Invalid source field.")
        if target_field not in self.VALID_FIELDS:
            raise DrillThroughError("Invalid target field.")

        matching = [
            record for record in self.filtered_records()
            if self._value(record, field) == value
        ]

        if not matching:
            raise DrillThroughError(
                f"No transactions found for {field}={value!r}"
            )

        return [
            {
                "transaction_id": record.transaction_id,
                "date": record.transaction_date.isoformat(),
                "region": record.region,
                "city": record.city,
                "category": record.category,
                "product": record.product,
                "quantity": record.quantity,
                "net_sales": round(record.net_sales, 2),
                "profit": round(record.profit, 2),
            }
            for record in matching
        ]

    def create_bookmark(
        self,
        name: str,
        description: str = "",
    ) -> None:
        if not name.strip():
            raise ValidationError("Bookmark name cannot be empty.")

        self.bookmarks[name] = DashboardBookmark(
            name=name,
            filters=self.filters.copy(),
            selected_visual=self.selected_visual,
            description=description,
        )

    def restore_bookmark(self, name: str) -> None:
        bookmark = self.bookmarks.get(name)

        if bookmark is None:
            raise BookmarkNotFoundError(name)

        # Replace the filter state rather than merging old and saved filters.
        self.filters = bookmark.filters.copy()
        self.selected_visual = bookmark.selected_visual

    def export_report(self, filename: str) -> None:
        report = {
            "filters": {
                key: (
                    sorted(value, key=str)
                    if isinstance(value, frozenset)
                    else list(value)
                    if isinstance(value, tuple)
                    else value
                )
                for key, value in self.filters.items()
            },
            "cards": {
                "net_sales": self.card("net_sales"),
                "profit": self.card("profit"),
            },
            "category_table": self.table(
                ["category"], ["net_sales", "profit"]
            ),
            "regional_matrix": self.matrix(
                "region", "category", "net_sales"
            ),
            "monthly_chart": self.chart(
                "month", "net_sales", VisualizationType.LINE_CHART
            ),
            "regional_map": self.map_data(),
            "record_count": len(self.filtered_records()),
        }

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8",
        )


def demonstrate() -> None:
    dashboard = SalesDashboard(SalesDashboard.sample_data())

    print("\nPOWER BI VISUALIZATION ENGINE")
    print("=" * 55)

    print("\n1. CARD")
    print(dashboard.card("net_sales"))

    print("\n2. TABLE")
    for row in dashboard.table(
        ["region", "category"], ["net_sales", "profit"]
    ):
        print(row)

    print("\n3. MATRIX")
    print(json.dumps(
        dashboard.matrix("region", "category", "net_sales"),
        indent=2,
    ))

    print("\n4. BAR CHART")
    print(dashboard.chart(
        "category", "net_sales", VisualizationType.BAR_CHART
    ))

    print("\n5. LINE CHART")
    print(dashboard.chart(
        "month", "net_sales", VisualizationType.LINE_CHART
    ))

    print("\n6. PIE CHART")
    print(dashboard.chart(
        "category", "net_sales", VisualizationType.PIE_CHART
    ))

    print("\n7. MAP")
    print(json.dumps(dashboard.map_data(), indent=2))

    print("\n8. SLICERS")
    dashboard.apply_slicer("region", "North")
    dashboard.apply_multi_select(
        "category", {"Electronics", "Clothing"}
    )
    print("Active filters:", dashboard.filters)
    print("Filtered card:", dashboard.card("net_sales"))

    print("\n9. DRILL-THROUGH")
    details = dashboard.drill_through("region", "North")
    for item in details:
        print(item)

    print("\n10. BOOKMARKS")
    dashboard.create_bookmark(
        "North_Overview",
        "Northern region sales analysis",
    )
    dashboard.clear_filters()
    dashboard.restore_bookmark("North_Overview")
    print("Restored filters:", dashboard.filters)

    print("\n11. VALIDATION")
    try:
        dashboard.apply_slicer("unknown_column", "value")
    except ValidationError as error:
        print("Expected validation error:", error)

    print("\n12. EXPORT")
    dashboard.export_report("powerbi_output/dashboard.json")
    print("Report exported to powerbi_output/dashboard.json")

    print("\n13. FILTER RESET")
    dashboard.clear_filters()
    print("Unfiltered records:", len(dashboard.filtered_records()))


if __name__ == "__main__":
    demonstrate()
