# Excel data cleaning

## Introduction

Excel data cleaning is the process of identifying, correcting, standardizing, validating, and documenting problems in spreadsheet data.

A spreadsheet may look organized while containing substantial data-quality problems. Examples include duplicate records, missing values, inconsistent capitalization, extra spaces, numbers stored as text, ambiguous dates, invalid categories, malformed email addresses, incorrect phone numbers, and values outside acceptable business ranges.

The Python study script demonstrates a complete cleaning workflow using `pandas` for data transformation and `openpyxl` for Excel workbook creation, validation, formatting, and inspection.

The examples are based on a customer dataset containing fields such as Customer ID, name, email, phone number, city, department, age, joining date, salary, status, and notes.

The workflow emphasizes an important principle: cleaning should not simply make data look neat. It should make the data structurally consistent, semantically meaningful, testable, and suitable for downstream use.

## Data structure and data quality

An Excel table normally consists of:

- Rows representing records or observations
- Columns representing variables or fields
- Cells containing individual values
- Headers defining the meaning of columns

For example, a customer table may contain one row per customer and columns for identity, contact information, demographics, employment information, and account status.

Data quality can be evaluated through several dimensions.

### Completeness

Completeness measures whether required information is present.

For example, a customer record without an email address may be incomplete if email is required for business communication.

A missing value is not automatically an error. Some fields may legitimately be optional.

### Validity

Validity asks whether a value conforms to an expected rule.

Examples:

- Age should be within a reasonable range.
- Status should belong to an approved category.
- Salary should be numeric and positive.
- Email should follow an acceptable structural pattern.
- A date should be a recognizable date.

### Consistency

Consistency means equivalent information is represented in the same way.

Examples:

- `Sales`, `sales`, and ` SALES ` should normally be standardized to one representation.
- `Lucknow`, `lucknow`, and `Lucknow ` should normally represent the same city.
- Currency values should use a consistent numeric representation.

### Uniqueness

Uniqueness concerns whether records that should be distinct are actually distinct.

A customer ID may be required to identify one customer uniquely. Repeated IDs can indicate duplicate records or conflicting information.

### Accuracy

Accuracy asks whether the value is actually correct.

A value can be properly formatted and still be wrong. For example, an age of 45 is structurally valid but may still be inaccurate for a particular person.

Automated cleaning can identify many structural problems, but factual accuracy often requires source verification.

## Missing values

Missing values are among the most common Excel data-quality problems.

The script demonstrates several representations that can mean "missing":

- Blank cells
- Empty strings
- Whitespace
- `N/A`
- `NA`
- `None`
- `NULL`
- `Unknown`
- Hyphens
- `Not available`

These representations should not automatically be treated as equivalent in every dataset. The correct interpretation depends on the business meaning of the source data.

A missing salary, for example, might mean that the salary was not collected. A salary of zero could mean something completely different.

The script converts defined textual missing markers to a consistent missing representation before further processing.

### Missing-value strategies

Common strategies include:

**Deletion**

A row or column may be removed when the missing information makes it unusable.

**Imputation**

A missing numeric value may be replaced with a statistically calculated value such as a median.

**Business-specific replacement**

A missing category may be represented as `Unknown` when the distinction between "unknown" and "not applicable" is meaningful.

**Preservation**

A missing value may be left missing when downstream analysis can correctly handle it.

**Quarantine**

A record can be separated for manual review instead of being deleted.

There is no universally correct missing-value strategy. The correct choice depends on the semantics of the field and the purpose of the dataset.

## Duplicate records

Duplicates occur when multiple records represent the same underlying entity or event.

The script demonstrates exact duplicate detection with pandas.

An exact duplicate means the relevant fields are identical.

A business-key duplicate is different. Two rows can have the same Customer ID but different values in other columns. Such records may represent conflicting versions of the same customer.

Duplicate rules should therefore be defined before deletion.

### Types of duplicates

**Exact duplicates**

Every relevant value is identical.

**Key duplicates**

A field such as Customer ID or Email occurs more than once.

**Composite-key duplicates**

Uniqueness is determined by several fields together.

For example:

`Customer + Date + Amount`

may define the uniqueness of a transaction.

**Potential duplicates**

Two records may represent the same entity despite having small textual differences. This is a more advanced problem often requiring fuzzy matching or domain-specific rules.

The script intentionally avoids automatically deleting all records that share a business key because duplicate detection and duplicate resolution are separate problems.

## Whitespace and hidden characters

Whitespace problems are common when data is copied between systems.

Examples include:

- Leading spaces
- Trailing spaces
- Multiple consecutive spaces
- Tabs
- Line breaks
- Non-breaking spaces

A value such as ` " Lucknow "` can look correct visually but fail exact comparisons against `Lucknow`.

The script normalizes whitespace by:

- Replacing non-breaking spaces
- Replacing tabs and line breaks
- Reducing repeated whitespace
- Removing leading and trailing spaces

Hidden Unicode control characters can also cause matching problems. The script includes a function for removing inappropriate control characters.

## Unicode normalization

Two visually similar strings can sometimes have different internal Unicode representations.

Unicode normalization provides a way to convert equivalent representations into a consistent form.

The script uses Unicode normalization before performing further text standardization.

This becomes particularly important when data originates from multiple applications, languages, operating systems, or copy-and-paste workflows.

## Text standardization

Text standardization changes inconsistent representations into a defined representation.

The script applies different transformations depending on the semantic purpose of the field.

Examples include:

- Names converted to title-style capitalization
- Email addresses converted to lowercase
- Customer IDs converted to uppercase
- Cities standardized to title-style capitalization
- Status values standardized to approved categories

The correct transformation depends on the field.

A universal rule such as converting every value to title case can be dangerous because some identifiers and technical values have meaningful capitalization.

## Category mapping

Categorical data often contains multiple representations of the same category.

For example:

- `HR`
- `Human Resources`
- `human resources`

may represent one business department.

The script uses an explicit mapping dictionary to standardize these values.

Explicit mappings are preferable to uncontrolled transformations when business meaning matters.

A mapping provides a documented relationship between source values and standardized values.

For example:

`hr -> Human Resources`

`finance -> Finance`

`it -> IT`

This approach is easier to audit and modify than relying solely on generic capitalization functions.

## Email cleaning and validation

The script performs two distinct operations on email addresses.

First, it standardizes the representation by trimming whitespace and converting the address to lowercase.

Second, it checks the resulting value against a structural validation pattern.

These operations illustrate the distinction between standardization and validation.

An email address may be standardized but still invalid.

For example:

`PERSON@EXAMPLE.COM`

can be normalized to:

`person@example.com`

But:

`person.example.com`

does not contain the expected email structure.

The validation implemented in the script is intentionally practical rather than a complete implementation of every technical rule allowed by email standards.

## Phone number standardization

Phone numbers frequently appear with different formatting.

Examples include:

- `9876543210`
- `98765 43210`
- `98765-43210`
- `+91 9876543210`

The script removes non-numeric formatting characters and supports a basic Indian ten-digit mobile-number rule.

The important concept is that formatting characters should be separated from the underlying value.

Phone validation should be adapted to the geographic and business requirements of the dataset.

A global customer dataset should not use an India-specific rule for every record.

## Numeric conversion

Numbers are frequently stored as text in Excel.

Examples include:

- `"62000"`
- `"₹55,000"`
- `"₹ 85,500"`

A visually numeric value may still be represented internally as text.

The script converts currency text into numeric values by removing currency symbols, spaces, and thousands separators before attempting numeric conversion.

For example:

`₹55,000`

becomes:

`55000.0`

This conversion is important because numerical analysis, sorting, aggregation, and statistical calculations require appropriate numeric types.

## Preserving identifiers

Identifiers should not automatically be converted to numbers.

For example:

`000123`

may be an identifier rather than the number `123`.

Converting it to a numeric type can remove leading zeros and permanently change its representation.

Examples of fields that should often remain text include:

- Customer IDs
- Employee IDs
- Product codes
- Postal codes
- Account identifiers
- Transaction IDs

The meaning of a field is more important than whether it contains only digits.

## Date standardization

Dates are another common source of ambiguity.

A dataset may contain:

- `15/01/2025`
- `2025-02-20`
- `April 8, 2025`
- `2025/05/12`
- `12-06-2025`

The script converts recognizable values into pandas datetime values.

Date parsing must be handled carefully because formats such as:

`01/02/2025`

can represent either:

- 1 February 2025
- January 2, 2025

depending on the source convention.

A production workflow should know the source system's date convention rather than guessing.

## Text-to-columns

Excel's Text to Columns feature separates a single column into multiple columns.

A delimiter can be used when a field contains structured separators.

Common delimiters include:

- Comma
- Semicolon
- Tab
- Pipe
- Space

For example:

`Rahul|Sharma|Sales`

can be separated into:

- Rahul
- Sharma
- Sales

The Python equivalent demonstrated in the script is based on string splitting.

Text-to-columns should only be used when the delimiter has a reliable structural meaning.

A space is often a poor delimiter for personal names because names can contain multiple words.

## Data validation

Data validation defines rules for what values should be accepted.

The script demonstrates validation for:

- Age
- Salary
- Email
- Phone
- Status
- Join date
- Required fields

It also creates Excel dropdown validation for the Status column.

The allowed values are:

- Active
- Inactive
- Pending

This is an important distinction between cleaning historical data and preventing future data-quality problems.

Cleaning fixes existing data.

Data validation helps prevent new invalid data from being entered.

## Validation rules

A validation rule can be expressed conceptually as:

`value must satisfy condition`

Examples:

Age:

`18 <= Age <= 100`

Salary:

`Salary > 0`

Status:

`Status ∈ {Active, Inactive, Pending}`

Email:

`Email must satisfy the defined structural pattern`

Required field:

`Customer ID must not be blank`

These rules should be documented because they represent business assumptions.

## Standardization versus validation

Standardization and validation solve different problems.

Standardization asks:

"How should this value be represented?"

Validation asks:

"Is this value acceptable?"

For example:

`" SALES "`

can be standardized to:

`"Sales"`

An age of:

`150`

cannot be corrected merely through formatting. It should be identified as invalid according to the defined business rule.

This distinction prevents cleaning logic from silently changing potentially incorrect information.

## Error handling

A data-cleaning pipeline should expect malformed input.

The script demonstrates safe conversion functions that return a missing value when a value cannot be converted.

For example:

`"invalid"`

cannot be converted into a meaningful integer.

A robust pipeline should distinguish between recoverable data problems and programming failures.

### Recoverable data problem

A malformed salary can be converted to a missing value and flagged for review.

### Critical schema failure

If the required Customer ID column does not exist, the pipeline may need to stop.

### Unexpected programming failure

A coding error should not be silently converted into a missing value.

Suppressing all exceptions is dangerous because it can create silent data corruption.

## Excel error values

Excel uses several standard error values.

### `#DIV/0!`

A calculation attempts to divide by zero.

### `#N/A`

A value required by a lookup or calculation is unavailable.

### `#VALUE!`

A formula received an inappropriate value or data type.

### `#REF!`

A formula refers to an invalid cell reference.

### `#NAME?`

Excel cannot recognize a function, name, or expression.

### `#NUM!`

A numerical operation is invalid or outside an acceptable range.

### `#NULL!`

An invalid range intersection or related reference problem occurs.

`IFERROR` can improve workbook usability, but hiding every error is not good data-quality practice. Errors can contain useful information about underlying problems.

## Data-quality scoring

The script demonstrates a basic quality score based on several validation checks.

The score considers conditions such as:

- Valid email
- Valid phone
- Valid age
- Valid salary
- Valid status
- Valid date
- Completeness

A quality score is useful for prioritizing records for review.

It should not be interpreted as an objective measure of truth. The score is only as meaningful as the rules used to calculate it.

## Issue flags

Instead of simply deleting invalid rows, the script creates explicit issue lists.

A record may receive issues such as:

- Invalid email
- Missing or invalid phone
- Missing or invalid age
- Missing or invalid salary
- Invalid status
- Invalid join date
- Low completeness

This approach provides traceability.

It also allows a business process to distinguish between:

- Clean records
- Records needing review
- Records that must be quarantined

## Quarantine workflow

The script demonstrates separating invalid records from valid records.

This is safer than automatically deleting all problematic rows.

A quarantine dataset allows a reviewer to inspect the records and determine whether:

- The original value was genuinely incorrect
- The validation rule was too restrictive
- The source data needs correction
- The record should be retained with a special status

Quarantine is particularly useful in operational data pipelines.

## Audit logging

A cleaning process should be auditable.

The script records operations such as:

- Exact duplicate removal
- Text normalization
- Numeric conversion
- Date conversion

An audit record can contain:

- Operation name
- Rows before transformation
- Rows after transformation
- Number of changed or removed records
- Description of the transformation

This makes the process easier to review and reproduce.

## Before-and-after comparison

A useful cleaning workflow measures data quality before and after processing.

The script compares:

- Number of rows
- Number of columns
- Missing cells
- Exact duplicate rows

The purpose is not to maximize the number of changes.

A good cleaning process changes data only when the transformation is justified.

A decrease in missing values is not automatically an improvement if the missing values were replaced with incorrect assumptions.

## Schema validation

Schema validation verifies that the expected columns exist.

For example, a customer dataset may require:

- Customer ID
- Full Name
- Email
- Phone
- City
- Department
- Age
- Join Date
- Salary
- Status

If a required column is missing, the cleaning pipeline may not be able to continue safely.

Schema validation should occur early in the process.

## Business rules

Technical validation and business validation are related but not identical.

A value can be technically valid while violating a business rule.

For example:

- Age 45 is numerically valid.
- Salary 50000 is numeric.
- Status `Active` belongs to the approved category set.

But a business may have additional rules such as:

- Certain departments require a particular employment status.
- Joining dates cannot be in the future.
- A customer ID must match a specific pattern.
- A transaction amount may have a maximum allowed value.

Business rules should be explicitly documented rather than hidden inside complicated transformations.

## Outlier detection

The script demonstrates basic interquartile range detection.

The IQR is:

`Q3 - Q1`

The common outlier boundaries are:

`Q1 - 1.5 × IQR`

and:

`Q3 + 1.5 × IQR`

Values outside these boundaries can be flagged.

An outlier is not automatically an error.

For example, an unusually high salary may represent a legitimate executive salary.

Outlier detection should therefore normally identify records for investigation rather than automatically delete them.

## Excel formulas for validation

The script creates an Excel workbook containing formula-based validation.

Examples include checks for:

- Email structure
- Age range
- Status membership

Excel formulas can be useful when validation needs to remain visible and editable inside the workbook.

Programmatic validation is generally easier to automate at scale, while Excel formulas are useful for analysts who need interactive workbook-based checks.

## Excel functions relevant to data cleaning

Several Excel functions are particularly useful for cleaning.

### TRIM

Removes leading and trailing spaces and normalizes repeated standard spaces.

### CLEAN

Removes many non-printing characters.

### SUBSTITUTE

Replaces specific text.

### UPPER

Converts text to uppercase.

### LOWER

Converts text to lowercase.

### PROPER

Converts words to title-style capitalization.

### VALUE

Converts appropriate text representations into numbers.

### TEXT

Formats values according to a specified text pattern.

### LEFT

Extracts characters from the beginning of a string.

### RIGHT

Extracts characters from the end.

### MID

Extracts characters from the middle.

### FIND and SEARCH

Locate text within another value.

### IFERROR

Provides an alternative result when a formula generates an error.

### COUNTIF and COUNTIFS

Count records meeting one or multiple criteria.

### XLOOKUP

Retrieves related values using a lookup relationship.

### TEXTSPLIT

Separates text into rows or columns using delimiters.

### UNIQUE

Returns unique values.

### FILTER

Returns records satisfying a condition.

### SORT

Sorts records according to specified criteria.

These functions can support manual or semi-automated Excel cleaning workflows.

## Conditional formatting

Conditional formatting can visually identify invalid or suspicious values.

The script adds conditional formatting for age values outside the accepted range.

This provides a visual review mechanism.

Conditional formatting should not be considered a replacement for validation. It highlights problems but does not necessarily prevent them.

## Data validation versus conditional formatting

These features have different purposes.

Data validation controls or restricts what can be entered.

Conditional formatting highlights values according to rules.

For example:

A dropdown can restrict Status to approved values.

Conditional formatting can highlight an invalid age.

Using both together can improve spreadsheet quality.

## Common mistakes

Several common approaches can damage data.

### Deleting all duplicates

Not every repeated key is an exact duplicate.

### Replacing all blanks with zero

Zero has a numerical meaning and should not automatically represent missingness.

### Converting IDs to numbers

Leading zeros can be lost.

### Guessing date formats

Ambiguous dates can be silently converted incorrectly.

### Applying title case everywhere

Some technical identifiers require specific capitalization.

### Removing outliers automatically

A legitimate extreme value can be incorrectly deleted.

### Hiding all formula errors

Errors may contain important information about underlying data problems.

### Overwriting the original file

This removes an important recovery point.

### Cleaning without an audit trail

It becomes difficult to determine what changed and why.

### Relying entirely on visual inspection

Many spreadsheet problems are not visually obvious.

## Limitations

Automated data cleaning has important limitations.

A program can detect that an age of 150 violates a defined range. It cannot necessarily determine the person's true age.

A program can detect an unusual salary. It cannot automatically determine whether that salary is legitimate.

A program can standardize city names according to a mapping. It cannot know the correct mapping for every ambiguous business case without appropriate reference data.

Validation rules therefore require domain knowledge.

## Performance considerations

For small and medium-sized Excel files, pandas provides convenient data-transformation capabilities.

Vectorized operations such as string methods, numeric conversion, date conversion, and duplicate removal are generally preferable to manually iterating through every row.

For larger datasets, performance considerations become more important.

Useful practices include:

- Load only required columns.
- Avoid unnecessary DataFrame copies.
- Prefer vectorized operations.
- Use efficient data types.
- Process data in chunks when appropriate.
- Avoid excessive row-level `apply()` operations.
- Keep Excel formatting separate from core transformations.

Excel is not an unlimited-scale database. When datasets become very large or workflows become highly concurrent, a database or analytical data-processing system may be more appropriate.

## Security considerations

Spreadsheet workflows can introduce security risks.

### Formula injection

Untrusted text beginning with characters such as:

`=`

`+`

`-`

`@`

can potentially be interpreted as spreadsheet formulas in some export and viewing environments.

The script demonstrates a conservative method for treating such values as literal text.

The exact mitigation should depend on the destination system and business requirements.

### Sensitive information

Customer and employee datasets may contain personal or confidential information.

Only required information should be processed and distributed.

### Macro-enabled workbooks

Untrusted VBA macros should not be automatically enabled or executed.

### External links

Workbook links to external files or data sources should be reviewed before distribution.

### Original files

Raw files should be preserved securely so that transformations can be audited or reversed.

## Implementation considerations

A robust cleaning workflow can be structured as:

Raw source → Schema validation → Missing-value normalization → Text normalization → Standardization → Type conversion → Duplicate handling → Validation → Quality checks → Clean output → Audit report

The order can change depending on the dataset, but transformations should be deliberate.

For example, duplicate detection may be more reliable after whitespace and case normalization because:

`C001`

and:

` c001 `

may otherwise appear different even though they represent the same identifier.

## Reproducibility

A reproducible cleaning process should explicitly define:

- Input source
- Expected columns
- Data types
- Missing-value policy
- Standardization mappings
- Validation rules
- Duplicate policy
- Output structure
- Audit information
- Error-handling behavior

The same input should produce the same result when the rules and environment remain unchanged.

This is especially important when cleaning is performed repeatedly on monthly or weekly Excel files.

## Data lineage

Data lineage describes where a value originated and what transformations were applied.

A basic lineage record can contain:

- Source file
- Source sheet
- Source row
- Transformation name
- Output row
- Processing timestamp

Detailed lineage becomes increasingly important when spreadsheet data feeds financial reports, operational systems, regulatory reporting, or analytical models.

## Production considerations

A production-grade Excel cleaning process should generally:

- Preserve the original source.
- Validate the expected schema.
- Define business rules explicitly.
- Normalize missing-value representations.
- Standardize controlled categories.
- Validate data types.
- Detect duplicates according to business definitions.
- Separate invalid records where appropriate.
- Record transformations.
- Generate quality metrics.
- Test edge cases.
- Protect exported files.
- Avoid silently suppressing errors.
- Keep the process reproducible.

The goal is not simply to produce a visually cleaner spreadsheet. The goal is to produce data whose structure, meaning, and quality can be understood and trusted.

## Files generated by the script

The Python script creates several Excel workbooks demonstrating different aspects of the workflow:

- `excel_data_cleaning_raw_and_cleaned.xlsx`
- `excel_data_cleaning_validated.xlsx`
- `excel_data_cleaning_validated_formatted.xlsx`
- `excel_formula_validation.xlsx`
- `excel_text_to_columns_example.xlsx`
- `excel_data_cleaning_complete_study.xlsx`

The complete study workbook contains raw data, cleaned data, validation information, audit information, and documented cleaning rules.
