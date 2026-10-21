import pandas as pd
from io import StringIO


def build_dataset() -> pd.DataFrame:
    csv_data = """customer_id,name,age,email,city,segment,signup_date,orders
101, Alice  Sharma ,29, ALICE.SHARMA@EXAMPLE.COM ,Lucknow,Premium,2026-01-15,12
102,Bob Khan,,bob.khan@example.com,Delhi,Standard,2026/02/20,5
103,Charlie  Rao,34,,Mumbai,Premium,2026-03-10,8
104,Alice  Sharma,29,alice.sharma@example.com,Lucknow,Premium,2026-01-15,12
105,David Mehta,unknown,david.mehta@example.com,Delhi,standard,2026-04-05,3
106,Esha Patel,41,esha.patel@example.com, ,Enterprise,2026-05-11,21
107,Farhan Ali,37,farhan.ali@example.com,Bengaluru,Standard,invalid,7
108,,26,neha@example.com,Pune,Standard,2026-06-30,2
109,George Sen,-5,george.sen@example.com,Chennai,Premium,2026-07-01,15
110,Hina Roy,30,hina.roy@example.com,Kolkata,premium,2026-07-18,10
"""
    return pd.read_csv(StringIO(csv_data))


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    string_columns = ["name", "email", "city", "segment"]

    for column in string_columns:
        result[column] = (
            result[column]
            .astype("string")
            .str.strip()
            .replace({"": pd.NA, "unknown": pd.NA, "UNKNOWN": pd.NA})
        )

    result["name"] = (
        result["name"]
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    result["email"] = result["email"].str.lower()

    result["city"] = result["city"].str.title()

    result["segment"] = result["segment"].str.title()

    return result


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # Invalid numeric values become missing instead of silently remaining strings.
    result["age"] = pd.to_numeric(result["age"], errors="coerce")
    result["orders"] = pd.to_numeric(result["orders"], errors="coerce")

    # Invalid dates become NaT and can be handled by a separate validation rule.
    result["signup_date"] = pd.to_datetime(
        result["signup_date"],
        errors="coerce"
    )

    result["customer_id"] = pd.to_numeric(
        result["customer_id"],
        errors="raise"
    ).astype("Int64")

    result["age"] = result["age"].astype("Int64")
    result["orders"] = result["orders"].astype("Int64")

    return result


def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # An age outside a realistic customer range is treated as invalid.
    result.loc[
        ~result["age"].between(18, 100, inclusive="both"),
        "age"
    ] = pd.NA

    result.loc[
        result["orders"].lt(0),
        "orders"
    ] = pd.NA

    return result


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # Numeric imputation uses the median because it is less affected by outliers.
    median_age = result["age"].median()
    median_orders = result["orders"].median()

    result["age"] = result["age"].fillna(round(median_age)).astype("Int64")
    result["orders"] = result["orders"].fillna(round(median_orders)).astype("Int64")

    result["name"] = result["name"].fillna("Unknown Customer")
    result["city"] = result["city"].fillna("Unknown")
    result["segment"] = result["segment"].fillna("Standard")

    # Missing email is intentionally retained because fabricating an email
    # address would create incorrect customer identity data.
    return result


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # customer_id is the business key. Keep the first occurrence.
    result = result.drop_duplicates(
        subset=["customer_id"],
        keep="first"
    )

    # A normalized email is also useful for detecting duplicate identities.
    result = result.drop_duplicates(
        subset=["email"],
        keep="first",
        ignore_index=True
    )

    return result


def add_categorical_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    segment_categories = [
        "Standard",
        "Premium",
        "Enterprise"
    ]

    result["segment"] = pd.Categorical(
        result["segment"],
        categories=segment_categories,
        ordered=False
    )

    return result


def clean_customer_data(df: pd.DataFrame) -> pd.DataFrame:
    result = clean_strings(df)
    result = convert_types(result)
    result = validate_ranges(result)
    result = remove_duplicates(result)
    result = fill_missing_values(result)
    result = add_categorical_data(result)

    return result


def quality_report(raw: pd.DataFrame, clean: pd.DataFrame) -> None:
    print("RAW DATA")
    print(raw.to_string(index=False))

    print("\nCLEAN DATA")
    print(clean.to_string(index=False))

    print("\nDATA TYPES")
    print(clean.dtypes)

    print("\nMISSING VALUES AFTER CLEANING")
    print(clean.isna().sum())

    print("\nSEGMENT DISTRIBUTION")
    print(clean["segment"].value_counts(dropna=False))

    print("\nDUPLICATE CUSTOMER IDS")
    duplicate_ids = clean[
        clean["customer_id"].duplicated(keep=False)
    ]
    print(duplicate_ids.to_string(index=False))

    print("\nQUALITY METRICS")
    print(f"Raw rows: {len(raw)}")
    print(f"Clean rows: {len(clean)}")
    print(f"Rows removed: {len(raw) - len(clean)}")
    print(f"Missing emails retained: {clean['email'].isna().sum()}")


def demonstrate_export(df: pd.DataFrame) -> None:
    # A buffer demonstrates CSV output without requiring filesystem permissions.
    output = df.to_csv(index=False)
    print("\nCSV OUTPUT PREVIEW")
    print(output)


def main() -> None:
    raw = build_dataset()
    cleaned = clean_customer_data(raw)

    quality_report(raw, cleaned)
    demonstrate_export(cleaned)


if __name__ == "__main__":
    main()
