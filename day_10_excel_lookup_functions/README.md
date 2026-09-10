# Excel Lookup Functions

## Topic introduction

Excel lookup functions are used to find a value in a dataset and return a related value from the same record, row, column, or lookup structure.

The major functions covered in this study are:

- VLOOKUP
- HLOOKUP
- XLOOKUP
- INDEX
- MATCH
- XMATCH

The material also covers exact matching, approximate matching, wildcard matching, duplicate values, left lookups, two-way lookups, multiple-criteria lookups, lookup errors, data-quality problems, performance, maintainability, and practical spreadsheet design.

The accompanying Python script models the core logic of these functions without requiring external packages. Python is used to make the underlying lookup mechanisms explicit and executable.

## What is a lookup?

A lookup generally involves three pieces of information:

1. A lookup value
2. A lookup range or array
3. A return range or array

For example, an employee table might contain:

| Employee ID | Employee | Department | Salary |
|---|---|---|---:|
| E101 | Anika | Finance | 72000 |
| E102 | Rahul | Sales | 68000 |
| E103 | Priya | IT | 85000 |
| E104 | Karan | HR | 64000 |

If `E103` is the lookup value and the required result is the department, the lookup operation finds the record associated with `E103` and returns `IT`.

The central distinction is between finding a position and returning a value. `MATCH` and `XMATCH` primarily determine a position, while `INDEX` retrieves a value at a specified position. `VLOOKUP`, `HLOOKUP`, and `XLOOKUP` combine these ideas into lookup operations.

## Fundamental terminology

### Lookup value

The value being searched for.

Examples include:

- Employee ID
- Product code
- Customer ID
- Invoice number
- Date
- Score
- Revenue threshold

### Lookup array

The range containing the values against which the lookup value is compared.

### Return array

The range containing the values that should be returned.

### Exact match

An exact match returns a result only when the lookup value corresponds to an appropriate value in the lookup range.

This is normally the correct behavior for identifiers such as:

- Employee IDs
- Customer IDs
- Product codes
- Transaction IDs
- Account numbers
- Invoice numbers

### Approximate match

An approximate match selects a boundary based on an ordered lookup range.

A common example is a grading table:

| Minimum score | Grade |
|---:|---|
| 0 | F |
| 40 | D |
| 50 | C |
| 60 | B |
| 75 | A |
| 90 | A+ |

A score of 82 belongs to the `75` boundary and therefore receives an `A`.

Approximate matching is not the same as finding the numerically closest value. It normally means selecting a valid boundary according to the matching mode.

## VLOOKUP

`VLOOKUP` means Vertical Lookup.

Its conceptual syntax is:

`VLOOKUP(lookup_value, table_array, col_index_num, [range_lookup])`

The major arguments are:

- `lookup_value`: value being searched for
- `table_array`: table containing the lookup and return data
- `col_index_num`: column number from which the result is returned
- `range_lookup`: controls exact or approximate matching

The fourth argument is especially important:

- `FALSE` or `0`: exact match
- `TRUE` or `1`: approximate match

An exact VLOOKUP can be represented conceptually as:

`=VLOOKUP(A2,$A$2:$D$100,4,FALSE)`

This searches for the value in `A2` in the first column of the table and returns the corresponding value from column 4.

### VLOOKUP's structural requirement

VLOOKUP searches the first column of its supplied table.

For example, if the table is:

| ID | Name | Department |
|---|---|---|
| E101 | Anika | Finance |
| E102 | Rahul | Sales |
| E103 | Priya | IT |

VLOOKUP can search the `ID` column and return `Name` or `Department`.

It cannot naturally perform a lookup where the desired return column is positioned to the left of the lookup column.

This limitation is one reason `INDEX + MATCH` and `XLOOKUP` are important.

## VLOOKUP approximate matching

Approximate VLOOKUP is useful for boundary tables.

Example:

| Minimum value | Category |
|---:|---|
| 0 | Low |
| 25 | Moderate |
| 50 | High |
| 75 | Very High |

For a value of 63, the appropriate boundary is 50.

Conceptually:

`=VLOOKUP(A2,$A$2:$B$5,2,TRUE)`

The lookup table must be correctly ordered for approximate matching.

For an ascending boundary table, the lookup operation identifies the largest boundary that does not exceed the lookup value.

### Why sorting matters

Suppose the valid boundaries are:

`0, 25, 50, 75`

This is correctly ordered.

An incorrectly ordered list such as:

`50, 0, 75, 25`

does not provide the ordering guarantee expected by an ascending approximate lookup.

Approximate matching should therefore be used only when the source data satisfies the ordering requirements of the selected lookup method.

## HLOOKUP

`HLOOKUP` means Horizontal Lookup.

Its conceptual syntax is:

`HLOOKUP(lookup_value, table_array, row_index_num, [range_lookup])`

Unlike VLOOKUP, HLOOKUP searches across the first row and returns a value from a specified row.

For example:

|  | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Revenue | 120000 | 135000 | 148000 | 162000 |
| Profit | 18000 | 22000 | 27000 | 31000 |

A formula such as:

`=HLOOKUP("Q3",$B$1:$E$3,2,FALSE)`

conceptually searches for `Q3` in the first row and returns the corresponding value from the second row.

HLOOKUP is particularly associated with horizontally structured or legacy spreadsheet layouts.

## XLOOKUP

`XLOOKUP` is a modern lookup function designed to provide a more flexible lookup structure.

Its conceptual syntax is:

`XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])`

The important distinction is that the lookup range and return range are specified separately.

For example:

`=XLOOKUP(A2,$A$2:$A$100,$C$2:$C$100,"Not found")`

The formula searches column A and returns the corresponding value from column C.

The return range does not need to be to the right of the lookup range.

## XLOOKUP match modes

XLOOKUP supports several matching behaviors.

### Match mode 0

Exact match.

This is the normal choice for identifiers.

Conceptually:

`match_mode = 0`

### Match mode -1

Exact match or next smaller item.

This is useful for threshold and boundary tables.

For a lookup value of 82 and boundaries:

`0, 40, 50, 60, 75, 90`

the selected boundary is 75.

### Match mode 1

Exact match or next larger item.

This is useful when the business rule requires the next available upper boundary.

For example, if package sizes are:

`10, 25, 50, 100`

and the package weighs 37, the next larger boundary is 50.

### Match mode 2

Wildcard matching.

This supports patterns involving wildcard characters.

## XLOOKUP search modes

XLOOKUP also controls the direction of the search.

### Search mode 1

Search from first to last.

This normally returns the first matching occurrence.

### Search mode -1

Search from last to first.

This returns the last matching occurrence.

This is useful when a dataset contains repeated identifiers and the most recent or last-listed record is required.

## XLOOKUP and duplicate values

Suppose:

| ID | Value |
|---|---:|
| A | 100 |
| B | 200 |
| A | 350 |
| C | 400 |
| A | 500 |

A normal first-to-last lookup for `A` returns 100.

A last-to-first lookup can return 500.

The important business question is whether duplicate keys are expected.

If a key is supposed to be unique, duplicate detection is generally better than silently selecting either the first or last record.

If duplicates are legitimate transactions, selecting the first, last, or all matching records should be an explicit business decision.

## INDEX

`INDEX` returns a value from a specified position.

A one-dimensional conceptual form is:

`INDEX(array, row_num)`

For a two-dimensional range:

`INDEX(array, row_num, column_num)`

For example:

`=INDEX(C2:C5,3)`

returns the third value from the specified return range.

The important feature of INDEX is that it does not need to know how the position was determined.

Another function can calculate the position, and INDEX can retrieve the value.

This separation makes INDEX especially useful with MATCH and XMATCH.

## MATCH

`MATCH` finds the position of a value in a lookup range.

Its conceptual syntax is:

`MATCH(lookup_value, lookup_array, match_type)`

The classic matching modes are:

- `0`: exact match
- `1`: exact match or next smaller value
- `-1`: exact match or next larger value

Excel positions are one-based. The first item in a range has position 1.

Python lists normally use zero-based indexes, so the Python demonstration explicitly converts between the two concepts.

### MATCH does not normally return the value

For example:

`=MATCH("E103",A2:A5,0)`

returns a position.

It does not directly return the employee's department.

That is where INDEX becomes useful.

## INDEX + MATCH

A classic lookup pattern is:

`=INDEX($C$2:$C$100,MATCH(A2,$A$2:$A$100,0))`

The two functions perform separate tasks.

`MATCH` answers:

"Which position contains the lookup value?"

`INDEX` answers:

"What value is stored at that position in the return range?"

This structure is more flexible than traditional VLOOKUP because the return range does not have to be to the right of the lookup range.

## Left lookup

Consider:

| Employee | ID |
|---|---|
| Anika | E101 |
| Rahul | E102 |
| Priya | E103 |

If `E102` is the lookup value and the required result is `Rahul`, the return data is positioned to the left of the lookup data.

A VLOOKUP-oriented structure does not naturally support this.

`INDEX + MATCH` can perform the lookup:

`=INDEX(A2:A4,MATCH(E102,B2:B4,0))`

XLOOKUP can express the same logic more directly:

`=XLOOKUP(E102,B2:B4,A2:A4)`

## XMATCH

`XMATCH` is the modern counterpart to MATCH.

Its conceptual syntax is:

`XMATCH(lookup_value, lookup_array, [match_mode], [search_mode])`

XMATCH supports more flexible matching and search behavior than traditional MATCH.

Its matching modes include:

- `0`: exact match
- `-1`: exact match or next smaller
- `1`: exact match or next larger
- `2`: wildcard match

Its search modes include:

- `1`: first-to-last
- `-1`: last-to-first
- `2`: binary search in ascending order
- `-2`: binary search in descending order

XMATCH is particularly useful when position-based lookup logic needs modern search behavior.

## INDEX + XMATCH

A modern position-based lookup can be expressed as:

`=INDEX($C$2:$C$100,XMATCH(A2,$A$2:$A$100,0))`

The relationship is:

1. XMATCH identifies the position.
2. INDEX returns the value at that position.

This combination is useful when lookup logic needs to remain separate from return logic.

## Two-way lookup

A two-way lookup determines both:

- the required row
- the required column

Consider:

| Product | Jan | Feb | Mar |
|---|---:|---:|---:|
| Product A | 100 | 120 | 130 |
| Product B | 200 | 220 | 240 |
| Product C | 300 | 320 | 350 |

If the requested product is Product B and the requested month is February, the lookup must identify:

- Product B's row
- February's column

A classic formula pattern is:

`=INDEX(B2:D4,MATCH("Product B",A2:A4,0),MATCH("Feb",B1:D1,0))`

This is an `INDEX + MATCH + MATCH` structure.

The first MATCH finds the row.

The second MATCH finds the column.

INDEX returns their intersection.

## Two-way XLOOKUP

Two-way lookup can also be constructed with nested XLOOKUP logic.

Conceptually:

`=XLOOKUP(column_name,header_range,XLOOKUP(row_name,row_header_range,data_range))`

The inner lookup selects the appropriate row.

The outer lookup selects the appropriate column from that row.

This approach is often easier to read when the spreadsheet is designed around named or structured ranges.

## Multiple-criteria lookups

Many real-world lookups require more than one condition.

For example:

- Department = IT
- City = Delhi

The target record must satisfy both conditions.

A spreadsheet can implement this using Boolean conditions or a helper key.

A helper key might combine:

`Department|City`

For example:

`IT|Delhi`

A lookup can then search the combined key.

This approach can make formulas easier to maintain when the same combination is repeatedly used.

The Python script also demonstrates direct multiple-criteria filtering, where every supplied condition must be satisfied.

## Wildcard matching

Wildcard matching is useful when the complete lookup value is not known.

The principal wildcard characters are:

- `*`: zero or more characters
- `?`: exactly one character
- `~`: escape character for literal wildcard symbols

For example:

`Pri*`

can match names beginning with `Pri`.

A wildcard pattern should be designed carefully because a broad pattern can return unintended records.

## Exact matching versus approximate matching

The distinction between exact and approximate matching is fundamental.

| Requirement | Appropriate approach |
|---|---|
| Employee ID | Exact |
| Product code | Exact |
| Invoice number | Exact |
| Customer ID | Exact |
| Grade boundary | Approximate |
| Commission band | Approximate |
| Tax threshold | Approximate |
| Credit-score band | Approximate |
| Date range boundary | Approximate |
| Shipping tier | Approximate |

A common spreadsheet error is using approximate matching for an identifier.

For example, an employee ID is normally a discrete key. It should not be interpreted as a numerical threshold.

## Approximate matching is not nearest-value matching

Suppose the boundaries are:

`0, 40, 50, 60, 75, 90`

For a value of 74, an approximate lower-bound lookup selects 60.

It does not select 75 because 75 is numerically closer to 74.

The business interpretation is:

"Select the largest valid boundary that does not exceed the input."

This distinction is critical for grading systems, tax brackets, commission structures, pricing tiers, risk bands, and similar models.

## Lookup errors

Common Excel errors relevant to lookup work include:

### #N/A

The requested value cannot be found.

Typical causes include:

- missing record
- incorrect lookup value
- extra whitespace
- inconsistent data types
- wrong lookup range
- spelling differences

### #VALUE!

The formula contains an invalid argument or incompatible value.

### #REF!

A reference is invalid.

This can occur when formulas refer to deleted or otherwise invalid ranges.

### #NAME?

Excel does not recognize a function, name, or formula component.

### #SPILL!

A dynamic-array result cannot occupy the cells required for the result.

### #NUM!

A numeric calculation or argument is invalid.

The accompanying Python script models lookup-related errors with custom exceptions.

## IFNA versus IFERROR

`IFNA` and `IFERROR` should not be treated as identical.

### IFNA

Use IFNA when the intended fallback applies specifically to a not-found condition.

Conceptually:

`=IFNA(XLOOKUP(A2,B:B,C:C),"Not found")`

### IFERROR

IFERROR handles a wider set of errors.

Conceptually:

`=IFERROR(formula,"Fallback")`

Broad error suppression can hide genuine formula or data problems.

If the business requirement is specifically "replace a missing lookup with a message," IFNA communicates that intention more precisely.

## Text normalization

Lookup failures can occur because visually similar text is technically different.

Examples include:

- `E103`
- ` E103`
- `E103 `
- different non-printing characters
- inconsistent capitalization
- different representations of the same identifier

Data-cleaning functions such as TRIM and CLEAN can help with relevant cases.

A reliable lookup design should clean and standardize data at an appropriate stage rather than repeatedly compensating for poor source data inside formulas.

## Numbers stored as text

Another common issue is the difference between:

`100`

and:

`"100"`

The first represents a number.

The second represents text.

They can appear identical in a worksheet but behave differently in comparisons and calculations.

Lookup keys and lookup ranges should use consistent representations.

This is especially important for:

- product codes
- account numbers
- postal codes
- employee IDs
- transaction IDs
- numeric measures

Not every numeric-looking identifier should be converted to a number. Identifiers that contain leading zeros should generally remain text.

## Case sensitivity

Standard Excel lookup behavior is generally not case-sensitive.

For many business lookups:

`abc`

and:

`ABC`

are therefore treated as equivalent for matching purposes.

If a business process genuinely requires case-sensitive matching, a dedicated case-sensitive comparison strategy is needed.

Case sensitivity should be an intentional data rule rather than an accidental property of the workbook.

## Duplicate keys

A lookup table should have a clearly defined key.

If an employee ID is expected to be unique but appears multiple times, the problem is usually data quality rather than a formula problem.

If duplicates are legitimate, the spreadsheet should define which record is required.

Possible requirements include:

- first matching record
- last matching record
- all matching records
- most recent record
- record satisfying an additional criterion

XLOOKUP's search mode supports first-to-last and last-to-first behavior.

When all matching records are needed, a filtering approach is usually more appropriate than a single-result lookup.

## Returning multiple matches

A lookup function normally returns one result.

A dataset may contain several matching rows.

For example:

| Transaction ID | Amount |
|---|---:|
| T001 | 100 |
| T002 | 200 |
| T001 | 350 |
| T003 | 400 |
| T001 | 500 |

A single-result lookup may return either 100 or 500 depending on the search direction.

If all three T001 transactions are required, a filtering operation is more suitable.

This is an important distinction between:

- lookup
- filtering
- aggregation

A lookup selects a related result. It is not inherently a complete data-retrieval system.

## Data validation and lookup design

Reliable lookup formulas depend on reliable data.

Important validation questions include:

- Is the lookup key defined?
- Are keys unique when they should be?
- Are data types consistent?
- Are blanks valid?
- Are duplicate records expected?
- Are approximate-match boundaries correctly ordered?
- Are lookup and return ranges the same length?
- Are source values normalized?
- Are headers and ranges correct?

Formula correctness and data quality are separate concerns.

A perfect formula can still return an incorrect business result when the source data is wrong.

## Lookup table design

A well-designed lookup table should generally have:

- clear headers
- a clearly defined key
- consistent data types
- one logical record per row
- no accidental duplicates
- no unnecessary merged cells in the data area
- appropriate sorting for approximate lookup
- predictable blank handling

Excel Tables can improve maintainability because structured references expand as data is added.

For example, instead of relying on fixed cell ranges, structured references can refer to columns such as:

`Employees[Employee ID]`

and:

`Employees[Department]`

A conceptual structured XLOOKUP is:

`=XLOOKUP([@[Employee ID]],Employees[Employee ID],Employees[Department],"Not found")`

## VLOOKUP versus XLOOKUP

| Feature | VLOOKUP | XLOOKUP |
|---|---|---|
| Vertical lookup | Yes | Yes |
| Horizontal lookup | No | Yes |
| Exact match | Yes | Yes |
| Approximate match | Yes | Yes |
| Left lookup | Not naturally | Yes |
| Separate lookup and return arrays | No | Yes |
| Explicit not-found argument | No | Yes |
| First/last search control | Limited | Yes |
| Wildcard mode | Limited compared with XLOOKUP | Yes |
| Return-column number required | Yes | No |
| Modern flexible lookup design | Limited | Strong |

XLOOKUP is generally easier to express because the lookup range and return range are explicitly separated.

## VLOOKUP versus INDEX + MATCH

| Characteristic | VLOOKUP | INDEX + MATCH |
|---|---|---|
| Simplicity | High | Moderate |
| Left lookup | No natural support | Yes |
| Return column selection | Column number | Independent return range |
| Position logic | Built in | Explicit |
| Legacy compatibility | Very high | Very high |
| Formula complexity | Usually lower | Usually higher |
| Maintainability | Can be affected by column insertion | Generally flexible |

VLOOKUP remains useful for straightforward vertical tables, particularly in existing workbooks.

INDEX + MATCH becomes valuable when lookup and return positions need to be independent.

## MATCH versus XMATCH

XMATCH extends the traditional MATCH concept.

| Feature | MATCH | XMATCH |
|---|---|---|
| Exact matching | Yes | Yes |
| Approximate matching | Yes | Yes |
| Wildcard matching | Limited by traditional modes | Yes |
| Search direction | Limited | Yes |
| Binary search modes | No | Yes |
| Modern lookup architecture | Older | Newer |

XMATCH is especially useful when the position itself is required and modern matching behavior is desired.

## INDEX + MATCH versus INDEX + XMATCH

Both combinations separate position detection from value retrieval.

Classic:

`=INDEX(return_range,MATCH(lookup_value,lookup_range,0))`

Modern:

`=INDEX(return_range,XMATCH(lookup_value,lookup_range,0))`

XMATCH provides additional search and matching options, making it more flexible for modern workbooks.

## Binary search

A linear search examines records sequentially.

Its approximate computational complexity is:

`O(n)`

A binary search repeatedly divides an ordered search range in half.

Its approximate computational complexity is:

`O(log n)`

For a million records, this distinction can become significant.

Binary search requires the correct ordering assumptions. An incorrectly sorted dataset can make a binary-search lookup return an incorrect result.

This is why performance improvements should never be separated from correctness requirements.

## Performance considerations

Large workbooks can contain thousands or millions of formula evaluations.

Performance considerations include:

- avoiding unnecessarily large lookup ranges
- avoiding repeated expensive calculations
- using structured tables appropriately
- reducing redundant formulas
- using suitable search modes
- maintaining correct sorting when binary search is used
- separating data transformation from presentation where appropriate
- avoiding unnecessary volatile calculations

A fast incorrect lookup is still incorrect.

Correctness should be established before optimizing lookup performance.

## Hard-coded VLOOKUP column numbers

A common VLOOKUP pattern is:

`=VLOOKUP(A2,A:D,4,FALSE)`

The number `4` identifies the return column.

This can be fragile when the structure of the table changes.

If a new column is inserted, the intended return field may no longer correspond to the original column number.

XLOOKUP avoids this specific dependency because the return array is explicitly supplied.

This improves readability and can improve maintainability.

## Absolute references

Spreadsheet formulas commonly use:

- `A2`: relative row and column
- `$A$2`: absolute row and column
- `A$2`: fixed row
- `$A2`: fixed column

Lookup formulas frequently use absolute references for static lookup ranges.

For example:

`=VLOOKUP(A2,$A$2:$D$100,4,FALSE)`

The lookup value changes as the formula is copied, while the lookup table remains fixed.

## Structured references

Excel Tables allow formulas to refer to named columns instead of fixed cell ranges.

A structured lookup can be easier to understand than:

`$A$2:$A$1000`

because the formula communicates the business meaning of the data.

For example:

`Employees[Employee ID]`

is more descriptive than an anonymous cell range.

Structured references also support expanding datasets more naturally.

## Practical applications

Lookup functions are widely applicable to spreadsheet-based analysis.

### Human resources

Examples include:

- employee ID to employee name
- employee ID to department
- employee ID to salary band
- employee ID to location

### Finance

Examples include:

- transaction ID to amount
- customer ID to credit limit
- revenue to commission rate
- income to tax bracket
- date to financial year
- amount to discount percentage

### Sales

Examples include:

- product code to price
- customer ID to sales representative
- sales amount to incentive rate
- region to target

### Operations

Examples include:

- product code to inventory category
- shipment weight to shipping class
- date to reporting period
- location code to region

### Risk analysis

Examples include:

- credit score to risk band
- probability to risk category
- exposure amount to classification
- portfolio metric to threshold category

## Common mistakes

### Using approximate matching for identifiers

An employee ID is normally an exact key.

Using approximate matching can produce an incorrect record.

### Failing to sort approximate lookup data

Boundary-based approximate lookup depends on ordering assumptions.

### Using the wrong VLOOKUP column number

The return column number must correspond to the supplied table.

### Assuming keys are unique

A duplicate key can cause a lookup to return an unexpected record.

### Ignoring whitespace

Leading or trailing spaces can cause apparent matches to fail.

### Mixing numbers and text

`100` and `"100"` are not necessarily equivalent representations.

### Suppressing every error

Using a broad IFERROR can hide problems that should be investigated.

### Returning a zero and treating it as failure

Zero is a legitimate result.

Lookup success should be determined by the lookup operation, not by whether the returned value is truthy.

### Overusing nested lookups

Deeply nested formulas can become difficult to audit and maintain.

A helper column, structured table, or clearer intermediate calculation can sometimes be preferable.

## Edge cases

The Python script demonstrates several important edge cases.

### Empty lookup arrays

A lookup against an empty range should be treated explicitly rather than silently producing an arbitrary result.

### Missing values

A missing lookup should normally produce a not-found condition.

### Duplicate values

First-match and last-match behavior should be intentional.

### Blank values

A blank can either be a legitimate key or an invalid input depending on the business rules.

### Zero values

A result of zero is not equivalent to "not found."

### Negative numbers

Approximate threshold logic must work correctly when boundaries include negative values.

### Decimal values

Floating-point and decimal boundaries require careful interpretation, particularly when they represent financial thresholds.

### Dates

Dates are ordered values and can be used effectively for approximate boundary lookups.

### Wildcards

Wildcard patterns can produce broader matches than intended.

### Array-size mismatch

The lookup and return arrays must correspond correctly.

## Error-handling principles

A robust lookup design should distinguish between:

- missing records
- invalid formulas
- invalid references
- malformed data
- inconsistent data types
- ambiguous duplicate keys

Not every error should be converted into the same message.

For example, "Customer not found" is useful when the customer ID does not exist.

It is misleading when the real problem is an invalid reference or malformed source range.

## Security considerations

Lookup functions are not security controls.

A formula can retrieve data that the workbook user can otherwise access.

Sensitive information should not be protected merely by hiding columns or worksheets.

Data security should consider:

- workbook permissions
- controlled access
- sensitive worksheet protection
- appropriate data sharing
- source-data access
- formula auditing
- accidental exposure of confidential fields

This is particularly important when lookup results contain:

- salaries
- financial account information
- tax identifiers
- credit limits
- customer information
- confidential business metrics

## Data-integrity considerations

Lookup functions are often used in calculations where an incorrect result may appear plausible.

For example, if a commission lookup selects the wrong threshold, the resulting commission can still look like a valid number.

For critical workbooks, lookup logic should therefore be validated with known test cases.

Important validation cases include:

- minimum boundary
- maximum boundary
- value between boundaries
- exact boundary
- missing value
- duplicate key
- blank value
- invalid value
- incorrectly ordered approximate data

## Testing lookup formulas

Lookup formulas should be tested with representative examples.

A useful test set includes:

1. Known valid exact key
2. Missing key
3. Duplicate key
4. First boundary
5. Last boundary
6. Value immediately below a boundary
7. Value immediately above a boundary
8. Blank input
9. Zero result
10. Unexpected data type

The Python script implements simple assertions and edge-case tests to demonstrate this approach.

## Formula selection

A practical decision framework is:

| Requirement | Suitable function or pattern |
|---|---|
| Simple vertical exact lookup | XLOOKUP |
| Simple vertical lookup in older workbooks | VLOOKUP |
| Horizontal legacy lookup | HLOOKUP |
| Find a position | MATCH or XMATCH |
| Return a value by position | INDEX |
| Flexible position-based lookup | INDEX + XMATCH |
| Left lookup | XLOOKUP or INDEX + MATCH |
| Approximate threshold lookup | XLOOKUP, MATCH, or VLOOKUP |
| First duplicate match | XLOOKUP with first-to-last search |
| Last duplicate match | XLOOKUP with last-to-first search |
| Two-way lookup | INDEX + XMATCH or nested XLOOKUP |
| Multiple matching rows | Filtering approach |

## Common Excel formula patterns

Exact VLOOKUP:

`=VLOOKUP(A2,$A$2:$D$100,4,FALSE)`

Approximate VLOOKUP:

`=VLOOKUP(A2,$A$2:$B$10,2,TRUE)`

Exact HLOOKUP:

`=HLOOKUP(B1,$B$1:$F$4,4,FALSE)`

INDEX + MATCH:

`=INDEX($C$2:$C$100,MATCH(A2,$A$2:$A$100,0))`

XLOOKUP:

`=XLOOKUP(A2,$A$2:$A$100,$C$2:$C$100,"Not found")`

XLOOKUP with approximate lower boundary:

`=XLOOKUP(A2,$A$2:$A$100,$C$2:$C$100,"Not found",-1)`

XMATCH:

`=XMATCH(A2,$A$2:$A$100,0)`

INDEX + XMATCH:

`=INDEX($C$2:$C$100,XMATCH(A2,$A$2:$A$100,0))`

Two-way INDEX + XMATCH:

`=INDEX($B$2:$F$100,XMATCH(A2,$A$2:$A$100,0),XMATCH(B1,$B$1:$F$1,0))`

## Production considerations

A production-quality spreadsheet lookup design should have:

- clear lookup keys
- documented matching assumptions
- appropriate exact or approximate matching
- validated source data
- controlled duplicate behavior
- explicit error handling
- stable references
- understandable formulas
- appropriate performance
- test cases for important boundaries
- controlled access for sensitive information

Lookup formulas should be treated as part of a larger data model rather than isolated pieces of syntax.

The reliability of the final result depends on both formula logic and source-data quality.

## Script coverage

The Python study script implements and demonstrates:

- basic lookup concepts
- Excel-style lookup errors
- exact matching
- approximate matching
- VLOOKUP
- HLOOKUP
- XLOOKUP
- INDEX
- MATCH
- XMATCH
- IFNA
- IFERROR
- wildcard matching
- first and last duplicate matches
- left lookups
- two-way lookups
- multiple-criteria lookups
- helper-key lookups
- date-based lookups
- threshold-based lookups
- financial boundary lookups
- text normalization
- numeric versus text values
- case-sensitive and case-insensitive comparisons
- binary search
- performance concepts
- data validation
- duplicate-key detection
- error diagnostics
- formula maintainability
- structured-reference concepts
- testing and edge cases
- security and data-integrity considerations
