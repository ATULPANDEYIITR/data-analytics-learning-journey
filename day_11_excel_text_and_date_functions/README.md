# Excel text & date functions

## Introduction

Excel text and date functions are fundamental tools for cleaning data, extracting information, constructing labels, formatting values, analyzing calendar periods, and preparing business reports.

This study file focuses on the following Excel functions:

| Function | Category | Primary purpose |
|---|---|---|
| `LEFT` | Text | Extract characters from the beginning of text |
| `RIGHT` | Text | Extract characters from the end of text |
| `MID` | Text | Extract characters from a specified position |
| `LEN` | Text | Count characters |
| `TRIM` | Text | Remove unnecessary ordinary spaces |
| `CLEAN` | Text | Remove non-printable control characters |
| `SUBSTITUTE` | Text | Replace selected text |
| `TEXT` | Text/formatting | Convert values into formatted text |
| `CONCAT` | Text | Combine text values |
| `TEXTJOIN` | Text | Combine text using a delimiter |
| `DATE` | Date | Construct a date |
| `YEAR` | Date | Extract the year |
| `MONTH` | Date | Extract the month |
| `DAY` | Date | Extract the day |
| `EOMONTH` | Date | Return the last day of a month |

The Python script models these concepts using standard Python strings and `datetime.date` values. The purpose is not to replace Excel syntax, but to make the underlying operations explicit and executable.

---

## Excel text functions

Text functions operate on characters rather than treating a value purely as a numeric or date quantity.

They are particularly useful for:

- cleaning imported data
- parsing employee and transaction identifiers
- extracting portions of codes
- standardizing inconsistent text
- constructing readable reports
- combining multiple fields
- preparing data for analysis

A typical workflow is:

`clean → extract → format → combine`

The script demonstrates this pattern repeatedly.

---

## LEFT

### Syntax

`=LEFT(text,[num_chars])`

`LEFT` returns characters beginning from the left side of a text value.

For example:

`=LEFT("Atul Pandey",4)`

returns:

`Atul`

The optional `num_chars` argument determines how many characters are returned. If it is omitted, Excel returns one character.

### Important behavior

If the requested number of characters exceeds the length of the source text, Excel returns the complete available text.

For example:

`=LEFT("ABC",10)`

returns:

`ABC`

Requesting zero characters produces an empty result.

A negative character count is invalid.

### Practical applications

`LEFT` is useful when:

- an identifier has a fixed prefix
- a product code begins with a category
- a country or region code occurs at the beginning of a string
- a text field has a known fixed-width structure

Example:

`=LEFT(A2,3)`

can extract `EMP` from `EMP-IND-2026-00452`.

---

## RIGHT

### Syntax

`=RIGHT(text,[num_chars])`

`RIGHT` extracts characters from the end of a text value.

For example:

`=RIGHT("INV-2026-00452",5)`

returns:

`00452`

### Practical applications

`RIGHT` is useful for:

- extracting sequence numbers
- retrieving suffixes
- obtaining file extensions
- extracting the final portion of identifiers
- working with fixed-length codes

As with `LEFT`, requesting more characters than exist returns the available text.

---

## MID

### Syntax

`=MID(text,start_num,num_chars)`

`MID` extracts a specified number of characters beginning at a specified position.

A crucial distinction is that Excel character positions are **1-based**.

For example:

`=MID("PRD-IND-2026-001",5,3)`

starts at character position 5 and returns:

`IND`

Python normally uses zero-based indexes, so the Python implementation in the study file explicitly converts the Excel position to a Python index.

### Why MID is important

`MID` is especially useful for structured identifiers.

For:

`EMP-IND-2026-00452`

the different components can be extracted using:

- `LEFT` for `EMP`
- `MID` for `IND`
- `MID` for `2026`
- `RIGHT` for `00452`

### Edge cases

If `start_num` is beyond the end of the string, the result is empty.

A zero or negative starting position is invalid.

A negative `num_chars` value is also invalid.

---

## LEN

### Syntax

`=LEN(text)`

`LEN` returns the number of characters in a text value.

Spaces are included in the count.

For example:

`=LEN("Excel")`

returns `5`.

A trailing space changes the length:

`=LEN("Excel ")`

returns `6`.

### Practical importance

`LEN` is useful for:

- validating identifier lengths
- detecting unexpected spaces
- checking imported data
- determining how many characters remain after an extraction
- supporting dynamic text formulas

One common mistake is assuming that `LEN` ignores spaces. It does not.

---

## TRIM

### Syntax

`=TRIM(text)`

`TRIM` removes unnecessary ordinary spaces.

It removes leading and trailing spaces and reduces repeated internal ordinary spaces to a single space.

For example:

`=TRIM("   Atul    Pandey   ")`

produces:

`Atul Pandey`

### Important limitation

`TRIM` is not a universal invisible-character cleaning function.

Imported data can contain characters that look like ordinary spaces but are actually different Unicode characters. A common example is the non-breaking space.

For that reason, `TRIM` is frequently combined with `CLEAN` and `SUBSTITUTE`.

---

## CLEAN

### Syntax

`=CLEAN(text)`

`CLEAN` removes non-printable control characters from text.

These characters can enter a worksheet through:

- copied data
- external reports
- exported systems
- web pages
- imported files

For example, line breaks and other control characters can cause apparently identical values to behave differently.

### TRIM versus CLEAN

The functions address different problems.

| Function | Main purpose |
|---|---|
| `TRIM` | Handles unnecessary ordinary spaces |
| `CLEAN` | Handles non-printable control characters |

A common combination is:

`=TRIM(CLEAN(A2))`

This is more effective than using either function alone when imported text contains both unwanted spaces and control characters.

---

## SUBSTITUTE

### Syntax

`=SUBSTITUTE(text,old_text,new_text,[instance_num])`

`SUBSTITUTE` replaces matching text with another value.

For example:

`=SUBSTITUTE("98765-43210","-","")`

removes all hyphens.

The optional `instance_num` argument allows only a particular occurrence to be replaced.

For example:

`=SUBSTITUTE("2026-09-11-REPORT","-","/",2)`

replaces only the second occurrence of the hyphen.

### Case sensitivity

`SUBSTITUTE` is case-sensitive.

Replacing `excel` does not automatically replace `Excel` or `EXCEL`.

### Practical applications

`SUBSTITUTE` is useful for:

- removing separators
- standardizing identifiers
- changing delimiters
- replacing unwanted characters
- correcting known data-entry patterns
- converting non-breaking spaces into ordinary spaces

A practical cleaning pattern for web-imported data is:

`=TRIM(CLEAN(SUBSTITUTE(A2,CHAR(160)," ")))`

The logic is:

1. replace non-breaking spaces with ordinary spaces
2. remove control characters
3. normalize ordinary spaces

---

## TEXT

### Syntax

`=TEXT(value,format_text)`

`TEXT` converts a value into text using a specified display format.

Common examples include:

`=TEXT(A2,"#,##0.00")`

`=TEXT(A2,"0.0%")`

`=TEXT(A2,"dd-mm-yyyy")`

`=TEXT(A2,"mmm yyyy")`

### Numeric formatting

A value such as:

`1250000.5`

can be displayed as:

`1,250,000.50`

using:

`=TEXT(1250000.5,"#,##0.00")`

### Percentage formatting

A numeric value of:

`0.1845`

can be formatted as:

`18.5%`

using:

`=TEXT(0.1845,"0.0%")`

### Date formatting

A date can be converted to readable text:

`=TEXT(DATE(2026,9,11),"dd-mm-yyyy")`

produces a formatted representation such as:

`11-09-2026`

A month label can be generated using:

`=TEXT(DATE(2026,9,11),"mmm yyyy")`

### Important distinction: value versus formatted text

`TEXT` returns text.

This matters when calculations are involved.

A numeric cell can participate directly in arithmetic:

`=A2*2`

A `TEXT` result is intended for presentation or concatenation rather than numeric calculation.

If a value needs to remain numeric, ordinary cell formatting is generally preferable to converting it to text.

---

## CONCAT

### Syntax

`=CONCAT(text1,[text2],...)`

`CONCAT` combines multiple text values.

For example:

`=CONCAT(A2," ",B2)`

combines a first name and last name.

A key characteristic is that `CONCAT` does not automatically insert separators.

If a space is required, it must be supplied explicitly.

For example:

`=CONCAT("INV-",2026,"-",452)`

produces an identifier containing the specified components.

---

## TEXTJOIN

### Syntax

`=TEXTJOIN(delimiter,ignore_empty,text1,[text2],...)`

`TEXTJOIN` combines values using a delimiter.

For example:

`=TEXTJOIN(", ",TRUE,A2:E2)`

can combine multiple cells using a comma and space.

### ignore_empty

The second argument determines how empty values are handled.

`TRUE` means empty values are ignored.

`FALSE` means empty positions are retained.

This distinction becomes important when constructing lists from partially populated records.

### CONCAT versus TEXTJOIN

| Requirement | Better fit |
|---|---|
| Combine specific pieces with manually supplied separators | `CONCAT` |
| Apply the same delimiter between many values | `TEXTJOIN` |
| Ignore empty cells while joining | `TEXTJOIN` |
| Construct a fixed string from known components | `CONCAT` |

---

## Combining text functions

The real power of Excel text functions comes from combining them.

For an identifier such as:

`EMP-IND-2026-00452`

different functions can extract different components.

Examples:

`=LEFT(A2,3)`

extracts the prefix.

`=MID(A2,5,3)`

extracts the country code.

`=MID(A2,9,4)`

extracts the year.

`=RIGHT(A2,5)`

extracts the employee number.

A more robust approach is to calculate positions from delimiters rather than assuming that every record will always have exactly the same length.

---

## Delimiter-driven extraction

Hard-coded character positions work well when the source structure is guaranteed to remain fixed.

They become fragile when the source changes.

For example, extracting a domain from an email address should ideally be based on the position of `@`.

A conceptual Excel formula is:

`=LEFT(A2,FIND("@",A2)-1)`

This extracts the username portion.

Delimiter-based extraction is generally more maintainable when source fields have variable-length components.

The study script includes a Python implementation of the underlying `FIND` behavior to demonstrate this principle, even though `FIND` is outside the primary function list.

---

## Cleaning imported text

A frequent business-data problem is text containing:

- leading spaces
- trailing spaces
- repeated spaces
- line breaks
- control characters
- non-breaking spaces
- inconsistent separators

A common cleaning formula is:

`=TRIM(CLEAN(A2))`

For data that contains non-breaking spaces:

`=TRIM(CLEAN(SUBSTITUTE(A2,CHAR(160)," ")))`

This illustrates the distinction between cleaning operations and extraction operations.

Cleaning should normally happen before extraction when invisible characters could change positions or comparisons.

---

# Excel date functions

Dates are fundamental to:

- financial reporting
- accounting periods
- employee records
- project schedules
- invoices
- subscriptions
- portfolio analysis
- KPI reporting
- transaction analysis

The requested date functions are:

- `DATE`
- `YEAR`
- `MONTH`
- `DAY`
- `EOMONTH`

---

## DATE

### Syntax

`=DATE(year,month,day)`

`DATE` constructs a date from its individual components.

For example:

`=DATE(2026,9,11)`

creates the date 11 September 2026.

### Why DATE is preferable to manually typed text

A date constructed with `DATE` is an actual date value.

A string such as:

`"11/09/2026"`

may be text depending on how it was entered or interpreted.

Actual dates are preferable for:

- sorting
- comparison
- date arithmetic
- filtering
- month calculations
- date formatting

### Component normalization

Excel's `DATE` function can normalize certain out-of-range month and day values.

For example, a month value of 13 represents the next year's first month.

A day value of 0 represents the final day of the preceding month.

This differs from Python's basic `date()` constructor, which requires valid calendar components. The study script explicitly implements normalization to illustrate the Excel behavior.

---

## YEAR

### Syntax

`=YEAR(serial_number)`

`YEAR` extracts the year from a date.

For example:

`=YEAR(DATE(2026,9,11))`

returns:

`2026`

This is useful for:

- yearly reporting
- grouping
- filtering
- year-based calculations
- constructing labels

---

## MONTH

### Syntax

`=MONTH(serial_number)`

`MONTH` extracts the numeric month.

For:

`DATE(2026,9,11)`

the result is:

`9`

The function returns a month number from 1 through 12.

---

## DAY

### Syntax

`=DAY(serial_number)`

`DAY` extracts the day of the month.

For:

`DATE(2026,9,11)`

the result is:

`11`.

The function returns the day number rather than the day name.

---

## YEAR, MONTH and DAY together

The three extraction functions can decompose a date.

For a date stored in `A2`:

`=YEAR(A2)`

returns the year.

`=MONTH(A2)`

returns the month.

`=DAY(A2)`

returns the day.

This is useful when date components must be used separately in calculations or classification logic.

---

## EOMONTH

### Syntax

`=EOMONTH(start_date,months)`

`EOMONTH` returns the last day of a month that is a specified number of months before or after the starting date.

For example:

`=EOMONTH(DATE(2026,9,11),0)`

returns:

`30-Sep-2026`

Using a positive offset:

`=EOMONTH(DATE(2026,9,11),1)`

returns:

`31-Oct-2026`

Using a negative offset:

`=EOMONTH(DATE(2026,9,11),-1)`

returns:

`31-Aug-2026`

### Why EOMONTH matters

Calendar months do not all have the same number of days.

They can contain:

- 28 days
- 29 days
- 30 days
- 31 days

Therefore, adding 30 days is not equivalent to moving one calendar month.

`EOMONTH` performs a calendar-aware month calculation.

---

## EOMONTH and leap years

Leap years create an important edge case.

February has:

- 28 days in an ordinary year
- 29 days in a leap year

For example:

`=EOMONTH(DATE(2024,2,10),0)`

returns 29 February 2024.

For 2025:

`=EOMONTH(DATE(2025,2,10),0)`

returns 28 February 2025.

The study script demonstrates the underlying Gregorian leap-year rule.

---

## Month-end reporting

EOMONTH is particularly useful in financial and business reporting.

For a transaction date in September 2026:

`=EOMONTH(A2,0)`

returns the end of September.

This can support:

- monthly reporting
- accounting cut-offs
- month-end balances
- invoice periods
- subscription periods
- portfolio reporting
- monthly KPI classification

A transaction can be associated with a reporting period by using:

`=TEXT(A2,"mmm yyyy")`

and its corresponding month end by using:

`=EOMONTH(A2,0)`.

---

# Combining date and text functions

Text and date functions become especially useful when creating readable report labels.

For example:

`=TEXT(A2,"mmm yyyy")`

converts a date into a reporting-period label.

A combined expression can include:

`TEXT`

with:

`CONCAT`

For example:

`=CONCAT("Report: ",TEXT(A2,"mmm yyyy"))`

creates a readable label.

`TEXTJOIN` can combine several formatted fields:

`=TEXTJOIN(" | ",TRUE,A2:C2)`

This is useful for compact report descriptions and exported labels.

---

# Integrated business example

The study script uses a record containing:

- customer name
- customer code
- invoice date
- invoice amount

A practical processing sequence is:

1. Clean the customer name using `TRIM` and `CLEAN`.
2. Extract the country code using `MID`.
3. Extract the customer number using `RIGHT`.
4. Format the invoice date using `TEXT`.
5. Calculate month end using `EOMONTH`.
6. Format the amount using `TEXT`.
7. Combine the resulting fields using `TEXTJOIN`.

The conceptual Excel operations are:

`=TRIM(CLEAN(A2))`

`=MID(B2,5,3)`

`=RIGHT(B2,5)`

`=TEXT(C2,"mmm yyyy")`

`=EOMONTH(C2,0)`

`=TEXT(D2,"#,##0.00")`

These operations demonstrate how simple functions can be composed into a complete data-processing workflow.

---

# Excel dates and serial numbers

Excel commonly represents dates internally as serial numbers with formatting applied for display.

This explains why date arithmetic is possible.

If one cell contains an earlier date and another contains a later date, subtracting them can produce a number of days.

For example:

`=B2-A2`

can calculate the number of days between two dates.

The displayed appearance of a date is therefore different from its underlying value.

The study script includes a simplified Excel serial-date demonstration using an appropriate epoch for ordinary modern dates.

There is also a historical complication in Excel's 1900 date system: Excel maintains compatibility with a historical leap-year bug involving the year 1900. This is one reason date-serial conversions should be handled carefully when implementing Excel-compatible systems.

---

# Text values versus numeric values

Correct data types are important.

Typical classifications include:

| Data | Appropriate type |
|---|---|
| Person name | Text |
| Employee code | Text |
| Phone number | Text |
| Postal code | Text |
| Revenue | Number |
| Interest rate | Number |
| Transaction date | Date |
| Month-end date | Date |
| Report label | Text |

Identifiers should generally be treated as text when leading zeros or formatting are meaningful.

For example:

`00125`

should not automatically become:

`125`

if the zeros are part of the identifier.

---

# Date ambiguity

Dates entered as text can be ambiguous.

For example:

`03/04/2026`

could represent:

- 3 April 2026
- March 4, 2026

depending on the regional convention.

Using explicit date construction such as:

`=DATE(2026,4,3)`

makes the intended components unambiguous.

Consistent date storage is particularly important in organizations operating across multiple countries.

---

# Edge cases

## Text edge cases

Important text cases include:

- empty strings
- strings containing only spaces
- repeated spaces
- control characters
- non-breaking spaces
- missing delimiters
- delimiters appearing multiple times
- case differences
- values shorter than the requested extraction length
- requested extraction length of zero
- negative character counts

These conditions can affect the output of text functions and should be considered when designing formulas.

## Date edge cases

Important date cases include:

- February
- leap years
- month-end dates
- year boundaries
- negative month offsets
- positive month offsets
- invalid calendar dates
- ambiguous text dates

Date calculations should be based on calendar logic rather than assumptions about fixed month lengths.

---

# Common mistakes

## Using the wrong indexing assumption with MID

Excel positions start at 1.

Python indexes start at 0.

This difference is easy to overlook when translating Excel logic into another programming language.

## Assuming LEN ignores spaces

`LEN` counts spaces.

Unexpected spaces therefore increase the result.

## Expecting TRIM to remove every invisible character

`TRIM` handles ordinary spaces, while `CLEAN` handles non-printable control characters.

Neither function should be assumed to normalize every possible Unicode character.

## Assuming SUBSTITUTE is case-insensitive

`SUBSTITUTE` is case-sensitive.

Different capitalization must be handled separately when required.

## Converting numbers to text too early

`TEXT` produces text.

A formatted text value should not be used as a substitute for the original numeric value when calculations still need to be performed.

## Treating dates as ordinary strings

A string that looks like a date may not be an actual Excel date value.

Actual date values are preferable for calculations and comparisons.

## Adding a fixed number of days for month calculations

Adding 30 days does not mean adding one calendar month.

Use `EOMONTH` when month-end logic is required.

## Hard-coding positions unnecessarily

Fixed positions are appropriate for fixed-width identifiers.

For variable-length identifiers, delimiter-driven extraction is generally more robust.

---

# Performance considerations

Text functions are usually straightforward for ordinary worksheets, but formula design becomes more important as data volume grows.

Useful practices include:

- avoid repeating the same transformation unnecessarily
- perform common cleaning operations once where practical
- use helper columns when they improve readability
- avoid unnecessarily deep formula nesting
- keep raw data separate from cleaned data
- use Excel Tables and structured references for organized datasets
- avoid unnecessarily expensive repeated range calculations
- consider Power Query when worksheet formulas become difficult to maintain
- prioritize auditability in business spreadsheets

Performance should not be considered only in terms of calculation speed. A shorter formula is not necessarily a better formula if it is difficult to understand or audit.

---

# Security and data-quality considerations

Text functions are often applied to data imported from external systems.

Potential sources include:

- CSV files
- websites
- ERP systems
- CRM systems
- emails
- exported reports
- user-submitted forms

Important risks include:

- hidden control characters
- misleading whitespace
- unexpected delimiters
- malformed identifiers
- ambiguous dates
- accidental loss of leading zeros
- unexpected type conversion
- unsafe handling of imported text during downstream export

Imported text should be treated as untrusted data until its structure and meaning have been validated.

A particularly important consideration in automated spreadsheet workflows is formula injection when untrusted text is written into cells or exported into spreadsheet-compatible files. Data-processing logic should distinguish ordinary text from formulas and control how external values are written.

---

# Implementation considerations

The Python study file intentionally uses only the standard library.

The main mapping is:

| Excel concept | Python concept used in the script |
|---|---|
| Text value | `str` |
| Date value | `datetime.date` |
| `LEFT` | string slicing from the beginning |
| `RIGHT` | string slicing from the end |
| `MID` | slicing after converting Excel's 1-based position |
| `LEN` | `len()` |
| `TRIM` | space normalization |
| `CLEAN` | removal of ASCII control characters |
| `SUBSTITUTE` | string replacement |
| `TEXT` | explicit formatting logic |
| `CONCAT` | string joining |
| `TEXTJOIN` | delimiter-based joining |
| `DATE` | date construction with Excel-style normalization |
| `YEAR` | `.year` |
| `MONTH` | `.month` |
| `DAY` | `.day` |
| `EOMONTH` | calendar arithmetic and `monthrange()` |

The Python implementations are educational models rather than complete reimplementations of Microsoft's entire Excel calculation engine. Excel's custom number-format language, date-system behavior, error propagation, dynamic arrays, worksheet references, and broader formula engine contain many additional rules.

---

# Testing

The script contains executable assertions covering the core implementations.

The tests verify examples such as:

- `LEFT` extraction
- `RIGHT` extraction
- `MID` extraction
- character counting
- space trimming
- control-character removal
- text replacement
- concatenation
- delimiter-based joining
- date construction
- date component extraction
- month-end calculations
- Excel-style month normalization

Running the script executes these tests and reports whether they pass.

Testing is important when formulas or programmatic equivalents are used in data-processing workflows because small differences in edge-case behavior can produce incorrect business results.

---

# Practical applications

These functions have broad applications in spreadsheet-based analysis.

## Data cleaning

`TRIM`, `CLEAN`, and `SUBSTITUTE` can normalize imported data before analysis.

## Identifier parsing

`LEFT`, `MID`, and `RIGHT` can separate prefixes, region codes, years, and sequence numbers.

## Report generation

`TEXT`, `CONCAT`, and `TEXTJOIN` can create readable labels from numeric, date, and text values.

## Financial reporting

`DATE`, `YEAR`, `MONTH`, `DAY`, and `EOMONTH` support reporting periods and month-end calculations.

## Employee data

Employee codes, names, joining dates, and reporting periods can be cleaned and transformed into standardized records.

## Customer and transaction data

Customer identifiers, invoice codes, transaction dates, and amounts can be transformed into consistent reporting fields.

## Data preparation

These functions can form a first layer of spreadsheet-based ETL:

- extract
- transform
- standardize
- format
- combine

---

# Function selection guide

| Requirement | Function |
|---|---|
| Extract from the beginning | `LEFT` |
| Extract from the end | `RIGHT` |
| Extract from the middle | `MID` |
| Count characters | `LEN` |
| Remove extra ordinary spaces | `TRIM` |
| Remove control characters | `CLEAN` |
| Replace selected text | `SUBSTITUTE` |
| Format a number or date as text | `TEXT` |
| Combine text directly | `CONCAT` |
| Combine text with a delimiter | `TEXTJOIN` |
| Build an actual date | `DATE` |
| Extract year | `YEAR` |
| Extract month | `MONTH` |
| Extract day | `DAY` |
| Find the end of a month | `EOMONTH` |

---

# Core formula patterns

Common patterns demonstrated in the study file include:

`=LEFT(A2,3)`

Extract a fixed prefix.

`=RIGHT(A2,5)`

Extract a fixed suffix.

`=MID(A2,5,3)`

Extract a fixed-position component.

`=LEN(A2)`

Count characters.

`=TRIM(A2)`

Normalize ordinary spaces.

`=CLEAN(A2)`

Remove non-printable control characters.

`=SUBSTITUTE(A2,"-","")`

Remove a selected character.

`=TEXT(A2,"#,##0.00")`

Format a numeric value as text.

`=TEXT(A2,"dd-mm-yyyy")`

Format a date as text.

`=CONCAT(A2," ",B2)`

Combine fields with an explicit separator.

`=TEXTJOIN(", ",TRUE,A2:E2)`

Join multiple values using a delimiter while ignoring empty values.

`=DATE(2026,9,11)`

Construct a date.

`=YEAR(A2)`

Extract the year.

`=MONTH(A2)`

Extract the month.

`=DAY(A2)`

Extract the day.

`=EOMONTH(A2,0)`

Return the last day of the date's month.

---

# Function composition patterns

The functions become substantially more useful when composed.

A common cleaning formula is:

`=TRIM(CLEAN(A2))`

A stronger cleaning pattern for non-breaking spaces is:

`=TRIM(CLEAN(SUBSTITUTE(A2,CHAR(160)," ")))`

A formatted report component can use:

`=TEXT(A2,"mmm yyyy")`

A combined report field can use:

`=CONCAT("Period: ",TEXT(A2,"mmm yyyy"))`

Multiple report components can use:

`=TEXTJOIN(" | ",TRUE,A2:E2)`

The underlying principle is modularity. Each function performs one transformation, while composition creates a larger operation.

---

# Relationship between formatting and data

One of the most important concepts in spreadsheet work is the difference between:

- the underlying value
- the displayed format
- text representing a value

A date can have an underlying date value while being displayed as:

`11-Sep-2026`

A number can be stored as:

`1250000.5`

while displayed as:

`1,250,000.50`

Using `TEXT` changes the result into text. Ordinary cell formatting changes presentation without necessarily changing the underlying data type.

This distinction is critical for reliable calculations.

---

# Real-world design principles

Good spreadsheet design generally follows several principles demonstrated by the script:

1. Keep dates as actual dates when calculations are required.
2. Keep numeric values numeric until presentation requires text.
3. Treat identifiers as text when formatting and leading zeros matter.
4. Clean imported text before performing position-sensitive extraction.
5. Prefer delimiter-based extraction when field lengths can change.
6. Use `EOMONTH` for calendar-month logic rather than fixed day counts.
7. Use `TEXTJOIN` when a repeated delimiter and empty-value handling are required.
8. Use `CONCAT` when explicit control over individual components is preferable.
9. Validate assumptions about imported data.
10. Test edge cases such as empty values, missing delimiters, leap years, and month boundaries.

The Python study file puts these principles into executable examples so that the behavior of the corresponding Excel functions can be examined rather than treated as isolated formula syntax.
