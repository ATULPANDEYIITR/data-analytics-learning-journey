# Pandas Data Cleaning

This project models a realistic customer dataset that contains missing values, duplicate records, inconsistent strings, invalid numeric values, inconsistent dates, and categorical inconsistencies.

The five implementations deliberately use different programming perspectives:

| File | Primary perspective | Main purpose |
|---|---|---|
| Python | Pandas data-processing workflow | Build and execute a complete tabular cleaning pipeline |
| JavaScript | Event-driven data-processing model | Apply validation and normalization through objects, collections, and asynchronous execution |
| C++17 | Data-quality engine | Implement explicit validation, deduplication, and statistical imputation with standard-library data structures |
| Java 17 | Enterprise domain model | Represent cleaning rules with immutable records, enums, validation exceptions, and service boundaries |
| PostgreSQL | Relational data-quality workflow | Enforce cleaning and integrity rules through SQL types, constraints, functions, indexes, views, triggers, and transactions |

The central distinction is between **cleaning a value**, **validating a value**, and **deciding what should happen when a value cannot be trusted**.

---

## Data Quality Scenario

The source dataset represents customer records:

| Field | Intended meaning | Typical quality problem |
|---|---|---|
| `customer_id` | Stable customer identity | Duplicate identifiers |
| `name` | Customer name | Leading spaces, repeated spaces, missing values |
| `age` | Integer customer age | Empty strings, `unknown`, impossible values |
| `email` | Customer contact identity | Uppercase values, spaces, missing values |
| `city` | Customer location | Empty strings and inconsistent capitalization |
| `segment` | Business classification | `standard` versus `Standard` |
| `signup_date` | Registration date | Different separators and invalid dates |
| `orders` | Number of orders | Missing and invalid numeric values |

The sample contains a deliberate duplicate for customer `101/104` in order to demonstrate identity-based duplicate handling.

The value `George Sen` has an age of `-5`. This is not treated as an ordinary missing value. It is an invalid value that must first be rejected by the range rule before any missing-value strategy can be applied.

---

## Missing Values

Missing data and invalid data are separate conditions.

A blank age means that the source does not provide an age. A value such as `-5` provides a value, but that value violates the domain rule. The implementations normalize both into a state that can be processed safely, but they do not claim that the original source was correct.

The Python implementation uses Pandas nullable values and performs numeric conversion with `errors="coerce"`. Invalid values therefore become missing values that can be evaluated by subsequent rules.

Numeric fields use median imputation:

- `age` uses the median valid age.
- `orders` uses the median valid order count.
- Missing names become `Unknown Customer`.
- Missing cities become `Unknown`.
- Missing segments default to `Standard`.
- Missing emails remain missing.

Email is intentionally not fabricated. Creating an artificial email address would create false identity information rather than repair the source data.

The JavaScript, C++, and Java implementations reproduce the same policy through explicit nullable values rather than relying on a dataframe's missing-value representation.

The PostgreSQL workflow performs median calculation with `percentile_cont(0.5)` and applies the resulting values during insertion into the typed `customers` table.

---

## Duplicate Records

Duplicate detection requires a definition of identity.

The implementations treat `customer_id` as the authoritative business key. A repeated customer identifier therefore represents the same customer unless a different upstream identity policy is explicitly established.

Email is also checked when present. Two records with the same normalized email are treated as duplicate identities.

The Python implementation uses `drop_duplicates()` with explicit subsets.

The JavaScript implementation uses `Set` objects for customer IDs and normalized email addresses.

The C++ implementation uses `std::set`, making duplicate detection explicit and deterministic.

The Java implementation uses `HashSet` collections inside the cleaning service.

The PostgreSQL model makes `customer_id` a primary key and creates a partial unique index on normalized non-null email values.

This distinction matters because missing emails should not cause every record with no email to be considered a duplicate.

---

## Type Conversion

Raw data frequently arrives as strings even when the logical values are numeric or temporal.

The Python pipeline converts:

- `customer_id` to a nullable integer type.
- `age` to an integer.
- `orders` to an integer.
- `signup_date` to a datetime value.

Invalid conversions are not silently interpreted as valid data.

The JavaScript implementation explicitly parses integers and dates. `Number.isInteger()` prevents values such as fractional numbers from entering integer fields.

The C++ implementation uses `std::stoi` with validation of the complete input string. This prevents a value containing a valid numeric prefix and invalid trailing characters from being accepted accidentally.

The Java implementation uses `Integer.parseInt()` and `LocalDate.parse()`. Failed conversions increment the cleaning metrics and produce nullable values.

PostgreSQL separates the raw text representation from the typed relational representation. The `safe_integer()` and `safe_date()` functions perform guarded conversion before values reach the strongly constrained `customers` table.

---

## String Cleaning

String normalization is applied before duplicate detection where string identity matters.

The common transformations include:

- Removing leading and trailing whitespace.
- Collapsing repeated internal whitespace.
- Normalizing email addresses to lowercase.
- Converting customer names and cities to title case.
- Converting categorical values to a canonical representation.

For example:

`" Alice  Sharma "` becomes `Alice Sharma`.

`" ALICE.SHARMA@EXAMPLE.COM "` becomes `alice.sharma@example.com`.

`"premium"` becomes the canonical category `Premium`.

The Python implementation uses Pandas vectorized string operations such as `str.strip()`, `str.replace()`, `str.lower()`, and `str.title()`.

The JavaScript implementation uses regular expressions and string transformations.

The C++ implementation builds explicit string normalization functions using standard-library character processing.

The Java implementation isolates string normalization inside the domain service.

PostgreSQL uses `trim`, `regexp_replace`, `lower`, and `initcap`.

---

## Categorical Data

Categorical values should have a controlled vocabulary rather than accepting arbitrary strings.

The permitted customer segments are:

| Canonical value | Meaning |
|---|---|
| `Standard` | Normal customer segment |
| `Premium` | Higher-value customer segment |
| `Enterprise` | Enterprise customer segment |

The Python implementation creates a Pandas `Categorical` column with an explicit category list.

The JavaScript implementation uses a `Set` to represent the allowed vocabulary.

The C++ implementation validates the normalized segment against a `std::set`.

The Java implementation uses the `CustomerSegment` enum. This prevents arbitrary category strings from becoming domain values.

PostgreSQL enforces the same rule with a `CHECK` constraint:

`segment IN ('Standard', 'Premium', 'Enterprise')`

The database constraint is important because application-level validation alone cannot protect data from every possible database client.

---

## Python Implementation

The Python file is the most dataframe-oriented implementation.

Its workflow is:

`raw CSV text → DataFrame → string normalization → type conversion → range validation → deduplication → missing-value handling → categorical conversion → quality report`

Pandas provides vectorized operations for the operations most commonly required during tabular cleaning.

The script also reports:

- Raw row count.
- Clean row count.
- Number of removed rows.
- Remaining missing values.
- Segment distribution.
- Final data types.
- Duplicate customer identifiers.

The script uses only Pandas and Python's standard library. The CSV input is stored in an in-memory buffer so the program does not depend on a particular filesystem layout.

---

## JavaScript Implementation

The JavaScript implementation deliberately does not attempt to imitate Pandas.

`DataCleaner` owns the cleaning workflow and uses:

- `Set` for identity and duplicate detection.
- `Map`-compatible aggregation patterns for category counts.
- Regular expressions for email validation.
- Explicit numeric validation.
- `Date` parsing for temporal values.
- `structuredClone()` to prevent mutation of the supplied source records.
- A Promise boundary and `setImmediate()` to represent an asynchronous processing stage.

The asynchronous structure is useful when the same cleaning service is later placed behind file ingestion, a message queue, or an HTTP endpoint.

The program reports quality metrics separately from the cleaned records. This prevents cleaning from hiding the amount of source data that required intervention.

---

## C++17 Implementation

The C++ program models cleaning as a dedicated `CustomerDataQualityEngine`.

The design uses:

- `struct` for source and cleaned records.
- `std::optional` for values that remain missing.
- `std::set` for duplicate detection.
- `std::regex` for email validation and date shape validation.
- Explicit exception handling for unsupported categorical values.
- Median calculation after duplicate removal.
- Standard-library algorithms for normalization and ordering.

The engine does not use external dataframe libraries. This makes the data-quality decisions visible at the level of algorithms and data structures.

The duplicate lookup structures provide logarithmic lookup behavior. Median calculation requires sorting and therefore has `O(n log n)` complexity for the relevant numeric collection.

The program also separates source records from cleaned records rather than mutating the original representation.

---

## Java 17 Implementation

The Java implementation uses an enterprise-oriented domain model.

`Customer` is a Java record, providing an immutable representation of a cleaned customer.

`CustomerSegment` is an enum that constrains categorical domain values.

`CleaningService` owns:

- Text normalization.
- Numeric validation.
- Email validation.
- Date conversion.
- Segment validation.
- Duplicate detection.
- Median calculation.
- Missing-value imputation.

`DataValidationException` represents an invalid domain-level condition instead of treating every failure as a generic runtime problem.

The service also produces a `CleaningMetrics` record containing:

- Input row count.
- Invalid-value count.
- Duplicate count.
- Output row count.

This separation between domain data, validation policy, and cleaning service is appropriate for an enterprise application where the same rules may be invoked by multiple ingestion workflows.

---

## PostgreSQL Implementation

The SQL implementation separates untrusted raw text from validated relational data.

The `raw_customers` table intentionally retains source values as text. This is useful when an ingestion system must preserve the original representation for auditing.

`normalized_customers` performs initial string normalization.

The `safe_integer()` function performs guarded integer conversion.

The `safe_date()` function validates date structure and catches invalid conversions.

The typed `customers` table then applies database-level constraints:

- `PRIMARY KEY` on `customer_id`.
- `CHECK` constraint for age.
- `CHECK` constraint for non-negative orders.
- `CHECK` constraint for permitted segments.
- Email-format validation.
- Unique normalized email index.

This creates two levels of protection:

`raw source → cleaning functions → typed table → relational constraints`

A source-cleaning script can therefore fail to recognize a problem without allowing arbitrary invalid values into the final relational model.

---

## Database Performance

The database includes indexes only for access patterns represented in the example.

`customers_segment_idx` supports segment filtering and grouping-oriented access.

`customers_signup_date_idx` supports date-range searches.

The partial unique email index covers only non-null emails. This avoids treating multiple missing email values as duplicate identities while still enforcing uniqueness for actual email addresses.

The raw table intentionally does not receive indexes because it is primarily an ingestion-stage representation in this example.

For large production datasets, indexes should be selected from measured query patterns rather than created automatically for every column.

---

## Validation and Failure Handling

The cleaning rules distinguish several failure types.

| Condition | Treatment |
|---|---|
| Empty name | Replace with `Unknown Customer` |
| Empty city | Replace with `Unknown` |
| Missing email | Preserve as missing |
| `unknown` age | Treat as missing |
| Age below 18 | Treat as invalid/missing |
| Age above 100 | Treat as invalid/missing |
| Negative orders | Treat as invalid/missing |
| Invalid date | Preserve as missing |
| Unsupported segment | Reject the record or raise a validation error |
| Repeated customer ID | Remove duplicate |
| Repeated normalized email | Remove duplicate |
| Invalid email format | Preserve as missing |

The policies are intentionally different because not every bad value has the same business impact.

A missing email can be legitimate. An unsupported segment can indicate a schema or application-contract violation and therefore deserves stronger handling.

---

## Data Cleaning Workflow

The complete conceptual workflow is:

`Source records`
→ `Normalize strings`
→ `Convert data types`
→ `Validate ranges and formats`
→ `Identify duplicates`
→ `Apply missing-value policy`
→ `Normalize categorical values`
→ `Validate final representation`
→ `Produce quality metrics`

Ordering matters.

For example, duplicate detection should generally happen after email normalization. Otherwise these values would incorrectly appear different:

`USER@EXAMPLE.COM`

and

` user@example.com `

Likewise, median calculation should use validated values rather than including invalid ages or duplicate records.

---

## Security and Integrity Considerations

Data cleaning is also a data-integrity operation.

The implementations avoid constructing executable SQL from external strings. The PostgreSQL workflow uses SQL functions and typed values rather than dynamic SQL.

Email values are validated as data rather than interpreted as commands.

The database provides a final integrity boundary through constraints and triggers. Application-level cleaning should not be considered sufficient protection when multiple applications can write to the same database.

Missing-value imputation should also be auditable in production. A system that replaces a missing customer age with a median should retain enough lineage information to distinguish an observed age from an imputed age when that distinction affects downstream analysis.

---

## Edge Cases

Important cases represented by the implementations include:

- Empty strings.
- Whitespace-only strings.
- Repeated whitespace.
- Case differences in categorical data.
- Case differences in email addresses.
- Invalid integer strings.
- Negative values.
- Out-of-range ages.
- Invalid dates.
- Missing emails.
- Duplicate customer IDs.
- Duplicate normalized emails.
- Unknown categorical values.
- Nullable numeric fields.
- Empty categorical fields.

A production pipeline should also consider locale-specific names, Unicode normalization, timezone semantics for timestamps, malformed CSV quoting, extremely large files, encoding failures, schema drift, and whether median imputation is statistically appropriate for the target dataset.

---

## Practical Distinctions

**Cleaning** changes representation into a consistent form.

**Validation** determines whether a value satisfies an expected rule.

**Type conversion** changes the representation from text to a domain type.

**Deduplication** determines whether multiple source records represent the same entity.

**Imputation** supplies a replacement for a missing value according to an explicit policy.

**Categorical normalization** maps multiple textual representations onto a controlled vocabulary.

These operations are related, but they should not be treated as one generic "clean data" operation. Their order and business rules can materially change the resulting dataset.
