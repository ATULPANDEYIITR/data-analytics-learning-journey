import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory


def build_series():
    sales = pd.Series(
        [12500, 18400, 9800, 22100],
        index=["North", "South", "East", "West"],
        name="sales",
        dtype="float64",
    )

    print("Series:")
    print(sales)
    print("\nSouth:", sales.loc["South"])
    print("First two:", sales.iloc[:2])

    return sales


def build_dataframe():
    data = {
        "employee": ["Asha", "Ravi", "Meera", "John", "Fatima"],
        "department": ["Engineering", "Sales", "Engineering", "Sales", "Finance"],
        "salary": [95000, 72000, 105000, 68000, 88000],
        "performance": [4.5, 3.8, 4.8, 3.2, 4.1],
        "active": [True, True, True, False, True],
    }

    df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("The DataFrame cannot be empty.")

    required = {"employee", "department", "salary", "performance", "active"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df["salary"].isna().any() or (df["salary"] < 0).any():
        raise ValueError("Salary must contain non-negative values.")

    if not df["performance"].between(0, 5).all():
        raise ValueError("Performance must be between 0 and 5.")

    return df


def demonstrate_selection(df):
    print("\nComplete DataFrame:")
    print(df)

    print("\nSingle column:")
    print(df["employee"])

    print("\nMultiple columns:")
    print(df[["employee", "salary", "department"]])

    print("\nFirst three rows with iloc:")
    print(df.iloc[:3])

    print("\nRows by labels with loc:")
    print(df.loc[1:3, ["employee", "salary"]])


def demonstrate_filtering(df):
    high_performers = df[df["performance"] >= 4.0]
    engineering = df[df["department"].eq("Engineering")]
    active_high_paid = df[(df["active"]) & (df["salary"] >= 90000)]

    print("\nHigh performers:")
    print(high_performers)

    print("\nEngineering employees:")
    print(engineering)

    print("\nActive employees earning at least 90,000:")
    print(active_high_paid)

    selected = df.loc[
        (df["department"].isin(["Engineering", "Finance"]))
        & (df["performance"] >= 4.0),
        ["employee", "department", "performance"],
    ]

    print("\nCombined filter:")
    print(selected)


def demonstrate_missing_values():
    df = pd.DataFrame(
        {
            "employee": ["Asha", "Ravi", "Meera", "John"],
            "salary": [95000, None, 105000, 68000],
            "performance": [4.5, 3.8, None, 3.2],
        }
    )

    print("\nMissing-value detection:")
    print(df.isna())

    cleaned = df.copy()
    cleaned["salary"] = cleaned["salary"].fillna(cleaned["salary"].median())
    cleaned["performance"] = cleaned["performance"].fillna(0)

    print("\nAfter controlled filling:")
    print(cleaned)


def demonstrate_transformation_and_grouping(df):
    working = df.copy()

    working["bonus"] = working["salary"] * working["performance"] / 100
    working["total_compensation"] = working["salary"] + working["bonus"]

    department_summary = (
        working.groupby("department", as_index=False)
        .agg(
            employees=("employee", "count"),
            average_salary=("salary", "mean"),
            average_performance=("performance", "mean"),
            total_compensation=("total_compensation", "sum"),
        )
        .sort_values("average_salary", ascending=False)
    )

    print("\nDerived columns:")
    print(working[["employee", "salary", "bonus", "total_compensation"]])

    print("\nDepartment summary:")
    print(department_summary)


def demonstrate_indexing(df):
    indexed = df.set_index("employee")

    print("\nEmployee index:")
    print(indexed)

    print("\nOne employee:")
    print(indexed.loc["Meera"])

    print("\nEmployees ordered by salary:")
    print(indexed.sort_values("salary", ascending=False))

    restored = indexed.reset_index()

    if not restored.equals(df.reset_index(drop=True)):
        raise RuntimeError("Index restoration produced unexpected data.")

    print("\nIndex restored successfully.")


def demonstrate_file_round_trip(df):
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "employees.csv"

        df.to_csv(path, index=False)
        loaded = pd.read_csv(path)

        if list(loaded.columns) != list(df.columns):
            raise RuntimeError("CSV round-trip changed the schema.")

        print("\nCSV round-trip:")
        print(loaded)


def demonstrate_query(df):
    result = df.query(
        "active == True and salary >= 80000 and performance >= 4"
    )

    print("\nQuery result:")
    print(result)


def main():
    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 20)

    build_series()

    employees = build_dataframe()

    demonstrate_selection(employees)
    demonstrate_filtering(employees)
    demonstrate_missing_values()
    demonstrate_transformation_and_grouping(employees)
    demonstrate_indexing(employees)
    demonstrate_file_round_trip(employees)
    demonstrate_query(employees)

    print("\nPerformance note:")
    print(
        "Prefer vectorized Pandas operations such as boolean masks, "
        "assignments, and groupby over Python row-by-row loops."
    )

    print("\nSecurity note:")
    print(
        "Validate imported data before calculations, especially when "
        "CSV or other external files are used as input."
    )


if __name__ == "__main__":
    main()
