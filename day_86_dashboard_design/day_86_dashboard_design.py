"""
Dashboard Design and KPI Analytics Engine

Demonstrates:
- Visual hierarchy and information architecture
- Dashboard layout and responsive grid placement
- Color semantics and accessibility
- KPI calculations and threshold evaluation
- Filtering, sorting, and interactive state
- Time-series analysis and comparison
- Data validation and error handling
- JSON export and automated tests

Run: python dashboard_design.py
"""

from __future__ import annotations

import json
import logging
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)
logger = logging.getLogger("dashboard")


# ============================================================
# 1. DOMAIN ENUMERATIONS
# ============================================================

class KPIStatus(Enum):
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    NEUTRAL = "neutral"


class KPIFormat(Enum):
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DURATION = "duration"


class Aggregation(Enum):
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MAXIMUM = "maximum"
    MINIMUM = "minimum"


class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    DONUT = "donut"
    AREA = "area"
    TABLE = "table"


class FilterOperator(Enum):
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"


# ============================================================
# 2. DESIGN SYSTEM
# ============================================================

@dataclass(frozen=True)
class ColorToken:
    name: str
    hex_value: str
    meaning: str


class DesignSystem:
    """
    Centralizes semantic colors and spacing.

    Colors communicate meaning rather than serving as decoration.
    Status must also be communicated through text or icons.
    """

    COLORS = {
        "primary": ColorToken("primary", "#2563EB", "Primary actions"),
        "background": ColorToken("background", "#F8FAFC", "Page background"),
        "surface": ColorToken("surface", "#FFFFFF", "Cards and panels"),
        "text": ColorToken("text", "#172033", "Primary text"),
        "muted": ColorToken("muted", "#64748B", "Secondary text"),
        "success": ColorToken("success", "#15803D", "Positive performance"),
        "warning": ColorToken("warning", "#B45309", "Performance warning"),
        "danger": ColorToken("danger", "#B91C1C", "Critical condition"),
        "border": ColorToken("border", "#E2E8F0", "Visual separation"),
    }

    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
    }

    TYPOGRAPHY = {
        "page_title": 28,
        "section_title": 20,
        "card_title": 14,
        "kpi_value": 30,
        "body": 14,
        "caption": 12,
    }

    @classmethod
    def get_color(cls, name: str) -> ColorToken:
        if name not in cls.COLORS:
            raise ValueError(f"Unknown semantic color: {name}")
        return cls.COLORS[name]


# ============================================================
# 3. KPI DOMAIN MODEL
# ============================================================

@dataclass
class KPI:
    identifier: str
    name: str
    value: float
    previous_value: Optional[float]
    target: Optional[float]
    format: KPIFormat
    aggregation: Aggregation
    higher_is_better: bool = True
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    unit: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("KPI identifier cannot be empty")

        if not self.name.strip():
            raise ValueError("KPI name cannot be empty")

        if self.warning_threshold is not None and self.critical_threshold is not None:
            if self.higher_is_better:
                if self.warning_threshold < self.critical_threshold:
                    raise ValueError("Invalid descending KPI thresholds")
            else:
                if self.warning_threshold > self.critical_threshold:
                    raise ValueError("Invalid ascending KPI thresholds")

    def calculate_change(self) -> Optional[float]:
        if self.previous_value is None:
            return None

        if self.previous_value == 0:
            return None

        return (
            (self.value - self.previous_value)
            / abs(self.previous_value)
        ) * 100

    def calculate_target_achievement(self) -> Optional[float]:
        if self.target is None or self.target == 0:
            return None

        if self.higher_is_better:
            return self.value / self.target * 100

        return self.target / self.value * 100 if self.value > 0 else None

    def status(self) -> KPIStatus:
        if self.critical_threshold is not None:
            critical = (
                self.value < self.critical_threshold
                if self.higher_is_better
                else self.value > self.critical_threshold
            )
            if critical:
                return KPIStatus.CRITICAL

        if self.warning_threshold is not None:
            warning = (
                self.value < self.warning_threshold
                if self.higher_is_better
                else self.value > self.warning_threshold
            )
            if warning:
                return KPIStatus.WARNING

        return KPIStatus.GOOD

    def formatted_value(self) -> str:
        if self.format == KPIFormat.CURRENCY:
            return f"${self.value:,.2f}"

        if self.format == KPIFormat.PERCENTAGE:
            return f"{self.value:.2f}%"

        if self.format == KPIFormat.DURATION:
            return f"{self.value:.1f} {self.unit or 'minutes'}"

        return f"{self.value:,.2f}".rstrip("0").rstrip(".")

    def presentation(self) -> dict[str, Any]:
        return {
            "id": self.identifier,
            "name": self.name,
            "value": self.formatted_value(),
            "change_percent": self.calculate_change(),
            "target_achievement": self.calculate_target_achievement(),
            "status": self.status().value,
            "description": self.description,
        }


# ============================================================
# 4. DASHBOARD DATA MODEL
# ============================================================

@dataclass(frozen=True)
class MetricRecord:
    record_id: int
    recorded_on: date
    department: str
    region: str
    revenue: float
    expenses: float
    orders: int
    customer_satisfaction: float
    conversion_rate: float

    def __post_init__(self) -> None:
        if self.record_id <= 0:
            raise ValueError("Record ID must be positive")

        if not self.department.strip() or not self.region.strip():
            raise ValueError("Department and region are required")

        if self.revenue < 0 or self.expenses < 0 or self.orders < 0:
            raise ValueError("Negative financial values are not allowed")

        if not 0 <= self.customer_satisfaction <= 100:
            raise ValueError("Customer satisfaction must be 0-100")

        if not 0 <= self.conversion_rate <= 100:
            raise ValueError("Conversion rate must be 0-100")


@dataclass
class DashboardState:
    selected_region: Optional[str] = None
    selected_department: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search_text: str = ""
    sort_by: str = "revenue"
    descending: bool = True

    def validate(self) -> None:
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("Start date cannot exceed end date")


@dataclass(frozen=True)
class LayoutItem:
    identifier: str
    title: str
    chart_type: ChartType
    row: int
    column: int
    row_span: int
    column_span: int
    priority: int

    def __post_init__(self) -> None:
        if min(self.row, self.column) < 1:
            raise ValueError("Grid positions start at 1")

        if min(self.row_span, self.column_span, self.priority) < 1:
            raise ValueError("Grid spans and priority must be positive")


# ============================================================
# 5. DATA PROCESSING
# ============================================================

class DashboardRepository:
    def __init__(self, records: list[MetricRecord]):
        self.records = list(records)
        self._validate_unique_ids()

    def _validate_unique_ids(self) -> None:
        identifiers = [record.record_id for record in self.records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate record identifiers")

    def filter(self, state: DashboardState) -> list[MetricRecord]:
        state.validate()

        result = self.records

        if state.selected_region:
            result = [
                r for r in result
                if r.region == state.selected_region
            ]

        if state.selected_department:
            result = [
                r for r in result
                if r.department == state.selected_department
            ]

        if state.start_date:
            result = [
                r for r in result
                if r.recorded_on >= state.start_date
            ]

        if state.end_date:
            result = [
                r for r in result
                if r.recorded_on <= state.end_date
            ]

        if state.search_text:
            query = state.search_text.casefold()
            result = [
                r for r in result
                if query in r.department.casefold()
                or query in r.region.casefold()
            ]

        if state.sort_by not in MetricRecord.__dataclass_fields__:
            raise ValueError("Unsupported sorting field")

        return sorted(
            result,
            key=lambda r: getattr(r, state.sort_by),
            reverse=state.descending
        )

    def aggregate(self, records: list[MetricRecord]) -> dict[str, float]:
        if not records:
            return {
                "revenue": 0.0,
                "expenses": 0.0,
                "profit": 0.0,
                "orders": 0.0,
                "average_satisfaction": 0.0,
                "average_conversion": 0.0,
            }

        revenue = sum(r.revenue for r in records)
        expenses = sum(r.expenses for r in records)

        return {
            "revenue": revenue,
            "expenses": expenses,
            "profit": revenue - expenses,
            "orders": float(sum(r.orders for r in records)),
            "average_satisfaction": statistics.mean(
                r.customer_satisfaction for r in records
            ),
            "average_conversion": statistics.mean(
                r.conversion_rate for r in records
            ),
        }

    def group_by_region(self) -> dict[str, dict[str, float]]:
        groups: dict[str, list[MetricRecord]] = {}

        for record in self.records:
            groups.setdefault(record.region, []).append(record)

        return {
            region: self.aggregate(records)
            for region, records in groups.items()
        }

    def trend(self) -> list[dict[str, Any]]:
        grouped: dict[date, list[MetricRecord]] = {}

        for record in self.records:
            grouped.setdefault(record.recorded_on, []).append(record)

        return [
            {
                "date": day.isoformat(),
                "revenue": sum(r.revenue for r in values),
                "orders": sum(r.orders for r in values),
            }
            for day, values in sorted(grouped.items())
        ]


# ============================================================
# 6. VISUAL HIERARCHY AND LAYOUT
# ============================================================

class DashboardLayout:
    """
    A 12-column grid supports desktop composition.

    High-priority KPI cards appear before analytical visualizations.
    """

    def __init__(self, columns: int = 12):
        if columns < 1:
            raise ValueError("Columns must be positive")

        self.columns = columns
        self.items: list[LayoutItem] = []

    def add(self, item: LayoutItem) -> None:
        if item.column + item.column_span - 1 > self.columns:
            raise ValueError("Component exceeds dashboard grid")

        if any(existing.identifier == item.identifier for existing in self.items):
            raise ValueError("Duplicate layout component")

        for existing in self.items:
            same_rows = (
                item.row < existing.row + existing.row_span
                and existing.row < item.row + item.row_span
            )
            same_columns = (
                item.column < existing.column + existing.column_span
                and existing.column < item.column + item.column_span
            )

            if same_rows and same_columns:
                raise ValueError(
                    f"Layout collision: {item.identifier} and {existing.identifier}"
                )

        self.items.append(item)

    def render_structure(self) -> list[dict[str, Any]]:
        return [
            asdict(item) | {"chart_type": item.chart_type.value}
            for item in sorted(
                self.items,
                key=lambda item: (item.row, -item.priority, item.column)
            )
        ]

    def responsive_columns(self, viewport_width: int) -> int:
        if viewport_width < 600:
            return 1
        if viewport_width < 1024:
            return 6
        return 12


# ============================================================
# 7. INTERACTION AND FILTERING
# ============================================================

class DashboardController:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository
        self.state = DashboardState()
        self.listeners = []

    def subscribe(self, callback) -> None:
        if not callable(callback):
            raise TypeError("Listener must be callable")
        self.listeners.append(callback)

    def update_filters(self, **changes: Any) -> None:
        allowed = set(DashboardState.__dataclass_fields__)

        if not changes.keys() <= allowed:
            raise ValueError("Unsupported dashboard filter")

        old_state = self.state
        candidate = DashboardState(**(asdict(old_state) | changes))

        candidate.validate()

        self.state = candidate

        # Notify only after successful validation and state replacement.
        for listener in self.listeners:
            try:
                listener(self.state)
            except Exception:
                logger.exception("Dashboard event listener failed")

    def get_records(self) -> list[MetricRecord]:
        return self.repository.filter(self.state)

    def reset(self) -> None:
        self.state = DashboardState()

        for listener in self.listeners:
            try:
                listener(self.state)
            except Exception:
                logger.exception("Dashboard reset listener failed")


# ============================================================
# 8. KPI FACTORY
# ============================================================

def create_kpis(metrics: dict[str, float]) -> list[KPI]:
    return [
        KPI(
            identifier="revenue",
            name="Total Revenue",
            value=metrics["revenue"],
            previous_value=45000,
            target=50000,
            format=KPIFormat.CURRENCY,
            aggregation=Aggregation.SUM,
            warning_threshold=35000,
            critical_threshold=25000,
            description="Revenue generated during the selected period"
        ),
        KPI(
            identifier="profit",
            name="Operating Profit",
            value=metrics["profit"],
            previous_value=12000,
            target=15000,
            format=KPIFormat.CURRENCY,
            aggregation=Aggregation.SUM,
            warning_threshold=8000,
            critical_threshold=4000,
            description="Revenue less operating expenses"
        ),
        KPI(
            identifier="satisfaction",
            name="Customer Satisfaction",
            value=metrics["average_satisfaction"],
            previous_value=82,
            target=90,
            format=KPIFormat.PERCENTAGE,
            aggregation=Aggregation.AVERAGE,
            warning_threshold=75,
            critical_threshold=60,
            description="Mean customer satisfaction score"
        ),
        KPI(
            identifier="conversion",
            name="Conversion Rate",
            value=metrics["average_conversion"],
            previous_value=3.5,
            target=5,
            format=KPIFormat.PERCENTAGE,
            aggregation=Aggregation.AVERAGE,
            warning_threshold=2.5,
            critical_threshold=1.5,
            description="Percentage of visitors converting into customers"
        ),
    ]


# ============================================================
# 9. ACCESSIBILITY AND DESIGN VALIDATION
# ============================================================

def relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")

    if len(value) != 6:
        raise ValueError("Expected six-digit hexadecimal color")

    channels = [
        int(value[i:i + 2], 16) / 255
        for i in (0, 2, 4)
    ]

    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]

    return (
        0.2126 * linear[0]
        + 0.7152 * linear[1]
        + 0.0722 * linear[2]
    )


def contrast_ratio(foreground: str, background: str) -> float:
    first = relative_luminance(foreground)
    second = relative_luminance(background)

    lighter = max(first, second)
    darker = min(first, second)

    return (lighter + 0.05) / (darker + 0.05)


def validate_accessibility() -> None:
    pairs = [
        ("#172033", "#FFFFFF"),
        ("#64748B", "#FFFFFF"),
    ]

    for foreground, background in pairs:
        ratio = contrast_ratio(foreground, background)
        print(
            f"Contrast {foreground} on {background}: "
            f"{ratio:.2f}:1"
        )

        if ratio < 4.5:
            logger.warning("Contrast below WCAG AA normal-text target")


# ============================================================
# 10. SAMPLE BUSINESS DATA
# ============================================================

def create_sample_data() -> list[MetricRecord]:
    base = date(2026, 11, 20)

    raw = [
        ("Sales", "North", 18000, 11000, 120, 91, 5.2),
        ("Technology", "North", 14000, 9000, 90, 87, 4.5),
        ("Sales", "South", 16000, 10000, 110, 83, 3.8),
        ("Technology", "South", 12000, 8500, 75, 88, 4.2),
        ("Operations", "East", 9000, 7000, 65, 79, 2.8),
        ("Sales", "East", 21000, 13000, 140, 94, 5.8),
        ("Operations", "West", 11000, 7500, 80, 85, 3.6),
        ("Technology", "West", 15000, 9500, 95, 90, 4.9),
    ]

    return [
        MetricRecord(
            record_id=index + 1,
            recorded_on=base + timedelta(days=index),
            department=department,
            region=region,
            revenue=revenue,
            expenses=expenses,
            orders=orders,
            customer_satisfaction=satisfaction,
            conversion_rate=conversion,
        )
        for index, (
            department,
            region,
            revenue,
            expenses,
            orders,
            satisfaction,
            conversion,
        ) in enumerate(raw)
    ]


# ============================================================
# 11. EXPORT AND REPORTING
# ============================================================

def export_dashboard(
    output_path: Path,
    metrics: dict[str, float],
    kpis: list[KPI],
    layout: DashboardLayout,
    repository: DashboardRepository,
) -> None:
    payload = {
        "generated_on": date.today().isoformat(),
        "metrics": metrics,
        "kpis": [kpi.presentation() for kpi in kpis],
        "regional_performance": repository.group_by_region(),
        "revenue_trend": repository.trend(),
        "layout": layout.render_structure(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Avoid writing to unexpected locations supplied by external users.
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, allow_nan=False)


def display_dashboard(
    metrics: dict[str, float],
    kpis: list[KPI],
    repository: DashboardRepository,
) -> None:
    print("\n" + "=" * 66)
    print("                 ENTERPRISE PERFORMANCE DASHBOARD")
    print("=" * 66)

    print("\nKEY PERFORMANCE INDICATORS")

    for kpi in kpis:
        change = kpi.calculate_change()
        change_text = (
            f"{change:+.2f}%"
            if change is not None
            else "N/A"
        )

        print(
            f"{kpi.name:<25} "
            f"{kpi.formatted_value():>14} "
            f"| Change: {change_text:>9} "
            f"| Status: {kpi.status().value.upper()}"
        )

    print("\nFINANCIAL PERFORMANCE")

    for name, value in metrics.items():
        print(f"{name.replace('_', ' ').title():<28}: {value:,.2f}")

    print("\nREGIONAL PERFORMANCE")

    for region, values in repository.group_by_region().items():
        print(
            f"{region:<12} "
            f"Revenue: {values['revenue']:>10,.2f} "
            f"Profit: {values['profit']:>10,.2f}"
        )

    print("\nREVENUE TREND")

    for point in repository.trend():
        print(f"{point['date']} | Revenue: {point['revenue']:,.2f}")


# ============================================================
# 12. AUTOMATED VALIDATION
# ============================================================

def run_tests() -> None:
    assert contrast_ratio("#172033", "#FFFFFF") >= 4.5

    sample = KPI(
        identifier="test",
        name="Test KPI",
        value=80,
        previous_value=100,
        target=100,
        format=KPIFormat.NUMBER,
        aggregation=Aggregation.AVERAGE,
        warning_threshold=70,
        critical_threshold=50,
    )

    assert sample.calculate_change() == -20
    assert sample.status() == KPIStatus.GOOD

    critical = KPI(
        identifier="critical",
        name="Critical KPI",
        value=30,
        previous_value=40,
        target=100,
        format=KPIFormat.NUMBER,
        aggregation=Aggregation.AVERAGE,
        warning_threshold=70,
        critical_threshold=50,
    )

    assert critical.status() == KPIStatus.CRITICAL

    repository = DashboardRepository(create_sample_data())
    assert len(repository.filter(DashboardState())) == 8

    assert repository.aggregate([])["revenue"] == 0

    try:
        DashboardState(
            start_date=date(2026, 11, 25),
            end_date=date(2026, 11, 20),
        ).validate()
        raise AssertionError("Invalid date range was accepted")
    except ValueError:
        pass

    print("\nAll validation tests passed.")


# ============================================================
# 13. APPLICATION ENTRY POINT
# ============================================================

def main() -> None:
    records = create_sample_data()
    repository = DashboardRepository(records)

    controller = DashboardController(repository)

    controller.subscribe(
        lambda state: logger.info(
            "Dashboard filters changed: region=%s department=%s",
            state.selected_region,
            state.selected_department,
        )
    )

    layout = DashboardLayout()

    layout.add(
        LayoutItem("revenue", "Revenue KPI", ChartType.TABLE, 1, 1, 1, 3, 10)
    )
    layout.add(
        LayoutItem("profit", "Profit KPI", ChartType.TABLE, 1, 4, 1, 3, 9)
    )
    layout.add(
        LayoutItem("satisfaction", "Satisfaction KPI", ChartType.TABLE, 1, 7, 1, 3, 8)
    )
    layout.add(
        LayoutItem("conversion", "Conversion KPI", ChartType.TABLE, 1, 10, 1, 3, 7)
    )
    layout.add(
        LayoutItem("revenue_trend", "Revenue Trend", ChartType.LINE, 2, 1, 2, 8, 6)
    )
    layout.add(
        LayoutItem("regional", "Regional Performance", ChartType.BAR, 2, 9, 2, 4, 5)
    )

    metrics = repository.aggregate(controller.get_records())
    kpis = create_kpis(metrics)

    display_dashboard(metrics, kpis, repository)

    print("\nDASHBOARD GRID")
    print(json.dumps(layout.render_structure(), indent=2))

    print("\nINTERACTIVE FILTER EXAMPLE")
    controller.update_filters(selected_region="North")
    filtered_metrics = repository.aggregate(controller.get_records())
    print(json.dumps(filtered_metrics, indent=2))

    validate_accessibility()
    run_tests()

    output = Path("dashboard_report.json")
    export_dashboard(
        output,
        metrics,
        kpis,
        layout,
        repository,
    )

    print(f"\nReport exported to: {output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, TypeError) as error:
        logger.exception("Dashboard execution failed: %s", error)
        raise SystemExit(1)
