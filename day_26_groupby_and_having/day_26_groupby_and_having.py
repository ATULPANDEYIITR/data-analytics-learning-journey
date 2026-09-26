"""
GROUP BY & HAVING
=================

A comprehensive standalone study program covering:

- GROUP BY fundamentals
- Aggregate functions
- COUNT, SUM, AVG, MIN, MAX
- WHERE versus HAVING
- GROUP BY execution concepts
- Single-column and multi-column grouping
- Grouping categorical and numeric data
- Conditional aggregation
- DISTINCT versus GROUP BY
- NULL behavior
- HAVING with multiple conditions
- Aggregation after filtering
- Multidimensional aggregation concepts
- ROLLUP, CUBE, and GROUPING SETS concepts
- Window functions versus GROUP BY
- Common mistakes
- Validation and error handling
- Performance considerations
- Security considerations
- A realistic sales analytics case study
- Tests and edge cases

The program uses only the Python standard library.
It simulates relational-table behavior with Python data structures so that
the SQL concepts remain executable without requiring an external database.

The SQL examples shown in comments use conventional SQL syntax.
The executable Python implementation mirrors the same logical operations.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from statistics import mean
from typing import Any, Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# SECTION 1: DATA MODEL
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sale:
    sale_id: int
    customer: str
    region: str | None
    category: str | None
    product: str | None
    salesperson: str | None
    quantity: int
    unit_price: Decimal | None
    discount: Decimal | None
    month: str
    status: str

    @property
    def gross_amount(self) -> Decimal | None:
        if self.unit_price is None:
            return None
        return Decimal(self.quantity) * self.unit_price

    @property
    def net_amount(self) -> Decimal | None:
        """
        SQL-style NULL propagation is represented by None.

        If either price or discount is missing, the net amount is unknown.
        A real database may use COALESCE when a business rule requires a
        missing value to be treated as zero.
        """
        gross = self.gross_amount
        if gross is None or self.discount is None:
            return None
        return gross * (Decimal("1") - self.discount)


# ---------------------------------------------------------------------------
# SECTION 2: SAMPLE DATA
# ---------------------------------------------------------------------------

SALES: list[Sale] = [
    Sale(1, "Asha", "North", "Electronics", "Laptop", "Ravi", 2,
         Decimal("800"), Decimal("0.05"), "January", "Completed"),
    Sale(2, "Bharat", "North", "Electronics", "Phone", "Ravi", 5,
         Decimal("500"), Decimal("0.10"), "January", "Completed"),
    Sale(3, "Chen", "South", "Furniture", "Chair", "Meera", 10,
         Decimal("75"), Decimal("0.00"), "January", "Completed"),
    Sale(4, "Divya", "South", "Electronics", "Tablet", "Meera", 3,
         Decimal("300"), Decimal("0.05"), "January", "Completed"),
    Sale(5, "Eshan", "East", "Furniture", "Desk", "Arjun", 4,
         Decimal("250"), Decimal("0.08"), "February", "Completed"),
    Sale(6, "Fatima", "East", "Electronics", "Laptop", "Arjun", 1,
         Decimal("900"), Decimal("0.10"), "February", "Completed"),
    Sale(7, "Gopal", "West", "Office", "Printer", "Kiran", 6,
         Decimal("200"), Decimal("0.05"), "February", "Completed"),
    Sale(8, "Hina", "West", "Office", "Chair", "Kiran", 15,
         Decimal("70"), Decimal("0.00"), "February", "Completed"),
    Sale(9, "Ishaan", "North", "Furniture", "Desk", "Ravi", 2,
         Decimal("275"), Decimal("0.05"), "March", "Completed"),
    Sale(10, "Jaya", "South", "Office", "Printer", "Meera", 2,
         Decimal("220"), Decimal("0.00"), "March", "Completed"),
    Sale(11, "Kabir", "East", "Electronics", "Phone", "Arjun", 8,
         Decimal("450"), Decimal("0.12"), "March", "Completed"),
    Sale(12, "Leela", "West", "Furniture", "Desk", "Kiran", 3,
         Decimal("260"), Decimal("0.05"), "March", "Completed"),
    Sale(13, "Mohan", "North", "Electronics", "Laptop", "Ravi", 1,
         Decimal("850"), Decimal("0.00"), "April", "Cancelled"),
    Sale(14, "Nisha", "South", "Furniture", "Chair", "Meera", 20,
         Decimal("65"), Decimal("0.03"), "April", "Completed"),
    Sale(15, "Om", "East", "Office", "Printer", "Arjun", 5,
         Decimal("210"), Decimal("0.05"), "April", "Completed"),
    Sale(16, "Pooja", "West", "Electronics", "Tablet", "Kiran", 4,
         Decimal("320"), Decimal("0.07"), "April", "Completed"),
]


# ---------------------------------------------------------------------------
# SECTION 3: BASIC AGGREGATE FUNCTIONS
# ---------------------------------------------------------------------------

def sql_count_rows(rows: Sequence[Any]) -> int:
    """Equivalent to COUNT(*) for the supplied group."""
    return len(rows)


def sql_count_values(values: Iterable[Any]) -> int:
    """
    Equivalent to COUNT(expression).

    SQL COUNT(expression) ignores NULL values. None represents SQL NULL here.
    """
    return sum(value is not None for value in values)


def sql_sum(values: Iterable[Decimal | int | float | None]) -> Decimal | None:
    """
    SQL-like SUM.

    NULL values are ignored. If there are no non-NULL values, return None.
    """
    non_null = [Decimal(str(value)) for value in values if value is not None]
    return sum(non_null, Decimal("0")) if non_null else None


def sql_avg(values: Iterable[Decimal | int | float | None]) -> Decimal | None:
    """
    SQL-like AVG.

    NULL values do not participate in the denominator.
    """
    non_null = [Decimal(str(value)) for value in values if value is not None]
    if not non_null:
        return None
    return sum(non_null, Decimal("0")) / Decimal(len(non_null))


def sql_min(values: Iterable[Any]) -> Any:
    non_null = [value for value in values if value is not None]
    return min(non_null) if non_null else None


def sql_max(values: Iterable[Any]) -> Any:
    non_null = [value for value in values if value is not None]
    return max(non_null) if non_null else None


# ---------------------------------------------------------------------------
# SECTION 4: GENERIC GROUP BY IMPLEMENTATION
# ---------------------------------------------------------------------------

def group_by(
    rows: Iterable[Any],
    key_function: Callable[[Any], Any],
) -> dict[Any, list[Any]]:
    """
    Generic GROUP BY implementation.

    SQL idea:

        SELECT grouping_column, ...
        FROM table
        GROUP BY grouping_column;

    Every row is assigned to exactly one group for the supplied key.
    """
    groups: dict[Any, list[Any]] = defaultdict(list)

    for row in rows:
        key = key_function(row)
        groups[key].append(row)

    return dict(groups)


def print_grouped_counts(
    title: str,
    groups: dict[Any, list[Any]],
) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    for key, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        print(f"{key!r}: {len(rows)} row(s)")


# ---------------------------------------------------------------------------
# SECTION 5: BASIC GROUP BY EXAMPLES
# ---------------------------------------------------------------------------

def demonstrate_basic_group_by() -> None:
    print("\n" + "=" * 80)
    print("1. BASIC GROUP BY")
    print("=" * 80)

    by_region = group_by(SALES, lambda sale: sale.region)
    print_grouped_counts("Sales grouped by region", by_region)

    by_category = group_by(SALES, lambda sale: sale.category)
    print_grouped_counts("Sales grouped by category", by_category)

    """
    SQL equivalent:

        SELECT region, COUNT(*) AS sale_count
        FROM sales
        GROUP BY region;

        SELECT category, COUNT(*) AS sale_count
        FROM sales
        GROUP BY category;
    """


# ---------------------------------------------------------------------------
# SECTION 6: GROUP BY WITH MULTIPLE AGGREGATES
# ---------------------------------------------------------------------------

def summarize_group(rows: Sequence[Sale]) -> dict[str, Any]:
    quantities = [sale.quantity for sale in rows]
    net_values = [sale.net_amount for sale in rows]

    return {
        "row_count": sql_count_rows(rows),
        "quantity": sql_sum(quantities),
        "revenue": sql_sum(net_values),
        "average_revenue": sql_avg(net_values),
        "minimum_revenue": sql_min(net_values),
        "maximum_revenue": sql_max(net_values),
    }


def demonstrate_multiple_aggregates() -> None:
    print("\n" + "=" * 80)
    print("2. MULTIPLE AGGREGATES")
    print("=" * 80)

    groups = group_by(SALES, lambda sale: sale.region)

    for region, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        summary = summarize_group(rows)

        print(
            f"{region:>6} | "
            f"rows={summary['row_count']:2d} | "
            f"quantity={summary['quantity']:>4} | "
            f"revenue={summary['revenue']} | "
            f"avg={summary['average_revenue']}"
        )

    """
    SQL equivalent:

        SELECT
            region,
            COUNT(*) AS sale_count,
            SUM(quantity) AS total_quantity,
            SUM(net_amount) AS revenue,
            AVG(net_amount) AS average_revenue,
            MIN(net_amount) AS minimum_revenue,
            MAX(net_amount) AS maximum_revenue
        FROM sales
        GROUP BY region;
    """


# ---------------------------------------------------------------------------
# SECTION 7: MULTI-COLUMN GROUPING
# ---------------------------------------------------------------------------

def demonstrate_multidimensional_grouping() -> None:
    print("\n" + "=" * 80)
    print("3. MULTI-COLUMN GROUPING")
    print("=" * 80)

    groups = group_by(
        SALES,
        lambda sale: (sale.region, sale.category),
    )

    for (region, category), rows in sorted(groups.items()):
        revenue = sql_sum(sale.net_amount for sale in rows)
        print(
            f"region={region:<6} "
            f"category={category:<12} "
            f"rows={len(rows):2d} "
            f"revenue={revenue}"
        )

    """
    SQL equivalent:

        SELECT
            region,
            category,
            COUNT(*) AS sale_count,
            SUM(net_amount) AS revenue
        FROM sales
        GROUP BY region, category;

    GROUP BY region, category does NOT independently group all regions
    and all categories. It groups by each distinct combination:

        (North, Electronics)
        (North, Furniture)
        (South, Electronics)
        ...

    This is multidimensional aggregation.
    """


# ---------------------------------------------------------------------------
# SECTION 8: WHERE BEFORE GROUP BY
# ---------------------------------------------------------------------------

def demonstrate_where_before_group_by() -> None:
    print("\n" + "=" * 80)
    print("4. WHERE FILTERING BEFORE GROUPING")
    print("=" * 80)

    completed_sales = [
        sale for sale in SALES
        if sale.status == "Completed"
    ]

    groups = group_by(completed_sales, lambda sale: sale.region)

    for region, rows in sorted(groups.items()):
        revenue = sql_sum(sale.net_amount for sale in rows)
        print(f"{region}: {revenue}")

    """
    SQL:

        SELECT region, SUM(net_amount) AS revenue
        FROM sales
        WHERE status = 'Completed'
        GROUP BY region;

    Logical order:

        FROM
        WHERE
        GROUP BY
        aggregate functions
        HAVING
        SELECT
        ORDER BY

    WHERE filters individual rows before grouping.
    """


# ---------------------------------------------------------------------------
# SECTION 9: HAVING
# ---------------------------------------------------------------------------

def having(
    groups: dict[Any, list[Any]],
    predicate: Callable[[Any, Sequence[Any]], bool],
) -> dict[Any, list[Any]]:
    """
    Apply a condition to complete groups.

    This models SQL HAVING.

    WHERE:
        filters rows.

    HAVING:
        filters groups after aggregation.
    """
    return {
        key: rows
        for key, rows in groups.items()
        if predicate(key, rows)
    }


def demonstrate_having() -> None:
    print("\n" + "=" * 80)
    print("5. HAVING")
    print("=" * 80)

    groups = group_by(SALES, lambda sale: sale.region)

    large_groups = having(
        groups,
        lambda region, rows: len(rows) >= 4,
    )

    print("Regions with at least four sales:")
    for region, rows in sorted(large_groups.items()):
        print(region, len(rows))

    revenue_groups = having(
        groups,
        lambda region, rows: (
            (sql_sum(sale.net_amount for sale in rows) or Decimal("0"))
            >= Decimal("5000")
        ),
    )

    print("\nRegions with revenue >= 5000:")
    for region, rows in sorted(revenue_groups.items()):
        revenue = sql_sum(sale.net_amount for sale in rows)
        print(region, revenue)

    """
    SQL:

        SELECT region, COUNT(*) AS sale_count
        FROM sales
        GROUP BY region
        HAVING COUNT(*) >= 4;

        SELECT region, SUM(net_amount) AS revenue
        FROM sales
        GROUP BY region
        HAVING SUM(net_amount) >= 5000;
    """


# ---------------------------------------------------------------------------
# SECTION 10: WHERE VERSUS HAVING
# ---------------------------------------------------------------------------

def demonstrate_where_vs_having() -> None:
    print("\n" + "=" * 80)
    print("6. WHERE VERSUS HAVING")
    print("=" * 80)

    completed = [
        sale for sale in SALES
        if sale.status == "Completed"
    ]

    groups = group_by(completed, lambda sale: sale.region)

    filtered_groups = having(
        groups,
        lambda region, rows: (
            (sql_sum(sale.net_amount for sale in rows) or Decimal("0"))
            > Decimal("3000")
        ),
    )

    for region, rows in sorted(filtered_groups.items()):
        revenue = sql_sum(sale.net_amount for sale in rows)
        print(region, revenue)

    """
    Correct conceptual translation:

        SELECT region, SUM(net_amount)
        FROM sales
        WHERE status = 'Completed'
        GROUP BY region
        HAVING SUM(net_amount) > 3000;

    Incorrect pattern:

        WHERE SUM(net_amount) > 3000

    Why?

    WHERE operates on rows before groups exist.
    SUM(net_amount) is a group-level result.

    HAVING is designed to filter group-level results.
    """


# ---------------------------------------------------------------------------
# SECTION 11: CONDITIONAL AGGREGATION
# ---------------------------------------------------------------------------

def demonstrate_conditional_aggregation() -> None:
    print("\n" + "=" * 80)
    print("7. CONDITIONAL AGGREGATION")
    print("=" * 80)

    groups = group_by(SALES, lambda sale: sale.region)

    for region, rows in sorted(groups.items()):
        completed_count = sum(
            sale.status == "Completed"
            for sale in rows
        )

        cancelled_count = sum(
            sale.status == "Cancelled"
            for sale in rows
        )

        electronics_revenue = sql_sum(
            sale.net_amount
            for sale in rows
            if sale.category == "Electronics"
        )

        print(
            f"{region:<6} "
            f"completed={completed_count:<2} "
            f"cancelled={cancelled_count:<2} "
            f"electronics_revenue={electronics_revenue}"
        )

    """
    SQL pattern:

        SELECT
            region,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END)
                AS completed_count,
            SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END)
                AS cancelled_count,
            SUM(
                CASE
                    WHEN category = 'Electronics'
                    THEN net_amount
                    ELSE 0
                END
            ) AS electronics_revenue
        FROM sales
        GROUP BY region;
    """


# ---------------------------------------------------------------------------
# SECTION 12: DISTINCT VERSUS GROUP BY
# ---------------------------------------------------------------------------

def demonstrate_distinct_vs_group_by() -> None:
    print("\n" + "=" * 80)
    print("8. DISTINCT VERSUS GROUP BY")
    print("=" * 80)

    distinct_regions = sorted({
        sale.region for sale in SALES
    })

    grouped_regions = sorted(
        group_by(SALES, lambda sale: sale.region).keys(),
        key=str,
    )

    print("DISTINCT-style values:", distinct_regions)
    print("GROUP BY keys:", grouped_regions)

    """
    These queries can return the same region names:

        SELECT DISTINCT region
        FROM sales;

        SELECT region
        FROM sales
        GROUP BY region;

    But GROUP BY becomes more useful when aggregate calculations are needed:

        SELECT region, COUNT(*)
        FROM sales
        GROUP BY region;

    DISTINCT answers a uniqueness question.
    GROUP BY establishes groups for aggregation.
    """


# ---------------------------------------------------------------------------
# SECTION 13: NULL HANDLING
# ---------------------------------------------------------------------------

def demonstrate_null_behavior() -> None:
    print("\n" + "=" * 80)
    print("9. NULL BEHAVIOR")
    print("=" * 80)

    rows = [
        Sale(
            100,
            "Test",
            "North",
            "Special",
            "Unknown",
            "Tester",
            2,
            None,
            Decimal("0.05"),
            "May",
            "Completed",
        ),
        Sale(
            101,
            "Test",
            "North",
            "Special",
            "Known",
            "Tester",
            3,
            Decimal("100"),
            None,
            "May",
            "Completed",
        ),
    ]

    prices = [row.unit_price for row in rows]
    revenues = [row.net_amount for row in rows]

    print("COUNT(*) =", sql_count_rows(rows))
    print("COUNT(unit_price) =", sql_count_values(prices))
    print("SUM(unit_price) =", sql_sum(prices))
    print("AVG(unit_price) =", sql_avg(prices))
    print("SUM(net_amount) =", sql_sum(revenues))

    """
    Important SQL distinction:

        COUNT(*)         counts rows.
        COUNT(column)   counts non-NULL values.
        SUM(column)     ignores NULL values.
        AVG(column)     ignores NULL values and divides by the count of
                        non-NULL values.

    NULL is not the same as zero.

    Treating NULL as zero is a business decision and should be explicit:

        COALESCE(amount, 0)
    """


# ---------------------------------------------------------------------------
# SECTION 14: COMMON GROUP BY MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    print("\n" + "=" * 80)
    print("10. COMMON MISTAKES")
    print("=" * 80)

    print(
        """
Mistake 1:
Filtering an aggregate in WHERE.

    Incorrect:
        WHERE SUM(net_amount) > 5000

    Correct:
        HAVING SUM(net_amount) > 5000

Mistake 2:
Selecting a non-grouped, non-aggregated column.

    Problematic:
        SELECT region, customer, SUM(net_amount)
        FROM sales
        GROUP BY region;

    The customer is ambiguous because a region may contain many customers.

Mistake 3:
Forgetting that GROUP BY changes the result granularity.

    A normal SELECT can return one row per sale.
    GROUP BY region returns one row per region.

Mistake 4:
Using HAVING when WHERE would be more efficient.

    If status is a row-level condition, use:
        WHERE status = 'Completed'

    rather than grouping everything and then filtering with a condition
    that does not actually depend on an aggregate.

Mistake 5:
Misunderstanding COUNT(column).

    COUNT(column) does not count NULL values.

Mistake 6:
Using AVG without understanding NULL behavior.

    AVG ignores NULL values. The denominator is not necessarily the number
    of rows in the group.

Mistake 7:
Grouping by too many columns.

    GROUP BY region, category, product, customer

    may create a very fine-grained result that is difficult to analyze.

Mistake 8:
Grouping by too few columns.

    If the business question requires region and month, grouping only by
    region loses the month-level dimension.

Mistake 9:
Rounding before aggregation.

    SUM(rounded_values) can differ from ROUND(SUM(values), 2).

Mistake 10:
Ignoring data quality.

    Different spellings such as 'North', 'north', and ' NORTH ' may form
    different groups unless normalized.
        """
    )


# ---------------------------------------------------------------------------
# SECTION 15: DATA NORMALIZATION BEFORE GROUPING
# ---------------------------------------------------------------------------

def normalize_region(region: str | None) -> str:
    if region is None:
        return "UNKNOWN"

    normalized = " ".join(region.strip().split()).upper()

    return normalized if normalized else "UNKNOWN"


def demonstrate_normalization() -> None:
    print("\n" + "=" * 80)
    print("11. NORMALIZATION BEFORE GROUPING")
    print("=" * 80)

    messy_regions = [
        "North",
        " north ",
        "NORTH",
        "South",
        " south",
        None,
        "",
    ]

    groups = group_by(messy_regions, normalize_region)

    for key, values in sorted(groups.items()):
        print(f"{key}: {len(values)}")

    """
    Data normalization is often necessary before grouping.

    Otherwise visually equivalent values can become separate groups.

    In SQL, this might involve:

        GROUP BY UPPER(TRIM(region))

    but applying functions to columns can have indexing and performance
    implications depending on the database engine.
    """


# ---------------------------------------------------------------------------
# SECTION 16: MULTIDIMENSIONAL AGGREGATION
# ---------------------------------------------------------------------------

def rollup_region_category(
    rows: Sequence[Sale],
) -> list[tuple[str | None, str | None, Decimal | None]]:
    """
    Simulates:

        GROUP BY ROLLUP(region, category)

    Result levels:

        region + category
        region subtotal
        grand total
    """
    results: list[tuple[str | None, str | None, Decimal | None]] = []

    by_region_category = group_by(
        rows,
        lambda sale: (sale.region, sale.category),
    )

    for (region, category), grouped_rows in sorted(
        by_region_category.items(),
        key=lambda item: (str(item[0][0]), str(item[0][1])),
    ):
        results.append(
            (
                region,
                category,
                sql_sum(sale.net_amount for sale in grouped_rows),
            )
        )

    by_region = group_by(rows, lambda sale: sale.region)

    for region, grouped_rows in sorted(
        by_region.items(),
        key=lambda item: str(item[0]),
    ):
        results.append(
            (
                region,
                None,
                sql_sum(sale.net_amount for sale in grouped_rows),
            )
        )

    results.append(
        (
            None,
            None,
            sql_sum(sale.net_amount for sale in rows),
        )
    )

    return results


def demonstrate_rollup() -> None:
    print("\n" + "=" * 80)
    print("12. ROLLUP-STYLE MULTIDIMENSIONAL AGGREGATION")
    print("=" * 80)

    results = rollup_region_category(SALES)

    for region, category, revenue in results:
        print(
            f"region={str(region):<8} "
            f"category={str(category):<12} "
            f"revenue={revenue}"
        )

    """
    SQL in databases that support ROLLUP:

        SELECT
            region,
            category,
            SUM(net_amount) AS revenue
        FROM sales
        GROUP BY ROLLUP(region, category);

    Conceptually this produces:

        detail rows
        region subtotals
        grand total

    ROLLUP is hierarchical.
    """


def cube_like(rows: Sequence[Sale]) -> list[tuple[str | None, str | None, Decimal | None]]:
    """
    Simulates GROUP BY CUBE(region, category).

    CUBE creates every combination of the supplied dimensions:

        region + category
        region only
        category only
        grand total
    """
    dimensions = [
        ("region", lambda sale: sale.region),
        ("category", lambda sale: sale.category),
    ]

    results: list[tuple[str | None, str | None, Decimal | None]] = []

    for include_region, include_category in [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]:
        groups: dict[tuple[Any, ...], list[Sale]] = defaultdict(list)

        for sale in rows:
            key: list[Any] = []

            if include_region:
                key.append(dimensions[0][1](sale))
            else:
                key.append(None)

            if include_category:
                key.append(dimensions[1][1](sale))
            else:
                key.append(None)

            groups[tuple(key)].append(sale)

        for key, grouped_rows in sorted(
            groups.items(),
            key=lambda item: (str(item[0][0]), str(item[0][1])),
        ):
            results.append(
                (
                    key[0],
                    key[1],
                    sql_sum(sale.net_amount for sale in grouped_rows),
                )
            )

    return results


def demonstrate_cube() -> None:
    print("\n" + "=" * 80)
    print("13. CUBE-STYLE AGGREGATION")
    print("=" * 80)

    results = cube_like(SALES)

    for region, category, revenue in results:
        print(
            f"region={str(region):<8} "
            f"category={str(category):<12} "
            f"revenue={revenue}"
        )

    """
    SQL in systems supporting CUBE:

        GROUP BY CUBE(region, category)

    CUBE is different from ROLLUP.

    ROLLUP(region, category):
        region + category
        region
        grand total

    CUBE(region, category):
        region + category
        region
        category
        grand total

    With n dimensions, CUBE can produce up to 2^n grouping combinations.
    """


# ---------------------------------------------------------------------------
# SECTION 17: GROUPING SETS CONCEPT
# ---------------------------------------------------------------------------

def grouping_sets_like(rows: Sequence[Sale]) -> dict[str, dict[Any, Decimal | None]]:
    """
    Demonstrates the conceptual purpose of GROUPING SETS.

    A real SQL query might request:

        GROUP BY GROUPING SETS (
            (region),
            (category),
            ()
        )

    This asks for region totals, category totals, and a grand total
    without requiring multiple separate aggregation queries.
    """
    result: dict[str, dict[Any, Decimal | None]] = {}

    by_region = group_by(rows, lambda sale: sale.region)
    result["region"] = {
        region: sql_sum(sale.net_amount for sale in grouped_rows)
        for region, grouped_rows in by_region.items()
    }

    by_category = group_by(rows, lambda sale: sale.category)
    result["category"] = {
        category: sql_sum(sale.net_amount for sale in grouped_rows)
        for category, grouped_rows in by_category.items()
    }

    result["grand_total"] = {
        "ALL": sql_sum(sale.net_amount for sale in rows)
    }

    return result


def demonstrate_grouping_sets() -> None:
    print("\n" + "=" * 80)
    print("14. GROUPING SETS-STYLE AGGREGATION")
    print("=" * 80)

    result = grouping_sets_like(SALES)

    for grouping_name, values in result.items():
        print(f"\n{grouping_name}:")
        for key, value in values.items():
            print(f"  {key}: {value}")


# ---------------------------------------------------------------------------
# SECTION 18: GROUP BY VERSUS WINDOW FUNCTIONS
# ---------------------------------------------------------------------------

def demonstrate_group_by_vs_window() -> None:
    print("\n" + "=" * 80)
    print("15. GROUP BY VERSUS WINDOW FUNCTIONS")
    print("=" * 80)

    by_region = group_by(SALES, lambda sale: sale.region)

    group_totals = {
        region: sql_sum(sale.net_amount for sale in rows)
        for region, rows in by_region.items()
    }

    print("GROUP BY produces one result per group:")

    for region, total in sorted(group_totals.items()):
        print(region, total)

    print("\nWindow-style result preserves individual rows:")

    for sale in SALES[:6]:
        region_total = group_totals[sale.region]
        print(
            sale.sale_id,
            sale.region,
            sale.net_amount,
            region_total,
        )

    """
    GROUP BY changes result granularity.

    A window function such as:

        SUM(net_amount) OVER (PARTITION BY region)

    calculates a region total while preserving each original sale row.

    This distinction is fundamental:

        GROUP BY  -> collapse rows into groups
        WINDOW    -> calculate across related rows while retaining rows
    """


# ---------------------------------------------------------------------------
# SECTION 19: ADVANCED HAVING CONDITIONS
# ---------------------------------------------------------------------------

def demonstrate_advanced_having() -> None:
    print("\n" + "=" * 80)
    print("16. ADVANCED HAVING CONDITIONS")
    print("=" * 80)

    groups = group_by(SALES, lambda sale: sale.salesperson)

    selected = having(
        groups,
        lambda salesperson, rows: (
            len(rows) >= 3
            and (
                sql_sum(sale.net_amount for sale in rows)
                or Decimal("0")
            ) >= Decimal("3000")
            and (
                sql_avg(sale.quantity for sale in rows)
                or Decimal("0")
            ) >= Decimal("3")
        ),
    )

    for salesperson, rows in sorted(selected.items()):
        print(
            salesperson,
            "count=", len(rows),
            "revenue=", sql_sum(s.net_amount for s in rows),
            "avg_quantity=", sql_avg(s.quantity for s in rows),
        )

    """
    SQL pattern:

        GROUP BY salesperson
        HAVING COUNT(*) >= 3
           AND SUM(net_amount) >= 3000
           AND AVG(quantity) >= 3;
    """


# ---------------------------------------------------------------------------
# SECTION 20: HAVING WITH CONDITIONAL LOGIC
# ---------------------------------------------------------------------------

def demonstrate_having_with_conditions() -> None:
    print("\n" + "=" * 80)
    print("17. HAVING WITH CONDITIONAL LOGIC")
    print("=" * 80)

    groups = group_by(SALES, lambda sale: sale.category)

    for category, rows in sorted(groups.items()):
        completed = [
            sale for sale in rows
            if sale.status == "Completed"
        ]

        completed_revenue = sql_sum(
            sale.net_amount for sale in completed
        )

        completed_count = len(completed)

        if (
            completed_count >= 3
            and (completed_revenue or Decimal("0")) >= Decimal("3000")
        ):
            print(
                category,
                "completed_count=", completed_count,
                "completed_revenue=", completed_revenue,
            )


# ---------------------------------------------------------------------------
# SECTION 21: EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 80)
    print("18. EDGE CASES")
    print("=" * 80)

    empty_rows: list[Sale] = []

    empty_groups = group_by(empty_rows, lambda sale: sale.region)

    print("Empty input groups:", empty_groups)
    print("COUNT empty:", sql_count_rows(empty_rows))
    print("SUM empty:", sql_sum([]))
    print("AVG empty:", sql_avg([]))

    null_region_sale = Sale(
        999,
        "Null Region Customer",
        None,
        "Electronics",
        "Unknown",
        "Tester",
        1,
        Decimal("100"),
        Decimal("0"),
        "May",
        "Completed",
    )

    null_group = group_by(
        [null_region_sale],
        lambda sale: sale.region,
    )

    print("NULL-like group key:", null_group)

    """
    Important edge cases include:

    - Empty input
    - All values NULL
    - Some values NULL
    - NULL grouping keys
    - Zero values
    - Negative values where business rules permit them
    - Duplicate rows
    - Very large groups
    - Extremely high-cardinality grouping keys
    - Inconsistent text casing and whitespace
    """


# ---------------------------------------------------------------------------
# SECTION 22: INPUT VALIDATION
# ---------------------------------------------------------------------------

def validate_sale(sale: Sale) -> list[str]:
    errors: list[str] = []

    if sale.sale_id <= 0:
        errors.append("sale_id must be positive")

    if not sale.customer.strip():
        errors.append("customer cannot be empty")

    if sale.quantity < 0:
        errors.append("quantity cannot be negative")

    if sale.unit_price is not None and sale.unit_price < 0:
        errors.append("unit_price cannot be negative")

    if sale.discount is not None and not (
        Decimal("0") <= sale.discount <= Decimal("1")
    ):
        errors.append("discount must be between 0 and 1")

    allowed_statuses = {"Completed", "Cancelled"}

    if sale.status not in allowed_statuses:
        errors.append("invalid status")

    return errors


def demonstrate_validation() -> None:
    print("\n" + "=" * 80)
    print("19. VALIDATION")
    print("=" * 80)

    invalid_sale = Sale(
        -1,
        "",
        "North",
        "Electronics",
        "Phone",
        "Ravi",
        -10,
        Decimal("-50"),
        Decimal("1.5"),
        "May",
        "Unknown",
    )

    errors = validate_sale(invalid_sale)

    for error in errors:
        print("ERROR:", error)


# ---------------------------------------------------------------------------
# SECTION 23: PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def demonstrate_performance_concepts() -> None:
    print("\n" + "=" * 80)
    print("20. PERFORMANCE CONSIDERATIONS")
    print("=" * 80)

    print(
        """
For a typical hash-based grouping implementation:

    Time:
        approximately O(n) for n input rows

    Space:
        approximately O(n) in the worst case because groups retain rows.

Database engines can implement GROUP BY using several strategies:

1. Hash aggregation
   - Build a hash table keyed by grouping columns.
   - Often efficient for unsorted data.
   - Requires memory for groups.

2. Sort-based aggregation
   - Sort rows by grouping keys.
   - Aggregate consecutive rows.
   - Can benefit from existing ordering or indexes.
   - Sorting can cost approximately O(n log n).

3. Parallel aggregation
   - Partition work among workers.
   - Compute partial aggregates.
   - Merge partial results.

Performance practices:

- Filter rows early with WHERE when possible.
- Select only required columns.
- Avoid unnecessary high-cardinality grouping.
- Use appropriate indexes where they help the filtering/grouping workload.
- Inspect execution plans for large production queries.
- Be careful with functions applied to indexed columns.
- Consider pre-aggregation or materialized views for repeated expensive reports.

A HAVING condition generally cannot replace a selective WHERE predicate when
the condition can be evaluated before grouping.
        """
    )


# ---------------------------------------------------------------------------
# SECTION 24: SECURITY CONSIDERATIONS
# ---------------------------------------------------------------------------

def demonstrate_security_concepts() -> None:
    print("\n" + "=" * 80)
    print("21. SECURITY CONSIDERATIONS")
    print("=" * 80)

    print(
        """
GROUP BY itself is not an injection vulnerability.

The risk appears when application code constructs SQL dynamically from
untrusted input.

Unsafe conceptual pattern:

    SQL string = "SELECT ... GROUP BY " + user_input

Safer approaches include:

- Whitelist permitted grouping columns.
- Use parameterized queries for values.
- Do not assume parameters can safely represent SQL identifiers.
- Validate sort and grouping choices against known column names.
- Apply authorization before exposing sensitive aggregates.
- Consider whether aggregate results can reveal confidential information.

Aggregation can also create privacy risks.

For example, if a report exposes groups containing only one person's data,
an aggregate can indirectly reveal that person's information.

Possible controls include:

- Minimum group-size thresholds.
- Role-based access.
- Data masking.
- Aggregation policies.
- Careful handling of NULL and missing categories.
        """
    )


# ---------------------------------------------------------------------------
# SECTION 25: REALISTIC ANALYTICS REPORT
# ---------------------------------------------------------------------------

def sales_analytics_report(
    sales: Sequence[Sale],
) -> list[dict[str, Any]]:
    """
    Produce a business report:

    1. Ignore cancelled transactions.
    2. Group by region and category.
    3. Calculate transaction count, units, and revenue.
    4. Retain groups with at least two transactions.
    5. Sort by revenue descending.
    """
    completed = [
        sale for sale in sales
        if sale.status == "Completed"
    ]

    groups = group_by(
        completed,
        lambda sale: (sale.region, sale.category),
    )

    report: list[dict[str, Any]] = []

    for (region, category), rows in groups.items():
        revenue = sql_sum(sale.net_amount for sale in rows) or Decimal("0")

        if len(rows) < 2:
            continue

        report.append(
            {
                "region": region,
                "category": category,
                "transactions": len(rows),
                "units": sql_sum(sale.quantity for sale in rows) or 0,
                "revenue": revenue,
                "average_transaction": (
                    revenue / Decimal(len(rows))
                ),
            }
        )

    report.sort(
        key=lambda item: item["revenue"],
        reverse=True,
    )

    return report


def demonstrate_realistic_report() -> None:
    print("\n" + "=" * 80)
    print("22. REALISTIC SALES ANALYTICS REPORT")
    print("=" * 80)

    report = sales_analytics_report(SALES)

    for item in report:
        print(
            f"{item['region']:<6} | "
            f"{item['category']:<12} | "
            f"transactions={item['transactions']:<2} | "
            f"units={item['units']:<3} | "
            f"revenue={item['revenue']} | "
            f"average={item['average_transaction']}"
        )

    """
    SQL equivalent:

        SELECT
            region,
            category,
            COUNT(*) AS transactions,
            SUM(quantity) AS units,
            SUM(net_amount) AS revenue,
            AVG(net_amount) AS average_transaction
        FROM sales
        WHERE status = 'Completed'
        GROUP BY region, category
        HAVING COUNT(*) >= 2
        ORDER BY revenue DESC;

    This is a canonical example of the relationship between:

        WHERE
            -> row filtering

        GROUP BY
            -> group formation

        aggregate functions
            -> group calculations

        HAVING
            -> group filtering

        ORDER BY
            -> final result ordering
    """


# ---------------------------------------------------------------------------
# SECTION 26: TESTING
# ---------------------------------------------------------------------------

def assert_equal(actual: Any, expected: Any, message: str) -> None:
    if actual != expected:
        raise AssertionError(
            f"{message}\nExpected: {expected!r}\nActual: {actual!r}"
        )


def run_tests() -> None:
    print("\n" + "=" * 80)
    print("23. TESTS")
    print("=" * 80)

    assert_equal(
        sql_count_rows([1, 2, 3]),
        3,
        "COUNT(*) should count rows",
    )

    assert_equal(
        sql_count_values([1, None, 2, None]),
        2,
        "COUNT(column) should ignore NULL",
    )

    assert_equal(
        sql_sum([Decimal("10"), None, Decimal("20")]),
        Decimal("30"),
        "SUM should ignore NULL",
    )

    assert_equal(
        sql_avg([Decimal("10"), None, Decimal("20")]),
        Decimal("15"),
        "AVG should ignore NULL",
    )

    region_groups = group_by(
        SALES,
        lambda sale: sale.region,
    )

    assert_equal(
        len(region_groups),
        4,
        "Expected four regions",
    )

    completed = [
        sale for sale in SALES
        if sale.status == "Completed"
    ]

    assert all(
        sale.status == "Completed"
        for sale in completed
    )

    selected = having(
        region_groups,
        lambda region, rows: len(rows) >= 4,
    )

    assert all(
        len(rows) >= 4
        for rows in selected.values()
    )

    report = sales_analytics_report(SALES)

    assert all(
        item["transactions"] >= 2
        for item in report
    )

    assert report == sorted(
        report,
        key=lambda item: item["revenue"],
        reverse=True,
    )

    print("All tests passed.")


# ---------------------------------------------------------------------------
# SECTION 27: SQL QUERY REFERENCE
# ---------------------------------------------------------------------------

def print_sql_reference() -> None:
    print("\n" + "=" * 80)
    print("24. SQL REFERENCE")
    print("=" * 80)

    print(
        """
1. Basic grouping

   SELECT region, COUNT(*)
   FROM sales
   GROUP BY region;

2. Multiple aggregates

   SELECT
       region,
       COUNT(*) AS count,
       SUM(net_amount) AS revenue,
       AVG(net_amount) AS average_revenue
   FROM sales
   GROUP BY region;

3. WHERE + GROUP BY

   SELECT region, SUM(net_amount)
   FROM sales
   WHERE status = 'Completed'
   GROUP BY region;

4. GROUP BY + HAVING

   SELECT region, COUNT(*)
   FROM sales
   GROUP BY region
   HAVING COUNT(*) >= 4;

5. WHERE + GROUP BY + HAVING

   SELECT region, SUM(net_amount)
   FROM sales
   WHERE status = 'Completed'
   GROUP BY region
   HAVING SUM(net_amount) > 3000;

6. Multidimensional grouping

   SELECT region, category, SUM(net_amount)
   FROM sales
   GROUP BY region, category;

7. Conditional aggregation

   SELECT
       region,
       SUM(
           CASE WHEN status = 'Completed'
                THEN 1 ELSE 0 END
       ) AS completed_count
   FROM sales
   GROUP BY region;

8. ROLLUP

   SELECT region, category, SUM(net_amount)
   FROM sales
   GROUP BY ROLLUP(region, category);

9. CUBE

   SELECT region, category, SUM(net_amount)
   FROM sales
   GROUP BY CUBE(region, category);

10. GROUPING SETS

    SELECT region, category, SUM(net_amount)
    FROM sales
    GROUP BY GROUPING SETS (
        (region),
        (category),
        ()
    );

The exact availability and syntax of ROLLUP, CUBE, GROUPING SETS, FILTER,
and related features depend on the SQL database system.
        """
    )


# ---------------------------------------------------------------------------
# SECTION 28: EXECUTION ORDER
# ---------------------------------------------------------------------------

def print_logical_query_order() -> None:
    print("\n" + "=" * 80)
    print("25. LOGICAL SQL PROCESSING ORDER")
    print("=" * 80)

    order = [
        "1. FROM / JOIN",
        "2. WHERE",
        "3. GROUP BY",
        "4. Aggregate calculation",
        "5. HAVING",
        "6. SELECT",
        "7. DISTINCT",
        "8. ORDER BY",
        "9. LIMIT / OFFSET",
    ]

    for step in order:
        print(step)

    print(
        """
This is a logical processing model, not necessarily the physical order
used internally by a database engine.

The distinction explains many SQL errors.

For example, a group aggregate is not available to a normal WHERE predicate
because WHERE logically operates before grouping.

HAVING exists specifically for conditions involving grouped results.
        """
    )


# ---------------------------------------------------------------------------
# SECTION 29: ADVANCED DESIGN OBSERVATIONS
# ---------------------------------------------------------------------------

def print_advanced_observations() -> None:
    print("\n" + "=" * 80)
    print("26. ADVANCED DESIGN OBSERVATIONS")
    print("=" * 80)

    print(
        """
1. Result grain

Before writing GROUP BY, define the desired grain.

Examples:

    one row per region
    one row per region and category
    one row per month and product
    one row per salesperson and quarter

The GROUP BY columns normally define that grain.

2. Measures versus dimensions

Dimensions:
    region
    category
    month
    salesperson

Measures:
    quantity
    revenue
    discount
    transaction count

GROUP BY generally organizes dimensions while aggregate functions calculate
measures.

3. Functional dependencies

Some database systems permit selecting columns that are functionally
dependent on grouping columns, while others enforce stricter grouping rules.

Do not rely on permissive behavior unless the database's semantics are known.

4. Aggregation levels

A report may require:

    transaction
    product
    category
    region
    organization

Moving between these levels changes the meaning of every measure.

5. Double counting

Joining multiple one-to-many tables before aggregation can multiply rows.

For example:

    customers
        -> orders
        -> order_items

A careless join can cause COUNT and SUM to become larger than expected.

Always verify the row grain before aggregation.

6. Numerical precision

Financial values should use suitable exact numeric types in database systems.
Binary floating-point arithmetic can introduce rounding effects.

7. Materialization

Repeatedly expensive grouped reports may be candidates for:

    materialized views
    summary tables
    incremental aggregation

The correct choice depends on freshness requirements and workload.

8. High-cardinality groups

Grouping by a nearly unique identifier can create almost one group per row.
This can increase memory consumption and reduce the usefulness of aggregation.

9. HAVING and optimizer behavior

A database optimizer may transform or push predicates when semantics allow.
Therefore, the SQL's logical processing order explains correctness, while
the execution plan explains actual physical performance.
        """
    )


# ---------------------------------------------------------------------------
# SECTION 30: MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("GROUP BY & HAVING: COMPREHENSIVE PYTHON STUDY PROGRAM")
    print("=" * 80)

    demonstrate_basic_group_by()
    demonstrate_multiple_aggregates()
    demonstrate_multidimensional_grouping()
    demonstrate_where_before_group_by()
    demonstrate_having()
    demonstrate_where_vs_having()
    demonstrate_conditional_aggregation()
    demonstrate_distinct_vs_group_by()
    demonstrate_null_behavior()
    demonstrate_common_mistakes()
    demonstrate_normalization()
    demonstrate_rollup()
    demonstrate_cube()
    demonstrate_grouping_sets()
    demonstrate_group_by_vs_window()
    demonstrate_advanced_having()
    demonstrate_having_with_conditions()
    demonstrate_edge_cases()
    demonstrate_validation()
    demonstrate_performance_concepts()
    demonstrate_security_concepts()
    demonstrate_realistic_report()
    run_tests()
    print_sql_reference()
    print_logical_query_order()
    print_advanced_observations()

    print("\n" + "=" * 80)
    print("PROGRAM COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
