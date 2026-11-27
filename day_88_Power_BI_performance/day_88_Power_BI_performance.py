#!/usr/bin/env python3
"""
Power BI Performance Engineering
================================

A self-contained performance-analysis and optimization simulator.

Covers:
1. Semantic model optimization
2. Star schema and relationship design
3. Cardinality and dictionary encoding
4. Import, DirectQuery, and Dual storage modes
5. DAX expression optimization
6. Query performance analysis
7. VertiPaq memory estimation
8. Query folding and source optimization
9. Aggregation strategies
10. Performance recommendations and benchmarking

Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("powerbi_performance")


# ============================================================
# 1. DOMAIN TYPES
# ============================================================

class StorageMode(Enum):
    IMPORT = "Import"
    DIRECTQUERY = "DirectQuery"
    DUAL = "Dual"
    DIRECTLAKE = "DirectLake"


class TableRole(Enum):
    FACT = "Fact"
    DIMENSION = "Dimension"
    BRIDGE = "Bridge"


class DAXPattern(Enum):
    ROW_ITERATION = "Row iteration"
    FILTER_ALL = "FILTER over ALL"
    FILTERED_AGGREGATION = "Filtered aggregation"
    VARIABLE_REUSE = "Variable reuse"
    PREAGGREGATED = "Pre-aggregated measure"
    SIMPLE_AGGREGATION = "Simple aggregation"


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ============================================================
# 2. DATA VALIDATION
# ============================================================

def validate_positive(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


# ============================================================
# 3. SEMANTIC MODEL
# ============================================================

@dataclass
class Column:
    name: str
    data_type: str
    cardinality: int
    nullable: bool = False
    is_key: bool = False
    is_hidden: bool = False
    is_used: bool = True

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Column name cannot be empty")

        if self.data_type not in {
            "integer", "decimal", "string", "date",
            "datetime", "boolean"
        }:
            raise ValueError(f"Unsupported type: {self.data_type}")

        if self.cardinality < 0:
            raise ValueError("Cardinality cannot be negative")


@dataclass
class Table:
    name: str
    role: TableRole
    row_count: int
    columns: list[Column]
    storage_mode: StorageMode = StorageMode.IMPORT
    source_name: str = ""
    query_folding: bool = True

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Table name cannot be empty")

        if self.row_count < 0:
            raise ValueError("Row count cannot be negative")

        names = [column.name.lower() for column in self.columns]

        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate columns in {self.name}")

        for column in self.columns:
            if column.cardinality > self.row_count:
                raise ValueError(
                    f"{self.name}.{column.name}: "
                    "cardinality exceeds row count"
                )

    @property
    def column_count(self) -> int:
        return len(self.columns)

    @property
    def unused_columns(self) -> list[str]:
        return [
            column.name
            for column in self.columns
            if not column.is_used and not column.is_key
        ]

    def estimated_memory_mb(self) -> float:
        """
        Approximate dictionary and encoded value memory.

        This is an educational estimate, not an actual VertiPaq
        memory measurement.
        """
        if self.storage_mode not in {
            StorageMode.IMPORT, StorageMode.DUAL
        }:
            return 0.0

        total_bytes = 0

        for column in self.columns:
            bits = max(1, math.ceil(
                math.log2(max(2, column.cardinality))
            ))

            encoded_bytes = math.ceil(
                self.row_count * bits / 8
            )

            if column.data_type == "string":
                dictionary_bytes = (
                    column.cardinality * 24
                )
            else:
                dictionary_bytes = (
                    column.cardinality * 8
                )

            total_bytes += encoded_bytes + dictionary_bytes

        return total_bytes / (1024 * 1024)


@dataclass
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str = "ManyToOne"
    active: bool = True
    bidirectional: bool = False

    def validate(self, tables: dict[str, Table]) -> None:
        if self.from_table not in tables:
            raise ValueError("Source table does not exist")

        if self.to_table not in tables:
            raise ValueError("Target table does not exist")

        source = tables[self.from_table]
        target = tables[self.to_table]

        if self.from_column not in {
            c.name for c in source.columns
        }:
            raise ValueError("Source column does not exist")

        if self.to_column not in {
            c.name for c in target.columns
        }:
            raise ValueError("Target column does not exist")

        if self.cardinality not in {
            "OneToOne", "OneToMany", "ManyToOne", "ManyToMany"
        }:
            raise ValueError("Invalid relationship cardinality")


class SemanticModel:

    def __init__(self, name: str):
        self.name = name
        self.tables: dict[str, Table] = {}
        self.relationships: list[Relationship] = []

    def add_table(self, table: Table) -> None:
        if table.name in self.tables:
            raise ValueError(f"Duplicate table: {table.name}")

        self.tables[table.name] = table

    def add_relationship(self, relationship: Relationship) -> None:
        relationship.validate(self.tables)
        self.relationships.append(relationship)

    def estimated_memory_mb(self) -> float:
        return sum(
            table.estimated_memory_mb()
            for table in self.tables.values()
        )

    def model_statistics(self) -> dict[str, Any]:
        return {
            "model": self.name,
            "tables": len(self.tables),
            "relationships": len(self.relationships),
            "total_rows": sum(
                table.row_count for table in self.tables.values()
            ),
            "total_columns": sum(
                table.column_count for table in self.tables.values()
            ),
            "estimated_import_memory_mb": round(
                self.estimated_memory_mb(), 2
            ),
            "unused_columns": {
                table.name: table.unused_columns
                for table in self.tables.values()
                if table.unused_columns
            }
        }


# ============================================================
# 4. MODEL OPTIMIZATION
# ============================================================

@dataclass
class Recommendation:
    category: str
    severity: Severity
    subject: str
    finding: str
    action: str
    estimated_benefit: str


class ModelOptimizer:

    def analyze(self, model: SemanticModel) -> list[Recommendation]:
        recommendations = []

        for table in model.tables.values():

            if table.unused_columns:
                recommendations.append(
                    Recommendation(
                        category="Model size",
                        severity=Severity.HIGH,
                        subject=table.name,
                        finding=(
                            f"{len(table.unused_columns)} "
                            "unused columns detected"
                        ),
                        action=(
                            "Remove unused columns from the model "
                            "and preferably from the source query"
                        ),
                        estimated_benefit="Reduced memory and refresh work"
                    )
                )

            for column in table.columns:
                if (
                    column.data_type == "string"
                    and table.row_count > 100000
                    and column.cardinality > 50000
                ):
                    recommendations.append(
                        Recommendation(
                            category="Cardinality",
                            severity=Severity.HIGH,
                            subject=f"{table.name}.{column.name}",
                            finding=(
                                f"High-cardinality text column: "
                                f"{column.cardinality:,} distinct values"
                            ),
                            action=(
                                "Check whether the column is required. "
                                "Consider a numeric surrogate key, "
                                "reduced precision, or source-side "
                                "normalization where semantically valid."
                            ),
                            estimated_benefit=(
                                "Potentially lower dictionary memory"
                            )
                        )
                    )

            if (
                table.role == TableRole.FACT
                and table.row_count > 1000000
                and table.storage_mode == StorageMode.IMPORT
                and not table.query_folding
            ):
                recommendations.append(
                    Recommendation(
                        category="Refresh",
                        severity=Severity.HIGH,
                        subject=table.name,
                        finding="Large Import table lacks query folding",
                        action=(
                            "Push supported filters and transformations "
                            "to the data source"
                        ),
                        estimated_benefit="Reduced refresh processing"
                    )
                )

        for relationship in model.relationships:
            if relationship.bidirectional:
                recommendations.append(
                    Recommendation(
                        category="Relationships",
                        severity=Severity.MEDIUM,
                        subject=(
                            f"{relationship.from_table} -> "
                            f"{relationship.to_table}"
                        ),
                        finding="Bidirectional filter propagation detected",
                        action=(
                            "Use single-direction filtering where "
                            "the business logic permits it"
                        ),
                        estimated_benefit=(
                            "Simpler filter propagation and fewer "
                            "ambiguous paths"
                        )
                    )
                )

            if relationship.cardinality == "ManyToMany":
                recommendations.append(
                    Recommendation(
                        category="Relationships",
                        severity=Severity.HIGH,
                        subject=relationship.from_table,
                        finding="Many-to-many relationship detected",
                        action=(
                            "Evaluate a bridge table and explicit "
                            "filtering semantics"
                        ),
                        estimated_benefit=(
                            "More predictable relationship behavior"
                        )
                    )
                )

        return recommendations


# ============================================================
# 5. DAX PERFORMANCE ANALYSIS
# ============================================================

@dataclass
class DAXMeasure:
    name: str
    expression: str
    pattern: DAXPattern
    iterations: int = 0
    repeated_expressions: int = 0
    filter_complexity: int = 1

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Measure name cannot be empty")

        if not self.expression.strip():
            raise ValueError("DAX expression cannot be empty")

        if min(
            self.iterations,
            self.repeated_expressions,
            self.filter_complexity
        ) < 0:
            raise ValueError("Complexity values cannot be negative")


class DAXAnalyzer:

    def analyze(self, measure: DAXMeasure) -> list[str]:
        findings = []

        if measure.pattern == DAXPattern.ROW_ITERATION:
            findings.append(
                "Review row-by-row iteration. Prefer a storage-engine "
                "aggregation when the expression is mathematically "
                "equivalent and preserves filter semantics."
            )

        if measure.pattern == DAXPattern.FILTER_ALL:
            findings.append(
                "Review FILTER(ALL(...)). Restrict the filter table "
                "to the required columns or use a simpler Boolean "
                "filter when valid."
            )

        if measure.pattern == DAXPattern.VARIABLE_REUSE:
            findings.append(
                "Variables can avoid repeated expression evaluation. "
                "Check evaluation context before reusing results."
            )

        if measure.iterations > 1000000:
            findings.append(
                "Large iterator workload detected. Test storage-engine "
                "aggregation alternatives."
            )

        if measure.repeated_expressions > 1:
            findings.append(
                "Repeated expressions detected. Consider variables "
                "when the expressions share the same filter context."
            )

        if measure.filter_complexity > 5:
            findings.append(
                "Complex filtering detected. Review context transition, "
                "relationship propagation, and unnecessary filter removal."
            )

        if not findings:
            findings.append(
                "No obvious structural DAX optimization issue detected. "
                "Measure actual query execution."
            )

        return findings


# ============================================================
# 6. DAX EXAMPLES
# ============================================================

DAX_EXAMPLES = {
    "basic_sales": """
Total Sales :=
SUM ( Sales[SalesAmount] )
""",
    "variable_reuse": """
Sales Growth % :=
VAR CurrentSales =
    [Total Sales]
VAR PreviousSales =
    CALCULATE (
        [Total Sales],
        DATEADD ( 'Date'[Date], -1, YEAR )
    )
RETURN
    DIVIDE (
        CurrentSales - PreviousSales,
        PreviousSales
    )
""",
    "iterator": """
Extended Revenue :=
SUMX (
    Sales,
    Sales[Quantity] * Sales[UnitPrice]
)
""",
    "precalculated_column_alternative": """
-- If Quantity and UnitPrice are stable source attributes,
-- calculate the extended amount in the source or Power Query.
-- Then use:
Extended Revenue :=
SUM ( Sales[ExtendedAmount] )
""",
    "filtered_aggregation": """
Online Sales :=
CALCULATE (
    [Total Sales],
    Sales[Channel] = "Online"
)
""",
    "date_intelligence": """
Year To Date Sales :=
TOTALYTD (
    [Total Sales],
    'Date'[Date]
)
"""
}


# ============================================================
# 7. STORAGE MODE ANALYSIS
# ============================================================

@dataclass
class StorageAssessment:
    table_name: str
    storage_mode: StorageMode
    expected_behavior: str
    primary_risk: str


class StorageModeAdvisor:

    def assess(
        self,
        table: Table,
        workload: str
    ) -> StorageAssessment:

        workload = workload.lower()

        if workload not in {
            "interactive", "large", "near_real_time",
            "composite", "dimension"
        }:
            raise ValueError("Unsupported workload")

        if table.storage_mode == StorageMode.IMPORT:
            behavior = "Data is loaded into the in-memory model"
            risk = "Refresh latency and memory consumption"

        elif table.storage_mode == StorageMode.DIRECTQUERY:
            behavior = "Queries are translated to the source system"
            risk = "Source latency, concurrency, and query translation"

        elif table.storage_mode == StorageMode.DUAL:
            behavior = (
                "Table can use Import or DirectQuery behavior "
                "depending on query context"
            )
            risk = "Incorrect expectations about composite behavior"

        else:
            behavior = (
                "Data is accessed through a supported Direct Lake "
                "storage architecture"
            )
            risk = "Capacity, source compatibility, and fallback behavior"

        if (
            workload == "near_real_time"
            and table.storage_mode == StorageMode.IMPORT
        ):
            risk += "; imported data may be stale between refreshes"

        if (
            workload == "interactive"
            and table.storage_mode == StorageMode.DIRECTQUERY
        ):
            risk += "; repeated interactions may increase source workload"

        return StorageAssessment(
            table.name,
            table.storage_mode,
            behavior,
            risk
        )


# ============================================================
# 8. QUERY PERFORMANCE SIMULATOR
# ============================================================

@dataclass
class QueryMetrics:
    query_name: str
    storage_engine_ms: float
    formula_engine_ms: float
    source_ms: float = 0
    visual_render_ms: float = 0
    rows_scanned: int = 0
    rows_returned: int = 0
    cache_hit: bool = False

    def __post_init__(self):
        for name in (
            "storage_engine_ms",
            "formula_engine_ms",
            "source_ms",
            "visual_render_ms"
        ):
            validate_positive(getattr(self, name), name)

        if min(self.rows_scanned, self.rows_returned) < 0:
            raise ValueError("Row counts cannot be negative")

        if self.rows_returned > self.rows_scanned:
            raise ValueError(
                "Returned rows cannot exceed scanned rows"
            )

    @property
    def total_ms(self) -> float:
        return (
            self.storage_engine_ms
            + self.formula_engine_ms
            + self.source_ms
            + self.visual_render_ms
        )

    @property
    def formula_engine_share(self) -> float:
        return safe_ratio(
            self.formula_engine_ms,
            self.total_ms
        )

    @property
    def scan_efficiency(self) -> float:
        return safe_ratio(
            self.rows_returned,
            self.rows_scanned
        )


class QueryPerformanceAnalyzer:

    def analyze(self, metrics: QueryMetrics) -> dict[str, Any]:

        bottlenecks = []

        if metrics.formula_engine_share > 0.40:
            bottlenecks.append(
                "High Formula Engine contribution. "
                "Inspect complex DAX and iterator operations."
            )

        if metrics.source_ms > 500:
            bottlenecks.append(
                "Slow source execution. Inspect source query plans, "
                "indexes, network latency, and concurrency."
            )

        if metrics.visual_render_ms > 300:
            bottlenecks.append(
                "Visual rendering is significant. Reduce unnecessary "
                "visual complexity and data points."
            )

        if (
            metrics.rows_scanned > 0
            and metrics.scan_efficiency < 0.01
        ):
            bottlenecks.append(
                "Low scan efficiency. Review filter selectivity, "
                "model design, and query shape."
            )

        if metrics.cache_hit:
            bottlenecks.append(
                "Cache hit recorded. Compare with cold-cache "
                "measurements separately."
            )

        if not bottlenecks:
            bottlenecks.append(
                "No threshold-based bottleneck detected."
            )

        return {
            "query": metrics.query_name,
            "total_ms": round(metrics.total_ms, 2),
            "formula_engine_share": round(
                metrics.formula_engine_share * 100, 2
            ),
            "scan_efficiency_percent": round(
                metrics.scan_efficiency * 100, 2
            ),
            "bottlenecks": bottlenecks
        }


# ============================================================
# 9. BENCHMARKING
# ============================================================

class Benchmark:

    @staticmethod
    def measure(
        operation: Callable[[], Any],
        repetitions: int = 5
    ) -> dict[str, float]:

        if repetitions < 1 or repetitions > 1000:
            raise ValueError("Repetitions must be between 1 and 1000")

        durations = []

        for _ in range(repetitions):
            start = time.perf_counter()
            operation()
            durations.append(
                (time.perf_counter() - start) * 1000
            )

        return {
            "runs": repetitions,
            "minimum_ms": round(min(durations), 4),
            "median_ms": round(statistics.median(durations), 4),
            "maximum_ms": round(max(durations), 4),
            "mean_ms": round(statistics.mean(durations), 4)
        }


# ============================================================
# 10. SAMPLE ENTERPRISE MODEL
# ============================================================

def build_sample_model() -> SemanticModel:

    model = SemanticModel("Enterprise Sales Analytics")

    model.add_table(
        Table(
            name="Sales",
            role=TableRole.FACT,
            row_count=2_000_000,
            columns=[
                Column("SalesID", "integer", 2_000_000, is_key=True),
                Column("DateKey", "integer", 1825),
                Column("ProductKey", "integer", 5000),
                Column("CustomerKey", "integer", 180000),
                Column("Quantity", "integer", 100),
                Column("UnitPrice", "decimal", 10000),
                Column("SalesAmount", "decimal", 250000),
                Column("TransactionReference", "string", 1900000),
                Column(
                    "UnusedDescription",
                    "string",
                    2000,
                    is_used=False
                ),
            ],
            storage_mode=StorageMode.IMPORT,
            query_folding=True
        )
    )

    model.add_table(
        Table(
            name="Product",
            role=TableRole.DIMENSION,
            row_count=5000,
            columns=[
                Column("ProductKey", "integer", 5000, is_key=True),
                Column("ProductName", "string", 4500),
                Column("Category", "string", 12),
                Column("Brand", "string", 150),
            ]
        )
    )

    model.add_table(
        Table(
            name="Customer",
            role=TableRole.DIMENSION,
            row_count=180000,
            columns=[
                Column("CustomerKey", "integer", 180000, is_key=True),
                Column("CustomerName", "string", 175000),
                Column("Region", "string", 25),
                Column("CustomerSegment", "string", 6),
            ]
        )
    )

    model.add_table(
        Table(
            name="Date",
            role=TableRole.DIMENSION,
            row_count=1825,
            columns=[
                Column("DateKey", "integer", 1825, is_key=True),
                Column("Date", "date", 1825),
                Column("Year", "integer", 5),
                Column("Month", "integer", 12),
                Column("Quarter", "string", 4),
            ]
        )
    )

    model.add_relationship(
        Relationship(
            "Sales", "ProductKey",
            "Product", "ProductKey"
        )
    )

    model.add_relationship(
        Relationship(
            "Sales", "CustomerKey",
            "Customer", "CustomerKey"
        )
    )

    model.add_relationship(
        Relationship(
            "Sales", "DateKey",
            "Date", "DateKey"
        )
    )

    return model


# ============================================================
# 11. REPORT GENERATION
# ============================================================

def create_report() -> dict[str, Any]:

    model = build_sample_model()

    optimizer = ModelOptimizer()
    dax_analyzer = DAXAnalyzer()
    storage_advisor = StorageModeAdvisor()
    query_analyzer = QueryPerformanceAnalyzer()

    measures = [
        DAXMeasure(
            name="Extended Revenue",
            expression=(
                "SUMX(Sales, "
                "Sales[Quantity] * Sales[UnitPrice])"
            ),
            pattern=DAXPattern.ROW_ITERATION,
            iterations=2_000_000
        ),
        DAXMeasure(
            name="Total Sales",
            expression="SUM(Sales[SalesAmount])",
            pattern=DAXPattern.SIMPLE_AGGREGATION
        ),
        DAXMeasure(
            name="Sales Growth",
            expression="Variable-based comparison",
            pattern=DAXPattern.VARIABLE_REUSE,
            repeated_expressions=2
        )
    ]

    query = QueryMetrics(
        query_name="Monthly Sales by Region",
        storage_engine_ms=120,
        formula_engine_ms=180,
        source_ms=0,
        visual_render_ms=85,
        rows_scanned=2_000_000,
        rows_returned=24
    )

    return {
        "model_statistics": model.model_statistics(),
        "model_recommendations": [
            {
                **asdict(item),
                "severity": item.severity.value
            }
            for item in optimizer.analyze(model)
        ],
        "dax_analysis": {
            measure.name: dax_analyzer.analyze(measure)
            for measure in measures
        },
        "storage_assessments": [
            asdict(storage_advisor.assess(
                table,
                "interactive"
            ))
            for table in model.tables.values()
        ],
        "query_analysis": query_analyzer.analyze(query),
        "dax_examples": DAX_EXAMPLES
    }


# ============================================================
# 12. EXECUTION AND VALIDATION
# ============================================================

def run_tests() -> None:

    model = build_sample_model()

    assert len(model.tables) == 4
    assert len(model.relationships) == 3
    assert model.estimated_memory_mb() > 0

    metrics = QueryMetrics(
        "Test Query",
        100,
        50,
        rows_scanned=10000,
        rows_returned=10
    )

    assert metrics.total_ms == 150
    assert metrics.scan_efficiency == 0.001

    assert safe_ratio(10, 0) == 0

    try:
        validate_positive(-1, "test")
        raise AssertionError("Negative value was accepted")
    except ValueError:
        pass

    print("All validation tests passed.")


def main() -> None:

    run_tests()

    report = create_report()

    print("\nPOWER BI PERFORMANCE REPORT")
    print("=" * 65)

    print(json.dumps(report, indent=2, default=str))

    output_file = "powerbi_performance_report.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    print(f"\nReport saved to {output_file}")


if __name__ == "__main__":
    main()
