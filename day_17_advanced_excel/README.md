# Advanced Excel: Dynamic arrays, FILTER, SORT, UNIQUE, SEQUENCE, LET, and LAMBDA

## Introduction

Modern Excel can perform array-based calculations directly inside worksheet formulas. Instead of requiring a separate formula in every output cell, a single formula can return multiple values and automatically populate a range of cells.

This capability is commonly called **dynamic arrays**.

The central functions covered in this repository are:

- `FILTER`
- `SORT`
- `UNIQUE`
- `SEQUENCE`
- `LET`
- `LAMBDA`

These functions are particularly useful for data analysis, reporting, financial models, operational dashboards, business intelligence, data preparation, and reusable spreadsheet logic.

The three implementations demonstrate the same computational ideas from different programming perspectives:

- Python models the concepts with readable data-processing functions and progressively more advanced analytical pipelines.
- JavaScript demonstrates the same ideas through arrays, higher-order functions, objects, closures, asynchronous processing, and application-style data transformations.
- C++ implements a complete sales-analysis case study with explicit data structures, validation, reusable functions, algorithms, complexity considerations, and performance-oriented aggregation.

---

## Dynamic arrays

A traditional spreadsheet formula generally produces one result in one cell. A dynamic-array formula can produce a collection of values.

For example:

`=SEQUENCE(5)`

produces the conceptual result:

`1`

`2`

`3`

`4`

`5`

The formula exists in a single starting cell, while Excel automatically places the resulting values into the cells below it.

This automatic placement is called **spilling**.

A dynamic-array formula therefore has two important dimensions:

1. The formula itself.
2. The resulting spill range.

The size of the spill range can change when the source data changes.

This is different from manually copying formulas down a fixed number of rows.

---

## Spill behavior

When a dynamic-array formula produces multiple cells, Excel must have sufficient space to place the result.

For example:

`=FILTER(A2:D100,D2:D100="East")`

may return five rows today and twenty rows tomorrow.

The formula therefore controls a variable-sized output region.

If an existing value occupies a cell that Excel needs for the result, Excel can report a `#SPILL!` error.

Common causes include:

- another value occupying the spill range
- merged cells
- an inappropriate placement of the formula
- insufficient available worksheet space
- structural restrictions in the destination area

The Python implementation models this concept with the `SpillArea` class. It checks whether a rectangular output area is occupied.

The JavaScript implementation does not reproduce the Excel worksheet grid, but its array operations demonstrate the underlying variable-sized result.

The C++ implementation represents dynamic-array behavior through vectors whose sizes are determined at runtime.

---

## SEQUENCE

### Purpose

`SEQUENCE` generates a numeric array.

General syntax:

`=SEQUENCE(rows, [columns], [start], [step])`

The first argument specifies the number of rows.

The second argument specifies the number of columns.

The third argument specifies the starting value.

The fourth argument specifies the increment.

Examples:

`=SEQUENCE(5)`

generates five rows.

`=SEQUENCE(3,2)`

generates three rows and two columns.

`=SEQUENCE(4,1,10,5)`

generates:

`10`

`15`

`20`

`25`

The Python `sequence()` function explicitly constructs the same two-dimensional structure.

The C++ `sequence()` function uses `vector<vector<int>>` to represent the resulting matrix.

The JavaScript version creates nested arrays.

### Practical uses

`SEQUENCE` is useful for:

- generating row numbers
- creating test data
- generating dates
- building numerical ranges
- creating period indexes
- constructing matrix-like calculations
- generating dynamic report labels

For example, a date-oriented workbook can use a sequence of integers as an offset from a starting date.

---

## FILTER

### Purpose

`FILTER` returns only the records that satisfy a condition.

General syntax:

`=FILTER(array, include, [if_empty])`

For example:

`=FILTER(A2:D100,D2:D100="East","No matching records")`

selects rows where the corresponding value in column D is `East`.

The important concept is the **Boolean inclusion array**.

Conceptually:

`TRUE`

`FALSE`

`TRUE`

`FALSE`

`TRUE`

The `TRUE` positions are returned.

### Python implementation

The Python implementation uses:

`excel_filter(values, predicate)`

A predicate is a function that determines whether each value should remain in the result.

For employee records, the implementation can filter by department:

`employee.department == "Technology"`

This demonstrates a key difference between spreadsheet and programming terminology. Excel commonly represents the condition as an array of Boolean values, while Python can represent the same logic with a callable predicate.

### JavaScript implementation

JavaScript's built-in `Array.prototype.filter()` directly represents this computational model.

The implementation wraps that behavior in `excelFilter()`.

For example, a record can be retained when:

`employee.salary > 90000`

and:

`employee.department === "Technology"`

are both true.

### C++ implementation

The C++ implementation uses a generic template function:

`filter<T>()`

It accepts a vector and a `std::function<bool(const T&)>` predicate.

This makes the operation reusable for integers, sales records, or other data types.

---

## Boolean logic in FILTER

Complex filters often combine multiple conditions.

An AND-style condition can be expressed conceptually as:

`(department="Technology") AND (salary>90000)`

In Excel array formulas, multiplication is commonly used to combine Boolean conditions:

`(B2:B100="Technology")*(D2:D100>90000)`

Because Boolean values can participate in numeric array calculations, `TRUE` and `FALSE` can behave as `1` and `0`.

An OR-style condition can be represented using addition:

`(B2:B100="Technology")+(B2:B100="Finance")`

Care must be taken with more complex expressions because overlapping conditions can produce values greater than one.

In Python, the equivalent logic is explicit:

`employee.department == "Technology" and employee.salary > 90000`

JavaScript uses:

`employee.department === "Technology" && employee.salary > 90000`

C++ uses the corresponding `&&` operator.

---

## FILTER and empty results

A filter may produce no matching rows.

For example:

`=FILTER(A2:D100,D2:D100="East","No matching records")`

provides a controlled fallback.

This is important in production workbooks because a condition that matches nothing is not necessarily a data error.

The workbook should define what an empty result means.

Possible treatments include:

- displaying a message
- returning a blank
- returning zero
- returning a controlled error
- displaying an alternative calculation

The Python, JavaScript, and C++ implementations all demonstrate an empty-result case.

---

## SORT

### Purpose

`SORT` returns an array in a specified order.

General syntax:

`=SORT(array, [sort_index], [sort_order], [by_col])`

A common example is:

`=SORT(A2:D100,4,-1)`

where the fourth column is sorted in descending order.

Ascending order uses `1`.

Descending order uses `-1`.

The original data does not need to be manually rearranged.

### Sorting records

Suppose employee records contain:

- employee name
- department
- salary
- performance

A report can sort the records by performance.

A second sorting criterion can resolve ties.

For example, the conceptual ordering can be:

1. performance descending
2. department ascending
3. name ascending

The Python implementation uses a tuple of sorting keys.

The JavaScript implementation uses a comparator function.

The C++ implementation uses `std::sort` through a reusable sorting helper.

---

## Multiple sorting criteria

A related function, `SORTBY`, is useful when the sorting criteria come from separate ranges.

Conceptually:

`=SORTBY(A2:D100,D2:D100,-1,C2:C100,1)`

means:

- sort by column D descending
- use column C ascending to resolve ties

This approach is often clearer when the sort criteria are calculated separately from the returned array.

Multi-key sorting is especially useful in:

- sales reports
- employee reports
- financial statements
- inventory analysis
- customer rankings
- operational dashboards

---

## UNIQUE

### Purpose

`UNIQUE` returns distinct values.

General syntax:

`=UNIQUE(array, [by_col], [exactly_once])`

A simple example is:

`=UNIQUE(B2:B100)`

If the source contains:

`North`

`West`

`North`

`South`

`West`

the result is:

`North`

`West`

`South`

The order depends on the source order unless the result is subsequently sorted.

### UNIQUE and exactly_once

The third argument changes the behavior.

`=UNIQUE(B2:B100,,TRUE)`

returns only values that appear exactly once.

For example:

`A`

`B`

`A`

`C`

`D`

`D`

produces:

`B`

`C`

The Python implementation uses `Counter` for the exactly-once calculation.

The JavaScript implementation uses `Map`.

The C++ implementation uses `unordered_map`.

---

## FILTER, UNIQUE, and SORT together

Dynamic-array functions become especially powerful when composed.

A formula such as:

`=SORT(UNIQUE(FILTER(B2:B100,C2:C100="Technology")))`

can be interpreted from the inside outward.

First:

`FILTER(...)`

selects the relevant records.

Then:

`UNIQUE(...)`

removes duplicates.

Finally:

`SORT(...)`

orders the remaining values.

This is a spreadsheet equivalent of a data-processing pipeline.

The same structure appears in all three implementations.

Python performs the operations sequentially.

JavaScript uses array methods.

C++ uses reusable algorithms and vectors.

---

## LET

### Purpose

`LET` assigns names to intermediate calculations.

General syntax:

`=LET(name1,value1,calculation)`

A complex formula might conceptually be written as:

`=LET(revenue,B2:B100,cost,C2:C100,profit,revenue-cost,FILTER(profit,profit>0))`

The intermediate arrays are named:

- `revenue`
- `cost`
- `profit`

The final calculation can then refer to those names.

### Why LET matters

LET improves formulas in several ways.

#### Readability

Meaningful names can make a long formula easier to understand.

Instead of repeating a large expression several times, the expression can receive a name.

#### Maintainability

If a calculation changes, the named expression can be updated in one location.

#### Performance

When an expensive expression would otherwise be repeated, LET can allow the expression to be calculated once and reused.

The actual performance improvement depends on the calculation engine and expression.

### Python equivalent

Python does not need a special LET keyword because ordinary variable assignment provides this capability.

For example:

`profit = revenue - cost`

creates a named intermediate result.

The Python script deliberately uses named intermediate variables to model this pattern.

### JavaScript equivalent

JavaScript uses `const` and `let` bindings.

The implementation demonstrates:

- source arrays
- calculated arrays
- filtered arrays
- derived values

The variables make the pipeline explicit.

### C++ equivalent

C++ local variables provide the same structural idea.

The `calculateSale()` function calculates:

- revenue
- cost
- profit
- margin

once and stores the results in a `CalculatedSale` object.

---

## LAMBDA

### Purpose

`LAMBDA` allows reusable custom functions inside Excel.

General structure:

`=LAMBDA(parameter1,parameter2,calculation)`

A reusable tax function could conceptually be:

`=LAMBDA(price,rate,price*(1+rate))`

Once stored under a suitable name, it can be reused in many formulas.

### Why LAMBDA matters

LAMBDA is useful when the same business rule occurs repeatedly.

Examples include:

- tax calculations
- discount calculations
- margin calculations
- custom scoring rules
- normalization
- validation
- financial calculations
- domain-specific transformations

Instead of copying a long expression into many cells, the logic can be encapsulated.

---

## LAMBDA and programming languages

Python, JavaScript, and C++ already support functions as reusable computational objects.

### Python

Python functions can be stored in variables and passed as arguments.

The Python implementation uses:

`Callable`

and function values to model reusable LAMBDA-style logic.

### JavaScript

JavaScript functions are first-class values.

Arrow functions such as:

`price => price * 1.18`

can be assigned to variables, passed to array methods, and returned by other functions.

### C++

C++ provides lambda expressions and `std::function`.

The C++ case study uses:

`function<optional<double>(double,double)>`

for a reusable margin calculation.

This is particularly useful because the function can be passed into another calculation function.

---

## LAMBDA and recursion

Excel LAMBDA functions can participate in recursive designs when the named function calls itself.

Recursion can be useful for hierarchical problems, but it introduces risks.

Potential issues include:

- excessive calculation depth
- difficult debugging
- poor performance
- accidental nontermination
- difficult maintenance

The Python implementation demonstrates recursion with factorial calculation.

The example is deliberately simple because recursive spreadsheet formulas should be used only when the structure of the problem justifies them.

---

## Dynamic-array composition as a pipeline

A modern Excel analytical formula can be viewed as a pipeline.

A typical architecture is:

`source data`

then:

`FILTER`

then:

`calculated fields`

then:

`UNIQUE`

then:

`SORT`

The `LET` function can name intermediate results.

`LAMBDA` can encapsulate reusable business rules.

This makes modern Excel increasingly similar to a functional data-processing environment.

The underlying principles are:

- transformation
- selection
- deduplication
- ordering
- composition
- reuse
- controlled intermediate state

---

# Python implementation

The Python program is designed as an educational computational model.

It includes:

- arrays
- sequence generation
- filtering
- Boolean conditions
- sorting
- unique-value extraction
- exactly-once uniqueness
- LET-style intermediate variables
- reusable LAMBDA-style functions
- recursive functions
- spill-range simulation
- validation
- error handling
- statistical analysis
- testing
- performance discussion
- an integrated sales analysis

The `Employee` and `Sale` data classes provide structured records instead of unstructured dictionaries.

The `filter_rows()` function demonstrates predicate-based filtering.

The `excel_sort()` function provides a generic sorting abstraction.

The `excel_unique()` function preserves first-occurrence order while removing duplicates.

The `LambdaLibrary` class models the idea of maintaining named reusable functions.

The integrated sales analysis demonstrates how several operations can be composed into a complete analytical workflow.

---

# JavaScript implementation

JavaScript provides a particularly natural environment for demonstrating array operations.

The implementation uses:

- `Array.prototype.filter()`
- `map()`
- `sort()`
- `Set`
- `Map`
- arrow functions
- classes
- promises
- `async` and `await`
- validation
- error handling

JavaScript's `filter()` is directly related to the conceptual behavior of Excel `FILTER`.

JavaScript's `Set` provides an efficient representation for simple distinct-value operations and therefore models `UNIQUE`.

JavaScript's array sorting requires special attention because `sort()` mutates the source array. The implementation copies the array before sorting when preservation of the original data matters.

The `LambdaLibrary` class demonstrates how reusable functions can be registered and invoked by name.

The asynchronous example demonstrates an application-level scenario in which data arrives before the analytical pipeline is executed.

---

# C++ case study

## Problem being solved

The C++ program models a sales-analysis system for a company that needs to analyze transactions by region and product.

Each transaction contains:

- transaction ID
- product
- region
- units
- unit price
- cost per unit

The system must answer questions such as:

- Which records belong to a particular region?
- Which products appear in that region?
- Which transactions are profitable?
- What are the total units and revenue by product?
- What is the profit margin?
- How should products be ordered by profit?
- What should happen when no records match?
- How should invalid data be rejected?

These requirements map naturally to dynamic-array concepts.

---

## C++ architecture

The program is organized into several layers.

### Data model

The `Sale` structure represents one transaction.

It provides methods for:

- revenue
- cost
- profit
- margin

This keeps domain calculations close to the data they describe.

### FILTER layer

The generic `filter()` function accepts a vector and a predicate.

This provides a reusable selection mechanism.

### UNIQUE layer

`uniqueStrings()` uses `unordered_set` to preserve first occurrence while removing duplicate strings.

`uniqueExactlyOnce()` uses a frequency map to identify values that occur once.

### SORT layer

`sortedCopy()` creates a copy and sorts it with a supplied comparator.

This avoids unintentionally changing the original source vector.

### LET-style calculation layer

`calculateSale()` creates named intermediate calculations for:

- revenue
- cost
- profit
- margin

The resulting `CalculatedSale` object stores the derived values.

### Aggregation layer

`sumarizeProducts()` groups transactions by product.

A second implementation, `fastProductAggregation()`, uses `unordered_map` to improve the aggregation algorithm.

### Validation layer

The program validates:

- transaction IDs
- product names
- region names
- unit counts
- numerical values
- duplicate transaction IDs

### Testing layer

The program contains built-in assertions for:

- SEQUENCE
- FILTER
- UNIQUE
- SORT
- LAMBDA-style calculations

---

## Integrated C++ workflow

The main analytical pipeline is:

`source transactions`

→ `FILTER by region`

→ `calculate revenue, cost, profit, margin`

→ `FILTER by minimum profit`

→ `UNIQUE products`

→ `aggregate products`

→ `SORT by profit`

This is conceptually similar to a complex Excel formula using `LET`, `FILTER`, `UNIQUE`, and `SORT`.

The C++ implementation makes each stage explicit.

That is useful for understanding what a spreadsheet formula is doing computationally even when the Excel formula itself is compact.

---

# Comparing the three implementations

| Concept | Excel | Python | JavaScript | C++ |
|---|---|---|---|---|
| Dynamic array | Spill range | List | Array | `vector` |
| SEQUENCE | `SEQUENCE()` | `sequence()` | `sequence()` | `sequence()` |
| FILTER | `FILTER()` | `excel_filter()` | `filter()` / `excelFilter()` | `filter()` |
| SORT | `SORT()` | `sorted()` | `sort()` | `std::sort()` |
| UNIQUE | `UNIQUE()` | Set-based logic | `Set` | `unordered_set` |
| LET | Named formula variables | Local variables | `const` / `let` | Local variables |
| LAMBDA | `LAMBDA()` | Functions / callables | Functions / closures | Lambda expressions / `std::function` |
| Empty result | Optional `if_empty` | Explicit result handling | Explicit fallback | Empty vector handling |
| Validation | Formula logic | Exceptions | Exceptions | Exceptions |
| Testing | Workbook testing | Assertions | Custom assertions | `require()` |
| Sorting complexity | Engine-dependent | Typically `O(n log n)` | Typically `O(n log n)` | `O(n log n)` |

The implementations are not Excel engines. They model the underlying computational ideas.

---

# Important distinctions

## FILTER versus SORT

`FILTER` selects records.

`SORT` changes their ordering.

Filtering answers:

> Which records should remain?

Sorting answers:

> In what order should the remaining records appear?

They can therefore be composed.

---

## UNIQUE versus SORT

`UNIQUE` removes repeated values.

`SORT` orders values.

For a clean categorical list, the common composition is:

`=SORT(UNIQUE(A2:A100))`

The order of operations can matter.

For simple distinct-value extraction followed by ordering, both operations are conceptually independent, but the final output depends on their composition.

---

## FILTER versus UNIQUE

`FILTER` can reduce the source population before `UNIQUE` operates.

For example:

`=UNIQUE(FILTER(B2:B100,C2:C100="Technology"))`

first restricts the population to Technology records and then obtains distinct values.

This is different from obtaining unique values from the entire source and filtering those values afterward.

---

## LET versus LAMBDA

`LET` names intermediate values inside one formula.

`LAMBDA` defines reusable function logic.

A useful distinction is:

`LET = name calculations`

`LAMBDA = name behavior`

They can also work together.

A LAMBDA can encapsulate business logic while LET can organize intermediate calculations inside that function.

---

# Edge cases

Dynamic-array formulas should be tested against more than ordinary successful input.

Important cases include:

### Empty source

The source range contains no meaningful records.

### No FILTER matches

The condition is valid, but no record satisfies it.

### Duplicate values

The source contains repeated categories or identifiers.

### Exactly-once values

Some values occur once while others occur repeatedly.

### Blank values

Blank cells can interact with comparisons and calculations differently from explicit zero values.

### Zero

A zero denominator can cause division-by-zero errors.

### Negative values

Negative revenue, cost, quantities, or financial metrics may require business-specific handling.

### Mixed data types

Text and numeric values should not be assumed to behave identically.

### Mismatched ranges

FILTER conditions must align with the filtered array dimensions.

### Spill blockage

A dynamic-array result cannot overwrite an occupied destination cell.

### Source errors

Errors in source cells can propagate through dependent formulas.

### Recursive LAMBDA

A recursive custom function requires a terminating condition.

---

# Common mistakes

## Repeating expensive expressions

A long expression may be repeated several times inside one formula.

`LET` can make the formula easier to read and may reduce repeated calculation.

## Using excessively large ranges

Entire-column references can increase the amount of data that must be processed.

Where appropriate, structured tables or bounded ranges can provide better control.

## Ignoring empty FILTER results

A filter that returns nothing should be deliberately handled.

## Blocking spill ranges

Manually entering values inside an expected spill region can cause `#SPILL!`.

## Overusing nested formulas

Deeply nested formulas can become difficult to debug.

A combination of `LET`, named LAMBDAs, helper calculations, and structured source data can improve maintainability.

## Assuming UNIQUE always sorts

`UNIQUE` and `SORT` solve different problems.

If sorted unique values are required, use both operations.

## Forgetting that LAMBDA is executable logic

A LAMBDA containing an incorrect business rule can consistently produce incorrect results.

Reusable logic should therefore be tested just like ordinary software functions.

## Ignoring data quality

Dynamic-array formulas do not automatically make source data correct.

Incorrect source values can produce technically correct calculations with incorrect business meaning.

---

# Performance considerations

The computational model of the major operations is approximately:

| Operation | Typical conceptual complexity |
|---|---:|
| SEQUENCE | `O(n)` |
| FILTER | `O(n)` |
| UNIQUE with hashing | Approximately `O(n)` average |
| SORT | `O(n log n)` |
| LET | Depends on contained calculations |
| LAMBDA | Depends on its body and number of calls |

The actual Excel calculation engine has additional behavior involving dependency tracking, recalculation, volatile functions, workbook structure, memory, and formula dependencies.

## FILTER

Filtering normally requires examining each candidate record.

For `n` records, a simple filter is approximately `O(n)`.

## UNIQUE

A hash-based uniqueness operation can approach linear average-case behavior.

The Python and C++ examples use hash-based structures for this reason.

## SORT

Sorting generally requires approximately `O(n log n)` comparisons.

Sorting a very large dynamic result can therefore become more expensive than filtering it.

## LET

LET can be useful when an expensive expression is reused.

For example, if a calculation is needed several times, assigning it once may avoid repeated work and makes the formula easier to understand.

## LAMBDA

LAMBDA itself is not automatically slow or fast.

Performance depends on:

- number of invocations
- complexity of the function body
- size of the arrays being processed
- recursive depth
- other functions called by the LAMBDA

---

# Security and reliability considerations

These Excel functions are primarily calculation features rather than security mechanisms.

Important reliability practices include:

- validate imported data
- control who can edit critical formulas
- protect sensitive worksheets where appropriate
- separate raw data from analytical calculations
- avoid hidden assumptions
- document business rules
- test formulas against abnormal data
- control external data connections
- avoid using untrusted workbook content as if it were validated business data

A formula can be mathematically correct while still producing a poor business result if its assumptions are incorrect.

---

# Implementation considerations

## Excel

Excel provides the actual dynamic-array calculation engine.

Important workbook design decisions include:

- source table structure
- spill location
- formula dependencies
- named functions
- error handling
- workbook protection
- refresh behavior
- calculation mode

## Python

Python is useful for demonstrating the underlying algorithms explicitly.

The code makes the stages visible:

`filter`

then:

`unique`

then:

`sort`

This is valuable when learning how a spreadsheet calculation can be represented algorithmically.

## JavaScript

JavaScript is particularly useful when spreadsheet-style calculations become part of a web application.

Its array methods and first-class functions map naturally to:

- FILTER
- SORT
- UNIQUE
- LAMBDA-style behavior

It also demonstrates asynchronous processing, which is common when application data is retrieved from APIs or services.

## C++

C++ makes memory, types, algorithms, and complexity more explicit.

The case study demonstrates how the same analytical model could become part of a high-performance application.

The use of `unordered_map` for aggregation demonstrates an important optimization: instead of repeatedly scanning all source records for every unique product, a hash map can aggregate each record during a single pass.

---

# Practical applications

Dynamic arrays and the functions covered here can support many real-world spreadsheet tasks.

## Sales analysis

Examples include:

- filtering transactions by region
- extracting unique products
- sorting products by revenue
- identifying profitable transactions
- building dynamic sales reports

## Financial analysis

Possible uses include:

- filtering investments
- sorting securities by return
- generating periods with SEQUENCE
- creating reusable financial LAMBDAs
- calculating margins and ratios

## Human resources

Examples include:

- filtering employees by department
- extracting unique locations
- sorting performance records
- creating reusable scoring rules

## Operations

Dynamic arrays can support:

- inventory analysis
- exception reports
- order tracking
- supplier lists
- regional operations reports

## Data preparation

The combination of:

`FILTER`

`UNIQUE`

`SORT`

can provide a lightweight transformation pipeline before data is consumed by another report or analysis.

---

# Formula patterns

## Generate numbers

`=SEQUENCE(10)`

## Generate a matrix

`=SEQUENCE(5,3,1,1)`

## Filter records

`=FILTER(A2:D100,D2:D100="East","No results")`

## Sort records

`=SORT(A2:D100,4,-1)`

## Unique values

`=UNIQUE(B2:B100)`

## Unique values that occur exactly once

`=UNIQUE(B2:B100,,TRUE)`

## Filter and sort

`=SORT(FILTER(A2:D100,D2:D100="East"))`

## Filter, unique, and sort

`=SORT(UNIQUE(FILTER(B2:B100,D2:D100="East")))`

## LET

`=LET(revenue,B2:B100,cost,C2:C100,profit,revenue-cost,FILTER(profit,profit>0))`

## LAMBDA

`=LAMBDA(price,rate,price*(1+rate))`

These examples demonstrate the structural patterns implemented in the three programs.

---

# Design principles

A maintainable dynamic-array workbook should generally follow these principles:

- Keep source data organized.
- Prefer structured tables for changing datasets.
- Use clear field names.
- Separate raw data from calculations.
- Use FILTER for selection.
- Use UNIQUE for distinct-value extraction.
- Use SORT for ordering.
- Use LET to name complex intermediate calculations.
- Use LAMBDA for genuinely reusable logic.
- Handle empty results deliberately.
- Keep spill regions free of conflicting content.
- Test formulas with duplicate, missing, zero, negative, and unexpected values.
- Avoid unnecessarily large calculation ranges.
- Document important business assumptions.
- Keep complex formulas understandable enough to audit.

---

# Testing approach

The Python implementation contains tests for:

- SEQUENCE
- FILTER
- UNIQUE
- SORT
- LAMBDA-style calculations

The JavaScript implementation contains equivalent assertions.

The C++ program uses a `require()` function to test core operations and throws an exception when a test fails.

Testing is important because reusable calculations can affect many outputs.

A single incorrect LAMBDA or shared formula can therefore create errors across an entire report.

---

# Relationship between spreadsheet formulas and programming

The three implementations demonstrate a broader relationship between spreadsheets and programming.

A spreadsheet formula can often be interpreted as a small program.

For example:

`=SORT(UNIQUE(FILTER(A2:A100,B2:B100="West")))`

can be viewed as:

1. read the source array
2. select rows satisfying a condition
3. remove duplicates
4. sort the result
5. return the resulting array

`LET` gives names to intermediate results.

`LAMBDA` packages reusable behavior.

This perspective makes complex Excel formulas easier to reason about because each function can be understood as one transformation in a data-processing pipeline.

---

# Repository structure

The three primary implementations are conceptually organized as:

`advanced_excel_dynamic_arrays.py`

Python study implementation covering the fundamentals through advanced examples.

`advanced_excel_dynamic_arrays.js`

JavaScript implementation using arrays, functions, objects, and application-style processing.

`advanced_excel_dynamic_arrays.cpp`

C++17 industry-style sales-analysis case study.

`README.md`

This document.

---

# Running the implementations

## Python

The Python program uses only the standard library.

Run it with:

`python advanced_excel_dynamic_arrays.py`

The program prints educational explanations, examples, edge cases, calculations, and test results.

## JavaScript

The JavaScript file uses standard JavaScript features and does not require third-party packages.

Run it with:

`node advanced_excel_dynamic_arrays.js`

The asynchronous section demonstrates how a JavaScript application can process retrieved data before applying the analytical pipeline.

## C++

The C++ program requires a compiler supporting C++17 or later.

A typical compilation command is:

`g++ -std=c++17 -O2 advanced_excel_dynamic_arrays.cpp -o advanced_excel_dynamic_arrays`

Run the resulting executable normally.

The program validates the dataset, performs the sales analysis, demonstrates dynamic-array concepts, and runs its tests.

---

# Technical vocabulary

| Term | Meaning |
|---|---|
| Array | An ordered collection of values |
| Dynamic array | An array whose size can change as its formula result changes |
| Spill | Automatic placement of a dynamic-array result into neighboring cells |
| Spill range | The cells occupied by a dynamic-array result |
| Boolean mask | A collection of true/false values used to select records |
| Predicate | A condition that evaluates whether an item should be selected |
| FILTER | Selects records satisfying a condition |
| SORT | Orders an array |
| UNIQUE | Removes duplicate values |
| SEQUENCE | Generates a numeric array |
| LET | Assigns names to intermediate calculations |
| LAMBDA | Defines reusable custom calculation logic |
| Composition | Combining functions so the output of one becomes the input of another |
| Aggregation | Combining multiple records into totals or other grouped statistics |
| Recursion | A function calling itself |
| Hashing | A technique used for efficient lookup and uniqueness operations |
| Complexity | A measure of how computational work grows as input size increases |

---

# Core conceptual model

The functions can be understood as different stages of data processing:

`SEQUENCE`

creates data.

`FILTER`

selects data.

`UNIQUE`

deduplicates data.

`SORT`

orders data.

`LET`

names intermediate calculations.

`LAMBDA`

encapsulates reusable behavior.

Dynamic arrays provide the mechanism through which the results of these operations can become variable-sized worksheet outputs.

The combination is particularly powerful because the functions are composable. A single formula can represent an entire analytical pipeline while retaining a direct relationship with the source data.
