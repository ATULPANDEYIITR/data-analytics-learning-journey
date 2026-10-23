#!/usr/bin/env python3

"""
Pandas Grouping: groupby, aggregation, transform, pivot_table, crosstab

A self-contained repository sales-analysis workflow demonstrating:
- groupby for partitioning records
- aggregation for group-level metrics
- transform for row-level metrics derived from groups
- pivot_table for multidimensional summaries
- crosstab for categorical frequency analysis
- validation, missing values, edge cases, and reproducible reporting

Requires:
    Python 3.10+
    pandas
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


CSV_DATA = """order_id,order_date,region,department,channel,product,customer_segment,units,unit_price,discount,returned
1001,2026-01-05,North,Cloud,Online,Compute,Enterprise,8,1200,0.05,false
1002,2026-01-07,North,Security,Partner,Firewall,Enterprise,4,2100,0.00,false
1003,2026-01-09,South,Cloud,Online,Storage,SMB,15,400,0.10,false
1004,2026-01-11,West,Data,Direct,Analytics,Enterprise,6,1800,0.05,false
1005,2026-01-13,East,Security,Online,Identity,SMB,20,250,0.00,true
1006,2026-01-15,North,Data,Partner,Analytics,SMB,5,1800,0.15,false
1007,2026-01-18,South,Security,Direct,Firewall,Enterprise,3,2100,0.05,false
1008,2026-01-20,West,Cloud,Online,Compute,12,1200,0.00,false
1009,2026-01-22,East,Data,Direct,Analytics,Enterprise,7,1800,0.10,false
1010,2026-01-25,North,Cloud,Partner,Storage,SMB,30,400,0.05,false
1011,2026-02-02,South,Cloud,Online,Compute,Enterprise,5,1200,0.00,false
1012,2026-02-04,West,Security,Partner,Identity,SMB,18,250,0.10,true
1013,2026-02-06,East,Cloud,Direct,Storage,SMB,22,400,0.05,false
1014,2026-02-08,North,Data,Online,Analytics,Enterprise,4,1800,0.00,false
1015,2026-02-11,South,Security,Online,Firewall,SMB,9,2100,0.15,false
1016,2026-02-14,West,Cloud,Direct,Compute,10,1200,0.05,false
1017,2026-02-17,East,Security,Partner,Identity,Enterprise,11,250,0.00,false
1018,2026-02-20,North,Data,Direct,Analytics,SMB,8,1800,0.10,true
"""


@dataclass(frozen=True)
class AnalysisConfig:
    revenue_column: str = "revenue"
    net_revenue_column: str = "net_revenue"
    high_value_threshold: float = 5000.0


def load_orders(source: str | Path | StringIO) -> pd.DataFrame:
    """Load and validate the raw order dataset."""
    frame = pd.read_csv(source)

    required = {
        "order_id",
        "order_date",
        "region",
        "department",
        "channel",
        "product",
        "customer_segment",
        "units",
        "unit_price",
        "discount",
        "returned",
    }

    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if frame["order_id"].duplicated().any():
        duplicates = frame.loc[frame["order_id"].duplicated(), "order_id"].tolist()
        raise ValueError(f"Duplicate order IDs: {duplicates}")

    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="raise")

    numeric_columns = ["units", "unit_price", "discount"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    if (frame["units"] <= 0).any():
        raise ValueError("Units must be positive.")

    if (frame["unit_price"] < 0).any():
        raise ValueError("Unit price cannot be negative.")

    if not frame["discount"].between(0, 1).all():
        raise ValueError("Discount must be between 0 and 1.")

    frame["returned"] = frame["returned"].astype(bool)

    if frame[
        ["region", "department", "channel", "product", "customer_segment"]
    ].isna().any().any():
        raise ValueError("Grouping dimensions cannot contain missing values.")

    return frame


def enrich_orders(frame: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """Create row-level measures before group-level analysis."""
    result = frame.copy()

    # Revenue is calculated at the individual transaction level.
    result[config.revenue_column] = result["units"] * result["unit_price"]

    # Discount is represented as a fraction, so net revenue remains numeric.
    result[config.net_revenue_column] = (
        result[config.revenue_column] * (1 - result["discount"])
    )

    result["month"] = result["order_date"].dt.to_period("M").astype(str)

    result["high_value_order"] = (
        result[config.net_revenue_column] >= config.high_value_threshold
    )

    return result


def basic_groupby(frame: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """Aggregate revenue, units, orders, and returns by region."""
    grouped = (
        frame.groupby("region", observed=True)
        .agg(
            orders=("order_id", "count"),
            units=("units", "sum"),
            gross_revenue=(config.revenue_column, "sum"),
            net_revenue=(config.net_revenue_column, "sum"),
            returned_orders=("returned", "sum"),
        )
        .reset_index()
    )

    grouped["return_rate"] = (
        grouped["returned_orders"] / grouped["orders"]
    ).round(4)

    return grouped.sort_values("net_revenue", ascending=False)


def multi_key_groupby(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """Aggregate at the region and department level."""
    return (
        frame.groupby(["region", "department"], observed=True)
        .agg(
            orders=("order_id", "count"),
            units=("units", "sum"),
            net_revenue=(config.net_revenue_column, "sum"),
            average_order_value=(config.net_revenue_column, "mean"),
        )
        .reset_index()
        .sort_values(["region", "net_revenue"], ascending=[True, False])
    )


def custom_aggregation(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """Use multiple aggregation functions for distributional information."""
    result = (
        frame.groupby("department", observed=True)
        .agg(
            order_count=("order_id", "count"),
            total_units=("units", "sum"),
            revenue_mean=(config.net_revenue_column, "mean"),
            revenue_median=(config.net_revenue_column, "median"),
            revenue_min=(config.net_revenue_column, "min"),
            revenue_max=(config.net_revenue_column, "max"),
        )
        .reset_index()
    )

    result["revenue_range"] = result["revenue_max"] - result["revenue_min"]
    return result.sort_values("revenue_mean", ascending=False)


def transform_analysis(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """
    Demonstrate transform.

    Unlike aggregation, transform returns one value per original row.
    This permits group-level metrics to be attached to transaction records.
    """
    result = frame.copy()

    region_totals = result.groupby("region", observed=True)[
        config.net_revenue_column
    ].transform("sum")

    department_means = result.groupby("department", observed=True)[
        config.net_revenue_column
    ].transform("mean")

    result["region_net_revenue"] = region_totals
    result["region_revenue_share"] = (
        result[config.net_revenue_column] / region_totals
    )

    result["department_average_revenue"] = department_means
    result["above_department_average"] = (
        result[config.net_revenue_column] > department_means
    )

    return result


def pivot_analysis(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """Build a multidimensional region-by-channel revenue table."""
    pivot = pd.pivot_table(
        frame,
        index="region",
        columns="channel",
        values=config.net_revenue_column,
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Grand Total",
    )

    return pivot.round(2)


def crosstab_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """Count orders across two categorical dimensions."""
    return pd.crosstab(
        frame["department"],
        frame["channel"],
        margins=True,
        margins_name="Total",
    )


def conditional_grouping(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """Group only records satisfying a business condition."""
    high_value = frame.loc[frame["high_value_order"]].copy()

    if high_value.empty:
        return pd.DataFrame(
            columns=["region", "high_value_orders", "high_value_revenue"]
        )

    return (
        high_value.groupby("region", observed=True)
        .agg(
            high_value_orders=("order_id", "count"),
            high_value_revenue=(config.net_revenue_column, "sum"),
        )
        .reset_index()
        .sort_values("high_value_revenue", ascending=False)
    )


def group_filtering(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """Keep groups whose total net revenue exceeds a threshold."""
    threshold = 9000.0

    filtered = frame.groupby("region", observed=True).filter(
        lambda group: group[config.net_revenue_column].sum() >= threshold
    )

    return filtered


def safe_grouped_ratio(
    frame: pd.DataFrame, config: AnalysisConfig
) -> pd.DataFrame:
    """
    Demonstrate a ratio that remains valid when a denominator is zero.

    Current data has positive order counts, but the explicit guard makes
    the transformation safe for future filtered or sparse datasets.
    """
    result = (
        frame.groupby("customer_segment", observed=True)
        .agg(
            orders=("order_id", "count"),
            returned_orders=("returned", "sum"),
            revenue=(config.net_revenue_column, "sum"),
        )
        .reset_index()
    )

    result["return_rate"] = result["returned_orders"].div(
        result["orders"].where(result["orders"].ne(0))
    )

    return result


def demonstrate_file_round_trip(
    frame: pd.DataFrame, directory: Path
) -> pd.DataFrame:
    """Persist and reload grouped output to validate a practical workflow."""
    output_path = directory / "regional_summary.csv"

    summary = (
        frame.groupby("region", observed=True)
        .agg(net_revenue=("net_revenue", "sum"))
        .reset_index()
    )

    summary.to_csv(output_path, index=False)
    return pd.read_csv(output_path)


def assert_invariants(
    frame: pd.DataFrame,
    region_summary: pd.DataFrame,
    transformed: pd.DataFrame,
) -> None:
    """Check relationships that should remain true after grouping."""
    source_revenue = frame["net_revenue"].sum()
    grouped_revenue = region_summary["net_revenue"].sum()

    if not abs(source_revenue - grouped_revenue) < 1e-9:
        raise AssertionError("Grouped revenue does not reconcile with source data.")

    if len(transformed) != len(frame):
        raise AssertionError("transform changed the number of source rows.")

    if not transformed["region_revenue_share"].between(0, 1).all():
        raise AssertionError("Regional revenue shares must be between 0 and 1.")

    share_sum = transformed.groupby("region", observed=True)[
        "region_revenue_share"
    ].sum()

    if not share_sum.sub(1).abs().lt(1e-9).all():
        raise AssertionError("Regional revenue shares must sum to one.")


def print_report(
    region_summary: pd.DataFrame,
    multi_summary: pd.DataFrame,
    aggregation: pd.DataFrame,
    pivot: pd.DataFrame,
    crosstab: pd.DataFrame,
    high_value: pd.DataFrame,
    segment_summary: pd.DataFrame,
    file_round_trip: pd.DataFrame,
) -> None:
    print("\nREGION GROUPBY")
    print(region_summary.to_string(index=False))

    print("\nREGION + DEPARTMENT GROUPBY")
    print(multi_summary.to_string(index=False))

    print("\nDEPARTMENT AGGREGATION")
    print(aggregation.to_string(index=False))

    print("\nPIVOT TABLE: REGION × CHANNEL")
    print(pivot.to_string())

    print("\nCROSSTAB: DEPARTMENT × CHANNEL")
    print(crosstab.to_string())

    print("\nHIGH-VALUE ORDER GROUPING")
    print(high_value.to_string(index=False))

    print("\nCUSTOMER SEGMENT GROUPING")
    print(segment_summary.to_string(index=False))

    print("\nCSV ROUND-TRIP")
    print(file_round_trip.to_string(index=False))


def main() -> None:
    config = AnalysisConfig()

    orders = load_orders(StringIO(CSV_DATA))
    orders = enrich_orders(orders, config)

    region_summary = basic_groupby(orders, config)
    multi_summary = multi_key_groupby(orders, config)
    aggregation = custom_aggregation(orders, config)
    transformed = transform_analysis(orders, config)
    pivot = pivot_analysis(orders, config)
    crosstab = crosstab_analysis(orders)
    high_value = conditional_grouping(orders, config)
    _ = group_filtering(orders, config)
    segment_summary = safe_grouped_ratio(orders, config)

    with TemporaryDirectory() as temporary_directory:
        file_round_trip = demonstrate_file_round_trip(
            orders,
            Path(temporary_directory),
        )

    assert_invariants(orders, region_summary, transformed)

    print_report(
        region_summary,
        multi_summary,
        aggregation,
        pivot,
        crosstab,
        high_value,
        segment_summary,
        file_round_trip,
    )

    print("\nVALIDATION")
    print(f"Source orders: {len(orders)}")
    print(f"Source net revenue: {orders['net_revenue'].sum():,.2f}")
    print(f"Returned orders: {orders['returned'].sum()}")
    print("All grouping and reconciliation invariants passed.")


if __name__ == "__main__":
    main()
