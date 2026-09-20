from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "order_id",
    "order_date",
    "product",
    "category",
    "region",
    "salesperson",
    "city",
    "quantity",
    "unit_price",
    "discount_rate",
    "channel",
]

PRODUCT_CATEGORY = {
    "Laptop Pro 14": "Electronics",
    "Wireless Mouse": "Electronics",
    "Monitor 27": "Electronics",
    "Keyboard": "Electronics",
    "USB-C Hub": "Electronics",
    "Office Chair": "Furniture",
    "Desk Lamp": "Furniture",
    "Standing Desk": "Furniture",
    "Notebook Pack": "Stationery",
    "Pen Set": "Stationery",
}


@dataclass(frozen=True)
class CleaningReport:
    """Records the important transformations performed on the raw dataset."""

    input_rows: int
    output_rows: int
    duplicate_rows_removed: int
    missing_categories_repaired: int
    missing_quantities_repaired: int
    invalid_prices_repaired: int
    missing_discounts_repaired: int


def load_raw_data(path: str | Path) -> pd.DataFrame:
    """Load the raw CSV and verify that the expected columns exist."""
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(f"Sales dataset not found: {source}")

    frame = pd.read_csv(source, dtype=str)

    missing = sorted(set(EXPECTED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    return frame[EXPECTED_COLUMNS].copy()


def clean_sales_data(
    raw: pd.DataFrame,
) -> tuple[pd.DataFrame, CleaningReport]:
    """
    Clean sales records using explicit, auditable rules.

    Text fields are stripped, dates and numeric columns are converted safely,
    product metadata repairs missing categories, and exact duplicate order
    records are removed using order_id.
    """
    frame = raw.copy()
    input_rows = len(frame)

    text_columns = [
        "order_id",
        "product",
        "category",
        "region",
        "salesperson",
        "city",
        "channel",
    ]

    for column in text_columns:
        frame[column] = frame[column].astype("string").str.strip()

    frame["order_date"] = pd.to_datetime(
        frame["order_date"],
        errors="coerce",
        format="mixed",
    )

    for column in ["quantity", "unit_price", "discount_rate"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    missing_categories_before = frame["category"].isna().sum()
    frame["category"] = frame["category"].fillna(frame["product"].map(PRODUCT_CATEGORY))
    missing_categories_repaired = int(
        missing_categories_before - frame["category"].isna().sum()
    )

    missing_quantities_before = frame["quantity"].isna().sum()
    product_quantity_median = frame.groupby("product")["quantity"].transform("median")
    frame["quantity"] = frame["quantity"].fillna(product_quantity_median)
    frame["quantity"] = frame["quantity"].fillna(frame["quantity"].median())
    missing_quantities_repaired = int(
        missing_quantities_before - frame["quantity"].isna().sum()
    )

    invalid_prices_before = frame["unit_price"].isna().sum()
    product_price_median = frame.groupby("product")["unit_price"].transform("median")
    frame["unit_price"] = frame["unit_price"].fillna(product_price_median)
    frame["unit_price"] = frame["unit_price"].fillna(frame["unit_price"].median())
    invalid_prices_repaired = int(
        invalid_prices_before - frame["unit_price"].isna().sum()
    )

    missing_discounts_before = frame["discount_rate"].isna().sum()
    frame["discount_rate"] = frame["discount_rate"].fillna(0)
    missing_discounts_repaired = int(
        missing_discounts_before - frame["discount_rate"].isna().sum()
    )

    frame = frame.dropna(subset=["order_id", "order_date", "product"])
    frame = frame.drop_duplicates(subset=["order_id"], keep="first")

    frame["quantity"] = frame["quantity"].clip(lower=0)
    frame["unit_price"] = frame["unit_price"].clip(lower=0)
    frame["discount_rate"] = frame["discount_rate"].clip(lower=0, upper=1)

    frame["gross_sales"] = frame["quantity"] * frame["unit_price"]
    frame["discount_amount"] = frame["gross_sales"] * frame["discount_rate"]
    frame["net_sales"] = frame["gross_sales"] - frame["discount_amount"]
    frame["month"] = frame["order_date"].dt.to_period("M").astype(str)
    frame["quarter"] = frame["order_date"].dt.to_period("Q").astype(str)

    frame = frame.sort_values(["order_date", "order_id"]).reset_index(drop=True)

    report = CleaningReport(
        input_rows=input_rows,
        output_rows=len(frame),
        duplicate_rows_removed=input_rows - len(frame),
        missing_categories_repaired=missing_categories_repaired,
        missing_quantities_repaired=missing_quantities_repaired,
        invalid_prices_repaired=invalid_prices_repaired,
        missing_discounts_repaired=missing_discounts_repaired,
    )

    LOGGER.info(
        "Cleaned %d rows into %d rows; removed %d duplicates.",
        report.input_rows,
        report.output_rows,
        report.duplicate_rows_removed,
    )

    return frame, report


def calculate_kpis(clean: pd.DataFrame) -> pd.DataFrame:
    """Return business KPIs as a two-column table suitable for Excel."""
    orders = clean["order_id"].nunique()
    units = clean["quantity"].sum()
    net_sales = clean["net_sales"].sum()
    gross_sales = clean["gross_sales"].sum()
    discounts = clean["discount_amount"].sum()

    metrics = [
        ("Total Orders", orders),
        ("Units Sold", units),
        ("Gross Sales", gross_sales),
        ("Discount Amount", discounts),
        ("Net Sales", net_sales),
        ("Average Order Value", net_sales / orders if orders else 0),
        (
            "Average Selling Price",
            net_sales / units if units else 0,
        ),
        (
            "Discount Rate",
            discounts / gross_sales if gross_sales else 0,
        ),
    ]

    return pd.DataFrame(metrics, columns=["KPI", "Value"])


def create_pivots(clean: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create Excel-ready pivot-style aggregations."""
    by_region = (
        clean.groupby("region", as_index=False)
        .agg(
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum"),
            Gross_Sales=("gross_sales", "sum"),
            Discounts=("discount_amount", "sum"),
            Net_Sales=("net_sales", "sum"),
        )
        .sort_values("Net_Sales", ascending=False)
    )

    by_category = (
        clean.groupby("category", as_index=False)
        .agg(
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum"),
            Net_Sales=("net_sales", "sum"),
            Average_Order_Value=("net_sales", lambda values: values.sum() / values.count()),
        )
        .sort_values("Net_Sales", ascending=False)
    )

    by_product = (
        clean.groupby(["product", "category"], as_index=False)
        .agg(
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum"),
            Gross_Sales=("gross_sales", "sum"),
            Discounts=("discount_amount", "sum"),
            Net_Sales=("net_sales", "sum"),
        )
        .sort_values("Net_Sales", ascending=False)
    )

    by_channel = (
        clean.groupby("channel", as_index=False)
        .agg(
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum"),
            Net_Sales=("net_sales", "sum"),
        )
        .sort_values("Net_Sales", ascending=False)
    )

    by_month = (
        clean.groupby("month", as_index=False)
        .agg(
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum"),
            Net_Sales=("net_sales", "sum"),
        )
        .sort_values("month")
    )

    by_salesperson = (
        clean.groupby("salesperson", as_index=False)
        .agg(
            Orders=("order_id", "nunique"),
            Units=("quantity", "sum"),
            Net_Sales=("net_sales", "sum"),
        )
        .sort_values("Net_Sales", ascending=False)
    )

    region_category = pd.pivot_table(
        clean,
        index="region",
        columns="category",
        values="net_sales",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    return {
        "By Region": by_region,
        "By Category": by_category,
        "By Product": by_product,
        "By Channel": by_channel,
        "By Month": by_month,
        "By Salesperson": by_salesperson,
        "Region Category": region_category,
    }


def create_business_recommendations(
    clean: pd.DataFrame,
    pivots: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Create evidence-based business observations from the cleaned data."""
    region = pivots["By Region"]
    category = pivots["By Category"]
    product = pivots["By Product"]
    channel = pivots["By Channel"]

    top_region = region.iloc[0]
    top_category = category.iloc[0]
    top_product = product.iloc[0]
    top_channel = channel.iloc[0]

    high_discount = clean.loc[clean["discount_rate"] >= 0.15]
    regular = clean.loc[clean["discount_rate"] < 0.15]

    high_discount_aov = (
        high_discount["net_sales"].sum() / high_discount["order_id"].nunique()
        if high_discount["order_id"].nunique()
        else 0
    )
    regular_aov = (
        regular["net_sales"].sum() / regular["order_id"].nunique()
        if regular["order_id"].nunique()
        else 0
    )

    recommendations = [
        {
            "Area": "Regional focus",
            "Observation": (
                f"{top_region['region']} has the highest net sales at "
                f"{top_region['Net_Sales']:.2f}."
            ),
            "Action": (
                "Review the product, customer, and channel mix in this region "
                "and use the findings to define repeatable sales practices."
            ),
            "Evidence": f"Net sales: {top_region['Net_Sales']:.2f}",
        },
        {
            "Area": "Category focus",
            "Observation": (
                f"{top_category['category']} generates the highest net sales "
                f"at {top_category['Net_Sales']:.2f}."
            ),
            "Action": (
                "Track inventory availability and conversion for this category "
                "because changes in its sales mix can materially affect total revenue."
            ),
            "Evidence": f"Net sales: {top_category['Net_Sales']:.2f}",
        },
        {
            "Area": "Product focus",
            "Observation": (
                f"{top_product['product']} is the highest-net-sales product at "
                f"{top_product['Net_Sales']:.2f}."
            ),
            "Action": (
                "Monitor its demand, stock availability, and discounting separately "
                "from lower-volume products."
            ),
            "Evidence": f"Units sold: {top_product['Units']:.0f}",
        },
        {
            "Area": "Channel mix",
            "Observation": (
                f"{top_channel['channel']} contributes the most net sales at "
                f"{top_channel['Net_Sales']:.2f}."
            ),
            "Action": (
                "Compare customer acquisition, order frequency, and discount behavior "
                "across channels before reallocating sales effort."
            ),
            "Evidence": f"Orders: {top_channel['Orders']}",
        },
        {
            "Area": "Discount monitoring",
            "Observation": (
                f"Orders with discounts of 15% or more have an average order value "
                f"of {high_discount_aov:.2f}, compared with {regular_aov:.2f} "
                "for orders below 15%."
            ),
            "Action": (
                "Evaluate discounts against incremental units and revenue rather than "
                "using a discount percentage alone as a performance measure."
            ),
            "Evidence": (
                f"High-discount AOV: {high_discount_aov:.2f}; "
                f"regular AOV: {regular_aov:.2f}"
            ),
        },
    ]

    return pd.DataFrame(recommendations)


def run_analysis(data_path: str | Path) -> dict[str, object]:
    """Run the complete cleaning and analytical pipeline."""
    raw = load_raw_data(data_path)
    clean, cleaning_report = clean_sales_data(raw)
    pivots = create_pivots(clean)
    kpis = calculate_kpis(clean)
    recommendations = create_business_recommendations(clean, pivots)

    return {
        "raw": raw,
        "clean": clean,
        "cleaning_report": cleaning_report,
        "kpis": kpis,
        "pivots": pivots,
        "recommendations": recommendations,
    }
