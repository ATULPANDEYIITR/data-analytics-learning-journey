# Pandas Fundamentals

This artifact set develops the core Pandas data model through a common employee-analysis scenario. The central concepts are `Series`, `DataFrame`, indexing, column selection, and row filtering. The five implementations use different programming models so that the underlying tabular operations can be understood independently of one language.

## Conceptual Model

Pandas represents structured tabular data primarily through two objects:

| Object | Structure | Typical use |
|---|---|---|
| `Series` | One-dimensional labeled values | A single measurement or column |
| `DataFrame` | Two-dimensional labeled table | Multiple related columns and rows |

A useful conceptual relationship is:

`Series → columns → DataFrame → indexed rows and columns`

A `DataFrame` can be viewed as a collection of aligned `Series` objects that share a row index.

For example, employee data can contain:

| employee | department | salary | performance | active |
|---|---|---:|---:|---|
| Asha | Engineering | 95000 | 4.5 | true |
| Ravi | Sales | 72000 | 3.8 | true |
| Meera | Engineering | 105000 | 4.8 | true |
| John | Sales | 68000 | 3.2 | false |
| Fatima | Finance | 88000 | 4.1 | true |

The important operation is not merely storing this table. Pandas makes it possible to select columns, select rows, construct boolean masks, transform columns, group records, and preserve meaningful indexes.

## Series

The Python implementation begins with a `Series` representing regional sales. A `Series` contains values and an associated index.

The index allows label-based access:

`series.loc["South"]`

while positional access uses:

`series.iloc[1]`

These are different concepts. Label-based selection identifies a value through its index label, while positional selection identifies it by its physical position.

A `Series` can contain numeric, textual, Boolean, datetime, or other compatible data. Its name also provides useful metadata when the series represents a particular field.

## DataFrame Construction

The Python program creates a `DataFrame` from a dictionary of columns. Each dictionary key becomes a column name and each value sequence becomes column data.

Before analytical operations, the program validates:

- required columns
- non-negative salaries
- performance values within the expected `0` to `5` range
- non-empty input

This illustrates an important practical distinction: Pandas performs data manipulation, but application-level validation still has to define what constitutes valid business data.

## Column Selection

Selecting one column:

`df["salary"]`

returns a `Series`.

Selecting several columns:

`df[["employee", "salary", "department"]]`

returns another `DataFrame`.

This distinction is significant because subsequent operations depend on whether the result is one-dimensional or two-dimensional.

The examples deliberately use explicit column names rather than relying on positional assumptions. This makes transformations more robust when the original column order changes.

## Row Selection and Indexing

Pandas provides several indexing mechanisms.

`iloc` is positional:

`df.iloc[:3]`

selects the first three rows.

`loc` is label-oriented:

`df.loc[1:3, ["employee", "salary"]]`

selects rows and columns through their labels.

The Python implementation also changes the employee column into an index using `set_index("employee")`. This demonstrates why an index is more than a display feature. It provides a label-based addressing mechanism for records.

`reset_index()` converts index information back into a normal column.

Index design matters when data is repeatedly accessed by a stable identifier. It also matters when joining, aligning, resampling, or performing time-series operations.

## Filtering Rows

Boolean filtering is one of the most important Pandas operations.

The Python implementation uses conditions such as:

`df[df["performance"] >= 4.0]`

and:

`df[(df["active"]) & (df["salary"] >= 90000)]`

Each comparison produces a Boolean `Series`. Pandas then uses that Boolean mask to retain matching rows.

For multiple conditions, Pandas requires element-wise Boolean operators such as `&` and `|`. Python's scalar `and` and `or` operators should not be used for element-wise Series filtering.

Membership filtering uses `isin`, as in:

`df["department"].isin(["Engineering", "Finance"])`

This is preferable to constructing a long chain of equality comparisons.

## Query-Based Filtering

The Python implementation also uses `DataFrame.query()` for a readable compound condition:

`active == True and salary >= 80000 and performance >= 4`

`query()` can make complex filtering easier to read. For dynamically supplied expressions, input should be handled carefully. External values should not be treated as trusted executable expressions merely because they are being used for data filtering.

## Derived Columns

The employee examples calculate:

`bonus = salary × performance / 100`

and:

`total_compensation = salary + bonus`

Pandas performs these operations vectorially across the entire column. This is generally preferable to explicitly iterating through every row with Python-level loops.

Vectorization is one of the major reasons Pandas is useful for analytical workloads. The expression describes the operation on the column rather than manually controlling every row.

## Missing Values

The Python implementation creates a separate table containing missing salary and performance values.

`isna()` identifies missing entries.

`fillna()` provides controlled replacement.

The example fills a missing salary with the median salary and a missing performance value with zero. Those choices are demonstration policies, not universal statistical rules.

Real datasets require domain-specific decisions about whether missing values should be:

- removed
- imputed
- represented explicitly
- propagated as missing
- rejected during validation

Blindly filling every missing value can introduce analytical bias.

## Grouping and Aggregation

The Python program groups employees by department and calculates:

- employee count
- average salary
- average performance
- total compensation

The operation:

`df.groupby("department")`

creates grouped views of the records. Aggregation then computes statistics for each group.

The SQL implementation represents the same analytical concept with `GROUP BY`. The JavaScript and C++ implementations construct their own grouping logic rather than pretending that native JavaScript or C++ collections are Pandas objects.

## Python Implementation

The Python file is the most direct Pandas implementation.

It includes:

- `Series` construction
- `DataFrame` construction
- validation
- label-based indexing
- positional indexing
- single-column selection
- multi-column selection
- Boolean row filtering
- membership filtering
- derived columns
- missing-value handling
- grouping and aggregation
- sorting
- CSV round-tripping
- `query()` filtering
- exception handling

The CSV round-trip demonstrates a realistic boundary between external data and an in-memory DataFrame. The imported schema is checked after loading rather than assuming that the file is correct.

The temporary directory keeps the demonstration self-contained and avoids leaving generated files in the working directory.

## JavaScript Implementation

The JavaScript implementation does not attempt to reproduce Pandas syntax. It builds a small event-compatible tabular abstraction using native arrays, objects, `Map`, classes, and asynchronous execution.

`Series` represents one-dimensional values and supports:

- indexed access
- mapping
- filtering
- numeric mean calculation

`DataFrame` supports:

- column projection
- row filtering
- derived columns
- sorting
- grouping

The design emphasizes a key conceptual distinction. Pandas provides optimized, specialized data structures, while native JavaScript requires explicit representation of rows and columns.

The `processData()` function is asynchronous and uses a rejected promise as the error boundary for processing failures.

## C++ Implementation

The C++ program models employee records with a strongly typed `Employee` structure and stores them in a `std::vector`.

The `EmployeeTable` class provides:

- insertion with validation
- predicate-based filtering
- grouped salary aggregation
- salary sorting
- immutable access to stored data through a const reference

The implementation uses `std::map` for department aggregation. This gives ordered keys and logarithmic key lookup while the original rows remain contiguous in a vector.

The design intentionally differs from the Python implementation. C++ requires explicit type decisions and gives direct control over the data structures used for storage and aggregation.

For `n` employees:

- filtering is `O(n)`
- aggregation with ordered `std::map` is approximately `O(n log k)`, where `k` is the number of departments
- sorting is `O(n log n)`

## Java Implementation

The Java program treats employee information as a domain model.

The `Employee` record provides immutable row data and validates its fields when constructed. `Department` is an enum, preventing arbitrary department strings from entering the domain model.

The `EmployeeTable` provides:

- filtering through a policy interface
- sorting through Java comparators
- grouping and averaging through streams
- immutable snapshots of the underlying employee list

The record's `bonus()` and `totalCompensation()` methods represent derived domain behavior rather than exposing calculations as unstructured expressions.

This is useful when tabular data eventually becomes part of a larger enterprise application. Data validation and business behavior can be placed closer to the domain model instead of treating every row as an unvalidated dictionary.

## PostgreSQL Representation

The SQL implementation represents the same concepts relationally.

The `employees` table uses:

- a generated primary key
- typed columns
- `NOT NULL` constraints
- salary validation
- performance-range validation
- Boolean state
- hiring date

Column selection is represented through `SELECT`.

Row filtering is represented through `WHERE`.

Derived columns use expressions.

Grouped analysis uses `GROUP BY`.

Multi-stage transformations use common table expressions.

The analytical view `active_employee_analysis` provides a reusable projection containing only active employees and calculated bonus information.

PostgreSQL constraints demonstrate an important production principle: validation should not exist only in application code when the database can enforce fundamental integrity rules.

## Relationship Between the Implementations

The same conceptual operation appears differently in each environment:

| Analytical operation | Python/Pandas | JavaScript | C++ | Java | PostgreSQL |
|---|---|---|---|---|---|
| One-dimensional values | `Series` | `Series` class | `vector` | `List` | column |
| Table | `DataFrame` | `DataFrame` class | `EmployeeTable` | `EmployeeTable` | table |
| Select columns | column indexing | `select()` | field access | stream mapping | `SELECT` |
| Filter rows | Boolean mask | `filter()` | predicate | stream `filter()` | `WHERE` |
| Derived values | vectorized expression | `assign()` | member/function calculation | record methods | SQL expression |
| Grouping | `groupby()` | `Map` | `std::map` | `groupingBy()` | `GROUP BY` |
| Sorting | `sort_values()` | `sortBy()` | `std::sort` | stream sorting | `ORDER BY` |
| Validation | explicit checks | constructor checks | validation function | record constructor | constraints |

The implementations therefore teach the underlying tabular concepts without assuming that every language has the same data model.

## Practical Considerations

Pandas is optimized for analytical manipulation, but it is not a substitute for a relational database or a validation system.

For moderate in-memory datasets, vectorized DataFrame operations are usually concise and efficient. Very large datasets can exceed available memory, making database-side aggregation, chunked processing, distributed systems, or other storage strategies more appropriate.

Repeated row-by-row Python loops can be significantly slower than vectorized Pandas operations. The preferred pattern is to express operations over entire columns or groups when the operation can be vectorized.

External files should not be treated as trusted data. Schema validation, type validation, range checks, missing-value analysis, and appropriate error handling should occur before important calculations are performed.

Indexes also have a cost. They can make label-based access and certain operations more convenient, but they consume memory and should be chosen according to actual access patterns.

## Edge Cases

Several failure conditions are represented directly in the implementations:

- empty datasets
- missing columns
- invalid salary values
- performance values outside the valid range
- missing values
- invalid positional access
- unknown column selection
- invalid grouping fields
- failed database constraints
- malformed domain records

These cases matter because tabular operations often appear simple until real data violates the assumptions behind the analysis.

The central workflow can be expressed as:

`External data → validation → Series/DataFrame → selection → filtering → transformation → aggregation → validated result`

That workflow is the foundation for reliable Pandas-based data analysis.
