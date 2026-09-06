"""
DATA QUALITY: FROM BEGINNER TO ADVANCED
=======================================

A self-contained educational Python script covering:

- Accuracy
- Completeness
- Consistency
- Validity
- Uniqueness
- Timeliness
- Integrity
- Missing data
- Duplicate data
- Anomalous records
- Data-quality dimensions and measurement
- Validation rules
- Profiling
- Detection and remediation
- Referential integrity
- Cross-field consistency
- Outliers and anomalies
- Quality scoring
- Data-quality pipelines
- Testing and monitoring
- Advanced implementation patterns
- Performance considerations
- Production considerations

The script uses only the Python standard library.

Run directly:

    python data_quality.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from collections import Counter, defaultdict
from statistics import mean, median, pstdev
from typing import Any, Callable, Iterable, Optional
import math
import re
import uuid


# ============================================================================
# 1. INTRODUCTION
# ============================================================================

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def explain_data_quality() -> None:
    """
    Data quality describes how suitable data is for its intended purpose.

    High-quality data is not simply "data without errors". A dataset may be
    technically valid but still be unsuitable for a business decision.

    Example:
        A customer age of 17 is syntactically valid and may be accurate, but
        it could be invalid for a dataset that specifically represents adult
        customers.

    Quality is therefore contextual and should be evaluated against defined
    business requirements.
    """
    print("Data quality is the degree to which data satisfies defined requirements.")
    print("Common dimensions:")
    print("  Accuracy      : Does the value represent reality?")
    print("  Completeness  : Is required information present?")
    print("  Consistency   : Do related values agree?")
    print("  Validity      : Does data conform to rules and formats?")
    print("  Uniqueness    : Are unintended duplicates absent?")
    print("  Timeliness    : Is data sufficiently current?")
    print("  Integrity     : Are relationships and constraints preserved?")


# ============================================================================
# 2. FUNDAMENTAL DATA TYPES AND MISSING VALUES
# ============================================================================

MISSING_VALUES = {
    None,
    "",
    " ",
    "NA",
    "N/A",
    "NULL",
    "null",
    "None",
    "unknown",
    "UNKNOWN",
}


def is_missing(value: Any) -> bool:
    """
    Determine whether a value should be interpreted as missing.

    In production systems, the definition of missingness should be explicit.
    For example, zero should normally NOT be considered missing.
    """
    if value is None:
        return True

    if isinstance(value, str):
        normalized = value.strip()
        return normalized == "" or normalized.upper() in {
            "NA",
            "N/A",
            "NULL",
            "NONE",
            "UNKNOWN",
        }

    return False


def normalize_missing(value: Any) -> Any:
    """Convert recognized missing representations into None."""
    return None if is_missing(value) else value


def demonstrate_missing_values() -> None:
    section("2. MISSING DATA")

    examples = [None, "", "   ", "NA", "N/A", "NULL", 0, False, "John"]

    for value in examples:
        print(f"{value!r:>8} -> missing={is_missing(value)}")

    print("\nImportant distinction:")
    print("  None      -> missing")
    print("  0         -> usually a legitimate numeric value")
    print("  False     -> usually a legitimate Boolean value")
    print("  'unknown' -> often missing, depending on the data contract")


# ============================================================================
# 3. SAMPLE DATASET
# ============================================================================

RAW_CUSTOMERS = [
    {
        "customer_id": "C001",
        "name": "Alice Sharma",
        "email": "alice@example.com",
        "age": 31,
        "country": "India",
        "signup_date": "2026-08-01",
        "status": "active",
        "credit_limit": 50000,
        "updated_at": "2026-09-05T09:00:00",
    },
    {
        "customer_id": "C002",
        "name": "Bob Kumar",
        "email": "bob@example.com",
        "age": 42,
        "country": "India",
        "signup_date": "2026-07-15",
        "status": "active",
        "credit_limit": 75000,
        "updated_at": "2026-09-04T09:00:00",
    },
    {
        "customer_id": "C002",
        "name": "Bob Kumar",
        "email": "bob@example.com",
        "age": 42,
        "country": "India",
        "signup_date": "2026-07-15",
        "status": "active",
        "credit_limit": 75000,
        "updated_at": "2026-09-04T09:00:00",
    },
    {
        "customer_id": "C003",
        "name": "Carol Singh",
        "email": None,
        "age": 29,
        "country": "India",
        "signup_date": "2026-08-20",
        "status": "active",
        "credit_limit": 45000,
        "updated_at": "2026-08-21T09:00:00",
    },
    {
        "customer_id": "C004",
        "name": "David Rao",
        "email": "david@example",
        "age": 150,
        "country": "India",
        "signup_date": "2026-08-10",
        "status": "active",
        "credit_limit": -5000,
        "updated_at": "2026-09-01T09:00:00",
    },
    {
        "customer_id": "C005",
        "name": "Eva Mehta",
        "email": "eva@example.com",
        "age": 36,
        "country": "India",
        "signup_date": "2026-09-30",
        "status": "inactive",
        "credit_limit": 60000,
        "updated_at": "2026-09-30T09:00:00",
    },
    {
        "customer_id": "C006",
        "name": "Farhan Ali",
        "email": "farhan@example.com",
        "age": None,
        "country": "India",
        "signup_date": "2026-08-25",
        "status": "ACTIVE",
        "credit_limit": 55000,
        "updated_at": "2026-09-05T09:00:00",
    },
]


# ============================================================================
# 4. DATA PROFILING
# ============================================================================

def profile_column(records: list[dict[str, Any]], column: str) -> dict[str, Any]:
    """Calculate basic statistics for one column."""
    values = [record.get(column) for record in records]
    non_missing = [value for value in values if not is_missing(value)]

    unique_count = len({repr(value) for value in non_missing})

    return {
        "column": column,
        "row_count": len(values),
        "missing_count": len(values) - len(non_missing),
        "missing_rate": (
            (len(values) - len(non_missing)) / len(values) if values else 0.0
        ),
        "non_missing_count": len(non_missing),
        "unique_count": unique_count,
        "distinct_rate": unique_count / len(non_missing) if non_missing else 0.0,
        "sample_values": non_missing[:5],
    }


def profile_dataset(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Profile every column appearing in a collection of records."""
    columns = sorted({key for record in records for key in record})

    return {
        column: profile_column(records, column)
        for column in columns
    }


def print_profile(records: list[dict[str, Any]]) -> None:
    section("4. DATA PROFILING")

    profiles = profile_dataset(records)

    for column, information in profiles.items():
        print(
            f"{column:15} "
            f"rows={information['row_count']:2} "
            f"missing={information['missing_count']:2} "
            f"missing_rate={information['missing_rate']:.1%} "
            f"unique={information['unique_count']:2}"
        )


# ============================================================================
# 5. COMPLETENESS
# ============================================================================

def completeness_rate(
    records: list[dict[str, Any]],
    required_columns: Iterable[str],
) -> float:
    """
    Measure the percentage of required field cells that are populated.

    Formula:
        populated required cells / total required cells
    """
    columns = list(required_columns)

    if not records or not columns:
        return 1.0

    total_cells = len(records) * len(columns)
    populated_cells = sum(
        not is_missing(record.get(column))
        for record in records
        for column in columns
    )

    return populated_cells / total_cells


def record_completeness(
    record: dict[str, Any],
    required_columns: Iterable[str],
) -> float:
    """Measure completeness for one record."""
    columns = list(required_columns)

    if not columns:
        return 1.0

    populated = sum(
        not is_missing(record.get(column))
        for column in columns
    )

    return populated / len(columns)


def demonstrate_completeness(records: list[dict[str, Any]]) -> None:
    section("5. COMPLETENESS")

    required = [
        "customer_id",
        "name",
        "email",
        "age",
        "country",
        "signup_date",
        "status",
    ]

    rate = completeness_rate(records, required)

    print(f"Dataset completeness: {rate:.2%}")

    for record in records:
        score = record_completeness(record, required)
        print(record.get("customer_id"), f"{score:.2%}")


# ============================================================================
# 6. VALIDITY
# ============================================================================

@dataclass
class ValidationResult:
    """Result of applying a validation rule."""

    rule_name: str
    passed: bool
    message: str
    field: Optional[str] = None
    value: Any = None


@dataclass
class ValidationRule:
    """
    A reusable validation rule.

    The validator receives a record and returns a ValidationResult.
    """

    name: str
    validator: Callable[[dict[str, Any]], ValidationResult]


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


def validate_required(record: dict[str, Any], field_name: str) -> ValidationResult:
    value = record.get(field_name)

    return ValidationResult(
        rule_name=f"required:{field_name}",
        passed=not is_missing(value),
        message=(
            "Required value is present"
            if not is_missing(value)
            else "Required value is missing"
        ),
        field=field_name,
        value=value,
    )


def validate_email(record: dict[str, Any]) -> ValidationResult:
    value = record.get("email")

    if is_missing(value):
        return ValidationResult(
            rule_name="email_format",
            passed=False,
            message="Email is missing",
            field="email",
            value=value,
        )

    passed = bool(EMAIL_PATTERN.fullmatch(str(value).strip()))

    return ValidationResult(
        rule_name="email_format",
        passed=passed,
        message="Valid email syntax" if passed else "Invalid email syntax",
        field="email",
        value=value,
    )


def validate_age(record: dict[str, Any]) -> ValidationResult:
    value = record.get("age")

    if is_missing(value):
        return ValidationResult(
            rule_name="age_range",
            passed=False,
            message="Age is missing",
            field="age",
            value=value,
        )

    passed = isinstance(value, int) and 0 <= value <= 120

    return ValidationResult(
        rule_name="age_range",
        passed=passed,
        message="Age is within 0-120" if passed else "Age must be an integer from 0 to 120",
        field="age",
        value=value,
    )


def validate_credit_limit(record: dict[str, Any]) -> ValidationResult:
    value = record.get("credit_limit")

    if is_missing(value):
        return ValidationResult(
            rule_name="credit_limit_non_negative",
            passed=False,
            message="Credit limit is missing",
            field="credit_limit",
            value=value,
        )

    passed = isinstance(value, (int, float, Decimal)) and value >= 0

    return ValidationResult(
        rule_name="credit_limit_non_negative",
        passed=passed,
        message=(
            "Credit limit is non-negative"
            if passed
            else "Credit limit cannot be negative"
        ),
        field="credit_limit",
        value=value,
    )


def validate_status(record: dict[str, Any]) -> ValidationResult:
    value = record.get("status")

    allowed = {"active", "inactive", "suspended"}

    passed = isinstance(value, str) and value.lower() in allowed

    return ValidationResult(
        rule_name="status_enum",
        passed=passed,
        message=(
            "Status is allowed"
            if passed
            else "Status must be active, inactive, or suspended"
        ),
        field="status",
        value=value,
    )


def validate_date_format(record: dict[str, Any]) -> ValidationResult:
    value = record.get("signup_date")

    if is_missing(value):
        return ValidationResult(
            rule_name="signup_date_format",
            passed=False,
            message="Signup date is missing",
            field="signup_date",
            value=value,
        )

    try:
        datetime.strptime(str(value), "%Y-%m-%d")
        passed = True
        message = "Valid ISO date"
    except ValueError:
        passed = False
        message = "Date must use YYYY-MM-DD"

    return ValidationResult(
        rule_name="signup_date_format",
        passed=passed,
        message=message,
        field="signup_date",
        value=value,
    )


def validate_business_date(record: dict[str, Any]) -> ValidationResult:
    """
    A syntactically valid date may still violate business rules.

    This rule prevents a signup date from being in the future.
    """
    value = record.get("signup_date")

    if is_missing(value):
        return ValidationResult(
            rule_name="signup_date_not_future",
            passed=False,
            message="Signup date is missing",
            field="signup_date",
            value=value,
        )

    try:
        signup = datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return ValidationResult(
            rule_name="signup_date_not_future",
            passed=False,
            message="Signup date cannot be interpreted",
            field="signup_date",
            value=value,
        )

    today = date(2026, 9, 6)
    passed = signup <= today

    return ValidationResult(
        rule_name="signup_date_not_future",
        passed=passed,
        message=(
            "Signup date is not in the future"
            if passed
            else "Signup date is in the future"
        ),
        field="signup_date",
        value=value,
    )


def build_validation_rules() -> list[ValidationRule]:
    """Construct the dataset's validation rule set."""
    required_fields = [
        "customer_id",
        "name",
        "email",
        "age",
        "country",
        "signup_date",
        "status",
    ]

    rules = [
        ValidationRule(
            name=f"required:{field_name}",
            validator=lambda record, field_name=field_name:
                validate_required(record, field_name),
        )
        for field_name in required_fields
    ]

    rules.extend(
        [
            ValidationRule("email_format", validate_email),
            ValidationRule("age_range", validate_age),
            ValidationRule("credit_limit_non_negative", validate_credit_limit),
            ValidationRule("status_enum", validate_status),
            ValidationRule("signup_date_format", validate_date_format),
            ValidationRule("signup_date_not_future", validate_business_date),
        ]
    )

    return rules


def validate_record(
    record: dict[str, Any],
    rules: list[ValidationRule],
) -> list[ValidationResult]:
    """Apply every validation rule to a record."""
    return [rule.validator(record) for rule in rules]


def demonstrate_validation(records: list[dict[str, Any]]) -> None:
    section("6. VALIDITY AND VALIDATION RULES")

    rules = build_validation_rules()

    for record in records:
        results = validate_record(record, rules)
        failures = [result for result in results if not result.passed]

        print(
            f"{record.get('customer_id')}: "
            f"{len(results) - len(failures)}/{len(results)} rules passed"
        )

        for failure in failures:
            print(f"  - {failure.rule_name}: {failure.message}")


# ============================================================================
# 7. UNIQUENESS AND DUPLICATE DATA
# ============================================================================

def duplicate_records(
    records: list[dict[str, Any]],
    key_fields: Iterable[str],
) -> dict[tuple[Any, ...], list[int]]:
    """
    Find records sharing the same business key.

    A duplicate can be exact or semantic. Key-based duplicate detection is
    useful when records differ in non-key attributes.
    """
    fields = list(key_fields)
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)

    for index, record in enumerate(records):
        key = tuple(record.get(field) for field in fields)
        groups[key].append(index)

    return {
        key: indexes
        for key, indexes in groups.items()
        if len(indexes) > 1
    }


def exact_duplicate_records(
    records: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Find exact duplicate records using a deterministic representation."""
    groups: dict[str, list[int]] = defaultdict(list)

    for index, record in enumerate(records):
        representation = repr(sorted(record.items()))
        groups[representation].append(index)

    return {
        representation: indexes
        for representation, indexes in groups.items()
        if len(indexes) > 1
    }


def uniqueness_rate(
    records: list[dict[str, Any]],
    key_fields: Iterable[str],
) -> float:
    """Calculate the proportion of records having unique keys."""
    fields = list(key_fields)

    if not records:
        return 1.0

    keys = [
        tuple(record.get(field) for field in fields)
        for record in records
    ]

    return len(set(keys)) / len(keys)


def demonstrate_duplicates(records: list[dict[str, Any]]) -> None:
    section("7. UNIQUENESS AND DUPLICATE DATA")

    duplicates = duplicate_records(records, ["customer_id"])

    print(f"Duplicate customer IDs: {len(duplicates)}")

    for key, indexes in duplicates.items():
        print(f"  Key {key}: rows {indexes}")

    print(
        f"Uniqueness rate: "
        f"{uniqueness_rate(records, ['customer_id']):.2%}"
    )


# ============================================================================
# 8. CONSISTENCY
# ============================================================================

def normalize_status(status: Any) -> Any:
    """Normalize status values to a canonical representation."""
    if is_missing(status):
        return None

    return str(status).strip().lower()


def normalize_email(email: Any) -> Any:
    """Normalize email for comparison without changing its business meaning."""
    if is_missing(email):
        return None

    return str(email).strip().lower()


def consistency_check_status(record: dict[str, Any]) -> ValidationResult:
    """
    Demonstrate a normalization-based consistency check.

    'ACTIVE' and 'active' may be semantically equivalent but represent the
    same concept inconsistently at storage level.
    """
    original = record.get("status")
    normalized = normalize_status(original)

    passed = original == normalized if isinstance(original, str) else True

    return ValidationResult(
        rule_name="canonical_status",
        passed=passed,
        message=(
            "Status already uses canonical lowercase form"
            if passed
            else "Status should be normalized to lowercase"
        ),
        field="status",
        value=original,
    )


def demonstrate_consistency(records: list[dict[str, Any]]) -> None:
    section("8. CONSISTENCY")

    print("Consistency concerns whether equivalent representations agree.")

    for record in records:
        result = consistency_check_status(record)
        if not result.passed:
            print(
                f"{record.get('customer_id')}: "
                f"{result.message} ({record.get('status')!r})"
            )

    print("\nExamples of consistency violations:")
    print("  'IN' versus 'India'")
    print("  'ACTIVE' versus 'active'")
    print("  1000 INR versus 1000 USD")
    print("  date stored as DD/MM/YYYY versus YYYY-MM-DD")


# ============================================================================
# 9. ACCURACY
# ============================================================================

def accuracy_against_reference(
    records: list[dict[str, Any]],
    reference_values: dict[Any, dict[str, Any]],
    key_field: str,
    compared_fields: Iterable[str],
) -> float:
    """
    Compare records against a trusted reference source.

    Accuracy cannot normally be inferred from syntax alone. It requires a
    trustworthy reference, observation, verification process, or domain rule.
    """
    fields = list(compared_fields)
    total = 0
    correct = 0

    for record in records:
        key = record.get(key_field)

        if key not in reference_values:
            continue

        reference = reference_values[key]

        for field_name in fields:
            total += 1

            if record.get(field_name) == reference.get(field_name):
                correct += 1

    return correct / total if total else 1.0


def demonstrate_accuracy(records: list[dict[str, Any]]) -> None:
    section("9. ACCURACY")

    reference = {
        "C001": {"name": "Alice Sharma"},
        "C002": {"name": "Bob Kumar"},
        "C003": {"name": "Carol Singh"},
        "C004": {"name": "David Rao"},
        "C005": {"name": "Eva Mehta"},
        "C006": {"name": "Farhan Ali"},
    }

    rate = accuracy_against_reference(
        records,
        reference,
        "customer_id",
        ["name"],
    )

    print(f"Accuracy against trusted reference: {rate:.2%}")

    print("\nImportant:")
    print("  Validity asks whether data follows a rule.")
    print("  Accuracy asks whether data reflects reality or a trusted source.")


# ============================================================================
# 10. TIMELINESS
# ============================================================================

def parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse an ISO-like timestamp into a datetime."""
    if is_missing(value):
        return None

    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def timeliness_score(
    records: list[dict[str, Any]],
    timestamp_field: str,
    reference_time: datetime,
    maximum_age: timedelta,
) -> float:
    """
    Calculate the percentage of records updated within the permitted age.
    """
    if not records:
        return 1.0

    timely = 0

    for record in records:
        timestamp = parse_timestamp(record.get(timestamp_field))

        if timestamp is not None and reference_time - timestamp <= maximum_age:
            timely += 1

    return timely / len(records)


def demonstrate_timeliness(records: list[dict[str, Any]]) -> None:
    section("10. TIMELINESS")

    reference_time = datetime(2026, 9, 6, 12, 0, 0)

    score = timeliness_score(
        records,
        "updated_at",
        reference_time,
        timedelta(days=2),
    )

    print(f"Records updated within two days: {score:.2%}")

    print("\nTimeliness depends on business requirements.")
    print("A stock price may need seconds of freshness.")
    print("A yearly demographic report may tolerate months.")


# ============================================================================
# 11. INTEGRITY
# ============================================================================

@dataclass
class Customer:
    customer_id: str
    name: str


@dataclass
class Order:
    order_id: str
    customer_id: str
    amount: float


def check_referential_integrity(
    customers: list[Customer],
    orders: list[Order],
) -> list[Order]:
    """
    Detect foreign-key violations.

    Every order.customer_id should reference an existing customer.
    """
    customer_ids = {customer.customer_id for customer in customers}

    return [
        order
        for order in orders
        if order.customer_id not in customer_ids
    ]


def demonstrate_integrity() -> None:
    section("11. INTEGRITY")

    customers = [
        Customer("C001", "Alice"),
        Customer("C002", "Bob"),
    ]

    orders = [
        Order("O001", "C001", 1500.0),
        Order("O002", "C002", 2000.0),
        Order("O003", "C999", 700.0),
    ]

    violations = check_referential_integrity(customers, orders)

    print(f"Referential-integrity violations: {len(violations)}")

    for order in violations:
        print(f"  {order.order_id} references missing customer {order.customer_id}")

    print("\nIntegrity includes:")
    print("  Primary-key integrity")
    print("  Foreign-key integrity")
    print("  Domain integrity")
    print("  Constraint integrity")
    print("  Transactional integrity")


# ============================================================================
# 12. CROSS-FIELD CONSISTENCY
# ============================================================================

def validate_cross_field_rules(record: dict[str, Any]) -> list[ValidationResult]:
    """
    Validate relationships among multiple fields.

    Cross-field rules often detect problems that individual field validators
    cannot detect.
    """
    results = []

    status = normalize_status(record.get("status"))
    credit_limit = record.get("credit_limit")

    if status == "inactive" and credit_limit not in (None, 0):
        results.append(
            ValidationResult(
                rule_name="inactive_credit_limit",
                passed=False,
                message="Inactive customer should not have an active credit limit",
                field="credit_limit",
                value=credit_limit,
            )
        )
    else:
        results.append(
            ValidationResult(
                rule_name="inactive_credit_limit",
                passed=True,
                message="Status and credit limit are compatible",
            )
        )

    signup_date_value = record.get("signup_date")
    updated_at_value = record.get("updated_at")

    try:
        signup_date = datetime.strptime(
            str(signup_date_value),
            "%Y-%m-%d",
        )

        updated_at = datetime.fromisoformat(str(updated_at_value))

        passed = updated_at >= signup_date

        results.append(
            ValidationResult(
                rule_name="update_after_signup",
                passed=passed,
                message=(
                    "Update timestamp follows signup date"
                    if passed
                    else "Update timestamp precedes signup date"
                ),
            )
        )
    except (TypeError, ValueError):
        results.append(
            ValidationResult(
                rule_name="update_after_signup",
                passed=False,
                message="Could not compare signup and update timestamps",
            )
        )

    return results


# ============================================================================
# 13. ANOMALOUS RECORDS
# ============================================================================

def z_scores(values: list[float]) -> list[float]:
    """
    Calculate population z-scores.

    z = (x - mean) / population_standard_deviation

    A large absolute z-score can indicate an unusual observation.

    Z-scores are not universally suitable. They can be distorted by skewed
    distributions and extreme values.
    """
    if not values:
        return []

    average = mean(values)
    deviation = pstdev(values)

    if deviation == 0:
        return [0.0] * len(values)

    return [
        (value - average) / deviation
        for value in values
    ]


def iqr_bounds(values: list[float]) -> tuple[float, float]:
    """
    Calculate Tukey IQR outlier bounds.

    Lower bound = Q1 - 1.5 * IQR
    Upper bound = Q3 + 1.5 * IQR

    This implementation uses linear interpolation.
    """
    if not values:
        raise ValueError("At least one value is required")

    sorted_values = sorted(values)

    def percentile(p: float) -> float:
        position = (len(sorted_values) - 1) * p
        lower = math.floor(position)
        upper = math.ceil(position)

        if lower == upper:
            return sorted_values[lower]

        weight = position - lower

        return (
            sorted_values[lower] * (1 - weight)
            + sorted_values[upper] * weight
        )

    q1 = percentile(0.25)
    q3 = percentile(0.75)
    iqr = q3 - q1

    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def detect_iqr_outliers(values: list[float]) -> list[float]:
    """Return observations outside the IQR bounds."""
    if not values:
        return []

    lower, upper = iqr_bounds(values)

    return [
        value
        for value in values
        if value < lower or value > upper
    ]


def robust_median_absolute_deviation(values: list[float]) -> list[float]:
    """
    Calculate modified scores using median absolute deviation.

    MAD is often more robust than standard deviation in the presence of
    extreme observations.
    """
    if not values:
        return []

    center = median(values)
    deviations = [abs(value - center) for value in values]
    mad = median(deviations)

    if mad == 0:
        return [0.0] * len(values)

    return [
        0.6745 * (value - center) / mad
        for value in values
    ]


def demonstrate_anomalies(records: list[dict[str, Any]]) -> None:
    section("12. ANOMALOUS RECORDS")

    credit_limits = [
        record["credit_limit"]
        for record in records
        if isinstance(record.get("credit_limit"), (int, float))
    ]

    print("Credit limits:", credit_limits)
    print("IQR outliers:", detect_iqr_outliers(credit_limits))

    scores = z_scores([float(value) for value in credit_limits])

    print("Z-scores:")
    for value, score in zip(credit_limits, scores):
        print(f"  {value:8.2f} -> {score:7.3f}")

    print("\nAn anomaly is not automatically an error.")
    print("A high transaction may be legitimate, fraudulent, exceptional, or malformed.")


# ============================================================================
# 14. DATA STANDARDIZATION
# ============================================================================

def standardize_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Produce a canonical representation.

    Standardization improves consistency but does not prove accuracy.
    """
    standardized = dict(record)

    if isinstance(standardized.get("name"), str):
        standardized["name"] = " ".join(
            standardized["name"].strip().split()
        )

    standardized["email"] = normalize_email(standardized.get("email"))
    standardized["status"] = normalize_status(standardized.get("status"))

    if isinstance(standardized.get("country"), str):
        standardized["country"] = (
            standardized["country"].strip().title()
        )

    return standardized


def demonstrate_standardization(records: list[dict[str, Any]]) -> None:
    section("13. STANDARDIZATION")

    for record in records:
        before = record.get("status")
        after = standardize_record(record).get("status")

        if before != after:
            print(
                f"{record.get('customer_id')}: "
                f"{before!r} -> {after!r}"
            )


# ============================================================================
# 15. DATA QUALITY SCORING
# ============================================================================

@dataclass
class QualityMetric:
    name: str
    score: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")

        if self.weight < 0:
            raise ValueError("Weight cannot be negative")


def weighted_quality_score(metrics: Iterable[QualityMetric]) -> float:
    """Calculate a weighted quality score."""
    metrics = list(metrics)

    total_weight = sum(metric.weight for metric in metrics)

    if total_weight == 0:
        return 0.0

    return sum(
        metric.score * metric.weight
        for metric in metrics
    ) / total_weight


def calculate_quality_metrics(
    records: list[dict[str, Any]],
) -> list[QualityMetric]:
    """Create a multi-dimensional quality score."""
    required_fields = [
        "customer_id",
        "name",
        "email",
        "age",
        "country",
        "signup_date",
        "status",
    ]

    completeness = completeness_rate(records, required_fields)
    uniqueness = uniqueness_rate(records, ["customer_id"])

    validation_results = [
        validate_record(record, build_validation_rules())
        for record in records
    ]

    validation_total = sum(len(results) for results in validation_results)
    validation_passed = sum(
        result.passed
        for results in validation_results
        for result in results
    )

    validity = (
        validation_passed / validation_total
        if validation_total
        else 1.0
    )

    consistency_results = [
        consistency_check_status(record)
        for record in records
    ]

    consistency = (
        sum(result.passed for result in consistency_results)
        / len(consistency_results)
        if consistency_results
        else 1.0
    )

    reference = {
        record["customer_id"]: {"name": record["name"]}
        for record in records
        if record.get("customer_id")
    }

    accuracy = accuracy_against_reference(
        records,
        reference,
        "customer_id",
        ["name"],
    )

    return [
        QualityMetric("completeness", completeness, 1.0),
        QualityMetric("uniqueness", uniqueness, 1.0),
        QualityMetric("validity", validity, 1.5),
        QualityMetric("consistency", consistency, 1.0),
        QualityMetric("accuracy", accuracy, 1.5),
    ]


def demonstrate_quality_score(records: list[dict[str, Any]]) -> None:
    section("14. MULTI-DIMENSIONAL QUALITY SCORE")

    metrics = calculate_quality_metrics(records)

    for metric in metrics:
        print(
            f"{metric.name:15} "
            f"{metric.score:.2%} "
            f"weight={metric.weight}"
        )

    score = weighted_quality_score(metrics)

    print(f"\nWeighted quality score: {score:.2%}")

    print("\nImportant:")
    print("A composite score should never hide critical failures.")
    print("For example, 99% quality does not compensate for a broken primary key.")


# ============================================================================
# 16. DATA QUALITY RULE ENGINE
# ============================================================================

class DataQualityEngine:
    """Execute quality rules against records and aggregate results."""

    def __init__(self, rules: list[ValidationRule]):
        self.rules = rules

    def run(
        self,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        results_by_record = []

        for record in records:
            results = validate_record(record, self.rules)

            results_by_record.append(
                {
                    "record": record,
                    "results": results,
                }
            )

        total = sum(
            len(item["results"])
            for item in results_by_record
        )

        passed = sum(
            result.passed
            for item in results_by_record
            for result in item["results"]
        )

        failures_by_rule = Counter(
            result.rule_name
            for item in results_by_record
            for result in item["results"]
            if not result.passed
        )

        return {
            "records": len(records),
            "rules": len(self.rules),
            "total_checks": total,
            "passed_checks": passed,
            "failed_checks": total - passed,
            "pass_rate": passed / total if total else 1.0,
            "failures_by_rule": dict(failures_by_rule),
            "details": results_by_record,
        }


def demonstrate_quality_engine(records: list[dict[str, Any]]) -> None:
    section("15. DATA QUALITY RULE ENGINE")

    engine = DataQualityEngine(build_validation_rules())
    report = engine.run(records)

    print(f"Records: {report['records']}")
    print(f"Rules: {report['rules']}")
    print(f"Checks: {report['total_checks']}")
    print(f"Passed: {report['passed_checks']}")
    print(f"Failed: {report['failed_checks']}")
    print(f"Pass rate: {report['pass_rate']:.2%}")

    print("\nMost frequent rule failures:")

    for rule_name, count in sorted(
        report["failures_by_rule"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"  {rule_name}: {count}")


# ============================================================================
# 17. DATA QUALITY REMEDIATION
# ============================================================================

def impute_missing_age(
    record: dict[str, Any],
    default_age: Optional[int] = None,
) -> dict[str, Any]:
    """
    Example remediation.

    Missing values should not be filled blindly. The appropriate treatment
    depends on why the data is missing and how the field is used.
    """
    repaired = dict(record)

    if is_missing(repaired.get("age")) and default_age is not None:
        repaired["age"] = default_age

    return repaired


def repair_status(record: dict[str, Any]) -> dict[str, Any]:
    """Repair capitalization without inventing missing business information."""
    repaired = dict(record)
    repaired["status"] = normalize_status(repaired.get("status"))
    return repaired


def repair_dataset(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Apply conservative repairs.

    Notice that invalid emails and impossible ages are not fabricated.
    They should generally be quarantined or sent for correction.
    """
    repaired_records = []

    for record in records:
        repaired = standardize_record(record)
        repaired = repair_status(repaired)
        repaired_records.append(repaired)

    return repaired_records


def demonstrate_remediation(records: list[dict[str, Any]]) -> None:
    section("16. REMEDIATION")

    repaired = repair_dataset(records)

    for before, after in zip(records, repaired):
        if before != after:
            print(f"{before.get('customer_id')}: standardized")


# ============================================================================
# 18. QUARANTINING INVALID RECORDS
# ============================================================================

@dataclass
class QualityDecision:
    accepted: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    reasons: dict[str, list[str]] = field(default_factory=dict)


def partition_records(
    records: list[dict[str, Any]],
    rules: list[ValidationRule],
) -> QualityDecision:
    """
    Separate valid and invalid records.

    Production pipelines commonly use quarantine instead of silently deleting
    bad records.
    """
    decision = QualityDecision()

    for record in records:
        results = validate_record(record, rules)
        failures = [
            result.rule_name
            for result in results
            if not result.passed
        ]

        identifier = str(
            record.get("customer_id")
            or uuid.uuid4()
        )

        if failures:
            decision.rejected.append(record)
            decision.reasons[identifier] = failures
        else:
            decision.accepted.append(record)

    return decision


def demonstrate_quarantine(records: list[dict[str, Any]]) -> None:
    section("17. QUARANTINING INVALID RECORDS")

    decision = partition_records(records, build_validation_rules())

    print(f"Accepted records: {len(decision.accepted)}")
    print(f"Rejected records: {len(decision.rejected)}")

    for identifier, reasons in decision.reasons.items():
        print(f"  {identifier}: {', '.join(reasons)}")


# ============================================================================
# 19. DUPLICATE REMEDIATION
# ============================================================================

def deduplicate_keep_first(
    records: list[dict[str, Any]],
    key_fields: Iterable[str],
) -> list[dict[str, Any]]:
    """
    Keep the first occurrence of each key.

    This is only safe when the first record is known to be the preferred
    survivor. Real systems often need survivorship rules.
    """
    fields = list(key_fields)
    seen = set()
    result = []

    for record in records:
        key = tuple(record.get(field) for field in fields)

        if key not in seen:
            seen.add(key)
            result.append(record)

    return result


def deduplicate_by_latest_update(
    records: list[dict[str, Any]],
    key_field: str,
    timestamp_field: str,
) -> list[dict[str, Any]]:
    """
    Survivorship rule: keep the latest record for each business key.
    """
    latest: dict[Any, dict[str, Any]] = {}

    for record in records:
        key = record.get(key_field)
        current_timestamp = parse_timestamp(record.get(timestamp_field))

        if current_timestamp is None:
            continue

        previous = latest.get(key)

        if previous is None:
            latest[key] = record
            continue

        previous_timestamp = parse_timestamp(
            previous.get(timestamp_field)
        )

        if previous_timestamp is None or current_timestamp > previous_timestamp:
            latest[key] = record

    return list(latest.values())


# ============================================================================
# 20. FUZZY DUPLICATE CONCEPTS
# ============================================================================

def normalize_name_for_matching(name: Any) -> Optional[str]:
    """
    Basic deterministic normalization for candidate duplicate detection.

    This is not full fuzzy matching. Removing punctuation and whitespace can
    improve candidate generation while still requiring human or business-rule
    confirmation.
    """
    if is_missing(name):
        return None

    normalized = re.sub(r"[^a-z0-9]", "", str(name).lower())

    return normalized or None


def simple_name_similarity(first: Any, second: Any) -> float:
    """
    Calculate Jaccard similarity over character sets.

    This deliberately demonstrates a simple educational technique, not a
    production-grade entity-resolution algorithm.
    """
    first_normalized = normalize_name_for_matching(first)
    second_normalized = normalize_name_for_matching(second)

    if not first_normalized or not second_normalized:
        return 0.0

    first_set = set(first_normalized)
    second_set = set(second_normalized)

    union = first_set | second_set

    return (
        len(first_set & second_set) / len(union)
        if union
        else 1.0
    )


def demonstrate_duplicate_matching(records: list[dict[str, Any]]) -> None:
    section("18. CANDIDATE DUPLICATE MATCHING")

    pairs_checked = 0

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            similarity = simple_name_similarity(
                records[i].get("name"),
                records[j].get("name"),
            )

            if similarity >= 0.8:
                print(
                    f"Possible duplicate: "
                    f"{records[i].get('name')} / "
                    f"{records[j].get('name')} "
                    f"similarity={similarity:.2f}"
                )

            pairs_checked += 1

    print(f"Candidate pairs examined: {pairs_checked}")

    print("\nCaution:")
    print("Similarity is evidence, not proof of identity.")
    print("Entity resolution should consider multiple attributes.")


# ============================================================================
# 21. TYPE VALIDATION
# ============================================================================

def validate_type(
    record: dict[str, Any],
    field_name: str,
    expected_type: type,
) -> ValidationResult:
    """Validate Python-level type compatibility."""
    value = record.get(field_name)

    passed = is_missing(value) or isinstance(value, expected_type)

    return ValidationResult(
        rule_name=f"type:{field_name}",
        passed=passed,
        message=(
            f"{field_name} has expected type"
            if passed
            else f"{field_name} must be {expected_type.__name__}"
        ),
        field=field_name,
        value=value,
    )


# ============================================================================
# 22. NUMERIC PRECISION AND DOMAIN RULES
# ============================================================================

def parse_decimal(value: Any) -> Optional[Decimal]:
    """Safely convert numeric input to Decimal."""
    if is_missing(value):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def validate_currency_amount(
    record: dict[str, Any],
    field_name: str,
) -> ValidationResult:
    """
    Validate a monetary amount.

    Decimal is preferable to binary floating point for many financial
    calculations because it provides decimal arithmetic semantics.
    """
    value = record.get(field_name)
    amount = parse_decimal(value)

    passed = amount is not None and amount >= 0

    return ValidationResult(
        rule_name=f"currency:{field_name}",
        passed=passed,
        message=(
            "Valid non-negative monetary amount"
            if passed
            else "Invalid monetary amount"
        ),
        field=field_name,
        value=value,
    )


# ============================================================================
# 23. BUSINESS RULES VERSUS TECHNICAL RULES
# ============================================================================

def demonstrate_rule_categories() -> None:
    section("19. TECHNICAL RULES VERSUS BUSINESS RULES")

    print("Technical validation:")
    print("  - Type must be integer")
    print("  - Email must match a syntax pattern")
    print("  - Date must parse")
    print("  - Primary key must be non-null")

    print("\nBusiness validation:")
    print("  - Customer must be at least 18 for a particular product")
    print("  - Credit limit must depend on risk category")
    print("  - Shipment date cannot precede order date")
    print("  - Closed accounts cannot receive new transactions")

    print("\nA value can pass technical validation while failing business validation.")


# ============================================================================
# 24. NULL SEMANTICS
# ============================================================================

def demonstrate_null_semantics() -> None:
    section("20. NULL AND UNKNOWN SEMANTICS")

    values = [None, 0, False, "", "unknown"]

    for value in values:
        print(
            f"value={value!r:10} "
            f"is_missing={is_missing(value)} "
            f"equals_zero={value == 0}"
        )

    print("\nMissingness is not equivalent to zero, false, empty, or unknown.")
    print("Database systems can also implement three-valued logic involving NULL.")


# ============================================================================
# 25. QUALITY DIMENSION COMPARISONS
# ============================================================================

def demonstrate_dimension_comparison() -> None:
    section("21. IMPORTANT DISTINCTIONS")

    comparisons = [
        (
            "Accuracy vs Validity",
            "Accuracy asks whether data reflects reality; validity asks whether it follows rules.",
        ),
        (
            "Completeness vs Uniqueness",
            "Completeness concerns presence; uniqueness concerns unintended repetition.",
        ),
        (
            "Consistency vs Accuracy",
            "Consistent data can still be consistently wrong.",
        ),
        (
            "Timeliness vs Accuracy",
            "Fresh data can still be inaccurate; accurate historical data can be stale.",
        ),
        (
            "Anomaly vs Error",
            "An unusual record may be legitimate and should not automatically be deleted.",
        ),
        (
            "Standardization vs Correction",
            "Standardization changes representation; correction changes an incorrect value.",
        ),
    ]

    for title, explanation in comparisons:
        print(f"{title}: {explanation}")


# ============================================================================
# 26. DATA QUALITY MONITORING
# ============================================================================

@dataclass
class QualityObservation:
    timestamp: datetime
    metric_name: str
    score: float


class QualityMonitor:
    """Store metric observations and detect threshold violations."""

    def __init__(self, thresholds: dict[str, float]):
        self.thresholds = thresholds
        self.observations: list[QualityObservation] = []

    def record(
        self,
        metric_name: str,
        score: float,
        timestamp: datetime,
    ) -> None:
        if not 0 <= score <= 1:
            raise ValueError("Score must be between 0 and 1")

        self.observations.append(
            QualityObservation(
                timestamp=timestamp,
                metric_name=metric_name,
                score=score,
            )
        )

    def alerts(self) -> list[QualityObservation]:
        """Return observations below configured thresholds."""
        return [
            observation
            for observation in self.observations
            if observation.score
            < self.thresholds.get(observation.metric_name, 0.0)
        ]


def demonstrate_monitoring(records: list[dict[str, Any]]) -> None:
    section("22. QUALITY MONITORING")

    metrics = calculate_quality_metrics(records)

    monitor = QualityMonitor(
        thresholds={
            "completeness": 0.95,
            "uniqueness": 0.99,
            "validity": 0.95,
            "consistency": 0.95,
            "accuracy": 0.98,
        }
    )

    now = datetime(2026, 9, 6, 12, 0, 0)

    for metric in metrics:
        monitor.record(metric.name, metric.score, now)

    alerts = monitor.alerts()

    print(f"Metrics monitored: {len(metrics)}")
    print(f"Threshold alerts: {len(alerts)}")

    for alert in alerts:
        threshold = monitor.thresholds[alert.metric_name]
        print(
            f"  ALERT {alert.metric_name}: "
            f"{alert.score:.2%} < {threshold:.2%}"
        )


# ============================================================================
# 27. DATA QUALITY DIMENSION DRIFT
# ============================================================================

def percentage_change(old: float, new: float) -> float:
    """Calculate relative percentage change."""
    if old == 0:
        return math.inf if new != 0 else 0.0

    return (new - old) / old


def detect_quality_regression(
    previous_score: float,
    current_score: float,
    maximum_allowed_drop: float,
) -> bool:
    """Detect whether a quality score dropped beyond tolerance."""
    drop = previous_score - current_score
    return drop > maximum_allowed_drop


def demonstrate_quality_drift() -> None:
    section("23. QUALITY DRIFT")

    historical = 0.985
    current = 0.941

    change = percentage_change(historical, current)

    print(f"Historical score: {historical:.2%}")
    print(f"Current score:    {current:.2%}")
    print(f"Relative change:  {change:.2%}")

    regression = detect_quality_regression(
        historical,
        current,
        maximum_allowed_drop=0.02,
    )

    print(f"Significant regression: {regression}")


# ============================================================================
# 28. DATA QUALITY TESTING
# ============================================================================

def assert_no_duplicate_keys(
    records: list[dict[str, Any]],
    key_fields: list[str],
) -> None:
    """Raise AssertionError if business keys are duplicated."""
    duplicates = duplicate_records(records, key_fields)

    assert not duplicates, f"Duplicate keys found: {duplicates}"


def assert_required_fields_present(
    records: list[dict[str, Any]],
    required_fields: list[str],
) -> None:
    """Raise AssertionError if required values are missing."""
    failures = []

    for index, record in enumerate(records):
        for field_name in required_fields:
            if is_missing(record.get(field_name)):
                failures.append((index, field_name))

    assert not failures, f"Missing required values: {failures}"


def demonstrate_testing() -> None:
    section("24. DATA QUALITY TESTING")

    clean_records = [
        {
            "customer_id": "C001",
            "name": "Alice",
            "email": "alice@example.com",
        },
        {
            "customer_id": "C002",
            "name": "Bob",
            "email": "bob@example.com",
        },
    ]

    assert_no_duplicate_keys(
        clean_records,
        ["customer_id"],
    )

    assert_required_fields_present(
        clean_records,
        ["customer_id", "name", "email"],
    )

    print("Data-quality assertions passed.")


# ============================================================================
# 29. PROPERTY-BASED THINKING
# ============================================================================

def test_quality_invariants() -> None:
    section("25. QUALITY INVARIANTS")

    records = [
        {"customer_id": "C001", "status": "active"},
        {"customer_id": "C002", "status": "inactive"},
    ]

    # Invariant 1: IDs should be unique.
    ids = [record["customer_id"] for record in records]
    assert len(ids) == len(set(ids))

    # Invariant 2: Status belongs to an allowed domain.
    allowed = {"active", "inactive", "suspended"}

    assert all(
        record["status"] in allowed
        for record in records
    )

    print("Key quality invariants hold.")


# ============================================================================
# 30. PERFORMANCE CONSIDERATIONS
# ============================================================================

def demonstrate_complexity() -> None:
    section("26. PERFORMANCE CONSIDERATIONS")

    print("Common operations and typical complexity:")
    print("  Set-based duplicate detection       O(n)")
    print("  Hash-based key lookup               O(1) average per lookup")
    print("  Sorting for IQR                     O(n log n)")
    print("  Pairwise fuzzy matching             O(n^2)")
    print("  Column profiling                    O(n) per column")
    print("  Referential integrity using a set  O(n + m)")

    print("\nFor large datasets:")
    print("  - Prefer database constraints for database-resident data.")
    print("  - Use indexed keys.")
    print("  - Stream records instead of loading everything into memory.")
    print("  - Partition large workloads.")
    print("  - Avoid unnecessary pairwise comparisons.")
    print("  - Generate candidate duplicate pairs using blocking keys.")


# ============================================================================
# 31. STREAMING QUALITY CHECK
# ============================================================================

def streaming_missing_rate(
    records: Iterable[dict[str, Any]],
    field_name: str,
) -> float:
    """
    Calculate missingness without requiring a list in memory.

    This demonstrates a streaming-friendly pattern.
    """
    total = 0
    missing = 0

    for record in records:
        total += 1

        if is_missing(record.get(field_name)):
            missing += 1

    return missing / total if total else 0.0


def demonstrate_streaming(records: list[dict[str, Any]]) -> None:
    section("27. STREAMING-STYLE QUALITY CHECKS")

    rate = streaming_missing_rate(
        iter(records),
        "email",
    )

    print(f"Email missing rate: {rate:.2%}")
    print("The function processes one record at a time.")


# ============================================================================
# 32. DATA CONTRACTS
# ============================================================================

@dataclass(frozen=True)
class DataContract:
    """
    A simplified data contract.

    A real contract may define schema, ownership, freshness, semantics,
    allowed values, quality thresholds, privacy requirements, and SLAs.
    """

    name: str
    required_fields: tuple[str, ...]
    allowed_statuses: frozenset[str]
    max_age: timedelta


def validate_contract(
    record: dict[str, Any],
    contract: DataContract,
    reference_time: datetime,
) -> list[str]:
    """Validate a record against a simplified data contract."""
    failures = []

    for field_name in contract.required_fields:
        if is_missing(record.get(field_name)):
            failures.append(f"missing:{field_name}")

    status = normalize_status(record.get("status"))

    if status not in contract.allowed_statuses:
        failures.append("invalid:status")

    updated_at = parse_timestamp(record.get("updated_at"))

    if updated_at is None:
        failures.append("invalid:updated_at")
    elif reference_time - updated_at > contract.max_age:
        failures.append("stale:updated_at")

    return failures


def demonstrate_data_contract(records: list[dict[str, Any]]) -> None:
    section("28. DATA CONTRACTS")

    contract = DataContract(
        name="customer_master",
        required_fields=(
            "customer_id",
            "name",
            "email",
            "status",
            "updated_at",
        ),
        allowed_statuses=frozenset(
            {"active", "inactive", "suspended"}
        ),
        max_age=timedelta(days=3),
    )

    reference_time = datetime(2026, 9, 6, 12, 0, 0)

    for record in records:
        failures = validate_contract(
            record,
            contract,
            reference_time,
        )

        if failures:
            print(
                f"{record.get('customer_id')}: "
                f"{', '.join(failures)}"
            )


# ============================================================================
# 33. ROOT-CAUSE ANALYSIS
# ============================================================================

@dataclass
class QualityIssue:
    dimension: str
    symptom: str
    likely_causes: list[str]
    remediation: list[str]


def demonstrate_root_cause_analysis() -> None:
    section("29. ROOT-CAUSE ANALYSIS")

    issue = QualityIssue(
        dimension="completeness",
        symptom="Customer email missing",
        likely_causes=[
            "Source system did not collect email",
            "ETL mapping dropped the field",
            "Transformation converted a value to NULL",
            "Upstream schema changed",
        ],
        remediation=[
            "Trace lineage to the source",
            "Inspect ingestion logs",
            "Compare source and target counts",
            "Fix mapping or source collection",
        ],
    )

    print(f"Dimension: {issue.dimension}")
    print(f"Symptom:   {issue.symptom}")

    print("\nPossible causes:")
    for cause in issue.likely_causes:
        print(f"  - {cause}")

    print("\nPossible remediation:")
    for action in issue.remediation:
        print(f"  - {action}")

    print("\nA data-quality rule identifies a symptom; root-cause analysis explains why.")


# ============================================================================
# 34. DATA LINEAGE CONCEPT
# ============================================================================

@dataclass
class LineageEvent:
    source: str
    transformation: str
    destination: str


def demonstrate_lineage() -> None:
    section("30. DATA LINEAGE")

    events = [
        LineageEvent(
            source="CRM",
            transformation="Extract customer records",
            destination="Raw customer table",
        ),
        LineageEvent(
            source="Raw customer table",
            transformation="Normalize and validate",
            destination="Curated customer table",
        ),
        LineageEvent(
            source="Curated customer table",
            transformation="Aggregate",
            destination="Customer analytics",
        ),
    ]

    for event in events:
        print(
            f"{event.source} "
            f"--[{event.transformation}]--> "
            f"{event.destination}"
        )

    print("\nLineage helps determine where a quality defect originated.")


# ============================================================================
# 35. SECURITY AND DATA QUALITY
# ============================================================================

def demonstrate_security_considerations() -> None:
    section("31. SECURITY CONSIDERATIONS")

    print("Data-quality systems should consider:")
    print("  - Access control")
    print("  - Sensitive-data exposure in logs")
    print("  - Encryption in transit and at rest")
    print("  - Audit trails for corrections")
    print("  - Least-privilege access")
    print("  - Validation against injection and malformed input")
    print("  - Retention and deletion requirements")
    print("  - Protection of production data during testing")

    print("\nNever log complete passwords, authentication tokens, payment-card data,")
    print("or other sensitive values merely to diagnose a quality failure.")


# ============================================================================
# 36. PRODUCTION DESIGN
# ============================================================================

def demonstrate_production_design() -> None:
    section("32. PRODUCTION DESIGN PRINCIPLES")

    principles = [
        "Define quality requirements before measuring quality.",
        "Assign ownership to data domains and critical fields.",
        "Validate as early as practical without duplicating controls unnecessarily.",
        "Prefer prevention over downstream correction.",
        "Separate raw, validated, quarantined, and curated data.",
        "Record quality metrics over time.",
        "Alert on meaningful thresholds and regressions.",
        "Make remediation traceable and auditable.",
        "Do not silently discard invalid records.",
        "Treat critical integrity constraints as hard failures.",
        "Document the reason for every automated correction.",
        "Distinguish data-quality errors from legitimate exceptional events.",
    ]

    for number, principle in enumerate(principles, 1):
        print(f"{number:2}. {principle}")


# ============================================================================
# 37. END-TO-END DATA QUALITY PIPELINE
# ============================================================================

@dataclass
class PipelineResult:
    raw_count: int
    accepted_count: int
    rejected_count: int
    duplicate_count: int
    quality_score: float
    validation_pass_rate: float
    rejected_records: list[dict[str, Any]]


class DataQualityPipeline:
    """
    A simplified end-to-end quality pipeline.

    Stages:
        1. Standardization
        2. Profiling
        3. Duplicate detection
        4. Validation
        5. Quarantine
        6. Quality scoring
        7. Reporting
    """

    def __init__(self) -> None:
        self.rules = build_validation_rules()

    def process(
        self,
        records: list[dict[str, Any]],
    ) -> PipelineResult:
        raw_count = len(records)

        standardized = [
            standardize_record(record)
            for record in records
        ]

        duplicates = duplicate_records(
            standardized,
            ["customer_id"],
        )

        duplicate_count = sum(
            len(indexes) - 1
            for indexes in duplicates.values()
        )

        decision = partition_records(
            standardized,
            self.rules,
        )

        metrics = calculate_quality_metrics(standardized)

        score = weighted_quality_score(metrics)

        engine = DataQualityEngine(self.rules)
        report = engine.run(standardized)

        return PipelineResult(
            raw_count=raw_count,
            accepted_count=len(decision.accepted),
            rejected_count=len(decision.rejected),
            duplicate_count=duplicate_count,
            quality_score=score,
            validation_pass_rate=report["pass_rate"],
            rejected_records=decision.rejected,
        )


def demonstrate_end_to_end_pipeline(
    records: list[dict[str, Any]],
) -> None:
    section("33. END-TO-END DATA QUALITY PIPELINE")

    pipeline = DataQualityPipeline()
    result = pipeline.process(records)

    print(f"Raw records:          {result.raw_count}")
    print(f"Accepted records:     {result.accepted_count}")
    print(f"Rejected records:     {result.rejected_count}")
    print(f"Duplicate instances:  {result.duplicate_count}")
    print(f"Validation pass rate: {result.validation_pass_rate:.2%}")
    print(f"Quality score:        {result.quality_score:.2%}")


# ============================================================================
# 38. EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    section("34. EDGE CASES")

    edge_values = [
        None,
        "",
        " ",
        "NULL",
        "N/A",
        0,
        -0.0,
        float("nan"),
        float("inf"),
        "2026-02-29",
        "2024-02-29",
        "alice@example.com ",
        " ALICE@EXAMPLE.COM ",
    ]

    for value in edge_values:
        print(
            f"{value!r:30} "
            f"missing={is_missing(value)}"
        )

    print("\nSpecial numeric values require explicit handling.")
    print("NaN is not equal to itself:")
    nan = float("nan")
    print(f"nan == nan -> {nan == nan}")

    print("\nA date can be correctly formatted but semantically invalid:")
    print("'2026-02-29' has the correct YYYY-MM-DD shape but 2026 is not a leap year.")

    print("\nA normalized email may improve matching while the mailbox itself may not exist.")


# ============================================================================
# 39. COMMON MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    section("35. COMMON DATA QUALITY MISTAKES")

    mistakes = [
        "Treating validity as proof of accuracy.",
        "Replacing every missing value with zero.",
        "Deleting anomalies without investigation.",
        "Removing duplicates using only exact row equality.",
        "Ignoring business keys.",
        "Using a single quality score without dimension-level metrics.",
        "Changing production data without an audit trail.",
        "Hard-coding reference dates when freshness must be dynamic.",
        "Logging sensitive values during validation failures.",
        "Using fuzzy matching without measuring false positives.",
        "Ignoring schema changes upstream.",
        "Checking quality only after data reaches reporting systems.",
    ]

    for number, mistake in enumerate(mistakes, 1):
        print(f"{number:2}. {mistake}")


# ============================================================================
# 40. PRACTICAL APPLICATIONS
# ============================================================================

def demonstrate_applications() -> None:
    section("36. REAL-WORLD APPLICATIONS")

    applications = {
        "Banking": [
            "Customer identity completeness",
            "Transaction validity",
            "Account referential integrity",
            "Fraud anomaly detection",
        ],
        "Healthcare": [
            "Patient-record completeness",
            "Code validity",
            "Duplicate patient detection",
            "Clinical-data consistency",
        ],
        "E-commerce": [
            "Product catalog validity",
            "Inventory consistency",
            "Customer duplicate detection",
            "Order integrity",
        ],
        "Data Engineering": [
            "ETL validation",
            "Schema checks",
            "Pipeline freshness",
            "Data-contract enforcement",
        ],
        "Machine Learning": [
            "Missing-feature detection",
            "Label-quality checks",
            "Distribution drift",
            "Outlier investigation",
        ],
        "Government": [
            "Citizen-record consistency",
            "Duplicate records",
            "Reference-data validation",
            "Data lineage and auditability",
        ],
    }

    for domain, uses in applications.items():
        print(f"\n{domain}:")
        for use in uses:
            print(f"  - {use}")


# ============================================================================
# 41. QUALITY DASHBOARD REPRESENTATION
# ============================================================================

def print_quality_dashboard(records: list[dict[str, Any]]) -> None:
    section("37. QUALITY DASHBOARD")

    metrics = calculate_quality_metrics(records)

    width = 40

    for metric in metrics:
        filled = round(metric.score * width)
        bar = "#" * filled + "-" * (width - filled)

        print(
            f"{metric.name:15} "
            f"[{bar}] "
            f"{metric.score:.1%}"
        )


# ============================================================================
# 42. SAMPLE OUTPUT DATA GENERATION
# ============================================================================

def generate_synthetic_transactions(
    count: int,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Generate deterministic transaction-like data without external packages.

    This supports experimentation with anomaly detection.
    """
    import random

    random_generator = random.Random(seed)

    records = []

    for index in range(count):
        amount = round(
            random_generator.lognormvariate(
                math.log(100),
                0.8,
            ),
            2,
        )

        records.append(
            {
                "transaction_id": f"T{index + 1:05d}",
                "amount": amount,
            }
        )

    return records


def demonstrate_synthetic_anomaly_detection() -> None:
    section("38. SYNTHETIC ANOMALY DETECTION")

    transactions = generate_synthetic_transactions(100)

    amounts = [
        transaction["amount"]
        for transaction in transactions
    ]

    anomalies = detect_iqr_outliers(amounts)

    print(f"Transactions: {len(transactions)}")
    print(f"IQR anomalies detected: {len(anomalies)}")

    if anomalies:
        print("Largest detected values:")
        for value in sorted(anomalies, reverse=True)[:5]:
            print(f"  {value:.2f}")


# ============================================================================
# 43. DATA QUALITY SCORECARD
# ============================================================================

def build_scorecard(records: list[dict[str, Any]]) -> dict[str, float]:
    """Return dimension-level scores for reporting systems."""
    metrics = calculate_quality_metrics(records)

    return {
        metric.name: metric.score
        for metric in metrics
    }


def demonstrate_scorecard(records: list[dict[str, Any]]) -> None:
    section("39. QUALITY SCORECARD")

    scorecard = build_scorecard(records)

    for dimension, score in scorecard.items():
        print(f"{dimension:15}: {score:.2%}")


# ============================================================================
# 44. DECISION LOGIC FOR QUALITY FAILURES
# ============================================================================

def classify_failure(
    dimension: str,
    severity: str,
) -> str:
    """
    Map a quality failure to a high-level operational response.

    This is intentionally simple; production severity matrices are domain
    specific.
    """
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError("Invalid severity")

    if severity == "critical":
        return "block_pipeline"

    if severity == "high":
        return "quarantine_and_alert"

    if severity == "medium":
        return "repair_or_review"

    return "monitor"


def demonstrate_failure_classification() -> None:
    section("40. QUALITY FAILURE CLASSIFICATION")

    examples = [
        ("referential_integrity", "critical"),
        ("invalid_email", "medium"),
        ("slight_staleness", "low"),
        ("duplicate_primary_key", "critical"),
    ]

    for dimension, severity in examples:
        response = classify_failure(dimension, severity)

        print(
            f"{dimension:25} "
            f"{severity:8} -> {response}"
        )


# ============================================================================
# 45. GOVERNANCE
# ============================================================================

def demonstrate_governance() -> None:
    section("41. DATA QUALITY GOVERNANCE")

    governance_components = [
        "Data owner: accountable for the business meaning and quality requirements.",
        "Data steward: manages definitions, standards, and operational quality.",
        "Data engineer: implements ingestion and transformation controls.",
        "Analyst: identifies downstream quality effects.",
        "Domain expert: validates business semantics.",
        "Platform team: provides monitoring, storage, and observability.",
        "Security/privacy team: protects sensitive information.",
    ]

    for component in governance_components:
        print(f"- {component}")


# ============================================================================
# 46. ADVANCED CONCEPT: DIMENSION INTERACTIONS
# ============================================================================

def demonstrate_dimension_interactions() -> None:
    section("42. INTERACTIONS AMONG QUALITY DIMENSIONS")

    print(
        "A single defect may affect multiple dimensions."
    )

    examples = [
        (
            "Wrong customer email",
            ["accuracy", "validity"],
        ),
        (
            "Missing customer email",
            ["completeness"],
        ),
        (
            "Two rows for the same customer",
            ["uniqueness", "integrity"],
        ),
        (
            "Old exchange rate",
            ["timeliness", "accuracy"],
        ),
        (
            "Different country codes for the same customer",
            ["consistency"],
        ),
        (
            "Order references nonexistent customer",
            ["integrity", "validity"],
        ),
    ]

    for defect, dimensions in examples:
        print(f"{defect:50} -> {', '.join(dimensions)}")


# ============================================================================
# 47. ADVANCED CONCEPT: QUALITY VERSUS BUSINESS IMPACT
# ============================================================================

@dataclass
class QualityImpact:
    issue: str
    affected_records: int
    business_criticality: int

    @property
    def priority_score(self) -> int:
        """Simple prioritization metric."""
        return self.affected_records * self.business_criticality


def demonstrate_prioritization() -> None:
    section("43. PRIORITIZING QUALITY ISSUES")

    issues = [
        QualityImpact(
            issue="Missing optional marketing preference",
            affected_records=10000,
            business_criticality=1,
        ),
        QualityImpact(
            issue="Incorrect account balance",
            affected_records=100,
            business_criticality=10,
        ),
        QualityImpact(
            issue="Duplicate product descriptions",
            affected_records=5000,
            business_criticality=2,
        ),
    ]

    for issue in sorted(
        issues,
        key=lambda item: item.priority_score,
        reverse=True,
    ):
        print(
            f"{issue.issue:45} "
            f"priority={issue.priority_score}"
        )


# ============================================================================
# 48. ADVANCED CONCEPT: DATA QUALITY AND ML
# ============================================================================

def demonstrate_ml_data_quality_concepts() -> None:
    section("44. DATA QUALITY FOR MACHINE LEARNING")

    print("Important quality dimensions for ML datasets:")
    print("  - Feature completeness")
    print("  - Label correctness")
    print("  - Class balance")
    print("  - Duplicate samples")
    print("  - Outliers")
    print("  - Distribution shifts")
    print("  - Leakage")
    print("  - Temporal consistency")

    print("\nA dataset can be structurally valid while still producing a poor model.")
    print("For ML, quality must be evaluated against the modeling objective.")


# ============================================================================
# 49. ADVANCED CONCEPT: DATA LEAKAGE
# ============================================================================

def demonstrate_data_leakage() -> None:
    section("45. DATA LEAKAGE AS A DATA QUALITY PROBLEM")

    print("Example:")
    print("  Predict loan default at application time.")
    print("  A feature containing post-default recovery information is available.")
    print("  The feature may be non-null, correctly typed, and internally consistent.")
    print("  Yet it violates the temporal meaning of the prediction problem.")

    print("\nThis illustrates that quality includes semantic and temporal correctness.")


# ============================================================================
# 50. DATA QUALITY REPORT
# ============================================================================

def generate_text_report(records: list[dict[str, Any]]) -> str:
    """Generate a concise machine-readable-style textual report."""
    scorecard = build_scorecard(records)

    lines = [
        "DATA QUALITY REPORT",
        "-" * 60,
        f"Record count: {len(records)}",
    ]

    for dimension, score in scorecard.items():
        lines.append(f"{dimension}: {score:.2%}")

    duplicates = duplicate_records(records, ["customer_id"])

    lines.append(
        f"Duplicate customer keys: {len(duplicates)}"
    )

    return "\n".join(lines)


# ============================================================================
# 51. END-TO-END DEMONSTRATION
# ============================================================================

def main() -> None:
    """
    Execute the complete educational demonstration.

    The order moves from foundational concepts to operational and advanced
    data-quality engineering.
    """
    section("DATA QUALITY: COMPLETE STUDY SCRIPT")

    explain_data_quality()

    demonstrate_missing_values()
    print_profile(RAW_CUSTOMERS)
    demonstrate_completeness(RAW_CUSTOMERS)
    demonstrate_validation(RAW_CUSTOMERS)
    demonstrate_duplicates(RAW_CUSTOMERS)
    demonstrate_consistency(RAW_CUSTOMERS)
    demonstrate_accuracy(RAW_CUSTOMERS)
    demonstrate_timeliness(RAW_CUSTOMERS)
    demonstrate_integrity()
    demonstrate_anomalies(RAW_CUSTOMERS)
    demonstrate_standardization(RAW_CUSTOMERS)
    demonstrate_quality_score(RAW_CUSTOMERS)
    demonstrate_quality_engine(RAW_CUSTOMERS)
    demonstrate_remediation(RAW_CUSTOMERS)
    demonstrate_quarantine(RAW_CUSTOMERS)
    demonstrate_duplicate_matching(RAW_CUSTOMERS)
    demonstrate_rule_categories()
    demonstrate_null_semantics()
    demonstrate_dimension_comparison()
    demonstrate_monitoring(RAW_CUSTOMERS)
    demonstrate_quality_drift()
    demonstrate_testing()
    test_quality_invariants()
    demonstrate_complexity()
    demonstrate_streaming(RAW_CUSTOMERS)
    demonstrate_data_contract(RAW_CUSTOMERS)
    demonstrate_root_cause_analysis()
    demonstrate_lineage()
    demonstrate_security_considerations()
    demonstrate_production_design()
    demonstrate_end_to_end_pipeline(RAW_CUSTOMERS)
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    demonstrate_applications()
    print_quality_dashboard(RAW_CUSTOMERS)
    demonstrate_synthetic_anomaly_detection()
    demonstrate_scorecard(RAW_CUSTOMERS)
    demonstrate_failure_classification()
    demonstrate_governance()
    demonstrate_dimension_interactions()
    demonstrate_prioritization()
    demonstrate_ml_data_quality_concepts()
    demonstrate_data_leakage()

    section("46. FINAL REPORT")

    print(generate_text_report(RAW_CUSTOMERS))


if __name__ == "__main__":
    main()
