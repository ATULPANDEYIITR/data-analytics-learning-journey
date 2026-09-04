"""
Data Types: A Comprehensive Study Script

This script teaches how data is classified and interpreted in data analysis,
statistics, databases, machine learning, business intelligence, and software
systems.

Topics covered:
    - Numeric data
    - Categorical data
    - Nominal data
    - Ordinal data
    - Binary data
    - Discrete data
    - Continuous data
    - Temporal data
    - Textual data
    - Geographic data
    - Identifiers
    - Measures vs dimensions
    - Multiple classifications for the same variable
    - Measurement scales
    - Representation choices
    - Validation
    - Encoding
    - Aggregation
    - Edge cases
    - Common mistakes
    - Practical data-quality checks
    - Database-oriented considerations
    - Machine-learning considerations
    - Analytics and BI considerations
    - Performance and storage considerations
    - Security and privacy considerations
    - Advanced classification and schema design
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
import math
import re
import statistics
from collections import Counter
from typing import Any, Iterable, Optional


# ============================================================================
# 1. FUNDAMENTAL IDEA: WHAT IS DATA?
# ============================================================================

print("=" * 80)
print("DATA TYPES: FUNDAMENTALS TO ADVANCED CONCEPTS")
print("=" * 80)

"""
A data value is an observation representing some property, event, entity,
relationship, measurement, or description.

Examples:

    42                  -> number
    "India"             -> category/text
    True                -> binary/Boolean
    date(2026, 9, 4)    -> temporal value
    26.8467             -> geographic coordinate
    "customer_001"      -> identifier
    "excellent"         -> ordinal category

A critical principle is:

    The Python representation of a value is NOT necessarily its analytical
    data type.

For example:

    rating = 5

Python sees an integer, but analytically "5 stars" may be an ordinal measure.
The numbers represent ordered categories rather than equal-interval quantities.

Similarly:

    postal_code = 226001

Python sees an integer, but a postal code is normally an identifier or geographic
label, not a numeric quantity. Adding two postal codes is meaningless.

Data classification therefore depends on both:
    1. How the value is represented.
    2. What the value means.
"""

basic_values = {
    "age": 33,
    "country": "India",
    "customer_active": True,
    "temperature_celsius": 31.5,
    "registration_date": date(2026, 9, 4),
    "customer_id": "CUS-1001",
    "satisfaction": "Very Satisfied",
}

for field_name, value in basic_values.items():
    print(f"{field_name:22} -> {value!r:30} -> Python type: {type(value).__name__}")


# ============================================================================
# 2. A TAXONOMY OF DATA
# ============================================================================

"""
A useful taxonomy is multidimensional.

A variable can simultaneously be classified by several properties.

Example:

    number_of_orders = 12

It is:
    - numeric
    - quantitative
    - discrete
    - a measure

Another example:

    customer_id = "CUS-1001"

It is:
    - textual in representation
    - categorical in a broad analytical sense
    - nominal if treated as a label
    - an identifier
    - a dimension-like field in analytics

Another example:

    satisfaction = "High"

It is:
    - categorical
    - ordinal
    - qualitative
    - a dimension in a BI model

There is no requirement that one variable belong to exactly one category.
"""

classification_examples = [
    ("age", 33, ["numeric", "discrete", "measure"]),
    ("height_cm", 178.4, ["numeric", "continuous", "measure"]),
    ("country", "India", ["categorical", "nominal", "dimension"]),
    ("satisfaction", "High", ["categorical", "ordinal", "dimension"]),
    ("is_active", True, ["binary", "categorical", "nominal"]),
    ("order_date", date(2026, 9, 4), ["temporal", "dimension"]),
    ("customer_id", "CUS-1001", ["identifier", "nominal"]),
]

for name, value, classifications in classification_examples:
    print(f"{name:18} {value!r:18} {', '.join(classifications)}")


# ============================================================================
# 3. NUMERIC DATA
# ============================================================================

"""
Numeric data represents quantities for which numerical operations can have
meaning.

Common Python numeric representations include:
    int
    float
    Decimal

Analytical numeric data commonly includes:
    - counts
    - measurements
    - monetary amounts
    - scores
    - ratios
    - percentages
    - physical quantities

Numeric data is often divided into:
    - discrete numeric data
    - continuous numeric data
"""

integer_value = 42
floating_value = 42.75
decimal_value = Decimal("42.75")

print("\nNumeric examples:")
print(integer_value, type(integer_value).__name__)
print(floating_value, type(floating_value).__name__)
print(decimal_value, type(decimal_value).__name__)

print("\nNumeric operations:")
print("Addition:", 10 + 5)
print("Subtraction:", 10 - 5)
print("Multiplication:", 10 * 5)
print("Division:", 10 / 5)
print("Power:", 10 ** 2)


# ============================================================================
# 4. DISCRETE DATA
# ============================================================================

"""
Discrete data consists of countable, distinct values.

Typical examples:
    - number of employees
    - number of orders
    - number of defects
    - number of children
    - number of website visits

A count cannot normally take arbitrary fractional values.

For example:

    number_of_orders = 7

The value 7.35 orders does not make sense when counting completed orders.

Discrete data is commonly represented by integers, but integer representation
alone does not prove that a variable is discrete.
"""

number_of_orders = 7
number_of_employees = 125
number_of_defects = 3

discrete_values = [
    number_of_orders,
    number_of_employees,
    number_of_defects,
]

for value in discrete_values:
    print("Discrete value:", value)


def is_non_negative_integer(value: Any) -> bool:
    """Check whether a value can represent a non-negative count."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


for candidate in [0, 1, 10, -1, 2.5, True]:
    print(f"{candidate!r:8} -> valid count: {is_non_negative_integer(candidate)}")


# ============================================================================
# 5. CONTINUOUS DATA
# ============================================================================

"""
Continuous data can take values anywhere within an interval.

Examples:
    - height
    - weight
    - temperature
    - distance
    - duration
    - voltage
    - pressure

Physical measurements are conceptually continuous even when stored using
finite decimal precision.

For example, a person's height may be stored as:

    178.4 cm

The underlying physical quantity could conceptually be measured more precisely:

    178.43 cm
    178.431 cm
    178.4312 cm

The distinction between discrete and continuous is therefore conceptual,
not merely based on whether Python uses int or float.
"""

height_cm = 178.4
temperature_c = 31.75
distance_km = 12.384

continuous_values = {
    "height_cm": height_cm,
    "temperature_c": temperature_c,
    "distance_km": distance_km,
}

for name, value in continuous_values.items():
    print(f"{name:20}: {value}")


def classify_numeric_measure(value: Any) -> str:
    """
    Demonstrate representation-based classification.

    This function is intentionally conservative:
    actual analytical classification requires domain knowledge.
    """
    if isinstance(value, bool):
        return "binary"
    if isinstance(value, int):
        return "numeric integer; may be discrete or another numeric type"
    if isinstance(value, (float, Decimal)):
        return "numeric real-valued; often continuous"
    return "not a standard numeric representation"


for value in [10, 10.5, Decimal("10.5"), True, "10"]:
    print(f"{value!r:12} -> {classify_numeric_measure(value)}")


# ============================================================================
# 6. CATEGORICAL DATA
# ============================================================================

"""
Categorical data represents membership in categories or groups.

Examples:
    country = "India"
    department = "Finance"
    product_type = "Laptop"

Categories may be:
    - nominal
    - ordinal

Categorical values can be strings, integers, Boolean values, codes, or other
representations.

The important property is semantic meaning, not storage format.
"""

countries = ["India", "Japan", "India", "Germany", "Japan", "India"]
departments = ["Finance", "Technology", "Finance", "HR"]

print("\nCountry frequencies:")
print(Counter(countries))

print("\nDepartment frequencies:")
print(Counter(departments))


def frequency_table(values: Iterable[Any]) -> dict[Any, int]:
    """Return category frequencies."""
    return dict(Counter(values))


print(frequency_table(["A", "B", "A", "C", "A", "B"]))


# ============================================================================
# 7. NOMINAL DATA
# ============================================================================

"""
Nominal data consists of categories with no inherent ordering.

Examples:
    - blood group
    - country
    - department
    - eye color
    - product category
    - browser type

If:

    country = "India"

there is no meaningful statement such as:

    India > Japan

The categories are labels.

Nominal variables can have frequency counts and modes, but arithmetic
operations on category labels are not meaningful.
"""

nominal_data = [
    "India",
    "Japan",
    "Germany",
    "India",
    "Brazil",
]

print("\nNominal categories:")
print(nominal_data)

print("Most common category:", Counter(nominal_data).most_common(1)[0])


# ============================================================================
# 8. ORDINAL DATA
# ============================================================================

"""
Ordinal data has a meaningful order, but the distance between categories is
not necessarily equal.

Examples:
    - low, medium, high
    - poor, fair, good, excellent
    - bronze, silver, gold
    - education levels
    - satisfaction ratings

Suppose:

    Poor < Fair < Good < Excellent

We know the order.

We do NOT automatically know that:

    Good - Fair == Fair - Poor

Ordinal data therefore supports ranking, but arithmetic interpretation requires
careful justification.
"""

satisfaction_order = {
    "Very Dissatisfied": 1,
    "Dissatisfied": 2,
    "Neutral": 3,
    "Satisfied": 4,
    "Very Satisfied": 5,
}

customer_satisfaction = [
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
]

encoded_satisfaction = [
    satisfaction_order[value]
    for value in customer_satisfaction
]

print("\nOrdinal values:")
print(customer_satisfaction)

print("Ordered encoding:")
print(encoded_satisfaction)

print("Median encoded rating:", statistics.median(encoded_satisfaction))


def compare_ordinal(
    first: str,
    second: str,
    ordering: dict[str, int],
) -> int:
    """
    Compare two ordinal categories.

    Returns:
        -1 if first < second
         0 if first == second
         1 if first > second
    """
    first_rank = ordering[first]
    second_rank = ordering[second]

    if first_rank < second_rank:
        return -1
    if first_rank > second_rank:
        return 1
    return 0


print(
    "Satisfied vs Very Satisfied:",
    compare_ordinal("Satisfied", "Very Satisfied", satisfaction_order),
)


# ============================================================================
# 9. NOMINAL VS ORDINAL
# ============================================================================

"""
The key distinction:

Nominal:
    categories without meaningful order.

Ordinal:
    categories with meaningful order.

Examples:

Nominal:
    red, blue, green

Ordinal:
    low, medium, high

A common mistake is assigning arbitrary numbers to nominal categories and then
treating those numbers as quantities.

For example:

    red = 1
    blue = 2
    green = 3

The numbers are only labels unless a genuine ordering exists.
"""

nominal_encoding = {
    "Red": 1,
    "Blue": 2,
    "Green": 3,
}

print("\nArbitrary nominal encoding:")
print(nominal_encoding)
print(
    "The number 3 does not mean Green is quantitatively greater than Blue."
)


# ============================================================================
# 10. BINARY DATA
# ============================================================================

"""
Binary data has exactly two possible states for a variable.

Examples:
    - yes / no
    - true / false
    - active / inactive
    - approved / rejected
    - defective / non-defective

Binary data can be represented as:
    bool
    0/1
    Yes/No
    strings
    domain-specific codes

Binary data may be nominal or may represent a meaningful event/state.
"""

binary_values = [True, False, True, True, False]

print("\nBinary values:")
print(binary_values)

print("True count:", sum(binary_values))
print("False count:", len(binary_values) - sum(binary_values))


def validate_binary(value: Any) -> bool:
    """Validate a strict Boolean value."""
    return type(value) is bool


for value in [True, False, 0, 1, "yes", "no", None]:
    print(f"{value!r:8} -> strict Boolean: {validate_binary(value)}")


# ============================================================================
# 11. BINARY ENCODING AND CLASS IMBALANCE
# ============================================================================

"""
In analytics and machine learning, binary variables are frequently encoded
as 0 and 1.

Example:

    churned = 1
    retained = 0

The encoding makes calculations convenient.

For a binary variable X:

    mean(X)

is equal to the proportion of observations where X = 1.

Example:
    [1, 0, 1, 1, 0]

Mean = 3 / 5 = 0.60

Therefore 60% of observations belong to class 1.
"""

binary_sample = [1, 0, 1, 1, 0]

binary_mean = statistics.mean(binary_sample)

print("\nBinary mean:")
print(binary_mean)

print("Proportion of class 1:", binary_mean)

print("Percentage of class 1:", binary_mean * 100)


# ============================================================================
# 12. TEMPORAL DATA
# ============================================================================

"""
Temporal data represents time-related information.

Common forms include:
    - date
    - time
    - datetime
    - timestamp
    - duration
    - time interval
    - period
    - timezone-aware timestamp

Examples:
    order_date
    login_timestamp
    delivery_time
    subscription_duration

Temporal data requires careful handling of:
    - time zones
    - daylight saving transitions
    - date boundaries
    - precision
    - formatting
    - missing time components
"""

today = date(2026, 9, 4)
current_time = time(14, 30, 15)
event_timestamp = datetime(2026, 9, 4, 14, 30, 15)

print("\nTemporal values:")
print("Date:", today)
print("Time:", current_time)
print("Datetime:", event_timestamp)

tomorrow = today + timedelta(days=1)
print("Tomorrow:", tomorrow)

duration = timedelta(hours=2, minutes=30)
future_event = event_timestamp + duration

print("Future event:", future_event)


# ============================================================================
# 13. TEMPORAL DATA: ORDERING AND DIFFERENCES
# ============================================================================

start = datetime(2026, 9, 4, 9, 15)
end = datetime(2026, 9, 4, 17, 45)

elapsed = end - start

print("\nTemporal arithmetic:")
print("Start:", start)
print("End:", end)
print("Elapsed:", elapsed)
print("Hours:", elapsed.total_seconds() / 3600)


def is_valid_date_range(start_date: date, end_date: date) -> bool:
    """Validate chronological ordering."""
    return start_date <= end_date


print(is_valid_date_range(date(2026, 9, 1), date(2026, 9, 10)))
print(is_valid_date_range(date(2026, 9, 10), date(2026, 9, 1)))


# ============================================================================
# 14. TIME ZONES
# ============================================================================

"""
A naive datetime does not contain timezone information.

An aware datetime contains timezone information.

Production systems should be explicit about timezone semantics.

A common engineering practice is:
    - store timestamps in UTC
    - convert to local time at presentation boundaries
    - retain timezone information when the original local context matters

The standard library's zoneinfo module can provide IANA timezone support.
"""

from zoneinfo import ZoneInfo

utc_timestamp = datetime.now(ZoneInfo("UTC"))
india_timestamp = utc_timestamp.astimezone(ZoneInfo("Asia/Kolkata"))

print("\nTimezone-aware timestamps:")
print("UTC:", utc_timestamp)
print("India:", india_timestamp)


# ============================================================================
# 15. TEXTUAL DATA
# ============================================================================

"""
Textual data consists of natural language, free-form descriptions, labels,
documents, messages, comments, names, addresses, and similar character data.

Examples:
    "Customer reported delayed delivery."
    "Product description"
    "Support ticket"

Text can be:
    - structured
    - semi-structured
    - unstructured

Text often requires preprocessing before analytical use.

Potential operations:
    - normalization
    - tokenization
    - cleaning
    - pattern extraction
    - language detection
    - classification
    - sentiment analysis
    - search indexing

Not every string is textual data. A string can also represent:
    - an identifier
    - a code
    - a category
    - a date
    - a geographic coordinate
"""

text_value = "Customer reported that the delivery arrived late."

print("\nText:")
print(text_value)
print("Length:", len(text_value))
print("Words:", text_value.split())


def normalize_text(text: str) -> str:
    """Basic deterministic text normalization."""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


print(normalize_text("  CUSTOMER   reported   a delay.  "))


# ============================================================================
# 16. TEXTUAL DATA: STRUCTURED VS UNSTRUCTURED
# ============================================================================

structured_text = "ORDER-1001"
unstructured_text = (
    "The customer contacted support because the package "
    "arrived two days later than expected."
)

print("\nStructured text-like value:", structured_text)
print("Unstructured natural language:", unstructured_text)


def extract_order_id(text: str) -> Optional[str]:
    """
    Extract an order identifier embedded in text.

    This demonstrates that textual data may contain structured information.
    """
    match = re.search(r"\bORDER-\d+\b", text.upper())
    return match.group(0) if match else None


print(extract_order_id("Issue associated with order ORDER-1001."))


# ============================================================================
# 17. GEOGRAPHIC DATA
# ============================================================================

"""
Geographic or spatial data represents location or geometry.

Common examples:
    - latitude
    - longitude
    - postal code
    - city
    - state
    - country
    - address
    - polygon
    - line
    - point

A latitude and longitude pair is numeric in representation but geographic
in meaning.

A postal code is generally categorical or identifier-like, not a quantity.

Geographic data can be:
    - point data
    - line data
    - polygon data
    - raster data

This script focuses on basic point coordinates without external GIS packages.
"""

latitude = 26.8467
longitude = 80.9462

print("\nGeographic coordinate:")
print("Latitude:", latitude)
print("Longitude:", longitude)


def validate_latitude(latitude_value: float) -> bool:
    return -90 <= latitude_value <= 90


def validate_longitude(longitude_value: float) -> bool:
    return -180 <= longitude_value <= 180


print("Latitude valid:", validate_latitude(latitude))
print("Longitude valid:", validate_longitude(longitude))


def validate_coordinate(latitude_value: float, longitude_value: float) -> bool:
    return (
        validate_latitude(latitude_value)
        and validate_longitude(longitude_value)
    )


print("Coordinate valid:", validate_coordinate(latitude, longitude))


# ============================================================================
# 18. IDENTIFIERS
# ============================================================================

"""
An identifier uniquely identifies an entity or record.

Examples:
    customer_id
    employee_id
    transaction_id
    order_id
    UUID
    passport number
    product SKU

Identifiers are often stored as strings.

Important distinction:

    customer_id = "1001"

does not mean the customer has a quantity of 1001.

The value is a label used to identify an entity.

Identifiers often behave as nominal variables, but their primary analytical
purpose is identification rather than measurement.
"""

customer_ids = [
    "CUS-1001",
    "CUS-1002",
    "CUS-1003",
]

print("\nIdentifiers:")
for customer_id in customer_ids:
    print(customer_id)


def validate_identifier(identifier: str, prefix: str) -> bool:
    """Validate a simple prefixed identifier."""
    pattern = rf"^{re.escape(prefix)}-\d+$"
    return bool(re.fullmatch(pattern, identifier))


for identifier in ["CUS-1001", "CUS-ABC", "CUS-", "1001"]:
    print(
        f"{identifier:10} -> valid customer identifier:",
        validate_identifier(identifier, "CUS"),
    )


# ============================================================================
# 19. IDENTIFIER UNIQUENESS
# ============================================================================

"""
A candidate identifier should normally satisfy uniqueness constraints.

Example:

    customer_id = ["CUS-1", "CUS-2", "CUS-3"]

is unique.

If:

    ["CUS-1", "CUS-2", "CUS-1"]

appears in a table intended to have one row per customer, the identifier
constraint has been violated.
"""

def find_duplicates(values: Iterable[Any]) -> list[Any]:
    """Return duplicated values while preserving first-seen order."""
    seen = set()
    duplicates = []

    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)

    return duplicates


print(
    "\nDuplicate identifiers:",
    find_duplicates(["CUS-1", "CUS-2", "CUS-1", "CUS-3", "CUS-2"]),
)


# ============================================================================
# 20. MEASURES VS DIMENSIONS
# ============================================================================

"""
Measures and dimensions are particularly important in business intelligence,
analytics, reporting, and dimensional data modeling.

A measure is generally a value that can be quantified or aggregated.

Examples:
    revenue
    profit
    quantity_sold
    number_of_orders
    discount_amount

A dimension describes the context in which measures are analyzed.

Examples:
    customer
    country
    product
    department
    date
    region

Example:

    Revenue = 500000
    Country = India
    Product = Laptop
    Date = 2026-09-04

Revenue is a measure.

Country, Product, and Date are dimensions.

The classification depends on analytical usage and data modeling context.
"""

sales_records = [
    {
        "date": date(2026, 9, 1),
        "country": "India",
        "product": "Laptop",
        "revenue": 120000.0,
        "quantity": 3,
    },
    {
        "date": date(2026, 9, 1),
        "country": "India",
        "product": "Phone",
        "revenue": 90000.0,
        "quantity": 5,
    },
    {
        "date": date(2026, 9, 2),
        "country": "Japan",
        "product": "Laptop",
        "revenue": 150000.0,
        "quantity": 4,
    },
]


def total_measure(records: Iterable[dict[str, Any]], field: str) -> float:
    """Aggregate a numeric measure."""
    return sum(float(record[field]) for record in records)


print("\nTotal revenue:", total_measure(sales_records, "revenue"))
print("Total quantity:", total_measure(sales_records, "quantity"))


# ============================================================================
# 21. MEASURE AGGREGATION
# ============================================================================

"""
Not every numeric variable should be aggregated in the same way.

Common aggregation functions:

    SUM
    COUNT
    COUNT DISTINCT
    MIN
    MAX
    AVG
    MEDIAN
    PERCENTILE

Examples:

Revenue:
    SUM is often meaningful.

Customer ID:
    SUM is meaningless.

Age:
    AVG may be meaningful depending on the analysis.

Temperature:
    AVG may be meaningful when the time/location context is appropriate.

Rating:
    Mean may be used in some applications, but ordinal interpretation should
    be considered.

Identifier:
    COUNT DISTINCT is meaningful.
"""

ages = [25, 30, 35, 40, 45]
revenues = [100, 200, 300, 400, 500]
customer_ids_for_analysis = ["A", "B", "A", "C", "C"]

print("\nAge mean:", statistics.mean(ages))
print("Revenue sum:", sum(revenues))
print("Unique customers:", len(set(customer_ids_for_analysis)))


# ============================================================================
# 22. DIMENSION HIERARCHIES
# ============================================================================

"""
Dimensions can contain hierarchies.

For geography:

    Country
        -> State
            -> City
                -> Store

For time:

    Year
        -> Quarter
            -> Month
                -> Day

Hierarchies support drill-down and roll-up operations in BI systems.
"""

geography = {
    "country": "India",
    "state": "Uttar Pradesh",
    "city": "Lucknow",
}

time_dimension = {
    "year": 2026,
    "quarter": 3,
    "month": 9,
    "day": 4,
}

print("\nGeographic hierarchy:", geography)
print("Temporal hierarchy:", time_dimension)


# ============================================================================
# 23. DATA TYPE IS NOT THE SAME AS PYTHON TYPE
# ============================================================================

"""
This is one of the most important concepts.

Consider:

    value = 226001

Python:
    int

Business meaning:
    postal code

Analytical meaning:
    categorical/geographic identifier

Another example:

    value = 1

It could mean:
    - one order
    - class 1
    - true
    - high priority
    - product code 1
    - ordinal rank 1

Therefore classification requires semantic context.
"""

examples_of_integer_semantics = {
    "order_count": 1,
    "binary_flag": 1,
    "category_code": 1,
    "postal_code": 226001,
    "rank": 1,
    "customer_id": 1001,
}

for field, value in examples_of_integer_semantics.items():
    print(f"{field:18} -> {value}")


# ============================================================================
# 24. MEASUREMENT SCALES
# ============================================================================

"""
Classical measurement theory describes four major scales:

    Nominal
    Ordinal
    Interval
    Ratio

Nominal:
    categories only.

Ordinal:
    categories plus order.

Interval:
    ordered values with meaningful differences, but no meaningful absolute
    zero.

Ratio:
    ordered values with meaningful differences and a meaningful zero.

Examples commonly used:

Nominal:
    country

Ordinal:
    satisfaction level

Interval:
    temperature in Celsius

Ratio:
    weight, height, duration, revenue, distance

The distinction is important because it affects which mathematical operations
are conceptually justified.
"""

measurement_scale_examples = {
    "country": "nominal",
    "satisfaction": "ordinal",
    "temperature_celsius": "interval",
    "weight_kg": "ratio",
    "distance_km": "ratio",
    "revenue": "ratio",
}

for field, scale in measurement_scale_examples.items():
    print(f"{field:24} -> {scale}")


# ============================================================================
# 25. INTERVAL VS RATIO
# ============================================================================

"""
Interval scale:

    Difference is meaningful.

For Celsius:
    20°C is 10°C warmer than 10°C.

But:
    20°C is not meaningfully twice as hot as 10°C.

Why?

Because zero Celsius is not the absence of thermal energy.

Ratio scale:

    A meaningful zero exists.

For weight:
    20 kg is twice 10 kg.

For duration:
    20 minutes is twice 10 minutes.

This distinction prevents incorrect interpretations of ratios.
"""

temperature_a = 20
temperature_b = 10

print("\nTemperature difference:", temperature_a - temperature_b)
print(
    "A ratio interpretation such as 20 / 10 is not physically equivalent "
    "to saying one Celsius temperature is twice another."
)

weight_a = 20
weight_b = 10

print("Weight ratio:", weight_a / weight_b)


# ============================================================================
# 26. CATEGORICAL ENCODING
# ============================================================================

"""
Categorical values often need numerical representation for algorithms.

Common methods:

    Label encoding
    One-hot encoding
    Ordinal encoding
    Target encoding
    Frequency encoding

The correct method depends on the semantics.

Nominal:
    one-hot encoding is often appropriate.

Ordinal:
    ordered encoding can preserve rank.

Arbitrary integer encoding of nominal categories can accidentally introduce
false ordering.
"""

colors = ["Red", "Blue", "Green", "Blue", "Red"]

unique_colors = list(dict.fromkeys(colors))
color_to_code = {
    color: index
    for index, color in enumerate(unique_colors)
}

label_encoded_colors = [
    color_to_code[color]
    for color in colors
]

print("\nNominal labels:")
print(colors)
print("Label mapping:", color_to_code)
print("Encoded:", label_encoded_colors)


def one_hot_encode(
    values: list[str],
) -> tuple[list[str], list[dict[str, int]]]:
    """Simple educational one-hot encoder."""
    categories = list(dict.fromkeys(values))
    encoded_rows = []

    for value in values:
        row = {
            category: int(value == category)
            for category in categories
        }
        encoded_rows.append(row)

    return categories, encoded_rows


categories, encoded_rows = one_hot_encode(colors)

print("\nOne-hot categories:", categories)

for row in encoded_rows:
    print(row)


# ============================================================================
# 27. ORDINAL ENCODING
# ============================================================================

ordinal_values = ["Low", "Medium", "High", "Medium", "High"]

ordinal_mapping = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

ordinal_encoded = [
    ordinal_mapping[value]
    for value in ordinal_values
]

print("\nOrdinal encoding:")
print(ordinal_encoded)


# ============================================================================
# 28. DATA TYPE CONVERSION
# ============================================================================

"""
Conversion can change representation without changing meaning.

Examples:

    "42" -> 42

    "2026-09-04" -> date(2026, 9, 4)

But conversion can also create semantic errors.

Example:

    "226001" -> 226001

Technically valid numeric conversion, but analytically dangerous if the field
is a postal code.

Leading zeros are especially important:

    "00125"

converted to integer becomes:

    125

The original identifier formatting has been lost.
"""

numeric_text = "42"
converted_number = int(numeric_text)

print("\nString to integer:", converted_number)

postal_code = "00125"
postal_as_integer = int(postal_code)

print("Original postal code:", postal_code)
print("Incorrect numeric representation:", postal_as_integer)


# ============================================================================
# 29. MISSING VALUES
# ============================================================================

"""
Missingness is not itself a data type, but it interacts strongly with data
classification.

Possible representations include:
    None
    NaN
    empty string
    NULL
    special sentinel values

Different meanings include:
    - value unknown
    - value not collected
    - value not applicable
    - value intentionally withheld
    - value not yet available

These meanings should not automatically be collapsed into one category.
"""

missing_examples = {
    "unknown_age": None,
    "not_applicable_middle_name": None,
    "missing_comment": "",
}

for name, value in missing_examples.items():
    print(f"{name:32} -> {value!r}")


def is_missing(value: Any) -> bool:
    """Basic missing-value detector for common Python representations."""
    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    if isinstance(value, str) and value.strip() == "":
        return True

    return False


for value in [None, float("nan"), "", "India", 0, False]:
    print(f"{value!r:10} -> missing: {is_missing(value)}")


# ============================================================================
# 30. EDGE CASE: ZERO IS NOT MISSING
# ============================================================================

"""
Zero is usually a legitimate numeric value.

False is also a legitimate Boolean value.

An empty string may mean missing, but in some systems it can be a genuine
value.

Therefore:

    if not value:

is often an unsafe generic missing-value check.
"""

values_to_test = [0, False, "", None, [], "India"]

for value in values_to_test:
    print(
        f"value={value!r:8} | bool(value)={bool(value)!s:5} "
        f"| is_missing={is_missing(value)}"
    )


# ============================================================================
# 31. DATA VALIDATION
# ============================================================================

"""
Validation rules should be based on the semantics of the variable.

Examples:

Age:
    generally non-negative and within a domain-specific plausible range.

Percentage:
    often between 0 and 100.

Latitude:
    between -90 and 90.

Longitude:
    between -180 and 180.

Category:
    must belong to an allowed set.

Ordinal:
    must belong to an allowed ordered set.

Identifier:
    must satisfy formatting and uniqueness constraints.
"""

def validate_age(age: Any) -> bool:
    return (
        isinstance(age, (int, float))
        and not isinstance(age, bool)
        and 0 <= age <= 130
    )


def validate_percentage(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= value <= 100
    )


def validate_category(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


for age in [33, -5, 200, "33", None]:
    print(f"Age {age!r:8} valid -> {validate_age(age)}")

for percentage in [0, 25.5, 100, 101, -1]:
    print(
        f"Percentage {percentage!r:8} valid -> "
        f"{validate_percentage(percentage)}"
    )

allowed_departments = {"Finance", "Technology", "HR"}

for department in ["Finance", "Sales", "Technology", None]:
    print(
        f"Department {department!r:12} valid -> "
        f"{validate_category(department, allowed_departments)}"
    )


# ============================================================================
# 32. OUTLIERS AND PLAUSIBILITY
# ============================================================================

"""
A value can be valid according to a type rule but still be suspicious.

Example:

    age = 999

is numeric and non-negative, but probably invalid for a human age field.

Similarly:

    temperature = -273.15

is mathematically valid Celsius, but it represents absolute zero and may be
extremely unusual depending on the application.

Data validation should therefore distinguish:
    - type validity
    - domain validity
    - business-rule validity
    - statistical plausibility
"""

ages_with_possible_outliers = [25, 26, 27, 28, 29, 31, 250]

mean_age = statistics.mean(ages_with_possible_outliers)
median_age = statistics.median(ages_with_possible_outliers)

print("\nAge mean with extreme value:", mean_age)
print("Age median with extreme value:", median_age)


# ============================================================================
# 33. DATA QUALITY RULES
# ============================================================================

"""
A practical data-quality framework can examine:

    completeness
    uniqueness
    validity
    consistency
    accuracy
    timeliness
    conformity

Different data types require different checks.
"""

@dataclass
class DataQualityReport:
    total_values: int
    missing_values: int
    unique_values: int
    duplicate_values: int


def quality_report(values: list[Any]) -> DataQualityReport:
    missing_count = sum(is_missing(value) for value in values)
    unique_count = len(set(values))
    duplicate_count = len(values) - unique_count

    return DataQualityReport(
        total_values=len(values),
        missing_values=missing_count,
        unique_values=unique_count,
        duplicate_values=duplicate_count,
    )


sample_quality_values = ["India", "Japan", "India", None, "Germany"]

print("\nData quality report:")
print(quality_report(sample_quality_values))


# ============================================================================
# 34. TYPE INFERENCE
# ============================================================================

"""
In real datasets, types are often inferred from raw values.

Inference should be treated carefully.

Example:

    ["1", "2", "3"]

could be:
    - numeric measurements
    - category codes
    - identifiers
    - ordinal ranks

Automated inference can identify representation patterns, but semantic
classification often requires metadata or domain knowledge.
"""

raw_values = ["1", "2", "3", "4"]

all_integer_like = all(value.isdigit() for value in raw_values)

print("\nRaw values:", raw_values)
print("All integer-like:", all_integer_like)
print(
    "Inference result: numeric-looking, but semantic interpretation "
    "cannot be established from strings alone."
)


# ============================================================================
# 35. A SEMANTIC DATA TYPE CLASSIFIER
# ============================================================================

class SemanticType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    NOMINAL = "nominal"
    BINARY = "binary"
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    TEMPORAL = "temporal"
    TEXTUAL = "textual"
    GEOGRAPHIC = "geographic"
    IDENTIFIER = "identifier"
    MEASURE = "measure"
    DIMENSION = "dimension"


@dataclass
class VariableMetadata:
    name: str
    semantic_types: list[SemanticType]
    description: str
    nullable: bool = True


metadata = [
    VariableMetadata(
        name="customer_id",
        semantic_types=[
            SemanticType.IDENTIFIER,
            SemanticType.NOMINAL,
        ],
        description="Unique identifier for a customer.",
        nullable=False,
    ),
    VariableMetadata(
        name="revenue",
        semantic_types=[
            SemanticType.NUMERIC,
            SemanticType.CONTINUOUS,
            SemanticType.MEASURE,
        ],
        description="Monetary revenue generated by an order.",
        nullable=False,
    ),
    VariableMetadata(
        name="country",
        semantic_types=[
            SemanticType.CATEGORICAL,
            SemanticType.NOMINAL,
            SemanticType.DIMENSION,
        ],
        description="Country associated with the transaction.",
        nullable=False,
    ),
    VariableMetadata(
        name="satisfaction",
        semantic_types=[
            SemanticType.CATEGORICAL,
            SemanticType.ORDINAL,
            SemanticType.DIMENSION,
        ],
        description="Customer satisfaction category.",
    ),
]

print("\nVariable metadata:")
for item in metadata:
    types = ", ".join(value.value for value in item.semantic_types)
    print(f"{item.name:18} -> {types}")


# ============================================================================
# 36. MEASURES CAN BE ADDITIVE, SEMI-ADDITIVE, OR NON-ADDITIVE
# ============================================================================

"""
Advanced BI modeling distinguishes measures by aggregation behavior.

Additive measure:
    Can be summed across relevant dimensions.

Example:
    sales revenue

Semi-additive measure:
    Can be summed across some dimensions but not others.

Example:
    bank account balance can be summed across customers at a point in time,
    but summing balances across dates may be meaningless.

Non-additive measure:
    Should not normally be summed.

Examples:
    percentage
    ratio
    average
    margin percentage

This distinction is crucial for correct reporting.
"""

daily_balances = {
    date(2026, 9, 1): 1000,
    date(2026, 9, 2): 1200,
    date(2026, 9, 3): 1100,
}

print("\nDaily balances:")
for day, balance in daily_balances.items():
    print(day, balance)

print(
    "Summing balances across dates:",
    sum(daily_balances.values()),
    "(usually not a meaningful cumulative balance)"
)


# ============================================================================
# 37. DIMENSIONS CAN ALSO BE NUMERIC
# ============================================================================

"""
A dimension does not have to be categorical in storage.

Examples:
    latitude
    longitude
    age band code
    date key
    fiscal year

A field can be numeric and dimension-like.

For example:

    year = 2026

is numeric in representation but often used as a dimension for slicing
analytics.
"""

year_dimension = 2026
print("\nYear dimension:", year_dimension)


# ============================================================================
# 38. MEASURES CAN ORIGINATE FROM CATEGORICAL DATA
# ============================================================================

"""
A measure can be derived from categories.

Example:

    status = ["Approved", "Rejected", "Approved"]

The count of approved records is a measure:

    approved_count = 2

The original status is a categorical dimension, while the aggregation is a
numeric measure.
"""

statuses = ["Approved", "Rejected", "Approved", "Approved"]

approved_count = sum(status == "Approved" for status in statuses)

print("\nApproved count:", approved_count)


# ============================================================================
# 39. DERIVED VARIABLES
# ============================================================================

"""
Derived variables are calculated from existing data.

Examples:

    age_group from age
    profit from revenue - cost
    month from date
    customer_tenure from registration date
    distance from latitude/longitude
    churn_flag from customer activity

Derived fields may have a different semantic type from their source.
"""

age = 33

if age < 18:
    age_group = "Minor"
elif age < 30:
    age_group = "Young Adult"
elif age < 60:
    age_group = "Adult"
else:
    age_group = "Senior"

print("\nAge:", age)
print("Derived age group:", age_group)


# ============================================================================
# 40. BUCKETING CONTINUOUS DATA
# ============================================================================

"""
Continuous numeric data is sometimes converted into categorical bands.

Example:

    age = 33

becomes:

    age_group = "30-39"

This can improve interpretability but loses information.

Original:
    33

Binned:
    30-39

The exact value is no longer available in the binned representation.
"""

def age_band(age_value: int) -> str:
    if age_value < 0:
        raise ValueError("Age cannot be negative.")

    if age_value < 18:
        return "0-17"
    if age_value < 30:
        return "18-29"
    if age_value < 40:
        return "30-39"
    if age_value < 50:
        return "40-49"
    return "50+"

for age_value in [5, 18, 29, 30, 39, 40, 65]:
    print(f"Age {age_value:2} -> {age_band(age_value)}")


# ============================================================================
# 41. DISCRETIZATION TRADE-OFFS
# ============================================================================

"""
Discretization can:
    - simplify interpretation
    - reduce sensitivity to small numerical differences
    - support categorical reporting

But it can also:
    - discard information
    - introduce arbitrary boundaries
    - create artificial discontinuities
    - reduce statistical power
"""

continuous_scores = [61.2, 61.8, 69.9, 70.1]

def score_band(score: float) -> str:
    return "Low" if score < 70 else "High"

print("\nContinuous scores:", continuous_scores)
print("Binned scores:", [score_band(score) for score in continuous_scores])


# ============================================================================
# 42. TEXT THAT LOOKS NUMERIC
# ============================================================================

"""
A field can contain numeric-looking strings without being numeric.

Examples:
    phone_number = "9876543210"
    postal_code = "226001"
    employee_code = "001234"

Arithmetic on these values is usually meaningless.

Leading zeros, formatting, prefixes, and fixed widths can be semantically
important.
"""

phone_number = "09876543210"
employee_code = "001234"

print("\nPhone number:", phone_number)
print("Employee code:", employee_code)

print(
    "These values should not be treated as quantities merely because they "
    "contain digits."
)


# ============================================================================
# 43. CODES VS MEASURES
# ============================================================================

"""
A code is a label.

Example:

    department_code = 101

A measure is a quantity.

Example:

    department_headcount = 101

The values are identical numerically, but their meanings are completely
different.
"""

department_code = 101
department_headcount = 101

print("\nDepartment code:", department_code)
print("Department headcount:", department_headcount)


# ============================================================================
# 44. CARDINALITY
# ============================================================================

"""
Cardinality is the number of distinct values in a field.

Examples:

    gender -> relatively low cardinality
    country -> relatively low cardinality
    customer_id -> potentially very high cardinality
    transaction_id -> very high cardinality

Cardinality affects:
    - database indexing
    - storage
    - one-hot encoding size
    - aggregation
    - dashboard design
    - model performance
"""

def cardinality(values: Iterable[Any]) -> int:
    return len(set(values))


print("\nCardinality examples:")
print("Countries:", cardinality(["India", "Japan", "India", "Brazil"]))
print("Customer IDs:", cardinality(["C1", "C2", "C3", "C4"]))


# ============================================================================
# 45. HIGH-CARDINALITY CATEGORICAL VARIABLES
# ============================================================================

"""
High-cardinality categorical variables can cause practical problems.

Example:

    customer_id

If one-hot encoded, each customer can become a separate feature.

For N customers, naive one-hot encoding can produce approximately N columns.

Identifiers therefore usually should not be blindly treated as predictive
features.
"""

customer_ids_high_cardinality = [f"C{i}" for i in range(1, 11)]

print(
    "\nHigh-cardinality example:",
    len(customer_ids_high_cardinality),
    "distinct customer identifiers"
)


# ============================================================================
# 46. DATA TYPE AND MACHINE LEARNING
# ============================================================================

"""
Machine-learning algorithms often require numerical representations.

Typical treatment:

Numeric:
    scale, normalize, transform, or use directly.

Nominal categorical:
    one-hot encoding or other categorical techniques.

Ordinal:
    ordered encoding when the ordering is meaningful.

Binary:
    often 0/1.

Text:
    vectorization, embeddings, tokenization, or other representations.

Temporal:
    extract features such as year, month, day, hour, duration, cyclic
    representations, or elapsed time.

Geographic:
    coordinates, distances, spatial features, regions, or geospatial
    representations.

Identifiers:
    usually excluded unless they encode legitimate information.
"""

ml_feature_types = {
    "age": "numeric",
    "country": "nominal categorical",
    "satisfaction": "ordinal categorical",
    "is_active": "binary",
    "review": "textual",
    "signup_date": "temporal",
    "latitude": "geographic",
    "customer_id": "identifier",
}

for feature, treatment in ml_feature_types.items():
    print(f"{feature:18} -> {treatment}")


# ============================================================================
# 47. DATA LEAKAGE THROUGH IDENTIFIERS
# ============================================================================

"""
Identifiers can sometimes accidentally encode information.

For example:

    customer_id = 1000001

might appear harmless, but if IDs were assigned chronologically, the value
could indirectly encode customer acquisition period.

Identifiers can also leak information when generated from business processes.

They should therefore be examined before being used as model features.
"""

ids = [1001, 1002, 1003, 1004, 1005]

print("\nSequential IDs:")
print(ids)

print(
    "Sequential ordering does not automatically mean the identifier itself "
    "is a meaningful numerical feature."
)


# ============================================================================
# 48. TEMPORAL FEATURES
# ============================================================================

"""
A timestamp can be decomposed into analytical dimensions/features.

For example:

    datetime
        -> year
        -> month
        -> day
        -> weekday
        -> hour
        -> minute

This creates useful derived variables.
"""

timestamp = datetime(2026, 9, 4, 14, 30, 15)

temporal_features = {
    "year": timestamp.year,
    "month": timestamp.month,
    "day": timestamp.day,
    "weekday": timestamp.strftime("%A"),
    "hour": timestamp.hour,
    "minute": timestamp.minute,
}

print("\nDerived temporal features:")
for key, value in temporal_features.items():
    print(f"{key:10} -> {value}")


# ============================================================================
# 49. CYCLIC TEMPORAL FEATURES
# ============================================================================

"""
Some temporal features are cyclic.

For example:

    23:00 and 00:00 are close in time-of-day semantics.

If hour is represented only as:
    0, 1, ..., 23

a model may incorrectly interpret 23 and 0 as far apart.

A common technique maps the cycle to sine and cosine.
"""

hour = 23

hour_angle = 2 * math.pi * hour / 24

hour_sin = math.sin(hour_angle)
hour_cos = math.cos(hour_angle)

print("\nCyclic hour encoding:")
print("Hour:", hour)
print("sin:", hour_sin)
print("cos:", hour_cos)


# ============================================================================
# 50. GEOGRAPHIC DISTANCE
# ============================================================================

"""
Latitude and longitude are geographic coordinates.

Straight-line distance on a map is not simply:

    sqrt((lat1 - lat2)^2 + (lon1 - lon2)^2)

because Earth is approximately spherical.

The Haversine formula provides an approximation for great-circle distance.
"""

def haversine_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """Calculate approximate great-circle distance in kilometers."""
    radius_km = 6371.0088

    lat1 = math.radians(latitude_1)
    lat2 = math.radians(latitude_2)

    delta_lat = math.radians(latitude_2 - latitude_1)
    delta_lon = math.radians(longitude_2 - longitude_1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_km * c


lucknow = (26.8467, 80.9462)
delhi = (28.6139, 77.2090)

distance = haversine_distance_km(
    lucknow[0],
    lucknow[1],
    delhi[0],
    delhi[1],
)

print("\nApproximate geographic distance:")
print(f"{distance:.2f} km")


# ============================================================================
# 51. DATA TYPE COMPARISON TABLE AS PYTHON DATA
# ============================================================================

comparison_table = [
    {
        "type": "Nominal",
        "order": False,
        "arithmetic": False,
        "example": "Country",
    },
    {
        "type": "Ordinal",
        "order": True,
        "arithmetic": "Limited",
        "example": "Satisfaction",
    },
    {
        "type": "Discrete",
        "order": "Numeric order",
        "arithmetic": True,
        "example": "Order count",
    },
    {
        "type": "Continuous",
        "order": "Numeric order",
        "arithmetic": True,
        "example": "Height",
    },
    {
        "type": "Binary",
        "order": "Depends",
        "arithmetic": "Often 0/1",
        "example": "Active flag",
    },
    {
        "type": "Temporal",
        "order": True,
        "arithmetic": "Date/time operations",
        "example": "Order timestamp",
    },
    {
        "type": "Textual",
        "order": False,
        "arithmetic": False,
        "example": "Review",
    },
    {
        "type": "Identifier",
        "order": False,
        "arithmetic": False,
        "example": "Customer ID",
    },
]

print("\nConceptual comparison:")
for row in comparison_table:
    print(row)


# ============================================================================
# 52. COMMON MISTAKE DETECTOR
# ============================================================================

"""
This section demonstrates simple warnings for suspicious interpretations.
It is not a universal semantic classifier.
"""

def semantic_warning(
    field_name: str,
    value: Any,
    declared_type: str,
) -> list[str]:
    warnings = []

    if declared_type == "numeric":
        numeric_identifier_terms = (
            "id",
            "code",
            "zip",
            "postal",
            "phone",
        )

        if any(term in field_name.lower() for term in numeric_identifier_terms):
            warnings.append(
                "Field name suggests an identifier/code rather than a quantity."
            )

    if declared_type == "categorical" and isinstance(value, (int, float)):
        warnings.append(
            "Numeric storage does not prove that a field is quantitative."
        )

    if declared_type == "text" and isinstance(value, (int, float)):
        warnings.append(
            "Declared textual semantics conflict with numeric representation."
        )

    return warnings


tests = [
    ("postal_code", 226001, "numeric"),
    ("revenue", 50000, "numeric"),
    ("department", 101, "categorical"),
    ("review", 123, "text"),
]

for test in tests:
    print("\nField:", test[0])
    print("Warnings:", semantic_warning(*test))


# ============================================================================
# 53. DATA TYPE VALIDATION PIPELINE
# ============================================================================

@dataclass
class FieldRule:
    name: str
    expected_category: str
    nullable: bool = True


def validate_record(
    record: dict[str, Any],
    rules: list[FieldRule],
) -> list[str]:
    """
    Validate selected basic semantic expectations.

    This educational implementation intentionally avoids pretending that
    generic Python type checks can fully establish domain semantics.
    """
    errors = []

    for rule in rules:
        value = record.get(rule.name)

        if value is None:
            if not rule.nullable:
                errors.append(f"{rule.name}: value is required.")
            continue

        if rule.expected_category == "numeric":
            if (
                not isinstance(value, (int, float, Decimal))
                or isinstance(value, bool)
            ):
                errors.append(f"{rule.name}: expected numeric value.")

        elif rule.expected_category == "text":
            if not isinstance(value, str):
                errors.append(f"{rule.name}: expected text.")

        elif rule.expected_category == "binary":
            if type(value) is not bool:
                errors.append(f"{rule.name}: expected Boolean.")

        elif rule.expected_category == "temporal":
            if not isinstance(value, (date, datetime)):
                errors.append(f"{rule.name}: expected date/datetime.")

    return errors


record = {
    "age": 33,
    "name": "Asha",
    "active": True,
    "signup_date": date(2026, 9, 4),
}

rules = [
    FieldRule("age", "numeric", nullable=False),
    FieldRule("name", "text", nullable=False),
    FieldRule("active", "binary", nullable=False),
    FieldRule("signup_date", "temporal", nullable=False),
]

print("\nRecord validation:")
print(validate_record(record, rules))


# ============================================================================
# 54. ERROR HANDLING DURING CONVERSION
# ============================================================================

"""
Production pipelines must handle malformed values.

A conversion operation should not silently corrupt data.

Examples:
    "42"       -> valid integer
    "42.5"     -> invalid for int()
    "unknown"  -> invalid
    ""         -> invalid
"""

def safe_integer(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


for value in ["42", "42.5", "unknown", None, ""]:
    print(f"\nConvert {value!r:10} -> {safe_integer(value)!r}")


# ============================================================================
# 55. MONEY: NUMERIC BUT SPECIAL
# ============================================================================

"""
Money is numeric but requires special treatment.

Binary floating-point arithmetic can produce representation artifacts.

Decimal is often preferable for exact decimal monetary calculations.
"""

price = Decimal("19.99")
quantity = Decimal("3")

total = price * quantity

print("\nMonetary calculation:")
print("Price:", price)
print("Quantity:", quantity)
print("Total:", total)


# ============================================================================
# 56. FLOATING-POINT PECULIARITY
# ============================================================================

"""
Floating-point numbers use binary representations that cannot exactly
represent many decimal fractions.

Therefore:

    0.1 + 0.2

may not equal exactly 0.3 at the binary representation level.
"""

floating_result = 0.1 + 0.2

print("\nFloating-point result:")
print("0.1 + 0.2 =", floating_result)
print("Exact equality with 0.3:", floating_result == 0.3)
print("Approximate comparison:", math.isclose(floating_result, 0.3))


# ============================================================================
# 57. DATA TYPE NORMALIZATION
# ============================================================================

"""
Normalization means bringing values into a consistent representation.

Example:

    "india"
    "India"
    " INDIA "
    "INDIA"

may represent the same nominal category.

A normalization function can standardize representation before analysis.
"""

raw_countries = [
    "india",
    "India ",
    " INDIA",
    "INDIA",
    "Japan",
]

normalized_countries = [
    value.strip().casefold()
    for value in raw_countries
]

print("\nRaw countries:")
print(raw_countries)

print("Normalized countries:")
print(normalized_countries)

print("Frequencies:")
print(Counter(normalized_countries))


# ============================================================================
# 58. STANDARDIZATION VS SEMANTIC CORRECTION
# ============================================================================

"""
Formatting normalization does not necessarily solve semantic inconsistency.

Example:

    "USA"
    "United States"
    "US"

may all represent the same country, but case normalization alone does not
map them together.

A reference-data mapping may be required.
"""

country_mapping = {
    "usa": "United States",
    "us": "United States",
    "united states": "United States",
    "india": "India",
}

raw_country_values = ["USA", "US", "India", "United States"]

standardized_country_values = [
    country_mapping.get(value.casefold(), value)
    for value in raw_country_values
]

print("\nStandardized country values:")
print(standardized_country_values)


# ============================================================================
# 59. DIMENSION TABLE CONCEPT
# ============================================================================

"""
A dimension table stores descriptive context.

Example customer dimension:

    customer_key
    customer_id
    country
    segment

A fact table stores events/measures:

    customer_key
    date_key
    product_key
    quantity
    revenue

This separation supports analytical querying and dimensional modeling.
"""

customer_dimension = [
    {
        "customer_key": 1,
        "customer_id": "CUS-1001",
        "country": "India",
        "segment": "Premium",
    },
    {
        "customer_key": 2,
        "customer_id": "CUS-1002",
        "country": "Japan",
        "segment": "Standard",
    },
]

sales_fact = [
    {
        "customer_key": 1,
        "quantity": 3,
        "revenue": 120000,
    },
    {
        "customer_key": 2,
        "quantity": 2,
        "revenue": 80000,
    },
]

print("\nCustomer dimension:")
for row in customer_dimension:
    print(row)

print("\nSales fact:")
for row in sales_fact:
    print(row)


# ============================================================================
# 60. DIMENSION + FACT JOIN
# ============================================================================

customer_lookup = {
    row["customer_key"]: row
    for row in customer_dimension
}

joined_sales = []

for fact in sales_fact:
    customer = customer_lookup[fact["customer_key"]]

    joined_sales.append(
        {
            **fact,
            "customer_id": customer["customer_id"],
            "country": customer["country"],
            "segment": customer["segment"],
        }
    )

print("\nJoined analytical records:")
for row in joined_sales:
    print(row)


# ============================================================================
# 61. AGGREGATING MEASURES BY DIMENSION
# ============================================================================

revenue_by_country: dict[str, float] = {}

for row in joined_sales:
    country = row["country"]
    revenue_by_country[country] = (
        revenue_by_country.get(country, 0.0)
        + row["revenue"]
    )

print("\nRevenue by country:")
for country, revenue in revenue_by_country.items():
    print(country, revenue)


# ============================================================================
# 62. DATA TYPE CHOICE AND STORAGE
# ============================================================================

"""
Storage choices affect:
    - memory usage
    - disk usage
    - query performance
    - indexing
    - interoperability
    - precision

Examples:

Boolean:
    compact Boolean representation is preferable to arbitrary strings.

Integer:
    use an appropriate integer width when the storage system supports it.

Decimal:
    useful for exact decimal arithmetic.

Timestamp:
    use a standardized representation with explicit timezone semantics.

Text:
    choose appropriate character encoding and length constraints.

Categorical:
    dictionary encoding or category codes can reduce repeated storage.
"""

print("\nStorage principle:")
print(
    "Choose a representation that preserves meaning, precision, "
    "validation requirements, and operational needs."
)


# ============================================================================
# 63. CATEGORICAL COMPRESSION IDEA
# ============================================================================

"""
If a column contains millions of repeated category strings, storing the same
string repeatedly can be inefficient.

Dictionary encoding conceptually stores:

    0 -> India
    1 -> Japan
    2 -> Germany

Then rows can store:

    0, 1, 0, 2, 0

This is a storage optimization, not proof that categories are ordinal.
"""

category_dictionary = {
    index: category
    for index, category in enumerate(
        ["India", "Japan", "Germany"]
    )
}

category_codes = [0, 1, 0, 2, 0]

decoded_categories = [
    category_dictionary[code]
    for code in category_codes
]

print("\nDictionary encoding:")
print("Dictionary:", category_dictionary)
print("Codes:", category_codes)
print("Decoded:", decoded_categories)


# ============================================================================
# 64. DATA TYPE AND DATABASE DESIGN
# ============================================================================

"""
Database schemas should distinguish:

    quantity columns
    identifiers
    codes
    timestamps
    descriptive text
    Boolean flags
    monetary values

Good schema design prevents many downstream errors.

For example:

    customer_id should have uniqueness constraints.

    revenue should use a suitable exact numeric type.

    created_at should have an explicit temporal type.

    country_code should be constrained to an approved code system.
"""

database_schema_example = {
    "customer_id": "identifier",
    "country_code": "nominal category",
    "created_at": "timestamp",
    "order_quantity": "discrete measure",
    "unit_price": "decimal monetary measure",
    "customer_note": "text",
    "is_active": "binary",
}

print("\nConceptual database schema:")
for field, semantic_type in database_schema_example.items():
    print(f"{field:20} -> {semantic_type}")


# ============================================================================
# 65. SECURITY CONSIDERATIONS
# ============================================================================

"""
Data classification also has security and privacy implications.

Potentially sensitive fields may include:
    - identifiers
    - location
    - free-form text
    - personal contact information
    - transaction records

Security decisions should consider:
    - access control
    - encryption
    - masking
    - tokenization
    - retention
    - logging
    - minimization

A field being textual, numeric, or categorical says nothing by itself about
whether it is sensitive.

Sensitivity is a separate classification dimension.
"""

sensitive_data_example = {
    "customer_id": "identifier",
    "email": "textual",
    "latitude": "geographic",
    "purchase_amount": "numeric measure",
}

print("\nSecurity classification must be considered separately:")
for field, data_type in sensitive_data_example.items():
    print(f"{field:18} -> {data_type}")


# ============================================================================
# 66. TEXT AND SECURITY
# ============================================================================

"""
Free-form text can unexpectedly contain sensitive information.

For example, a customer note might contain:
    - names
    - phone numbers
    - addresses
    - account numbers
    - confidential business information

Text pipelines therefore require careful handling of logging and access.
"""

customer_note = (
    "Customer says the delivery was delayed and asks support for assistance."
)

print("\nCustomer note:")
print(customer_note)


# ============================================================================
# 67. GEOGRAPHIC DATA AND PRIVACY
# ============================================================================

"""
Geographic precision can influence privacy risk.

A broad region:

    country = "India"

contains less spatial precision than:

    latitude = 26.8467
    longitude = 80.9462

High-precision location can be sensitive depending on context.

Data minimization may therefore favor lower precision when exact location is
not necessary for the business purpose.
"""

location_precision = {
    "country": "India",
    "region": "Northern India",
    "city": "Lucknow",
    "latitude": 26.8467,
    "longitude": 80.9462,
}

print("\nLocation representations:")
for key, value in location_precision.items():
    print(f"{key:12} -> {value}")


# ============================================================================
# 68. COMMON CLASSIFICATION MISTAKES
# ============================================================================

mistakes = [
    "Treating identifiers as measures.",
    "Treating postal codes as quantities.",
    "Using arbitrary numeric codes as if nominal categories were ordered.",
    "Assuming every integer variable is discrete quantitative data.",
    "Assuming every float is continuous measurement data.",
    "Ignoring timezone semantics in timestamps.",
    "Dropping leading zeros from identifiers.",
    "Summing percentages.",
    "Summing account balances across time.",
    "Assuming missing and zero mean the same thing.",
    "Assuming string representation determines semantic type.",
    "Using identifiers blindly as machine-learning features.",
]

print("\nCommon mistakes:")
for number, mistake in enumerate(mistakes, start=1):
    print(f"{number:2}. {mistake}")


# ============================================================================
# 69. COMPARISON: DISCRETE VS CONTINUOUS
# ============================================================================

"""
Discrete:
    countable values.

Continuous:
    values within a range.

Example:

    Number of support tickets = discrete.

    Resolution time = continuous in principle.

A measured duration may be stored as integer seconds, but its conceptual
nature can still be continuous.
"""

discrete_vs_continuous = {
    "number_of_tickets": "discrete",
    "resolution_time_seconds": "continuous conceptually",
    "number_of_products": "discrete",
    "product_weight_kg": "continuous",
}

print("\nDiscrete vs continuous:")
for field, classification in discrete_vs_continuous.items():
    print(f"{field:28} -> {classification}")


# ============================================================================
# 70. COMPARISON: NUMERIC VS CATEGORICAL
# ============================================================================

"""
Numeric asks:

    Does the value represent a quantity?

Categorical asks:

    Does the value identify membership in a category?

Examples:

    revenue = 50000
        -> numeric measure

    product_code = 50000
        -> categorical/identifier-like code

The same Python type can represent either.
"""

numeric_vs_categorical = [
    ("revenue", 50000, "numeric measure"),
    ("product_code", 50000, "categorical/code"),
    ("customer_id", 50000, "identifier"),
]

print("\nNumeric vs categorical:")
for name, value, meaning in numeric_vs_categorical:
    print(f"{name:16} {value:8} -> {meaning}")


# ============================================================================
# 71. COMPARISON: ORDINAL VS NOMINAL
# ============================================================================

nominal_example = ["Small", "Large", "Medium"]
ordinal_example = ["Low", "Medium", "High"]

print("\nNominal example:")
print(nominal_example)

print("Ordinal example:")
print(ordinal_example)

print(
    "Nominal categories do not require an intrinsic order; ordinal categories do."
)


# ============================================================================
# 72. COMPARISON: IDENTIFIER VS DIMENSION
# ============================================================================

"""
An identifier answers:

    "Which entity is this?"

A dimension answers:

    "What descriptive context does this entity have?"

Customer ID identifies the customer.

Country describes a geographic attribute of the customer.

An identifier can participate in dimension modeling as a key, but its role is
different from descriptive analytical attributes.
"""

identifier_vs_dimension = {
    "customer_id": "identifies entity",
    "customer_country": "describes entity",
    "customer_segment": "describes entity",
}

print("\nIdentifier vs dimension:")
for field, role in identifier_vs_dimension.items():
    print(f"{field:22} -> {role}")


# ============================================================================
# 73. ROBUST DATA CLASSIFICATION RECORD
# ============================================================================

@dataclass
class DataField:
    name: str
    value: Any
    storage_type: str
    semantic_types: tuple[str, ...]
    measurement_scale: Optional[str]
    role: Optional[str]
    nullable: bool
    description: str


fields = [
    DataField(
        name="customer_id",
        value="CUS-1001",
        storage_type="string",
        semantic_types=("identifier", "nominal"),
        measurement_scale="nominal",
        role="key",
        nullable=False,
        description="Unique customer identifier.",
    ),
    DataField(
        name="revenue",
        value=125000.50,
        storage_type="decimal-like",
        semantic_types=("numeric", "continuous", "measure"),
        measurement_scale="ratio",
        role="measure",
        nullable=False,
        description="Revenue from the transaction.",
    ),
    DataField(
        name="country",
        value="India",
        storage_type="string",
        semantic_types=("categorical", "nominal", "dimension"),
        measurement_scale="nominal",
        role="dimension",
        nullable=False,
        description="Customer country.",
    ),
    DataField(
        name="satisfaction",
        value="High",
        storage_type="string",
        semantic_types=("categorical", "ordinal", "dimension"),
        measurement_scale="ordinal",
        role="dimension",
        nullable=True,
        description="Customer satisfaction category.",
    ),
]

print("\nComprehensive field metadata:")
for field in fields:
    print(
        f"{field.name}: "
        f"storage={field.storage_type}, "
        f"semantic={field.semantic_types}, "
        f"scale={field.measurement_scale}, "
        f"role={field.role}"
    )


# ============================================================================
# 74. TYPE-APPROPRIATE OPERATIONS
# ============================================================================

"""
Operations should respect semantics.

Nominal:
    count, mode, equality, grouping.

Ordinal:
    ordering, rank, median in suitable contexts.

Numeric:
    sum, mean, variance, min, max, arithmetic where justified.

Temporal:
    ordering, difference, extraction, windowing.

Text:
    search, tokenization, pattern matching, linguistic processing.

Geographic:
    distance, containment, proximity, spatial joins.

Identifier:
    equality, lookup, uniqueness, joins.
"""

operations = {
    "nominal": ["count", "mode", "group_by"],
    "ordinal": ["rank", "order", "median"],
    "numeric": ["sum", "mean", "variance"],
    "temporal": ["sort", "difference", "window"],
    "textual": ["search", "tokenize", "pattern_match"],
    "geographic": ["distance", "proximity", "spatial_join"],
    "identifier": ["lookup", "join", "uniqueness"],
}

print("\nTypical operations:")
for data_type, allowed_operations in operations.items():
    print(f"{data_type:12} -> {', '.join(allowed_operations)}")


# ============================================================================
# 75. STATISTICAL SUMMARY DEPENDS ON DATA TYPE
# ============================================================================

"""
Different data types support different summaries.

Nominal:
    frequency, mode.

Ordinal:
    frequency, mode, median, rank.

Numeric:
    mean, median, variance, standard deviation, quantiles.

Binary:
    prevalence/proportion, count.

Temporal:
    earliest, latest, duration, temporal frequency.

Identifier:
    count distinct, uniqueness rate.

Text:
    length, token frequency, linguistic statistics.

Geographic:
    bounding box, centroid, spatial density, distance statistics.
"""

nominal_values = ["A", "B", "A", "C", "A"]
ordinal_values_for_summary = [1, 2, 3, 3, 2]
numeric_values_for_summary = [10, 20, 30, 40, 50]

print("\nStatistical summaries:")
print("Nominal mode:", Counter(nominal_values).most_common(1)[0][0])
print("Ordinal median:", statistics.median(ordinal_values_for_summary))
print("Numeric mean:", statistics.mean(numeric_values_for_summary))
print(
    "Numeric standard deviation:",
    statistics.stdev(numeric_values_for_summary),
)


# ============================================================================
# 76. EDGE CASES
# ============================================================================

"""
Important edge cases include:

    - a binary variable with missing values
    - an ordinal variable with inconsistent labels
    - a numeric column containing strings
    - timestamps with mixed timezones
    - geographic coordinates outside valid ranges
    - identifiers converted to integers
    - numeric-looking category codes
    - percentages stored as 0.25 versus 25
    - monetary values represented using binary floating point
    - text containing structured identifiers
"""

percentage_fraction = 0.25
percentage_integer = 25

print("\nPercentage representation ambiguity:")
print("0.25 may mean a fraction representing 25%.")
print("25 may mean 25%.")
print(
    "The schema must specify which representation is expected."
)


# ============================================================================
# 77. PERCENTAGE SEMANTICS
# ============================================================================

def normalize_percentage(value: float, representation: str) -> float:
    """
    Normalize percentage to a fraction between 0 and 1.

    representation:
        "fraction" -> 0.25 means 25%
        "percent"  -> 25 means 25%
    """
    if representation == "fraction":
        if not 0 <= value <= 1:
            raise ValueError("Fractional percentage must be between 0 and 1.")
        return value

    if representation == "percent":
        if not 0 <= value <= 100:
            raise ValueError("Percentage must be between 0 and 100.")
        return value / 100

    raise ValueError("Representation must be 'fraction' or 'percent'.")


print("\nNormalized percentages:")
print(normalize_percentage(0.25, "fraction"))
print(normalize_percentage(25, "percent"))


# ============================================================================
# 78. WHY SEMANTIC METADATA MATTERS
# ============================================================================

"""
A robust data system benefits from metadata such as:

    field name
    business definition
    storage type
    semantic type
    unit
    measurement scale
    allowed values
    nullability
    uniqueness
    sensitivity classification
    aggregation rule
    source system
    update frequency

Without metadata, identical-looking values can easily be interpreted
incorrectly.
"""

metadata_fields = [
    "name",
    "business_definition",
    "storage_type",
    "semantic_type",
    "unit",
    "measurement_scale",
    "allowed_values",
    "nullable",
    "unique",
    "aggregation_rule",
    "sensitivity",
]

print("\nUseful metadata fields:")
for field_name in metadata_fields:
    print("-", field_name)


# ============================================================================
# 79. UNIT OF MEASURE
# ============================================================================

"""
A numeric value without its unit may be ambiguous.

Examples:

    10

could mean:
    10 kg
    10 meters
    10 seconds
    10 dollars
    10 percent

Units are therefore an essential part of semantic classification.
"""

measurements = [
    {"value": 10, "unit": "kg"},
    {"value": 10, "unit": "seconds"},
    {"value": 10, "unit": "percent"},
]

print("\nNumeric values with units:")
for measurement in measurements:
    print(measurement)


# ============================================================================
# 80. CONVERSION WITH UNITS
# ============================================================================

def kilometers_to_meters(kilometers: float) -> float:
    return kilometers * 1000


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


print("\nUnit conversions:")
print("5 km -> meters:", kilometers_to_meters(5))
print("25 C -> Fahrenheit:", celsius_to_fahrenheit(25))


# ============================================================================
# 81. DATA TYPE AND API DESIGN
# ============================================================================

"""
APIs should communicate semantic expectations clearly.

Examples:

    quantity: integer >= 0
    price: decimal >= 0
    country: controlled string category
    active: Boolean
    created_at: timezone-aware timestamp
    customer_id: identifier string

Good API schemas reduce ambiguity between systems.
"""

api_schema_concept = {
    "customer_id": {
        "representation": "string",
        "semantic_type": "identifier",
        "required": True,
    },
    "quantity": {
        "representation": "integer",
        "semantic_type": "discrete measure",
        "minimum": 0,
    },
    "active": {
        "representation": "boolean",
        "semantic_type": "binary",
    },
    "created_at": {
        "representation": "timestamp",
        "semantic_type": "temporal",
        "timezone": "UTC",
    },
}

print("\nConceptual API schema:")
for field, definition in api_schema_concept.items():
    print(field, "->", definition)


# ============================================================================
# 82. DATA TYPE AND FILE FORMATS
# ============================================================================

"""
Different formats represent types differently.

CSV:
    values are fundamentally text and require interpretation.

JSON:
    supports strings, numbers, Boolean values, null, arrays, objects.

Parquet:
    supports strongly typed columns and efficient analytical storage.

A CSV column containing:

    00123

may be interpreted as either:
    - identifier
    - integer

The schema should prevent accidental interpretation.
"""

csv_like_values = ["00123", "00124", "00125"]

print("\nCSV-like raw values:")
print(csv_like_values)

print(
    "A schema-aware ingestion process should decide whether these values "
    "represent codes or quantities."
)


# ============================================================================
# 83. DATA TYPE DRIFT
# ============================================================================

"""
Data type drift occurs when a field's representation or meaning changes.

Example:

Day 1:
    revenue = 100.50

Day 2:
    revenue = "100.50"

Day 3:
    revenue = "unknown"

This can break downstream systems.

Schema monitoring should detect unexpected changes.
"""

daily_revenue_values = [
    100.50,
    200.25,
    "300.75",
    "unknown",
]

print("\nPotential type drift:")
for value in daily_revenue_values:
    print(value, "->", type(value).__name__)


# ============================================================================
# 84. SCHEMA DRIFT DETECTION
# ============================================================================

def observed_python_types(values: Iterable[Any]) -> set[str]:
    return {type(value).__name__ for value in values}


print(
    "\nObserved types:",
    observed_python_types(daily_revenue_values),
)


# ============================================================================
# 85. DATA PROFILING
# ============================================================================

"""
Data profiling examines a dataset before analysis.

Typical profiling includes:

    row count
    missing count
    distinct count
    minimum
    maximum
    average
    frequency distribution
    data type distribution
    invalid values
    duplicates

Profiling helps discover incorrect assumptions.
"""

def numeric_profile(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("Cannot profile an empty numeric collection.")

    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
    }


print(
    "\nNumeric profile:",
    numeric_profile([10, 20, 30, 40, 50]),
)


# ============================================================================
# 86. PERFORMANCE: CHOOSING THE RIGHT REPRESENTATION
# ============================================================================

"""
Performance considerations include:

    - smaller numeric representations can reduce memory usage
    - categorical dictionary encoding can reduce repeated storage
    - indexes can accelerate identifier lookup
    - timestamps can support efficient range filtering
    - text indexing can improve search
    - high-cardinality one-hot encoding can become expensive

Correct representation is often both a correctness and performance concern.
"""

large_category_example = ["India"] * 1000 + ["Japan"] * 1000

print("\nRepeated category count:", len(large_category_example))
print("Distinct categories:", len(set(large_category_example)))


# ============================================================================
# 87. COMPUTATIONAL COMPLEXITY OF COMMON OPERATIONS
# ============================================================================

"""
For a Python set:

    membership lookup is typically O(1) average case.

For a list:

    membership lookup is O(n) in the general case.

This matters for validating categorical values against a large allowed set.
"""

allowed_categories_list = ["A", "B", "C", "D", "E"]
allowed_categories_set = set(allowed_categories_list)

candidate = "E"

print("\nMembership with list:", candidate in allowed_categories_list)
print("Membership with set:", candidate in allowed_categories_set)

print(
    "A set is generally preferable for repeated membership validation."
)


# ============================================================================
# 88. VALIDATING CONTROLLED CATEGORIES
# ============================================================================

def validate_controlled_category(
    value: str,
    allowed_values: set[str],
) -> None:
    if value not in allowed_values:
        raise ValueError(
            f"Invalid category {value!r}. "
            f"Expected one of {sorted(allowed_values)}."
        )


allowed_statuses = {"Pending", "Approved", "Rejected"}

for status in ["Approved", "Unknown"]:
    try:
        validate_controlled_category(status, allowed_statuses)
        print(f"{status}: valid")
    except ValueError as error:
        print(f"{status}: invalid -> {error}")


# ============================================================================
# 89. ORDINAL CONSISTENCY
# ============================================================================

"""
Ordinal categories should have one consistent ordering.

If one system defines:

    Low < Medium < High

and another defines:

    High < Medium < Low

the values cannot be reliably compared.

Centralized metadata should define the canonical ordering.
"""

canonical_order = ["Low", "Medium", "High"]

canonical_rank = {
    category: rank
    for rank, category in enumerate(canonical_order)
}

print("\nCanonical ordinal ranks:", canonical_rank)


# ============================================================================
# 90. TEXT LENGTH AND DATA QUALITY
# ============================================================================

texts = [
    "Good product.",
    "",
    "Customer requested a refund because the product arrived damaged.",
]

text_lengths = [len(text) for text in texts]

print("\nText lengths:")
print(text_lengths)

print("Empty text values:", sum(length == 0 for length in text_lengths))


# ============================================================================
# 91. TEMPORAL GRANULARITY
# ============================================================================

"""
Temporal data has granularity.

Examples:
    year
    quarter
    month
    week
    day
    hour
    minute
    second
    millisecond

A date and a timestamp are not interchangeable.

2026-09-04

does not identify a specific time of day.

2026-09-04 14:30:15

contains finer temporal information.
"""

date_only = date(2026, 9, 4)
timestamp_with_time = datetime(2026, 9, 4, 14, 30, 15)

print("\nTemporal granularity:")
print("Date:", date_only)
print("Timestamp:", timestamp_with_time)


# ============================================================================
# 92. DATE VS DURATION
# ============================================================================

"""
A date identifies a point on a calendar.

A duration represents elapsed time.

Examples:

    2026-09-04 -> date

    7 days -> duration

They should not be treated as interchangeable data types.
"""

seven_days = timedelta(days=7)

print("\nDate:", date_only)
print("Duration:", seven_days)


# ============================================================================
# 93. GEOGRAPHIC HIERARCHIES
# ============================================================================

"""
Geographic dimensions may have hierarchical relationships:

    Country
      State/Province
        City
          Postal Code
            Street

Not every hierarchy is perfectly strict in real-world datasets. Administrative
boundaries can overlap, change over time, and depend on the geographic
reference system.
"""

geographic_hierarchy = [
    ("Country", "India"),
    ("State", "Uttar Pradesh"),
    ("City", "Lucknow"),
]

print("\nGeographic hierarchy:")
for level, value in geographic_hierarchy:
    print(f"{level:12} -> {value}")


# ============================================================================
# 94. GEOGRAPHIC COORDINATE EDGE CASES
# ============================================================================

invalid_coordinates = [
    (91, 0),
    (0, 181),
    (-91, 0),
    (0, -181),
]

print("\nInvalid geographic coordinates:")
for lat, lon in invalid_coordinates:
    print(
        (lat, lon),
        "->",
        validate_coordinate(lat, lon),
    )


# ============================================================================
# 95. IDENTIFIERS AND PERSISTENCE
# ============================================================================

"""
Identifiers may be:

    natural keys
    surrogate keys
    UUIDs
    composite keys

Natural key:
    derived from business data.

Surrogate key:
    artificial database key.

Composite key:
    multiple fields jointly identify a record.

The best choice depends on system requirements, stability, uniqueness,
performance, and integration needs.
"""

key_examples = {
    "natural_key": "email@example.com",
    "surrogate_key": 100001,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "composite_key": ("2026-09-04", "STORE-001", "SKU-100"),
}

print("\nIdentifier examples:")
for key_type, example in key_examples.items():
    print(f"{key_type:16} -> {example}")


# ============================================================================
# 96. COMPOSITE IDENTIFIERS
# ============================================================================

"""
A composite identifier uses multiple fields.

For example:

    (date, store_id, product_id)

may identify one fact record.

Composite keys should be evaluated for:
    - uniqueness
    - stability
    - nullability
    - indexing
    - storage cost
"""

composite_records = [
    ("2026-09-04", "STORE-1", "SKU-1"),
    ("2026-09-04", "STORE-1", "SKU-2"),
    ("2026-09-05", "STORE-1", "SKU-1"),
]

print("\nComposite identifiers:")
print("Unique:", len(composite_records) == len(set(composite_records)))


# ============================================================================
# 97. DATA TYPE INTERACTIONS
# ============================================================================

"""
Real datasets contain combinations of types.

A sales transaction might contain:

    transaction_id -> identifier
    transaction_time -> temporal
    customer_id -> identifier
    country -> nominal dimension
    product -> nominal dimension
    quantity -> discrete measure
    unit_price -> continuous/decimal measure
    discount_percent -> ratio measure
    review -> textual
    latitude -> geographic
    longitude -> geographic
    is_returned -> binary

Correct analysis requires understanding the whole schema.
"""

transaction = {
    "transaction_id": "TXN-9001",
    "transaction_time": datetime(2026, 9, 4, 10, 15),
    "customer_id": "CUS-1001",
    "country": "India",
    "product": "Laptop",
    "quantity": 2,
    "unit_price": Decimal("75000.00"),
    "discount_percent": Decimal("10.00"),
    "review": "Fast delivery and good packaging.",
    "latitude": 26.8467,
    "longitude": 80.9462,
    "is_returned": False,
}

print("\nExample complete transaction:")
for field_name, value in transaction.items():
    print(f"{field_name:20} -> {value!r}")


# ============================================================================
# 98. DERIVING REVENUE
# ============================================================================

gross_amount = (
    transaction["quantity"]
    * transaction["unit_price"]
)

discount_amount = (
    gross_amount
    * transaction["discount_percent"]
    / Decimal("100")
)

net_amount = gross_amount - discount_amount

print("\nTransaction measures:")
print("Gross:", gross_amount)
print("Discount:", discount_amount)
print("Net:", net_amount)


# ============================================================================
# 99. TESTING DATA CLASSIFICATION FUNCTIONS
# ============================================================================

"""
Educational tests help prevent silent classification and validation errors.

These are simple assertion-based tests rather than a dependency on a testing
framework.
"""

assert validate_latitude(0)
assert validate_latitude(90)
assert validate_latitude(-90)
assert not validate_latitude(90.1)

assert validate_longitude(0)
assert validate_longitude(180)
assert validate_longitude(-180)
assert not validate_longitude(180.1)

assert validate_age(33)
assert not validate_age(-1)
assert not validate_age(200)

assert validate_percentage(0)
assert validate_percentage(100)
assert not validate_percentage(101)

assert is_missing(None)
assert is_missing(float("nan"))
assert is_missing("")
assert not is_missing(0)
assert not is_missing(False)

print("\nAll basic validation assertions passed.")


# ============================================================================
# 100. INTEGRATED DATA PROFILING EXAMPLE
# ============================================================================

dataset = [
    {
        "customer_id": "CUS-001",
        "country": "India",
        "age": 30,
        "active": True,
        "revenue": 10000.50,
        "order_date": date(2026, 9, 1),
        "review": "Good service.",
    },
    {
        "customer_id": "CUS-002",
        "country": "Japan",
        "age": 42,
        "active": False,
        "revenue": 20000.75,
        "order_date": date(2026, 9, 2),
        "review": "Fast delivery.",
    },
    {
        "customer_id": "CUS-003",
        "country": "India",
        "age": 35,
        "active": True,
        "revenue": 15000.00,
        "order_date": date(2026, 9, 3),
        "review": "",
    },
]


def profile_dataset(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Produce a basic field-level data profile."""
    if not records:
        return {}

    fields = records[0].keys()
    profile = {}

    for field in fields:
        values = [record.get(field) for record in records]

        profile[field] = {
            "count": len(values),
            "missing": sum(is_missing(value) for value in values),
            "distinct": len(set(values)),
            "python_types": sorted(observed_python_types(values)),
        }

    return profile


integrated_profile = profile_dataset(dataset)

print("\nIntegrated dataset profile:")
for field, profile in integrated_profile.items():
    print(field, "->", profile)


# ============================================================================
# 101. TYPE-AWARE ANALYTICAL PIPELINE
# ============================================================================

"""
A simplified analytical workflow can be:

    1. Identify fields.
    2. Inspect raw representation.
    3. Determine semantic meaning.
    4. Assign data type classifications.
    5. Validate values.
    6. Handle missingness.
    7. Normalize representations.
    8. Select appropriate transformations.
    9. Select appropriate aggregations.
    10. Monitor quality and drift.

The order may differ by application, but semantic understanding should happen
before irreversible transformations.
"""

pipeline_steps = [
    "Inspect",
    "Understand",
    "Classify",
    "Validate",
    "Normalize",
    "Transform",
    "Aggregate",
    "Monitor",
]

print("\nType-aware analytical pipeline:")
for step_number, step in enumerate(pipeline_steps, start=1):
    print(f"{step_number}. {step}")


# ============================================================================
# 102. FINAL INTEGRATED CLASSIFICATION
# ============================================================================

"""
The following records demonstrate how one dataset can contain nearly every
major type discussed in this script.
"""

final_schema = {
    "customer_id": {
        "types": ["identifier", "nominal"],
        "role": "key",
    },
    "age": {
        "types": ["numeric", "discrete"],
        "role": "measure",
    },
    "height_cm": {
        "types": ["numeric", "continuous"],
        "role": "measure",
    },
    "country": {
        "types": ["categorical", "nominal"],
        "role": "dimension",
    },
    "satisfaction": {
        "types": ["categorical", "ordinal"],
        "role": "dimension",
    },
    "is_active": {
        "types": ["binary"],
        "role": "attribute",
    },
    "order_count": {
        "types": ["numeric", "discrete"],
        "role": "measure",
    },
    "revenue": {
        "types": ["numeric", "continuous", "ratio"],
        "role": "measure",
    },
    "order_timestamp": {
        "types": ["temporal"],
        "role": "dimension/time attribute",
    },
    "review": {
        "types": ["textual"],
        "role": "descriptive attribute",
    },
    "latitude": {
        "types": ["numeric", "geographic"],
        "role": "spatial attribute",
    },
    "longitude": {
        "types": ["numeric", "geographic"],
        "role": "spatial attribute",
    },
}

print("\nFinal integrated schema:")
for field_name, definition in final_schema.items():
    print(
        f"{field_name:20} -> "
        f"types={definition['types']}, "
        f"role={definition['role']}"
    )


# ============================================================================
# 103. CORE PRINCIPLES ENFORCED BY THIS SCRIPT
# ============================================================================

"""
Core principles:

1. Representation is not meaning.
2. Numeric-looking data is not necessarily quantitative.
3. Strings are not necessarily textual.
4. Integer values are not necessarily discrete measures.
5. Float values are not automatically continuous measurements.
6. Nominal categories have no intrinsic order.
7. Ordinal categories have order but not necessarily equal intervals.
8. Binary data has two states.
9. Temporal data requires precision and timezone awareness where relevant.
10. Geographic data requires spatial semantics.
11. Identifiers identify; they do not normally measure.
12. Measures are analyzed quantitatively.
13. Dimensions provide analytical context.
14. A field may have multiple simultaneous classifications.
15. Units are part of meaning.
16. Missingness is different from zero or false.
17. Data validation must reflect domain rules.
18. Aggregation must respect measure semantics.
19. Encoding must preserve semantic relationships.
20. Security and privacy are separate classification dimensions.
21. Metadata is essential for reliable interpretation.
22. Data type decisions affect correctness, storage, performance, and modeling.
"""

core_principles = [
    "Representation is not meaning.",
    "Numeric-looking data is not necessarily quantitative.",
    "Identifiers identify rather than measure.",
    "Nominal data has categories without intrinsic order.",
    "Ordinal data has meaningful order.",
    "Discrete data is countable.",
    "Continuous data represents measurable quantities.",
    "Temporal data requires explicit temporal semantics.",
    "Geographic data requires spatial semantics.",
    "Measures and dimensions have different analytical roles.",
    "Missingness must not be confused with zero or false.",
    "Units are part of numerical meaning.",
    "Semantic metadata is essential.",
]

print("\nCore principles:")
for number, principle in enumerate(core_principles, start=1):
    print(f"{number:2}. {principle}")


# ============================================================================
# 104. SCRIPT COMPLETION
# ============================================================================

print("\n" + "=" * 80)
print("DATA TYPE STUDY SCRIPT COMPLETED")
print("=" * 80)
print(
    "The demonstrations above cover representation, semantic classification, "
    "measurement scales, analytical roles, validation, encoding, edge cases, "
    "and practical data engineering considerations."
)
