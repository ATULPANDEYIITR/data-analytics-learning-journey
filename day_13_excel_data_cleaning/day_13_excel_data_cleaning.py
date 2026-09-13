"""
Excel Data Cleaning: Beginner to Advanced
==========================================

This standalone study script teaches practical Excel data-cleaning concepts by
using Python to create, inspect, validate, standardize, clean, transform, and
export spreadsheet data.

Main topics covered:
- Excel data structure and data-quality concepts
- Missing values
- Duplicate records
- Inconsistent formatting
- Whitespace and hidden characters
- Text normalization
- Text-to-columns
- Data types
- Date and number standardization
- Error handling
- Data validation
- Standardization
- Outlier and range checks
- Rule-based quality checks
- Before/after comparisons
- Audit trails
- Reproducible cleaning pipelines
- Excel workbook generation
- Excel formulas for validation
- Conditional formatting
- Data validation dropdowns
- Sheet protection considerations
- Performance considerations
- Security considerations
- Testing and production practices

Required packages:
    pip install pandas openpyxl

The script creates demonstration Excel workbooks in the current directory.
"""

from __future__ import annotations

import math
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation


# ============================================================================
# 1. BASIC CONCEPTS
# ============================================================================

print("=" * 80)
print("EXCEL DATA CLEANING: BEGINNER TO ADVANCED")
print("=" * 80)

print(
    """
Data cleaning means identifying and correcting or handling problems in a
dataset before the data is analyzed, reported, imported into another system,
or used for decision-making.

A typical Excel table contains:
    Rows    -> records
    Columns -> variables or fields
    Cells   -> individual values

Common data-quality problems include:
    - Duplicate records
    - Blank cells
    - Different spellings of the same value
    - Extra spaces
    - Hidden characters
    - Mixed capitalization
    - Inconsistent date formats
    - Numbers stored as text
    - Invalid categories
    - Incorrect data types
    - Formula errors
    - Invalid ranges
    - Incorrectly split text
"""
)


# ============================================================================
# 2. SAMPLE EXCEL-LIKE DATA
# ============================================================================

print("\n" + "=" * 80)
print("2. CREATING A RAW DATASET")
print("=" * 80)

raw_data = [
    {
        "Customer ID": " C001 ",
        "Full Name": "  Rahul Sharma",
        "Email": "RAHUL.SHARMA@EXAMPLE.COM ",
        "Phone": "98765 43210",
        "City": "lucknow",
        "Department": "Sales",
        "Age": 29,
        "Join Date": "15/01/2025",
        "Salary": "₹55,000",
        "Status": " active ",
        "Notes": "Preferred customer",
    },
    {
        "Customer ID": "C002",
        "Full Name": "Priya Singh",
        "Email": "priya.singh@example.com",
        "Phone": "9876543211",
        "City": "Lucknow ",
        "Department": "sales",
        "Age": 31,
        "Join Date": "2025-02-20",
        "Salary": "62000",
        "Status": "Active",
        "Notes": "",
    },
    {
        "Customer ID": "C003",
        "Full Name": "Amit Verma",
        "Email": "amit.verma@example.com",
        "Phone": "98765-43212",
        "City": "Kanpur",
        "Department": "FINANCE",
        "Age": None,
        "Join Date": "03/03/2025",
        "Salary": "₹70,000",
        "Status": "active",
        "Notes": None,
    },
    {
        "Customer ID": "C003",
        "Full Name": "Amit Verma",
        "Email": "amit.verma@example.com",
        "Phone": "98765-43212",
        "City": "Kanpur",
        "Department": "Finance",
        "Age": None,
        "Join Date": "03/03/2025",
        "Salary": "₹70,000",
        "Status": "active",
        "Notes": None,
    },
    {
        "Customer ID": "C004",
        "Full Name": "  Neha  Gupta ",
        "Email": "neha.gupta@example.com",
        "Phone": "9876543214",
        "City": "NEW DELHI",
        "Department": "Human Resources",
        "Age": 42,
        "Join Date": "April 8, 2025",
        "Salary": "₹ 85,500",
        "Status": "ACTIVE",
        "Notes": "Needs review",
    },
    {
        "Customer ID": "C005",
        "Full Name": "Ravi Kumar",
        "Email": "ravi.kumar@example.com",
        "Phone": "9876543215",
        "City": "Delhi",
        "Department": "HR",
        "Age": 150,
        "Join Date": "not available",
        "Salary": "unknown",
        "Status": "Pending",
        "Notes": "Invalid age",
    },
    {
        "Customer ID": "C006",
        "Full Name": "Sonal Mehta",
        "Email": "sonal.mehta@example.com",
        "Phone": None,
        "City": "Mumbai",
        "Department": "Marketing",
        "Age": 27,
        "Join Date": "2025/05/12",
        "Salary": "₹48,000",
        "Status": "active",
        "Notes": None,
    },
    {
        "Customer ID": "C007",
        "Full Name": "Arjun Patel",
        "Email": " arjun.patel@example.com",
        "Phone": "9876543217",
        "City": "mumbai",
        "Department": "Marketing ",
        "Age": 35,
        "Join Date": "12-06-2025",
        "Salary": "75000",
        "Status": "Inactive",
        "Notes": "Follow up",
    },
    {
        "Customer ID": "C008",
        "Full Name": "Kiran Joshi",
        "Email": "kiran.joshi@example.com",
        "Phone": "9876543218",
        "City": "Jaipur",
        "Department": "Operations",
        "Age": 38,
        "Join Date": "2025-07-18",
        "Salary": "₹66,000",
        "Status": "active",
        "Notes": None,
    },
    {
        "Customer ID": "C009",
        "Full Name": "Maya Rao",
        "Email": "maya.rao@example.com",
        "Phone": "9876543219",
        "City": "Bengaluru",
        "Department": "Operations",
        "Age": 33,
        "Join Date": "18/08/2025",
        "Salary": "₹72,000",
        "Status": "ACTIVE",
        "Notes": "",
    },
    {
        "Customer ID": "C010",
        "Full Name": "Dev Malhotra",
        "Email": "dev.malhotra@example.com",
        "Phone": "9876543220",
        "City": "Hyderabad",
        "Department": "IT",
        "Age": 41,
        "Join Date": "2025-09-21",
        "Salary": "₹95,000",
        "Status": "active",
        "Notes": "Good standing",
    },
]

raw_df = pd.DataFrame(raw_data)

print("\nRaw dataset:")
print(raw_df.to_string(index=False))

print("\nShape:", raw_df.shape)
print("Rows:", len(raw_df))
print("Columns:", len(raw_df.columns))


# ============================================================================
# 3. UNDERSTANDING DATA TYPES
# ============================================================================

print("\n" + "=" * 80)
print("3. INSPECTING DATA TYPES")
print("=" * 80)

print(raw_df.dtypes)

print(
    """
Important distinction:

A value that looks numeric is not necessarily numeric.

Examples:
    62000       -> numeric
    "62000"     -> text
    "₹62,000"   -> text until currency symbols and separators are handled

Similarly:

    2025-02-20      -> a date
    "2025-02-20"    -> text representation of a date

Data cleaning often starts by converting values into appropriate data types.
"""
)


# ============================================================================
# 4. MISSING VALUES
# ============================================================================

print("\n" + "=" * 80)
print("4. IDENTIFYING MISSING VALUES")
print("=" * 80)

missing_counts = raw_df.isna().sum()
missing_percentages = raw_df.isna().mean().mul(100)

missing_report = pd.DataFrame(
    {
        "Missing Count": missing_counts,
        "Missing Percentage": missing_percentages.round(2),
    }
)

print(missing_report)

print(
    """
Missing data does not automatically mean that the row should be deleted.

Common strategies:

1. Remove:
   Appropriate when the missing field makes the record unusable.

2. Impute:
   Replace missing values with a calculated value such as a median.

3. Use a business-specific value:
   For example, "Unknown" for a non-critical text field.

4. Preserve as blank:
   Appropriate when missingness itself carries meaning.

5. Flag for review:
   Useful when a human needs to verify the record.
"""
)


# ============================================================================
# 5. DIFFERENT TYPES OF "EMPTY" VALUES
# ============================================================================

print("\n" + "=" * 80)
print("5. EMPTY VALUES ARE NOT ALWAYS THE SAME")
print("=" * 80)

empty_examples = pd.DataFrame(
    {
        "Value": [None, "", " ", "N/A", "NA", "null", "-", "Unknown"],
    }
)

print(empty_examples)

print(
    """
In Excel, an apparently empty cell may contain:
    - A true blank
    - An empty string
    - Spaces
    - A formula returning ""
    - A placeholder such as N/A
    - A business-specific missing-value marker

Cleaning requires a defined policy for which values mean "missing".
"""
)


# ============================================================================
# 6. NORMALIZING MISSING VALUES
# ============================================================================

MISSING_MARKERS = {
    "",
    " ",
    "na",
    "n/a",
    "none",
    "null",
    "unknown",
    "-",
    "--",
    "not available",
}


def normalize_missing_value(value: Any) -> Any:
    """Convert common textual missing-value markers to None."""
    if value is None:
        return None

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in MISSING_MARKERS:
            return None

    return value


missing_normalized_df = raw_df.map(normalize_missing_value)

print("\nAfter normalizing missing markers:")
print(missing_normalized_df.to_string(index=False))


# ============================================================================
# 7. DUPLICATES
# ============================================================================

print("\n" + "=" * 80)
print("7. IDENTIFYING DUPLICATES")
print("=" * 80)

duplicate_mask = missing_normalized_df.duplicated(keep=False)

print("Number of duplicated rows:", duplicate_mask.sum())

if duplicate_mask.any():
    print("\nDuplicated records:")
    print(missing_normalized_df.loc[duplicate_mask].to_string(index=False))

print(
    """
Duplicate detection depends on the definition of a duplicate.

Exact duplicate:
    Every relevant field is identical.

Business-key duplicate:
    The same Customer ID or Email appears more than once.

Potential duplicate:
    Names, phone numbers, or other fields are similar but not identical.

Never remove duplicates blindly. First identify the business rule that defines
record uniqueness.
"""
)


# ============================================================================
# 8. REMOVING EXACT DUPLICATES
# ============================================================================

deduplicated_df = missing_normalized_df.drop_duplicates()

print("\nRows before exact deduplication:", len(missing_normalized_df))
print("Rows after exact deduplication:", len(deduplicated_df))


# ============================================================================
# 9. BUSINESS-KEY DUPLICATES
# ============================================================================

print("\n" + "=" * 80)
print("9. DUPLICATES BASED ON A BUSINESS KEY")
print("=" * 80)

duplicate_customer_ids = (
    deduplicated_df["Customer ID"]
    .astype("string")
    .str.strip()
    .value_counts()
)

print(
    duplicate_customer_ids[duplicate_customer_ids > 1]
    if (duplicate_customer_ids > 1).any()
    else "No repeated Customer IDs detected."
)

print(
    """
An exact duplicate and a business-key duplicate are different.

For example, two rows may have the same Customer ID but different phone
numbers. That is not an exact duplicate, but it may indicate conflicting
records that require investigation.
"""
)


# ============================================================================
# 10. WHITESPACE CLEANING
# ============================================================================

print("\n" + "=" * 80)
print("10. REMOVING EXTRA WHITESPACE")
print("=" * 80)


def clean_whitespace(value: Any) -> Any:
    """Normalize repeated whitespace in text while preserving non-text values."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.replace("\u00A0", " ")
        value = value.replace("\t", " ")
        value = value.replace("\n", " ")
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    return value


whitespace_clean_df = deduplicated_df.map(clean_whitespace)

print(whitespace_clean_df[["Customer ID", "Full Name", "Email", "City"]].to_string(index=False))


# ============================================================================
# 11. HIDDEN AND NON-PRINTING CHARACTERS
# ============================================================================

print("\n" + "=" * 80)
print("11. HIDDEN CHARACTER CLEANING")
print("=" * 80)


def remove_control_characters(value: Any) -> Any:
    """Remove Unicode control characters that can interfere with matching."""
    if not isinstance(value, str):
        return value

    cleaned_characters = []

    for character in value:
        category = unicodedata.category(character)
        if category.startswith("C") and character not in ("\n", "\t"):
            continue
        cleaned_characters.append(character)

    return "".join(cleaned_characters)


def normalize_unicode(value: Any) -> Any:
    """Normalize visually equivalent Unicode representations."""
    if not isinstance(value, str):
        return value

    return unicodedata.normalize("NFKC", value)


character_clean_df = whitespace_clean_df.map(remove_control_characters)
character_clean_df = character_clean_df.map(normalize_unicode)


# ============================================================================
# 12. CASE STANDARDIZATION
# ============================================================================

print("\n" + "=" * 80)
print("12. CASE STANDARDIZATION")
print("=" * 80)


def title_case(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().title()
    return value


def lowercase(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def uppercase(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().upper()
    return value


standardized_text_df = character_clean_df.copy()

standardized_text_df["Full Name"] = standardized_text_df["Full Name"].map(title_case)
standardized_text_df["City"] = standardized_text_df["City"].map(title_case)
standardized_text_df["Email"] = standardized_text_df["Email"].map(lowercase)
standardized_text_df["Customer ID"] = standardized_text_df["Customer ID"].map(uppercase)
standardized_text_df["Status"] = standardized_text_df["Status"].map(title_case)

print(standardized_text_df[["Customer ID", "Full Name", "Email", "City", "Status"]].to_string(index=False))


# ============================================================================
# 13. CATEGORY STANDARDIZATION
# ============================================================================

print("\n" + "=" * 80)
print("13. STANDARDIZING CATEGORIES")
print("=" * 80)

department_mapping = {
    "sales": "Sales",
    "finance": "Finance",
    "hr": "Human Resources",
    "human resources": "Human Resources",
    "marketing": "Marketing",
    "operations": "Operations",
    "it": "IT",
}


def standardize_department(value: Any) -> Any:
    if value is None:
        return None

    cleaned = clean_whitespace(value).lower()
    return department_mapping.get(cleaned, title_case(cleaned))


standardized_text_df["Department"] = standardized_text_df["Department"].map(
    standardize_department
)

print(standardized_text_df[["Customer ID", "Department"]].to_string(index=False))


# ============================================================================
# 14. EMAIL STANDARDIZATION AND VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("14. EMAIL CLEANING AND VALIDATION")
print("=" * 80)


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def clean_email(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = clean_whitespace(value)

    if not isinstance(value, str) or not value:
        return None

    return value.lower()


def is_valid_email(value: Any) -> bool:
    if value is None:
        return False

    return bool(EMAIL_PATTERN.fullmatch(str(value)))


standardized_text_df["Email"] = standardized_text_df["Email"].map(clean_email)
standardized_text_df["Valid Email"] = standardized_text_df["Email"].map(is_valid_email)

print(standardized_text_df[["Email", "Valid Email"]].to_string(index=False))


# ============================================================================
# 15. PHONE NUMBER STANDARDIZATION
# ============================================================================

print("\n" + "=" * 80)
print("15. PHONE NUMBER STANDARDIZATION")
print("=" * 80)


def normalize_phone(value: Any) -> Optional[str]:
    if value is None:
        return None

    digits = re.sub(r"\D", "", str(value))

    if not digits:
        return None

    # Demonstration rule for Indian 10-digit mobile numbers.
    if len(digits) == 10:
        return digits

    # Accept a country-code representation.
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]

    return digits


def is_valid_indian_mobile(value: Any) -> bool:
    if value is None:
        return False

    return bool(re.fullmatch(r"[6-9]\d{9}", str(value)))


standardized_text_df["Phone"] = standardized_text_df["Phone"].map(normalize_phone)
standardized_text_df["Valid Phone"] = standardized_text_df["Phone"].map(
    is_valid_indian_mobile
)

print(standardized_text_df[["Phone", "Valid Phone"]].to_string(index=False))


# ============================================================================
# 16. NUMERIC CLEANING
# ============================================================================

print("\n" + "=" * 80)
print("16. CONVERTING CURRENCY TEXT TO NUMBERS")
print("=" * 80)


def parse_currency(value: Any) -> Optional[float]:
    """
    Convert common currency-formatted text into a numeric value.

    Examples:
        "₹55,000" -> 55000.0
        "₹ 85,500" -> 85500.0
        "unknown" -> None
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.replace(" ", "")

    try:
        return float(text)
    except ValueError:
        return None


standardized_text_df["Salary"] = standardized_text_df["Salary"].map(parse_currency)

print(standardized_text_df[["Customer ID", "Salary"]].to_string(index=False))
print("\nSalary dtype:", standardized_text_df["Salary"].dtype)


# ============================================================================
# 17. AGE CONVERSION
# ============================================================================

standardized_text_df["Age"] = pd.to_numeric(
    standardized_text_df["Age"], errors="coerce"
)

print("\nAge values after conversion:")
print(standardized_text_df[["Customer ID", "Age"]].to_string(index=False))


# ============================================================================
# 18. DATE STANDARDIZATION
# ============================================================================

print("\n" + "=" * 80)
print("18. DATE STANDARDIZATION")
print("=" * 80)


def parse_date(value: Any) -> pd.Timestamp:
    if value is None:
        return pd.NaT

    try:
        return pd.to_datetime(value, errors="coerce", dayfirst=True)
    except (TypeError, ValueError):
        return pd.NaT


standardized_text_df["Join Date"] = standardized_text_df["Join Date"].map(parse_date)

print(standardized_text_df[["Customer ID", "Join Date"]].to_string(index=False))


# ============================================================================
# 19. DATE PARSING EDGE CASE
# ============================================================================

ambiguous_dates = pd.Series(
    [
        "01/02/2025",
        "02/01/2025",
        "2025-03-10",
        "March 12, 2025",
        "invalid",
    ]
)

print("\nAmbiguous date examples:")
print(ambiguous_dates)

print(
    """
Date parsing requires care.

For example:
    01/02/2025

could mean:
    1 February 2025
or:
    January 2, 2025

A production cleaning process should know the source system's date convention
rather than guessing.
"""
)


# ============================================================================
# 20. VALID RANGE CHECKS
# ============================================================================

print("\n" + "=" * 80)
print("20. DATA VALIDATION: RANGE RULES")
print("=" * 80)


def validate_age(value: Any) -> bool:
    if pd.isna(value):
        return False

    return 18 <= float(value) <= 100


standardized_text_df["Valid Age"] = standardized_text_df["Age"].map(validate_age)

print(standardized_text_df[["Customer ID", "Age", "Valid Age"]].to_string(index=False))


# ============================================================================
# 21. VALID SALARY CHECK
# ============================================================================


def validate_salary(value: Any) -> bool:
    if pd.isna(value):
        return False

    return float(value) > 0


standardized_text_df["Valid Salary"] = standardized_text_df["Salary"].map(
    validate_salary
)


# ============================================================================
# 22. STATUS VALIDATION
# ============================================================================

allowed_statuses = {"Active", "Inactive", "Pending"}


def validate_status(value: Any) -> bool:
    return value in allowed_statuses


standardized_text_df["Valid Status"] = standardized_text_df["Status"].map(
    validate_status
)

print("\nStatus validation:")
print(
    standardized_text_df[
        ["Customer ID", "Status", "Valid Status"]
    ].to_string(index=False)
)


# ============================================================================
# 23. COMPLETENESS CHECK
# ============================================================================

required_columns = [
    "Customer ID",
    "Full Name",
    "Email",
    "City",
    "Department",
    "Age",
    "Join Date",
    "Salary",
    "Status",
]


def calculate_completeness(row: pd.Series, columns: Sequence[str]) -> float:
    present = 0

    for column in columns:
        value = row[column]

        if pd.notna(value) and str(value).strip() != "":
            present += 1

    return present / len(columns) * 100


standardized_text_df["Completeness %"] = standardized_text_df.apply(
    calculate_completeness,
    axis=1,
    columns=required_columns,
)

print("\nCompleteness:")
print(
    standardized_text_df[["Customer ID", "Completeness %"]].to_string(index=False)
)


# ============================================================================
# 24. COMBINED DATA-QUALITY SCORE
# ============================================================================

print("\n" + "=" * 80)
print("24. DATA-QUALITY SCORING")
print("=" * 80)


def calculate_quality_score(row: pd.Series) -> float:
    checks = [
        bool(row.get("Valid Email", False)),
        bool(row.get("Valid Phone", False)),
        bool(row.get("Valid Age", False)),
        bool(row.get("Valid Salary", False)),
        bool(row.get("Valid Status", False)),
        pd.notna(row.get("Join Date")),
        row.get("Completeness %", 0) >= 90,
    ]

    return round(sum(checks) / len(checks) * 100, 2)


standardized_text_df["Quality Score"] = standardized_text_df.apply(
    calculate_quality_score,
    axis=1,
)

print(
    standardized_text_df[
        ["Customer ID", "Completeness %", "Quality Score"]
    ].to_string(index=False)
)


# ============================================================================
# 25. TEXT-TO-COLUMNS CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("25. TEXT-TO-COLUMNS")
print("=" * 80)

print(
    """
Excel's Text to Columns feature separates one column into multiple columns
using a delimiter or a fixed-width rule.

Typical delimiters:
    comma
    semicolon
    tab
    space
    pipe |

Python equivalent:
    Series.str.split()

Example:
    "Rahul Sharma"
        -> ["Rahul", "Sharma"]

A delimiter-based split should be used only when the delimiter is structurally
reliable.
"""
)

name_parts = standardized_text_df["Full Name"].str.split(" ", n=1, expand=True)

standardized_text_df["First Name"] = name_parts[0]
standardized_text_df["Last Name"] = (
    name_parts[1] if name_parts.shape[1] > 1 else None
)

print(
    standardized_text_df[
        ["Full Name", "First Name", "Last Name"]
    ].to_string(index=False)
)


# ============================================================================
# 26. MORE TEXT-TO-COLUMNS EXAMPLES
# ============================================================================

contact_values = pd.Series(
    [
        "Rahul|Sharma|Sales",
        "Priya|Singh|Finance",
        "Amit|Verma|IT",
    ]
)

split_contacts = contact_values.str.split("|", expand=True)
split_contacts.columns = ["First Name", "Last Name", "Department"]

print("\nDelimiter-based split:")
print(split_contacts.to_string(index=False))


# ============================================================================
# 27. ERROR HANDLING
# ============================================================================

print("\n" + "=" * 80)
print("27. ERROR HANDLING")
print("=" * 80)


def safe_integer_conversion(value: Any) -> Optional[int]:
    """Return an integer or None instead of stopping the entire pipeline."""
    try:
        if value is None:
            return None

        if isinstance(value, float) and math.isnan(value):
            return None

        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


error_examples = ["42", "100", "invalid", "", None, "42.5"]

for example in error_examples:
    print(f"{example!r:>12} -> {safe_integer_conversion(example)!r}")


print(
    """
Good error handling should distinguish:

Expected invalid input:
    Convert to a missing value and record the problem.

Unexpected programming error:
    Raise the exception or log it.

Silent corruption:
    Avoid it. A cleaning process should not quietly turn bad input into
    apparently valid data.
"""
)


# ============================================================================
# 28. DATA-QUALITY ISSUE FLAGS
# ============================================================================

print("\n" + "=" * 80)
print("28. BUILDING EXPLICIT ISSUE FLAGS")
print("=" * 80)


def build_issue_list(row: pd.Series) -> List[str]:
    issues: List[str] = []

    if not row["Valid Email"]:
        issues.append("Invalid email")

    if not row["Valid Phone"]:
        issues.append("Missing or invalid phone")

    if not row["Valid Age"]:
        issues.append("Missing or invalid age")

    if not row["Valid Salary"]:
        issues.append("Missing or invalid salary")

    if not row["Valid Status"]:
        issues.append("Invalid status")

    if pd.isna(row["Join Date"]):
        issues.append("Invalid join date")

    if row["Completeness %"] < 90:
        issues.append("Low completeness")

    return issues


standardized_text_df["Issues"] = standardized_text_df.apply(
    build_issue_list,
    axis=1,
)

standardized_text_df["Needs Review"] = standardized_text_df["Issues"].map(
    lambda issues: len(issues) > 0
)

print(
    standardized_text_df[
        ["Customer ID", "Issues", "Needs Review"]
    ].to_string(index=False)
)


# ============================================================================
# 29. STANDARDIZED CLEAN DATASET
# ============================================================================

print("\n" + "=" * 80)
print("29. FINAL CLEAN DATASET")
print("=" * 80)

clean_columns = [
    "Customer ID",
    "First Name",
    "Last Name",
    "Email",
    "Phone",
    "City",
    "Department",
    "Age",
    "Join Date",
    "Salary",
    "Status",
    "Notes",
]

clean_df = standardized_text_df[clean_columns].copy()

print(clean_df.to_string(index=False))


# ============================================================================
# 30. CLEANING AUDIT REPORT
# ============================================================================

print("\n" + "=" * 80)
print("30. AUDIT REPORT")
print("=" * 80)


@dataclass
class CleaningAudit:
    operation: str
    rows_before: int
    rows_after: int
    changed: int
    description: str


audit_log: List[CleaningAudit] = []

audit_log.append(
    CleaningAudit(
        operation="Exact duplicate removal",
        rows_before=len(raw_df),
        rows_after=len(deduplicated_df),
        changed=len(raw_df) - len(deduplicated_df),
        description="Removed records identical across all columns.",
    )
)

audit_log.append(
    CleaningAudit(
        operation="Text normalization",
        rows_before=len(deduplicated_df),
        rows_after=len(standardized_text_df),
        changed=0,
        description="Trimmed whitespace and standardized selected text fields.",
    )
)

audit_log.append(
    CleaningAudit(
        operation="Numeric conversion",
        rows_before=len(standardized_text_df),
        rows_after=len(standardized_text_df),
        changed=0,
        description="Converted salary and age values to numeric representations.",
    )
)

audit_log.append(
    CleaningAudit(
        operation="Date conversion",
        rows_before=len(standardized_text_df),
        rows_after=len(standardized_text_df),
        changed=0,
        description="Converted recognized date values to datetime values.",
    )
)

audit_df = pd.DataFrame([audit.__dict__ for audit in audit_log])

print(audit_df.to_string(index=False))


# ============================================================================
# 31. BEFORE AND AFTER QUALITY METRICS
# ============================================================================

print("\n" + "=" * 80)
print("31. BEFORE/AFTER QUALITY METRICS")
print("=" * 80)


def dataset_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "Rows": len(df),
        "Columns": len(df.columns),
        "Missing Cells": int(df.isna().sum().sum()),
        "Exact Duplicate Rows": int(df.duplicated().sum()),
    }


before_metrics = dataset_metrics(raw_df)
after_metrics = dataset_metrics(clean_df)

comparison = pd.DataFrame(
    {
        "Metric": list(before_metrics.keys()),
        "Before": list(before_metrics.values()),
        "After": [after_metrics[key] for key in before_metrics],
    }
)

print(comparison.to_string(index=False))


# ============================================================================
# 32. VALIDATION SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("32. VALIDATION SUMMARY")
print("=" * 80)


validation_summary = pd.DataFrame(
    {
        "Rule": [
            "Customer ID present",
            "Email valid",
            "Phone valid",
            "Age valid",
            "Salary valid",
            "Status valid",
            "Join date valid",
        ],
        "Valid Records": [
            standardized_text_df["Customer ID"].notna().sum(),
            standardized_text_df["Valid Email"].sum(),
            standardized_text_df["Valid Phone"].sum(),
            standardized_text_df["Valid Age"].sum(),
            standardized_text_df["Valid Salary"].sum(),
            standardized_text_df["Valid Status"].sum(),
            standardized_text_df["Join Date"].notna().sum(),
        ],
        "Total Records": len(standardized_text_df),
    }
)

validation_summary["Pass %"] = (
    validation_summary["Valid Records"]
    / validation_summary["Total Records"]
    * 100
).round(2)

print(validation_summary.to_string(index=False))


# ============================================================================
# 33. EXCEL WORKBOOK CREATION
# ============================================================================

print("\n" + "=" * 80)
print("33. CREATING AN EXCEL WORKBOOK")
print("=" * 80)


def export_clean_workbook(
    output_path: Path,
    raw_data_frame: pd.DataFrame,
    cleaned_data_frame: pd.DataFrame,
    audit_data_frame: pd.DataFrame,
    validation_data_frame: pd.DataFrame,
) -> None:
    """
    Export raw data, cleaned data, audit information, and validation results
    into a structured Excel workbook.
    """
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        raw_data_frame.to_excel(writer, sheet_name="Raw Data", index=False)
        cleaned_data_frame.to_excel(writer, sheet_name="Clean Data", index=False)
        audit_data_frame.to_excel(writer, sheet_name="Audit Log", index=False)
        validation_data_frame.to_excel(
            writer,
            sheet_name="Validation Report",
            index=False,
        )

        workbook = writer.book

        header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
        header_font = Font(color="FFFFFF", bold=True)

        for worksheet in workbook.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    value = cell.value
                    if value is not None:
                        max_length = max(max_length, len(str(value)))

                worksheet.column_dimensions[column_letter].width = min(
                    max(max_length + 2, 12),
                    40,
                )


output_directory = Path.cwd()
raw_workbook_path = output_directory / "excel_data_cleaning_raw_and_cleaned.xlsx"

export_clean_workbook(
    raw_workbook_path,
    raw_df,
    clean_df,
    audit_df,
    validation_summary,
)

print("Created:", raw_workbook_path)


# ============================================================================
# 34. READING AN EXCEL WORKBOOK WITH OPENPYXL
# ============================================================================

print("\n" + "=" * 80)
print("34. READING EXCEL WITH OPENPYXL")
print("=" * 80)

workbook = load_workbook(raw_workbook_path)

print("Workbook sheets:", workbook.sheetnames)

for sheet_name in workbook.sheetnames:
    worksheet = workbook[sheet_name]
    print(
        f"{sheet_name}: "
        f"{worksheet.max_row} rows x {worksheet.max_column} columns"
    )


# ============================================================================
# 35. EXCEL DATA VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("35. ADDING EXCEL DATA VALIDATION")
print("=" * 80)


def add_excel_validation(
    input_path: Path,
    output_path: Path,
) -> None:
    workbook = load_workbook(input_path)

    worksheet = workbook["Clean Data"]

    # Locate the Status column dynamically.
    headers = {
        worksheet.cell(row=1, column=column).value: column
        for column in range(1, worksheet.max_column + 1)
    }

    status_column = headers["Status"]

    # Excel dropdown validation prevents users from entering arbitrary
    # status values in the specified cells.
    validation = DataValidation(
        type="list",
        formula1='"Active,Inactive,Pending"',
        allow_blank=False,
    )

    validation.error = "Choose a valid status."
    validation.errorTitle = "Invalid Status"
    validation.prompt = "Select Active, Inactive, or Pending."
    validation.promptTitle = "Status"
    validation.showErrorMessage = True
    validation.showInputMessage = True

    worksheet.add_data_validation(validation)

    validation_range = (
        f"{worksheet.cell(row=2, column=status_column).coordinate}:"
        f"{worksheet.cell(row=worksheet.max_row, column=status_column).coordinate}"
    )

    validation.add(validation_range)

    workbook.save(output_path)


validated_workbook_path = output_directory / "excel_data_cleaning_validated.xlsx"

add_excel_validation(
    raw_workbook_path,
    validated_workbook_path,
)

print("Created:", validated_workbook_path)


# ============================================================================
# 36. CONDITIONAL FORMATTING FOR VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("36. ADDING CONDITIONAL FORMATTING")
print("=" * 80)


def add_validation_formatting(
    input_path: Path,
    output_path: Path,
) -> None:
    workbook = load_workbook(input_path)

    worksheet = workbook["Clean Data"]

    # Locate the Age column.
    headers = {
        worksheet.cell(row=1, column=column).value: column
        for column in range(1, worksheet.max_column + 1)
    }

    age_column = headers["Age"]

    age_range = (
        f"{worksheet.cell(row=2, column=age_column).coordinate}:"
        f"{worksheet.cell(row=worksheet.max_row, column=age_column).coordinate}"
    )

    # Highlight values outside the accepted age range.
    worksheet.conditional_formatting.add(
        age_range,
        CellIsRule(
            operator="lessThan",
            formula=["18"],
            fill=PatternFill(fill_type="solid", fgColor="FFC7CE"),
        ),
    )

    worksheet.conditional_formatting.add(
        age_range,
        CellIsRule(
            operator="greaterThan",
            formula=["100"],
            fill=PatternFill(fill_type="solid", fgColor="FFC7CE"),
        ),
    )

    workbook.save(output_path)


formatted_workbook_path = (
    output_directory / "excel_data_cleaning_validated_formatted.xlsx"
)

add_validation_formatting(
    validated_workbook_path,
    formatted_workbook_path,
)

print("Created:", formatted_workbook_path)


# ============================================================================
# 37. EXCEL FORMULA-BASED VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("37. EXCEL FORMULA VALIDATION")
print("=" * 80)


def create_formula_validation_workbook(output_path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Validation"

    headers = [
        "Customer ID",
        "Email",
        "Age",
        "Status",
        "Email Valid?",
        "Age Valid?",
        "Status Valid?",
    ]

    worksheet.append(headers)

    sample_rows = [
        ["C001", "rahul@example.com", 29, "Active"],
        ["C002", "invalid-email", 31, "Active"],
        ["C003", "amit@example.com", 150, "Pending"],
    ]

    for row_number, row in enumerate(sample_rows, start=2):
        worksheet.append(row)

        # Excel formulas are intentionally stored as formulas, not evaluated
        # by openpyxl. Excel evaluates them when the workbook is opened.
        worksheet.cell(
            row=row_number,
            column=5,
            value=f'=IF(AND(B{row_number}<>"",ISNUMBER(SEARCH("@",B{row_number}))),"Valid","Invalid")',
        )

        worksheet.cell(
            row=row_number,
            column=6,
            value=f'=IF(AND(C{row_number}>=18,C{row_number}<=100),"Valid","Invalid")',
        )

        worksheet.cell(
            row=row_number,
            column=7,
            value=f'=IF(OR(D{row_number}="Active",D{row_number}="Inactive",D{row_number}="Pending"),"Valid","Invalid")',
        )

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    workbook.save(output_path)


formula_validation_path = output_directory / "excel_formula_validation.xlsx"

create_formula_validation_workbook(formula_validation_path)

print("Created:", formula_validation_path)


# ============================================================================
# 38. TEXT-TO-COLUMNS WITH OPENPYXL
# ============================================================================

print("\n" + "=" * 80)
print("38. SIMULATING TEXT-TO-COLUMNS IN EXCEL")
print("=" * 80)


def create_text_to_columns_example(output_path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Text to Columns"

    worksheet.append(["Original", "First Name", "Last Name", "Department"])

    values = [
        "Rahul|Sharma|Sales",
        "Priya|Singh|Finance",
        "Amit|Verma|IT",
        "Neha|Gupta|Human Resources",
    ]

    for row_number, value in enumerate(values, start=2):
        parts = value.split("|")

        worksheet.cell(row=row_number, column=1, value=value)

        for column_number, part in enumerate(parts, start=2):
            worksheet.cell(row=row_number, column=column_number, value=part)

    workbook.save(output_path)


text_to_columns_path = output_directory / "excel_text_to_columns_example.xlsx"

create_text_to_columns_example(text_to_columns_path)

print("Created:", text_to_columns_path)


# ============================================================================
# 39. EXCEL-SPECIFIC CLEANING CONCEPTS
# ============================================================================

print("\n" + "=" * 80)
print("39. IMPORTANT EXCEL CLEANING FUNCTIONS")
print("=" * 80)

print(
    """
Common Excel functions used for cleaning include:

TRIM(text)
    Removes leading and trailing spaces and reduces repeated standard spaces.

CLEAN(text)
    Removes many non-printing characters.

SUBSTITUTE(text, old_text, new_text)
    Replaces specific text.

UPPER(text)
    Converts text to uppercase.

LOWER(text)
    Converts text to lowercase.

PROPER(text)
    Converts words to title-style capitalization.

VALUE(text)
    Attempts to convert numeric text into a number.

TEXT(value, format)
    Formats a value as text.

LEFT(text, characters)
    Extracts characters from the left.

RIGHT(text, characters)
    Extracts characters from the right.

MID(text, start, characters)
    Extracts text from the middle.

FIND / SEARCH
    Locates text within another string.

IFERROR(value, fallback)
    Handles formula errors.

COUNTIF / COUNTIFS
    Counts values meeting conditions.

XLOOKUP
    Retrieves related values while supporting modern lookup workflows.

TEXTSPLIT
    Splits text into rows or columns using delimiters.

UNIQUE
    Returns unique values.

FILTER
    Returns records matching a condition.

SORT
    Sorts a dataset.

These functions are complementary to programmatic cleaning with Python.
"""
)


# ============================================================================
# 40. COMMON EXCEL ERROR VALUES
# ============================================================================

print("\n" + "=" * 80)
print("40. EXCEL ERROR VALUES")
print("=" * 80)

print(
    """
#DIV/0!
    A formula divides by zero.

#N/A
    A lookup or calculation has no available result.

#VALUE!
    A formula receives an inappropriate data type.

#REF!
    A formula refers to an invalid cell reference.

#NAME?
    Excel does not recognize a function, name, or text reference.

#NUM!
    A numeric calculation is invalid or outside an acceptable range.

#NULL!
    An invalid range intersection or related reference problem occurs.

Error handling is not the same as hiding errors. IFERROR can make a workbook
more readable, but excessive use can hide genuine data-quality problems.
"""
)


# ============================================================================
# 41. DATA STANDARDIZATION VERSUS DATA VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("41. STANDARDIZATION VERSUS VALIDATION")
print("=" * 80)

print(
    """
Standardization:
    Changes valid-but-inconsistent representations into one representation.

Example:
    "sales", "Sales", " SALES "
        -> "Sales"

Validation:
    Checks whether a value satisfies a rule.

Example:
    Age = 150
        -> invalid

These operations should not be confused.

Standardization answers:
    "How should this value be represented?"

Validation answers:
    "Is this value acceptable?"
"""
)


# ============================================================================
# 42. COMMON MISTAKES
# ============================================================================

print("\n" + "=" * 80)
print("42. COMMON DATA-CLEANING MISTAKES")
print("=" * 80)

mistakes = [
    "Deleting duplicate rows without defining what a duplicate means.",
    "Replacing every missing value with zero.",
    "Changing dates without confirming the source date convention.",
    "Converting IDs to numbers and accidentally removing leading zeros.",
    "Using title case on values where capitalization has semantic meaning.",
    "Changing valid business abbreviations without a mapping policy.",
    "Relying only on visual inspection.",
    "Overwriting the original dataset.",
    "Using formulas that hide errors instead of investigating them.",
    "Cleaning data without keeping an audit trail.",
    "Assuming formatting makes a value valid.",
    "Ignoring cells containing formulas that return empty strings.",
]

for number, mistake in enumerate(mistakes, start=1):
    print(f"{number}. {mistake}")


# ============================================================================
# 43. ID VALUES AND LEADING ZEROS
# ============================================================================

print("\n" + "=" * 80)
print("43. PRESERVING IDENTIFIERS")
print("=" * 80)

identifier_examples = pd.Series(
    ["000123", "000124", "001250", "100001"],
    dtype="string",
)

print("Identifiers as strings:")
print(identifier_examples)

print(
    """
Identifiers should usually be treated as text even when they contain only
digits.

For example:

    000123

is not necessarily the number 123. It may be a six-character business
identifier.

Converting it to a numeric type can destroy meaningful leading zeros.
"""
)


# ============================================================================
# 44. DUPLICATE DETECTION USING A COMPOSITE KEY
# ============================================================================

print("\n" + "=" * 80)
print("44. COMPOSITE DUPLICATE KEYS")
print("=" * 80)


composite_source = pd.DataFrame(
    {
        "Customer": ["A", "A", "A", "B"],
        "Date": ["2025-01-01", "2025-01-01", "2025-01-02", "2025-01-01"],
        "Amount": [100, 100, 200, 300],
    }
)

composite_source["Composite Key"] = (
    composite_source["Customer"].astype(str)
    + "|"
    + composite_source["Date"].astype(str)
    + "|"
    + composite_source["Amount"].astype(str)
)

print(composite_source)

print("\nDuplicate composite keys:")
print(composite_source[composite_source["Composite Key"].duplicated(keep=False)])


# ============================================================================
# 45. OUTLIER DETECTION
# ============================================================================

print("\n" + "=" * 80)
print("45. BASIC OUTLIER DETECTION")
print("=" * 80)


def detect_iqr_outliers(series: pd.Series) -> pd.Series:
    numeric_series = pd.to_numeric(series, errors="coerce")

    q1 = numeric_series.quantile(0.25)
    q3 = numeric_series.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return (numeric_series < lower_bound) | (numeric_series > upper_bound)


salary_outliers = detect_iqr_outliers(standardized_text_df["Salary"])

print("Salary values:")
print(standardized_text_df["Salary"].tolist())

print("IQR outlier flags:")
print(salary_outliers.tolist())

print(
    """
An outlier is not automatically an error.

For example, a very high salary may be perfectly legitimate.

Outlier detection should identify records for review, not automatically delete
them.
"""
)


# ============================================================================
# 46. RANGE CHECKS WITH BUSINESS RULES
# ============================================================================

print("\n" + "=" * 80)
print("46. BUSINESS RULE VALIDATION")
print("=" * 80)


def validate_customer_record(row: pd.Series) -> List[str]:
    issues: List[str] = []

    if pd.isna(row["Customer ID"]) or not str(row["Customer ID"]).strip():
        issues.append("Missing customer ID")

    if not is_valid_email(row["Email"]):
        issues.append("Invalid email")

    if not is_valid_indian_mobile(row["Phone"]):
        issues.append("Invalid Indian mobile number")

    if not validate_age(row["Age"]):
        issues.append("Age outside accepted range")

    if not validate_salary(row["Salary"]):
        issues.append("Salary must be greater than zero")

    if row["Status"] not in allowed_statuses:
        issues.append("Invalid status")

    if pd.isna(row["Join Date"]):
        issues.append("Invalid join date")

    return issues


business_validation = clean_df.copy()
business_validation["Validation Issues"] = business_validation.apply(
    validate_customer_record,
    axis=1,
)

print(
    business_validation[
        ["Customer ID", "Validation Issues"]
    ].to_string(index=False)
)


# ============================================================================
# 47. DATA CLEANING PIPELINE
# ============================================================================

print("\n" + "=" * 80)
print("47. REUSABLE DATA-CLEANING PIPELINE")
print("=" * 80)


def clean_customer_dataset(input_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Reusable cleaning pipeline.

    The order matters:
        1. Normalize missing markers.
        2. Normalize text.
        3. Standardize categories.
        4. Convert numeric fields.
        5. Convert dates.
        6. Normalize phones and emails.
        7. Remove exact duplicates.
        8. Add validation fields.
    """
    dataframe = input_dataframe.copy()

    # Normalize common missing-value representations.
    dataframe = dataframe.map(normalize_missing_value)

    # Clean whitespace and Unicode.
    dataframe = dataframe.map(clean_whitespace)
    dataframe = dataframe.map(remove_control_characters)
    dataframe = dataframe.map(normalize_unicode)

    # Standardize text fields.
    if "Customer ID" in dataframe.columns:
        dataframe["Customer ID"] = dataframe["Customer ID"].map(uppercase)

    if "Full Name" in dataframe.columns:
        dataframe["Full Name"] = dataframe["Full Name"].map(title_case)

    if "City" in dataframe.columns:
        dataframe["City"] = dataframe["City"].map(title_case)

    if "Email" in dataframe.columns:
        dataframe["Email"] = dataframe["Email"].map(clean_email)

    if "Status" in dataframe.columns:
        dataframe["Status"] = dataframe["Status"].map(title_case)

    if "Department" in dataframe.columns:
        dataframe["Department"] = dataframe["Department"].map(
            standardize_department
        )

    # Normalize phone numbers.
    if "Phone" in dataframe.columns:
        dataframe["Phone"] = dataframe["Phone"].map(normalize_phone)

    # Convert numeric fields.
    if "Age" in dataframe.columns:
        dataframe["Age"] = pd.to_numeric(
            dataframe["Age"],
            errors="coerce",
        )

    if "Salary" in dataframe.columns:
        dataframe["Salary"] = dataframe["Salary"].map(parse_currency)

    # Convert dates.
    if "Join Date" in dataframe.columns:
        dataframe["Join Date"] = dataframe["Join Date"].map(parse_date)

    # Remove exact duplicates only after normalization.
    dataframe = dataframe.drop_duplicates().reset_index(drop=True)

    # Validation fields.
    if "Email" in dataframe.columns:
        dataframe["Valid Email"] = dataframe["Email"].map(is_valid_email)

    if "Phone" in dataframe.columns:
        dataframe["Valid Phone"] = dataframe["Phone"].map(
            is_valid_indian_mobile
        )

    if "Age" in dataframe.columns:
        dataframe["Valid Age"] = dataframe["Age"].map(validate_age)

    if "Salary" in dataframe.columns:
        dataframe["Valid Salary"] = dataframe["Salary"].map(validate_salary)

    if "Status" in dataframe.columns:
        dataframe["Valid Status"] = dataframe["Status"].map(validate_status)

    return dataframe


pipeline_result = clean_customer_dataset(raw_df)

print("Pipeline result:")
print(pipeline_result.to_string(index=False))


# ============================================================================
# 48. TESTING THE CLEANING PIPELINE
# ============================================================================

print("\n" + "=" * 80)
print("48. BASIC TESTING")
print("=" * 80)


def test_normalize_missing_value() -> None:
    assert normalize_missing_value(None) is None
    assert normalize_missing_value("") is None
    assert normalize_missing_value("N/A") is None
    assert normalize_missing_value("valid") == "valid"


def test_currency_parser() -> None:
    assert parse_currency("₹55,000") == 55000.0
    assert parse_currency("62000") == 62000.0
    assert parse_currency("unknown") is None


def test_phone_normalization() -> None:
    assert normalize_phone("98765 43210") == "9876543210"
    assert normalize_phone("+91 9876543210") == "9876543210"


def test_email_validation() -> None:
    assert is_valid_email("person@example.com")
    assert not is_valid_email("invalid-email")


def test_age_validation() -> None:
    assert validate_age(18)
    assert validate_age(100)
    assert not validate_age(17)
    assert not validate_age(101)


def test_pipeline_removes_exact_duplicate() -> None:
    sample = pd.DataFrame(
        [
            {
                "Customer ID": "C1",
                "Full Name": "Test Person",
                "Email": "test@example.com",
            },
            {
                "Customer ID": "C1",
                "Full Name": "Test Person",
                "Email": "test@example.com",
            },
        ]
    )

    result = clean_customer_dataset(sample)
    assert len(result) == 1


test_normalize_missing_value()
test_currency_parser()
test_phone_normalization()
test_email_validation()
test_age_validation()
test_pipeline_removes_exact_duplicate()

print("All basic tests passed.")


# ============================================================================
# 49. EDGE CASE TESTING
# ============================================================================

print("\n" + "=" * 80)
print("49. EDGE CASES")
print("=" * 80)

edge_cases = [
    None,
    "",
    " ",
    "\t",
    "N/A",
    "NULL",
    "unknown",
    "₹0",
    "₹1,00,000",
    "not a number",
    "999999999999999",
]

for value in edge_cases:
    print(
        f"Input={value!r:>24} | "
        f"Currency={parse_currency(value)!r:>15} | "
        f"Phone={normalize_phone(value)!r}"
    )


# ============================================================================
# 50. PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("50. PERFORMANCE CONSIDERATIONS")
print("=" * 80)

print(
    """
For small and medium Excel files, pandas provides convenient vectorized
operations.

Prefer:
    Series.str.strip()
    Series.str.lower()
    Series.str.replace()
    pd.to_numeric()
    pd.to_datetime()
    DataFrame.drop_duplicates()

over:
    Python-level row-by-row loops whenever a vectorized operation can express
    the same rule.

For very large workbooks:

    - Avoid loading unnecessary columns.
    - Process data in chunks where appropriate.
    - Use efficient data types.
    - Avoid repeated DataFrame copies.
    - Avoid expensive apply() calls when vectorized operations are available.
    - Keep Excel formatting separate from core data transformation.
    - Consider a database or columnar processing system when Excel is no longer
      an appropriate storage format.

Excel itself also has practical row and memory limitations, so very large
datasets should not automatically be forced into a workbook.
"""
)


# ============================================================================
# 51. SECURITY CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("51. SECURITY CONSIDERATIONS")
print("=" * 80)

print(
    """
Important spreadsheet security concerns include:

1. Formula injection

Text beginning with characters such as:
    =
    +
    -
    @

may be interpreted as formulas by spreadsheet software in some workflows.

When exporting untrusted user-controlled text, consider neutralizing dangerous
formula prefixes according to the requirements of the target environment.

2. Sensitive information

Do not expose personal, financial, authentication, or confidential information
unnecessarily.

3. Macro-enabled files

Do not enable or execute untrusted VBA macros.

4. External links

Review external workbook references before distributing files.

5. File paths

Do not blindly trust file names or paths supplied by external users.

6. Data integrity

Preserve the original source file and write cleaned output to a separate file
unless controlled replacement is explicitly required.
"""
)


def neutralize_formula_text(value: Any) -> Any:
    """
    Demonstration of a conservative spreadsheet-export safeguard.

    This treats text beginning with common formula characters as literal text.
    The correct policy depends on the destination system and business context.
    """
    if not isinstance(value, str):
        return value

    if value.startswith(("=", "+", "-", "@")):
        return "'" + value

    return value


security_examples = [
    "=SUM(A1:A10)",
    "+123",
    "-123",
    "@username",
    "normal text",
]

print("\nFormula-injection examples:")
for value in security_examples:
    print(f"{value!r:>20} -> {neutralize_formula_text(value)!r}")


# ============================================================================
# 52. PRESERVING ORIGINAL DATA
# ============================================================================

print("\n" + "=" * 80)
print("52. PRESERVING THE SOURCE")
print("=" * 80)

print(
    """
A reliable cleaning process generally follows this pattern:

    Raw source
        |
        v
    Validation
        |
        v
    Cleaning
        |
        v
    Standardization
        |
        v
    Quality checks
        |
        v
    Clean output
        |
        v
    Audit report

The raw source should remain recoverable.

This is important because a cleaning rule may later be discovered to be
incorrect.
"""
)


# ============================================================================
# 53. REPRODUCIBILITY
# ============================================================================

print("\n" + "=" * 80)
print("53. REPRODUCIBILITY")
print("=" * 80)

print(
    """
A reproducible cleaning process should define:

    - Input source
    - Expected columns
    - Data types
    - Missing-value policy
    - Standardization mappings
    - Validation rules
    - Duplicate policy
    - Output structure
    - Audit information
    - Error behavior

The same input should produce the same cleaned result when the rules and
software environment are unchanged.
"""
)


# ============================================================================
# 54. SCHEMA VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("54. SCHEMA VALIDATION")
print("=" * 80)


expected_columns = {
    "Customer ID",
    "Full Name",
    "Email",
    "Phone",
    "City",
    "Department",
    "Age",
    "Join Date",
    "Salary",
    "Status",
    "Notes",
}


def validate_schema(
    dataframe: pd.DataFrame,
    required: set[str],
) -> Tuple[bool, List[str], List[str]]:
    actual = set(dataframe.columns)

    missing_columns = sorted(required - actual)
    unexpected_columns = sorted(actual - required)

    valid = not missing_columns

    return valid, missing_columns, unexpected_columns


schema_valid, missing_columns, unexpected_columns = validate_schema(
    raw_df,
    expected_columns,
)

print("Schema valid:", schema_valid)
print("Missing columns:", missing_columns)
print("Unexpected columns:", unexpected_columns)


# ============================================================================
# 55. FAIL-FAST VERSUS TOLERANT CLEANING
# ============================================================================

print("\n" + "=" * 80)
print("55. FAIL-FAST VERSUS TOLERANT CLEANING")
print("=" * 80)

print(
    """
Two common approaches exist.

Fail-fast:
    Stop the pipeline when a critical requirement is violated.

Example:
    Customer ID column is missing.

Tolerant:
    Continue processing while recording recoverable problems.

Example:
    One email address is malformed.

A production pipeline often combines both approaches:

    Critical schema failure -> stop
    Individual bad values -> flag and continue
    Serious integrity violation -> stop or quarantine affected records
"""
)


def require_columns(
    dataframe: pd.DataFrame,
    required_columns: Sequence[str],
) -> None:
    missing = [
        column for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            "Required columns are missing: " + ", ".join(missing)
        )


require_columns(
    raw_df,
    ["Customer ID", "Email", "Age"],
)

print("Critical schema requirements passed.")


# ============================================================================
# 56. QUARANTINING BAD RECORDS
# ============================================================================

print("\n" + "=" * 80)
print("56. QUARANTINING INVALID RECORDS")
print("=" * 80)

invalid_records = standardized_text_df[
    ~(
        standardized_text_df["Valid Email"]
        & standardized_text_df["Valid Age"]
        & standardized_text_df["Valid Salary"]
    )
].copy()

valid_records = standardized_text_df[
    standardized_text_df["Valid Email"]
    & standardized_text_df["Valid Age"]
    & standardized_text_df["Valid Salary"]
].copy()

print("Valid records:", len(valid_records))
print("Quarantined records:", len(invalid_records))

if not invalid_records.empty:
    print("\nQuarantined records:")
    print(
        invalid_records[
            ["Customer ID", "Email", "Age", "Salary"]
        ].to_string(index=False)
    )


# ============================================================================
# 57. DATA LINEAGE
# ============================================================================

print("\n" + "=" * 80)
print("57. DATA LINEAGE")
print("=" * 80)

print(
    """
Data lineage describes where data came from and how it was transformed.

A simple lineage record can contain:

    source file
    source sheet
    source row
    transformation
    timestamp
    output record

For regulated or business-critical workflows, lineage can be as important as
the cleaned dataset itself.
"""
)


lineage_df = pd.DataFrame(
    {
        "Source": ["demo_raw_data"] * len(clean_df),
        "Transformation": ["standardize_and_validate"] * len(clean_df),
        "Output Row": range(2, len(clean_df) + 2),
    }
)

print(lineage_df.head().to_string(index=False))


# ============================================================================
# 58. FINAL EXCEL PACKAGE
# ============================================================================

print("\n" + "=" * 80)
print("58. CREATING A FINAL STUDY WORKBOOK")
print("=" * 80)


def create_final_study_workbook(output_path: Path) -> None:
    workbook = Workbook()

    raw_sheet = workbook.active
    raw_sheet.title = "Raw Data"

    clean_sheet = workbook.create_sheet("Clean Data")
    validation_sheet = workbook.create_sheet("Validation")
    audit_sheet = workbook.create_sheet("Audit")
    instructions_sheet = workbook.create_sheet("Cleaning Rules")

    def write_dataframe(
        worksheet,
        dataframe: pd.DataFrame,
    ) -> None:
        worksheet.append(list(dataframe.columns))

        for row in dataframe.itertuples(index=False, name=None):
            converted_row = []

            for value in row:
                if pd.isna(value):
                    converted_row.append(None)
                elif isinstance(value, pd.Timestamp):
                    converted_row.append(value.to_pydatetime())
                else:
                    converted_row.append(value)

            worksheet.append(converted_row)

    write_dataframe(raw_sheet, raw_df)
    write_dataframe(clean_sheet, clean_df)
    write_dataframe(validation_sheet, validation_summary)
    write_dataframe(audit_sheet, audit_df)

    rules = [
        ("Rule", "Description"),
        (
            "Missing values",
            "Identify blanks and defined missing-value markers before analysis.",
        ),
        (
            "Duplicates",
            "Remove exact duplicates only after defining the duplicate policy.",
        ),
        (
            "Whitespace",
            "Trim leading/trailing whitespace and normalize repeated whitespace.",
        ),
        (
            "Email",
            "Normalize case and validate basic email structure.",
        ),
        (
            "Phone",
            "Remove formatting characters and validate the expected number format.",
        ),
        (
            "Age",
            "Accept only values within the defined business range.",
        ),
        (
            "Salary",
            "Convert currency text into numeric values and reject invalid values.",
        ),
        (
            "Date",
            "Convert recognized date values and investigate ambiguous formats.",
        ),
        (
            "Status",
            "Restrict values to the approved category set.",
        ),
    ]

    for row in rules:
        instructions_sheet.append(row)

    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = "A2"

        if worksheet.max_row > 1 and worksheet.max_column > 1:
            worksheet.auto_filter.ref = worksheet.dimensions

        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        for column_cells in worksheet.columns:
            maximum = 0

            for cell in column_cells:
                if cell.value is not None:
                    maximum = max(maximum, len(str(cell.value)))

            column_letter = column_cells[0].column_letter
            worksheet.column_dimensions[column_letter].width = min(
                max(maximum + 2, 12),
                45,
            )

    # Add status dropdown to the clean sheet.
    clean_headers = {
        clean_sheet.cell(row=1, column=column).value: column
        for column in range(1, clean_sheet.max_column + 1)
    }

    if "Status" in clean_headers:
        status_column = clean_headers["Status"]

        status_validation = DataValidation(
            type="list",
            formula1='"Active,Inactive,Pending"',
            allow_blank=False,
        )

        clean_sheet.add_data_validation(status_validation)

        status_validation.add(
            f"{clean_sheet.cell(row=2, column=status_column).coordinate}:"
            f"{clean_sheet.cell(row=clean_sheet.max_row, column=status_column).coordinate}"
        )

    workbook.save(output_path)


final_workbook_path = output_directory / "excel_data_cleaning_complete_study.xlsx"

create_final_study_workbook(final_workbook_path)

print("Created:", final_workbook_path)


# ============================================================================
# 59. VERIFY GENERATED WORKBOOKS
# ============================================================================

print("\n" + "=" * 80)
print("59. VERIFYING GENERATED FILES")
print("=" * 80)

generated_files = [
    raw_workbook_path,
    validated_workbook_path,
    formatted_workbook_path,
    formula_validation_path,
    text_to_columns_path,
    final_workbook_path,
]

for file_path in generated_files:
    exists = file_path.exists()
    size = file_path.stat().st_size if exists else 0

    print(
        f"{file_path.name:50} "
        f"exists={exists} "
        f"size={size:,} bytes"
    )


# ============================================================================
# 60. FINAL QUALITY GATES
# ============================================================================

print("\n" + "=" * 80)
print("60. FINAL QUALITY GATES")
print("=" * 80)


def run_quality_gates(dataframe: pd.DataFrame) -> Dict[str, bool]:
    gates = {
        "No exact duplicate rows": not dataframe.duplicated().any(),
        "Customer IDs present": dataframe["Customer ID"].notna().all(),
        "Emails normalized": dataframe["Email"].dropna().eq(
            dataframe["Email"].dropna().str.lower()
        ).all(),
        "Ages numeric": pd.api.types.is_numeric_dtype(dataframe["Age"]),
        "Salaries numeric": pd.api.types.is_numeric_dtype(dataframe["Salary"]),
        "Dates datetime": pd.api.types.is_datetime64_any_dtype(
            dataframe["Join Date"]
        ),
        "Statuses standardized": dataframe["Status"].dropna().isin(
            allowed_statuses
        ).all(),
    }

    return gates


quality_gates = run_quality_gates(clean_df)

for gate_name, passed in quality_gates.items():
    print(f"{'PASS' if passed else 'FAIL'}: {gate_name}")


# ============================================================================
# 61. CLEANING PRINCIPLES
# ============================================================================

print("\n" + "=" * 80)
print("61. CORE PRINCIPLES")
print("=" * 80)

principles = [
    "Understand the dataset before changing it.",
    "Preserve the original source.",
    "Define business rules before applying automated transformations.",
    "Separate standardization from validation.",
    "Treat missing values according to their meaning.",
    "Do not confuse formatting with data validity.",
    "Do not delete suspicious records automatically unless the rule is justified.",
    "Preserve identifiers as text when leading zeros or exact representations matter.",
    "Use explicit mappings for controlled categories.",
    "Validate dates according to the source locale and business convention.",
    "Keep an audit trail for important transformations.",
    "Test edge cases.",
    "Use vectorized operations for performance where practical.",
    "Quarantine questionable records instead of silently discarding them.",
    "Protect exported workbooks from accidental or unsafe interpretation.",
]

for principle in principles:
    print("-", principle)


# ============================================================================
# 62. COMPLETION
# ============================================================================

print("\n" + "=" * 80)
print("DATA CLEANING STUDY SCRIPT COMPLETED")
print("=" * 80)

print(
    f"""
The demonstration covered:
    - Missing values
    - Duplicate detection
    - Whitespace cleaning
    - Hidden character handling
    - Unicode normalization
    - Case standardization
    - Category mapping
    - Email validation
    - Phone normalization
    - Currency conversion
    - Numeric conversion
    - Date parsing
    - Text-to-columns
    - Data validation
    - Error handling
    - Quality scoring
    - Audit logging
    - Excel data validation
    - Conditional formatting
    - Formula validation
    - Schema validation
    - Business rules
    - Outlier detection
    - Quarantine workflows
    - Data lineage
    - Testing
    - Performance considerations
    - Security considerations
    - Reproducible cleaning pipelines

Generated Excel files are located in:
    {output_directory}
"""
)
