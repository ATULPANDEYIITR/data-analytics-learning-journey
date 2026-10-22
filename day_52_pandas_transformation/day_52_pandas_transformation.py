import pandas as pd
import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory


def validate_orders(df: pd.DataFrame) -> None:
    required = {"order_id", "customer", "region", "product", "quantity", "unit_price", "status"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df["order_id"].duplicated().any():
        raise ValueError("order_id values must be unique")

    if (df["quantity"] <= 0).any():
        raise ValueError("quantity must be positive")

    if (df["unit_price"] < 0).any():
        raise ValueError("unit_price cannot be negative")


def build_orders() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1001, "Asha", "North", "Laptop", 2, 75000, "completed"],
            [1002, "Ravi", "South", "Monitor", 3, 18000, "completed"],
            [1003, "Meera", "West", "Keyboard", 5, 3500, "pending"],
            [1004, "Kabir", "East", "Laptop", 1, 82000, "cancelled"],
            [1005, "Asha", "North", "Mouse", 4, 1500, "completed"],
            [1006, "Ravi", "South", "Laptop", 2, 78000, "completed"],
            [1007, "Meera", "West", "Monitor", 2, 19500, "pending"],
        ],
        columns=[
            "order_id",
            "customer",
            "region",
            "product",
            "quantity",
            "unit_price",
            "status",
        ],
    )


def main() -> None:
    orders = build_orders()
    validate_orders(orders)

    # Vectorized arithmetic operates on the entire Series without Python loops.
    orders["gross_value"] = orders["quantity"] * orders["unit_price"]

    # map is appropriate for one-to-one value transformations.
    region_codes = {
        "North": "N",
        "South": "S",
        "East": "E",
        "West": "W",
    }
    orders["region_code"] = orders["region"].map(region_codes)

    # replace is useful when known values must be normalized.
    orders["status"] = orders["status"].replace(
        {
            "completed": "Completed",
            "pending": "Pending",
            "cancelled": "Cancelled",
        }
    )

    # apply is useful when transformation logic depends on multiple fields.
    # It is more flexible than vectorization but generally slower on large data.
    orders["priority"] = orders.apply(
        lambda row: (
            "High"
            if row["gross_value"] >= 100000
            else "Medium"
            if row["gross_value"] >= 30000
            else "Low"
        ),
        axis=1,
    )

    # assign creates derived columns while keeping the transformation chain readable.
    orders = orders.assign(
        discount_rate=lambda df: np.where(
            df["gross_value"] >= 100000,
            0.10,
            np.where(df["gross_value"] >= 50000, 0.05, 0.0),
        ),
        net_value=lambda df: df["gross_value"]
        * (1 - df["discount_rate"]),
    )

    # rename changes selected column names without modifying unrelated columns.
    orders = orders.rename(
        columns={
            "gross_value": "gross_amount",
            "net_value": "net_amount",
        }
    )

    # Filtering uses boolean masks. Parentheses are important when combining conditions.
    active_orders = orders[
        (orders["status"] != "Cancelled")
        & (orders["net_amount"] >= 30000)
    ].copy()

    # Sorting can use different directions for different columns.
    active_orders = active_orders.sort_values(
        by=["priority", "net_amount"],
        ascending=[True, False],
        kind="stable",
    )

    # Vectorized string operations avoid explicit row-by-row loops.
    active_orders["customer_normalized"] = (
        active_orders["customer"].str.strip().str.title()
    )

    # Vectorized conditional replacement handles missing or unexpected mappings safely.
    active_orders["region_code"] = active_orders["region_code"].fillna("UNKNOWN")

    # A second transformation demonstrates a reusable function with Series input.
    def classify_amount(amount: float) -> str:
        if pd.isna(amount):
            return "Unknown"
        if amount >= 100000:
            return "Enterprise"
        if amount >= 50000:
            return "Standard"
        return "Small"

    active_orders["segment"] = active_orders["net_amount"].map(classify_amount)

    # Filtering can be expressed through query when the expression is readable.
    high_value = active_orders.query("net_amount >= 70000")

    # Aggregation after transformation is useful for operational reporting.
    regional_report = (
        orders.loc[orders["status"] == "Completed"]
        .groupby("region", as_index=False)
        .agg(
            completed_orders=("order_id", "count"),
            total_quantity=("quantity", "sum"),
            total_revenue=("net_amount", "sum"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    print("TRANSFORMED ORDERS")
    print(orders.to_string(index=False))

    print("\nFILTERED ACTIVE ORDERS")
    print(active_orders.to_string(index=False))

    print("\nHIGH-VALUE ORDERS")
    print(high_value.to_string(index=False))

    print("\nREGIONAL REPORT")
    print(regional_report.to_string(index=False))

    # File handling demonstrates a safe transformation pipeline around CSV input.
    with TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "orders.csv"
        output_path = Path(temp_dir) / "transformed_orders.csv"

        orders.to_csv(input_path, index=False)

        loaded = pd.read_csv(input_path)
        validate_orders(loaded)

        transformed = loaded.assign(
            gross_amount=loaded["quantity"] * loaded["unit_price"]
        ).sort_values("gross_amount", ascending=False)

        transformed.to_csv(output_path, index=False)

        if not output_path.exists():
            raise IOError("Transformation output was not created")

        print(f"\nCSV transformation written to: {output_path}")

    # Demonstrate an explicit failure rather than silently accepting invalid data.
    invalid = orders.copy()
    invalid.loc[0, "quantity"] = 0

    try:
        validate_orders(invalid)
    except ValueError as exc:
        print(f"\nValidation correctly rejected invalid data: {exc}")


if __name__ == "__main__":
    main()
