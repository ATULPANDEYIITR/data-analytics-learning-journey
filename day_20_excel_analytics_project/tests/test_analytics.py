from pathlib import Path

import pandas as pd

from analytics import (
    calculate_kpis,
    clean_sales_data,
    create_business_recommendations,
    create_pivots,
    load_raw_data,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw_sales.csv"


def test_raw_dataset_has_expected_columns():
    frame = load_raw_data(DATA_PATH)

    assert list(frame.columns) == [
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


def test_cleaning_removes_duplicate_order():
    raw = load_raw_data(DATA_PATH)
    clean, report = clean_sales_data(raw)

    assert report.duplicate_rows_removed == 1
    assert clean["order_id"].is_unique


def test_cleaning_repairs_missing_category():
    raw = load_raw_data(DATA_PATH)
    clean, report = clean_sales_data(raw)

    assert report.missing_categories_repaired == 1
    assert clean.loc[clean["product"] == "Desk Lamp", "category"].notna().all()


def test_cleaning_repairs_invalid_price():
    raw = load_raw_data(DATA_PATH)
    clean, report = clean_sales_data(raw)

    assert report.invalid_prices_repaired == 1
    assert clean["unit_price"].notna().all()


def test_cleaning_repairs_missing_discount():
    raw = load_raw_data(DATA_PATH)
    clean, report = clean_sales_data(raw)

    assert report.missing_discounts_repaired == 1
    assert clean["discount_rate"].notna().all()


def test_derived_sales_columns_are_consistent():
    raw = load_raw_data(DATA_PATH)
    clean, _ = clean_sales_data(raw)

    expected_gross = clean["quantity"] * clean["unit_price"]
    expected_discount = expected_gross * clean["discount_rate"]
    expected_net = expected_gross - expected_discount

    pd.testing.assert_series_equal(
        clean["gross_sales"],
        expected_gross,
        check_names=False,
    )
    pd.testing.assert_series_equal(
        clean["discount_amount"],
        expected_discount,
        check_names=False,
    )
    pd.testing.assert_series_equal(
        clean["net_sales"],
        expected_net,
        check_names=False,
    )


def test_kpis_contain_required_business_metrics():
    raw = load_raw_data(DATA_PATH)
    clean, _ = clean_sales_data(raw)
    kpis = calculate_kpis(clean)

    required = {
        "Total Orders",
        "Units Sold",
        "Gross Sales",
        "Discount Amount",
        "Net Sales",
        "Average Order Value",
        "Average Selling Price",
        "Discount Rate",
    }

    assert required.issubset(set(kpis["KPI"]))


def test_pivot_outputs_are_non_empty():
    raw = load_raw_data(DATA_PATH)
    clean, _ = clean_sales_data(raw)
    pivots = create_pivots(clean)

    expected = {
        "By Region",
        "By Category",
        "By Product",
        "By Channel",
        "By Month",
        "By Salesperson",
        "Region Category",
    }

    assert expected == set(pivots)
    assert all(not frame.empty for frame in pivots.values())


def test_recommendations_are_generated():
    raw = load_raw_data(DATA_PATH)
    clean, _ = clean_sales_data(raw)
    pivots = create_pivots(clean)
    recommendations = create_business_recommendations(clean, pivots)

    assert len(recommendations) >= 4
    assert {"Area", "Observation", "Action", "Evidence"} == set(
        recommendations.columns
    )
