from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import pandas as pd


@dataclass(frozen=True)
class CombineResult:
    name: str
    frame: pd.DataFrame


def build_data() -> dict[str, pd.DataFrame]:
    customers = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "customer_name": ["Atul", "Priya", "Rahul", "Neha"],
            "region": ["North", "South", "North", "West"],
        }
    )

    orders = pd.DataFrame(
        {
            "order_id": [101, 102, 103, 104, 105],
            "customer_id": [1, 2, 2, 5, 3],
            "amount": [1200.0, 850.0, 450.0, 700.0, 1500.0],
            "status": ["paid", "paid", "pending", "paid", "paid"],
        }
    )

    contacts = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "email": [
                "atul@example.com",
                "priya@example.com",
                "rahul@example.com",
                "neha@example.com",
            ],
        }
    )

    january = pd.DataFrame(
        {
            "order_id": [101, 102],
            "month": ["2026-01", "2026-01"],
            "amount": [1200.0, 850.0],
        }
    )

    february = pd.DataFrame(
        {
            "order_id": [103, 104, 105],
            "month": ["2026-02", "2026-02", "2026-02"],
            "amount": [450.0, 700.0, 1500.0],
        }
    )

    return {
        "customers": customers,
        "orders": orders,
        "contacts": contacts,
        "january": january,
        "february": february,
    }


def require_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
    frame_name: str,
) -> None:
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(
            f"{frame_name} is missing required columns: {sorted(missing)}"
        )


def safe_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: str,
    how: str = "inner",
    validate: str | None = None,
) -> pd.DataFrame:
    require_columns(left, [on], "left DataFrame")
    require_columns(right, [on], "right DataFrame")

    if left[on].isna().any() or right[on].isna().any():
        raise ValueError(f"Join key '{on}' contains missing values.")

    return left.merge(
        right,
        on=on,
        how=how,
        validate=validate,
        indicator=True,
    )


def demonstrate_merge(data: dict[str, pd.DataFrame]) -> CombineResult:
    result = safe_merge(
        data["customers"],
        data["orders"],
        on="customer_id",
        how="left",
        validate="one_to_many",
    )

    return CombineResult("merge_left_one_to_many", result)


def demonstrate_join(data: dict[str, pd.DataFrame]) -> CombineResult:
    customers = data["customers"].set_index("customer_id")
    contacts = data["contacts"].set_index("customer_id")

    result = customers.join(
        contacts,
        how="left",
        validate="one_to_one",
    )

    return CombineResult("index_based_join", result.reset_index())


def demonstrate_concat(data: dict[str, pd.DataFrame]) -> CombineResult:
    result = pd.concat(
        [data["january"], data["february"]],
        axis=0,
        ignore_index=True,
        verify_integrity=True,
    )

    return CombineResult("row_concat", result)


def demonstrate_append_alternative(data: dict[str, pd.DataFrame]) -> CombineResult:
    # DataFrame.append() was removed from modern pandas.
    # pd.concat() is the direct replacement for adding rows.
    historical = pd.DataFrame(
        {
            "order_id": [100],
            "month": ["2025-12"],
            "amount": [975.0],
        }
    )

    result = pd.concat(
        [historical, data["january"]],
        ignore_index=True,
    )

    return CombineResult("append_alternative", result)


def demonstrate_relational_operations(
    data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    customers = data["customers"]
    orders = data["orders"]

    matched = customers.merge(
        orders,
        on="customer_id",
        how="inner",
        validate="one_to_many",
    )

    unmatched_customers = customers[
        ~customers["customer_id"].isin(orders["customer_id"])
    ].copy()

    unmatched_orders = orders[
        ~orders["customer_id"].isin(customers["customer_id"])
    ].copy()

    customer_totals = (
        matched.groupby(
            ["customer_id", "customer_name"],
            as_index=False,
        )["amount"]
        .sum()
        .rename(columns={"amount": "total_order_amount"})
    )

    customer_totals["segment"] = customer_totals[
        "total_order_amount"
    ].map(lambda value: "high" if value >= 1500 else "standard")

    return {
        "matched": matched,
        "unmatched_customers": unmatched_customers,
        "unmatched_orders": unmatched_orders,
        "customer_totals": customer_totals,
    }


def demonstrate_column_collision(data: dict[str, pd.DataFrame]) -> CombineResult:
    customer_flags = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "status": ["active", "active", "inactive"],
        }
    )

    orders = data["orders"]

    result = orders.merge(
        customer_flags,
        on="customer_id",
        how="left",
        suffixes=("_order", "_customer"),
        validate="many_to_one",
    )

    return CombineResult("collision_safe_merge", result)


def demonstrate_validation_failure(data: dict[str, pd.DataFrame]) -> str:
    duplicate_contacts = pd.DataFrame(
        {
            "customer_id": [1, 1, 2],
            "email": [
                "first@example.com",
                "second@example.com",
                "priya@example.com",
            ],
        }
    )

    try:
        data["customers"].merge(
            duplicate_contacts,
            on="customer_id",
            how="left",
            validate="one_to_one",
        )
    except pd.errors.MergeError as exc:
        return f"Expected validation failure: {exc}"

    return "Unexpectedly passed one-to-one validation."


def demonstrate_outer_merge(data: dict[str, pd.DataFrame]) -> CombineResult:
    result = data["customers"].merge(
        data["orders"],
        on="customer_id",
        how="outer",
        indicator=True,
        suffixes=("_customer", "_order"),
    )

    return CombineResult("outer_relational_merge", result)


def print_result(result: CombineResult) -> None:
    print(f"\n=== {result.name} ===")
    print(result.frame.to_string(index=False))


def main() -> None:
    data = build_data()

    for operation in (
        demonstrate_merge,
        demonstrate_join,
        demonstrate_concat,
        demonstrate_append_alternative,
        demonstrate_column_collision,
        demonstrate_outer_merge,
    ):
        print_result(operation(data))

    print("\n=== Relational operations ===")
    for name, frame in demonstrate_relational_operations(data).items():
        print(f"\n{name}")
        print(frame.to_string(index=False))

    print("\n=== Validation ===")
    print(demonstrate_validation_failure(data))

    print("\n=== Assertions ===")
    merged = data["customers"].merge(
        data["orders"],
        on="customer_id",
        how="left",
        validate="one_to_many",
    )

    assert len(merged) == len(data["orders"]) + 2
    assert set(data["customers"]["customer_id"]) == {1, 2, 3, 4}
    assert set(data["orders"]["customer_id"]) - set(
        data["customers"]["customer_id"]
    ) == {5}

    print("All validation assertions passed.")


if __name__ == "__main__":
    main()
