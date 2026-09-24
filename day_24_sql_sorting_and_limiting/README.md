# SQL Sorting & Limiting

## Topic scope

This study covers the SQL mechanisms used to control the order and size of query results:

- `ORDER BY`
- `ASC`
- `DESC`
- multiple sort keys
- deterministic ordering
- unique tie-breakers
- `LIMIT`
- `OFFSET`
- pagination
- `NULL` ordering
- expression-based ordering
- conditional ordering
- top-N queries
- top-N per group
- keyset pagination
- dynamic sorting
- SQL injection considerations
- indexes and query performance
- SQL dialect differences
- application-level validation

The three implementations approach the topic from different perspectives:

- Python executes real SQL using SQLite.
- JavaScript models SQL-style ordering and pagination at the application level and constructs database-oriented SQL safely.
- C++ develops an industry-style employee-directory query service with explicit sorting, pagination, validation, security controls, keyset pagination, and performance measurements.

---

## Introduction

SQL queries frequently return more rows than an application needs. A database may contain millions of records, while a user interface may need only the ten highest-value records or the next twenty records in a paginated table.

Two separate problems must therefore be addressed:

1. Which rows should appear first?
2. How many rows should be returned, and where should the requested page begin?

`ORDER BY` addresses the first problem. `LIMIT` and `OFFSET` commonly address the second.

A query such as `ORDER BY salary DESC LIMIT 5` means that the result should be ordered by salary from highest to lowest and that at most five rows should be returned.

The distinction between ordering and limiting is important. `LIMIT` does not itself determine which rows qualify as the "top" rows. Without an appropriate `ORDER BY`, the query does not define a meaningful top-N result.

---

## Fundamental concepts

### `ORDER BY`

`ORDER BY` specifies the ordering of rows in a query result.

A basic form is:

`ORDER BY column_name`

The direction defaults to ascending in commonly used SQL systems.

An explicit ascending clause is:

`ORDER BY column_name ASC`

A descending clause is:

`ORDER BY column_name DESC`

For numerical values:

- ascending means smaller values appear first
- descending means larger values appear first

For text values, ordering follows the database's collation rules.

For dates represented by properly formatted date values or ISO-style date strings, chronological ordering can often be expressed with `ORDER BY date_column`.

---

## `ASC`

`ASC` means ascending.

Example:

`ORDER BY salary ASC`

If the salaries are:

`70000, 95000, 120000`

ascending order produces:

`70000, 95000, 120000`

Because ascending is normally the default, these two expressions have the same intended ordering:

`ORDER BY salary`

`ORDER BY salary ASC`

Explicit `ASC` can still improve readability because it documents the intended direction.

---

## `DESC`

`DESC` means descending.

Example:

`ORDER BY salary DESC`

The same values:

`70000, 95000, 120000`

become:

`120000, 95000, 70000`

Descending order is common for:

- highest salaries
- highest scores
- largest transactions
- newest dates
- most recent events
- highest revenue
- largest balances

---

## Multiple sort keys

SQL permits multiple expressions in `ORDER BY`.

Example:

`ORDER BY department ASC, salary DESC`

The database first sorts by `department`.

If two rows belong to the same department, their salaries determine their relative order.

A useful way to understand this is as a hierarchy:

1. primary ordering key
2. secondary ordering key
3. tertiary ordering key
4. additional tie-breakers

The Python implementation demonstrates this directly with queries that order employees by department and then salary.

The JavaScript and C++ implementations model the same hierarchy using arrays of sort specifications.

---

## Deterministic ordering

Deterministic ordering is one of the most important concepts in this topic.

Consider:

`ORDER BY salary DESC`

Suppose two employees have a salary of `125000`.

The query specifies that both employees belong at the same salary position, but it does not specify which employee must appear first among those two tied rows.

A database may return them in an order that appears stable during testing. That apparent stability should not be treated as a logical guarantee unless the query fully specifies the required ordering.

This becomes particularly important when using:

`ORDER BY salary DESC LIMIT 5`

or:

`ORDER BY salary DESC LIMIT 5 OFFSET 5`

If ties occur around a page boundary, an unspecified tie order can make pagination difficult to reason about.

A common solution is to add a unique key:

`ORDER BY salary DESC, employee_id ASC`

If `employee_id` is unique, equal-salary employees receive an explicit relative order.

The general pattern is:

`ORDER BY primary_sort_key DESC, unique_key ASC`

The direction of the unique key should be selected according to the required business ordering.

---

## Why deterministic ordering matters for pagination

Suppose a result contains:

| Employee | Salary |
|---|---:|
| Aarav | 125000 |
| Meera | 125000 |
| Vihaan | 110000 |
| Ishita | 110000 |

A query using only:

`ORDER BY salary DESC`

does not fully describe the relationship between Aarav and Meera or between Vihaan and Ishita.

A deterministic query can use:

`ORDER BY salary DESC, employee_id ASC`

Now every pair of employees can be ordered using the salary and, when necessary, the unique identifier.

This is especially useful when a user moves from page 1 to page 2.

---

## `LIMIT`

`LIMIT` restricts the maximum number of rows returned.

Example:

`LIMIT 5`

A top-five query normally combines `LIMIT` with an explicit order:

`ORDER BY salary DESC, employee_id ASC LIMIT 5`

This means:

1. establish the salary ordering
2. use employee ID to resolve ties
3. return at most five rows

The distinction is important.

`LIMIT 5` by itself means only that five rows may be returned. It does not define which five rows represent the desired top five.

---

## `LIMIT 0`

`LIMIT 0` returns no rows.

This can be useful in situations where an application wants to validate or inspect the shape of a query without retrieving data.

The exact behavior of unusual limit values can vary between database systems. Application-level validation is preferable when a system requires a strict pagination contract.

---

## `OFFSET`

`OFFSET` skips rows before returning the limited portion of the result.

Example:

`LIMIT 5 OFFSET 5`

means:

- skip five rows
- return the next five rows
- return no more than five rows

The ordering must be established first if the skipped rows are supposed to have a meaningful position.

A typical pagination query is:

`ORDER BY salary DESC, employee_id ASC LIMIT 10 OFFSET 20`

This asks for up to ten rows after the first twenty rows in the specified ordering.

---

## Page-number calculation

For one-indexed page numbers:

`OFFSET = (page_number - 1) * page_size`

For page 1 with a page size of 10:

`OFFSET = (1 - 1) * 10 = 0`

For page 2:

`OFFSET = (2 - 1) * 10 = 10`

For page 5:

`OFFSET = (5 - 1) * 10 = 40`

The Python, JavaScript, and C++ implementations all contain application-level pagination calculations.

---

## Offset pagination

Offset pagination is conceptually simple.

For a page size of 5:

`Page 1 = LIMIT 5 OFFSET 0`

`Page 2 = LIMIT 5 OFFSET 5`

`Page 3 = LIMIT 5 OFFSET 10`

`Page 4 = LIMIT 5 OFFSET 15`

This model works well for many ordinary administrative interfaces and datasets where page numbers are useful.

It becomes less attractive when:

- offsets become very large
- the dataset is changing rapidly
- users primarily move sequentially through pages
- the query must operate efficiently on very large datasets

---

## Large `OFFSET` values

An offset of 10 may be inexpensive.

An offset of 1,000,000 can be a different problem.

Depending on the database, indexes, predicates, and execution plan, the database may need to process or locate a substantial number of preceding rows before producing the requested page.

Therefore, reducing output with `LIMIT` does not automatically mean that the database performs only `LIMIT` units of work.

Performance depends on the execution strategy.

---

## Keyset pagination

Keyset pagination, also called seek pagination, uses the values of the last row from the previous page as a continuation cursor.

Suppose the stable order is:

`ORDER BY salary DESC, employee_id ASC`

Suppose the last row of the current page is:

`salary = 105000`

and:

`employee_id = 9`

The next page can be defined conceptually as:

`salary < 105000`

or:

`salary = 105000 AND employee_id > 9`

The full condition is:

`WHERE salary < ? OR (salary = ? AND employee_id > ?)`

followed by:

`ORDER BY salary DESC, employee_id ASC LIMIT ?`

This approach is particularly useful for:

- infinite scrolling
- "load more" interfaces
- event streams
- large tables
- sequential navigation through frequently changing datasets

Keyset pagination is not automatically the best solution for every interface. Direct navigation to an arbitrary page number is naturally expressed with offset pagination, while sequential navigation is a strong use case for keyset pagination.

---

## `NULL` and ordering

`NULL` represents missing or unknown information. It is not the same as zero or an empty string.

Example:

`performance_score` may be `NULL` when an employee has not yet been evaluated.

A query such as:

`ORDER BY performance_score ASC`

can place `NULL` values according to the database's rules.

The exact default position of `NULL` values differs between database systems and between ascending and descending cases.

When the placement of missing values matters to the application, it is safer to express the desired behavior explicitly.

The Python implementation demonstrates an approach using a `CASE` expression:

`CASE WHEN performance_score IS NULL THEN 1 ELSE 0 END`

followed by the actual score ordering.

This creates two logical groups:

- known scores
- missing scores

The final unique key then resolves remaining ties.

---

## Expressions in `ORDER BY`

`ORDER BY` can sort using expressions.

The Python implementation calculates:

`salary * 1.10 AS projected_salary`

and orders by the calculated alias.

This pattern is useful for:

- calculated prices
- projected revenue
- normalized scores
- percentages
- derived business metrics

An expression should remain understandable and maintainable. Extremely complex business logic inside `ORDER BY` can make queries difficult to test and optimize.

---

## Conditional ordering

`CASE` can be used inside `ORDER BY`.

For example, an organization may want:

1. employees with performance scores of 9.0 or higher
2. employees with lower scores
3. employees with missing scores

A conditional expression can assign these groups numeric priorities and then sort within each group.

This technique is useful when business ordering is not identical to simple numerical ascending or descending order.

The rule should be documented because custom priority expressions can become difficult to maintain when they grow too complex.

---

## Top-N queries

A top-N query normally has the structure:

`ORDER BY metric DESC LIMIT N`

For example:

`ORDER BY salary DESC LIMIT 5`

means the five highest salaries.

A bottom-N query normally uses:

`ORDER BY metric ASC LIMIT N`

For example:

`ORDER BY salary ASC LIMIT 5`

means the five lowest salaries.

A deterministic tie-breaker should be added when the identity and relative order of tied rows matter:

`ORDER BY salary DESC, employee_id ASC LIMIT 5`

---

## Top-N per group

A global `LIMIT` applies to the complete result set.

It does not mean "five rows per department."

For example:

`LIMIT 5`

returns at most five rows from the complete query result.

For top-N per group, SQL commonly uses window functions such as `ROW_NUMBER()`.

The Python implementation demonstrates:

`ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC, employee_id ASC)`

The result can then be filtered to positions less than or equal to the required N.

This is an important distinction between:

- top-N globally
- top-N within each group

---

## Python implementation

The Python script uses the standard-library `sqlite3` module, so no external database package is required.

It creates an in-memory SQLite database containing an `employees` table.

The dataset intentionally contains:

- duplicate salaries
- duplicate department values
- missing performance scores
- missing city values
- unique employee IDs
- different hire dates

This makes the dataset suitable for studying deterministic ordering and edge cases.

### Python fundamentals

The script demonstrates:

- `ORDER BY salary ASC`
- `ORDER BY salary DESC`
- multiple sort keys
- `LIMIT`
- `OFFSET`
- pagination calculations
- top-N queries
- bottom-N queries

### Python deterministic ordering

The script compares:

`ORDER BY salary DESC`

with:

`ORDER BY salary DESC, employee_id ASC`

The second version explicitly resolves equal-salary rows.

### Python `NULL` handling

The script uses a `CASE` expression to put missing performance scores after known scores.

### Python keyset pagination

The script demonstrates the cursor condition:

`salary < ? OR (salary = ? AND employee_id > ?)`

with a stable salary/employee-ID ordering.

### Python security example

The script shows an allow-list mapping:

`name -> employee_name`

`salary -> salary`

`score -> performance_score`

`hire_date -> hire_date`

Only approved application names become SQL identifiers.

The `LIMIT` value remains parameterized.

### Python performance study

The script creates a larger transaction dataset and compares query execution before and after creating an index matching:

`amount DESC, transaction_id ASC`

The timing is illustrative rather than a universal benchmark.

---

## JavaScript implementation

JavaScript does not include a general SQL database engine in the standard language runtime.

The JavaScript implementation therefore uses arrays to model relational records and implements SQL-style ordering and pagination explicitly.

This is useful for understanding the relationship between database results and application-side processing.

### JavaScript sorting model

The implementation defines:

`compareValues()`

for comparing numbers and strings while handling optional values.

`compareByKeys()` applies a sequence of sort specifications.

A sort specification contains concepts corresponding to SQL:

- field
- direction
- NULL placement

For example, a JavaScript representation can describe:

`salary DESC`

followed by:

`employeeId ASC`

### JavaScript `LIMIT`

The `limit()` function models the behavior of a SQL `LIMIT`.

It validates that the requested count is a non-negative integer.

### JavaScript `OFFSET`

The `offsetLimit()` function models:

`LIMIT n OFFSET m`

using array slicing.

It also validates the requested offset and limit.

### JavaScript pagination

The implementation calculates:

`(page - 1) * pageSize`

and applies the result to an ordered array.

The example also imposes a maximum page size of 100.

This reflects a common API design practice: clients should not be allowed to request arbitrarily large pages.

### JavaScript NULL handling

The comparator explicitly supports:

`nullsLast`

so the application can specify whether missing values should appear at the end.

### JavaScript keyset pagination

The implementation defines a cursor using:

- salary
- employee ID

It then identifies rows that occur after that cursor according to:

`salary DESC, employeeId ASC`

This models the same logic that would be expressed in SQL.

### JavaScript security

The JavaScript file demonstrates an allow-list for sort names:

- `name`
- `salary`
- `score`
- `hireDate`

These map to fixed SQL column names.

An untrusted value such as a SQL fragment is rejected rather than directly inserted into a query.

---

## C++ case study

The C++ implementation models an industry-style employee directory query service.

The system accepts conceptual API requirements such as:

- requested sort field
- requested direction
- page number
- page size

It then validates the request, filters and sorts employee records, applies pagination, and produces a result.

The case study deliberately separates the major responsibilities instead of placing the entire query operation in one function.

---

## C++ data model

The `Employee` structure contains:

- `employeeId`
- `employeeName`
- `department`
- `salary`
- `performanceScore`
- `hireDate`
- `city`

`std::optional<double>` represents a nullable performance score.

`std::optional<std::string>` represents a nullable city.

This models SQL `NULL` more accurately than using an ordinary numeric or string value as a substitute.

---

## C++ sort specifications

The C++ program defines:

`SortDirection`

with:

- `Ascending`
- `Descending`

It also defines:

`SortField`

with fields such as:

- employee name
- department
- salary
- performance score
- hire date
- employee ID

A `SortSpecification` combines:

- a field
- a direction
- a NULL-placement rule

This gives the application a structured representation of an `ORDER BY` clause.

---

## C++ comparison architecture

The program separates comparison into several levels.

`compareNonOptional()` handles ordinary values.

`compareOptionalDouble()` handles nullable numeric values.

`compareOptionalString()` handles nullable strings.

`compareBySpecification()` applies one SQL-like ordering criterion.

`employeeComesBefore()` evaluates several criteria in order.

This mirrors the conceptual behavior of a multi-column `ORDER BY`.

---

## C++ deterministic ordering

The employee directory uses:

`salary DESC`

followed by:

`employeeId ASC`

This is an explicit deterministic ordering.

The salary determines the primary position.

The employee ID resolves equal salaries.

This is important when the service exposes paginated data.

---

## C++ `LIMIT` and `OFFSET`

The program provides:

`applyLimit()`

and:

`applyOffsetAndLimit()`

These functions model the result-size behavior of SQL.

The implementation handles edge cases such as:

- limit larger than the dataset
- zero limit
- offset beyond the end of the result
- empty results

---

## C++ pagination validation

The `PageRequest` structure contains:

- page
- page size

`calculateOffset()` validates:

- page must be at least 1
- page size must be at least 1
- page size must not exceed 100
- offset calculation must not overflow

The overflow check is important because pagination parameters ultimately participate in integer arithmetic.

---

## C++ keyset pagination

The C++ case study uses:

`SalaryCursor`

containing:

- salary
- employee ID

For the stable order:

`salary DESC, employee_id ASC`

a row occurs after the cursor when:

`salary < cursor.salary`

or:

`salary = cursor.salary AND employee_id > cursor.employee_id`

This demonstrates how the cursor must contain enough information to continue the exact ordering.

---

## C++ dynamic sorting

The program maps external names to internal sort fields.

Examples include:

`salary -> SortField::Salary`

and:

`hireDate -> SortField::HireDate`

The requested direction is restricted to:

`ASC`

or:

`DESC`

Invalid fields and directions cause exceptions.

This prevents arbitrary SQL fragments from becoming part of an SQL statement.

---

## C++ SQL generation

The case study includes a function that constructs a database-oriented SQL statement only after validation.

The generated query has the conceptual structure:

`SELECT employee_id, employee_name, salary FROM employees ORDER BY salary DESC, employee_id ASC LIMIT ?`

The sort column and direction are derived from fixed allow-lists.

The limit remains a parameter placeholder.

A real database driver should bind the value through its parameter API.

---

## C++ top-N per group

The `topNPerDepartment()` function demonstrates why a global limit is insufficient for per-group requirements.

It:

1. identifies departments
2. filters employees by department
3. sorts each department by salary
4. takes the top N rows
5. combines the results
6. applies a final deterministic ordering

A SQL implementation would normally use a window function such as `ROW_NUMBER()`.

---

## C++ automated tests

The program verifies:

- descending salary ordering
- employee-ID tie-breaking
- correct `LIMIT` behavior
- correct `OFFSET` behavior
- empty results for offsets beyond the dataset

These assertions demonstrate an important principle: ordering behavior should be tested as part of application correctness rather than treated only as presentation.

---

## C++ performance experiment

The program creates a 100,000-row in-memory dataset and measures the time required to sort it using the application's comparison logic.

The experiment illustrates that sorting work grows with the amount of data being processed.

A generic comparison sort is commonly associated with approximately:

`O(n log n)`

time complexity.

The actual behavior of a database query can differ because a database optimizer may use:

- indexes
- query predicates
- statistics
- top-N strategies
- partial sorting
- different physical access paths
- specialized storage-engine behavior

Therefore, application-side sorting complexity should not be treated as an exact prediction of database execution time.

---

## Query processing concepts

A useful simplified logical model for a query containing these clauses is:

`FROM`

`WHERE`

`GROUP BY`

`HAVING`

`SELECT`

`ORDER BY`

`LIMIT/OFFSET`

This is a logical processing model.

It does not mean that the database physically executes every operation in that exact sequence.

A query optimizer may choose a substantially different execution strategy while still producing results that satisfy the SQL semantics.

---

## Performance considerations

### Sorting

Sorting a large result set can require significant computational resources.

For an ordinary comparison sort, a common complexity model is:

`O(n log n)`

where `n` represents the number of rows being sorted.

Database engines can use more specialized strategies, so actual query behavior depends on the database system and execution plan.

### Indexes

An index can sometimes allow a database to retrieve rows in the required order without performing a full explicit sort.

For a common query such as:

`ORDER BY salary DESC, employee_id ASC`

an index whose key order corresponds to those columns may be useful.

Indexes are not free.

They consume:

- storage
- memory/cache resources
- write-maintenance work

An index should therefore be justified by actual query patterns.

### `LIMIT` does not guarantee constant work

A query with:

`LIMIT 10`

does not necessarily mean that the database examines only ten rows.

The database may need to identify which rows belong in the first ten positions.

An appropriate index or query plan can sometimes make this substantially more efficient.

### Large offsets

`OFFSET 1000000`

may require substantial work even if:

`LIMIT 10`

is used.

This is one reason keyset pagination can be valuable for large sequential datasets.

---

## Important distinctions

### `ORDER BY` versus `LIMIT`

`ORDER BY` determines the requested sequence.

`LIMIT` determines how many rows are returned.

They solve different problems.

### `LIMIT` versus `OFFSET`

`LIMIT` controls the number of returned rows.

`OFFSET` controls how many rows are skipped before the returned segment.

### Global top-N versus top-N per group

`LIMIT N` applies to the entire result.

Top-N per group normally requires a window function or equivalent grouping strategy.

### Sorting versus deterministic ordering

Sorting by one field can produce a valid partial ordering.

Adding a unique tie-breaker can create a deterministic total ordering.

### Offset pagination versus keyset pagination

Offset pagination is simple and supports direct page-number access.

Keyset pagination is often better suited to sequential navigation over large or changing datasets.

---

## Edge cases

### Limit larger than the result

If the query contains more requested rows than are available, the database returns all available rows.

It does not manufacture additional rows.

### Offset beyond the result

If the offset exceeds the number of available rows, the result is empty.

### Empty table

An ordered query against an empty table returns an empty result.

### Duplicate sort values

Duplicate sort values are normal.

The important question is whether their relative order matters.

If it does, use a tie-breaker.

### `NULL`

Missing values should not automatically be treated as zero or an empty string.

When NULL placement matters, make the rule explicit.

### Invalid page numbers

An API should normally reject:

`page = 0`

when page numbering is one-based.

### Invalid page sizes

An API should reject:

`pageSize <= 0`

and normally impose a maximum page size.

---

## Common mistakes

### Using `LIMIT` without `ORDER BY`

Incorrect for a semantic top-N requirement:

`SELECT ... LIMIT 5`

This does not identify the five highest, newest, or lowest records.

### Assuming physical order

A query may appear to return rows in insertion order during testing.

That does not mean insertion order is a guaranteed result order.

Use `ORDER BY` when order matters.

### Sorting only by a non-unique column

`ORDER BY salary DESC`

may leave equal-salary rows without a specified relative position.

A unique tie-breaker is safer when deterministic output matters.

### Using raw user input in `ORDER BY`

A web application should not directly concatenate an HTTP parameter into SQL syntax.

Instead:

1. validate the requested field against an allow-list
2. map it to a known SQL identifier
3. validate the direction
4. use parameters for ordinary values

### Allowing unlimited page sizes

A request for an extremely large page can create unnecessary:

- database work
- application memory use
- network traffic
- serialization cost

A bounded page size is generally safer.

### Using OFFSET indefinitely

Offset pagination is convenient, but large offsets can become expensive.

For large sequential datasets, keyset pagination may be more appropriate.

---

## Security considerations

Dynamic ordering deserves special attention because column identifiers are SQL syntax rather than ordinary values.

A safe application design can expose:

`salary`

`name`

`score`

as application-level choices.

The application then maps those values to fixed identifiers such as:

`salary`

`employee_name`

`performance_score`

The direction should be restricted to:

`ASC`

or:

`DESC`

User-provided values such as department filters should use parameter binding.

The same principle applies to pagination values.

The security objective is to ensure that untrusted input cannot become arbitrary SQL syntax.

---

## Production implementation considerations

A production system should consider:

- deterministic ordering
- stable pagination rules
- maximum page sizes
- parameterized values
- allow-listed sort fields
- explicit NULL handling
- suitable indexes
- database query plans
- transaction and consistency requirements
- changing data between page requests
- API response size
- observability and query timing
- database-specific syntax

The correct strategy depends on the database engine, data volume, workload, API behavior, and consistency requirements.

---

## SQL dialect differences

SQL is standardized, but individual database systems implement different dialects and optimizer behaviors.

SQLite and PostgreSQL commonly support:

`LIMIT n OFFSET m`

MySQL supports both:

`LIMIT n OFFSET m`

and:

`LIMIT offset, count`

SQL Server commonly uses:

`OFFSET m ROWS FETCH NEXT n ROWS ONLY`

Modern Oracle systems support:

`OFFSET m ROWS FETCH NEXT n ROWS ONLY`

NULL ordering behavior and optimizer behavior can also differ.

A query should therefore be evaluated against the actual database engine used by the application.

---

## Practical applications

The concepts in this study are directly applicable to:

- employee directories
- product catalogs
- transaction histories
- financial dashboards
- customer lists
- audit logs
- news feeds
- search result pages
- administrative tables
- ranking systems
- monitoring dashboards
- event streams
- reporting systems
- REST API pagination
- infinite-scroll interfaces

Typical API parameters might include:

`sort=salary`

`direction=desc`

`page=2`

`pageSize=20`

The application should validate each parameter before using it.

---

## Comparison of the three implementations

| Area | Python | JavaScript | C++ |
|---|---|---|---|
| SQL execution | Real SQLite SQL | SQL represented through application logic | In-memory SQL-style engine plus SQL generation |
| Beginner accessibility | High | High | Moderate |
| Multi-key ordering | Real SQL | Comparator implementation | Comparator architecture |
| LIMIT | SQLite | Array operation | Explicit function |
| OFFSET | SQLite | Array operation | Explicit function |
| NULL handling | SQL `CASE` | Comparator logic | `std::optional` |
| Pagination | Real SQL | Application simulation | Application service model |
| Keyset pagination | Real SQL condition | Array filtering | Cursor structure |
| Dynamic sorting | SQL allow-list | JavaScript allow-list | C++ allow-list |
| Validation | Python exceptions | JavaScript exceptions | C++ exceptions |
| Performance study | SQLite query timing | Algorithmic discussion | In-memory benchmark |
| Industry-style architecture | Study-oriented | Application-oriented | Detailed service case study |

---

## File structure

The four deliverables are designed as independent study files:

`sql_sorting_limiting.py`

Contains real SQL examples using Python's built-in SQLite support.

`sql_sorting_limiting.js`

Contains JavaScript implementations of SQL-style ordering, limiting, pagination, security validation, and SQL query patterns.

`sql_sorting_limiting.cpp`

Contains the industry-style employee directory case study.

`README.md`

Contains the conceptual documentation for all three implementations.

---

## Complexity considerations

For generic in-memory comparison sorting:

`O(n log n)`

is a common average and worst-case complexity model for efficient comparison-based sorting algorithms, depending on the algorithm and implementation.

Pagination using offset can conceptually require processing or skipping many rows before the requested page.

Keyset pagination changes the problem from "skip the first k ordered rows" to "continue after this known ordering boundary."

With an appropriate index, a database can sometimes use the cursor boundary efficiently.

The exact complexity of a database query should be determined from the database engine's execution plan rather than inferred solely from the SQL text.

---

## Deterministic ordering checklist

Before using `LIMIT` or pagination in production, verify:

- Does the query contain `ORDER BY`?
- Is the primary sort field unique?
- If not, is there a unique tie-breaker?
- Is NULL placement important?
- Is the ordering compatible with the pagination strategy?
- Can the dataset change between requests?
- Is the page size bounded?
- Is the sort field allow-listed?
- Is the direction allow-listed?
- Is an appropriate database index available?
- Has the query plan been examined?

These questions address correctness, security, and performance at the same time.

---

## Quick reference

| Requirement | SQL pattern |
|---|---|
| Ascending | `ORDER BY salary ASC` |
| Descending | `ORDER BY salary DESC` |
| Default ascending | `ORDER BY salary` |
| Multiple keys | `ORDER BY department ASC, salary DESC` |
| Deterministic ties | `ORDER BY salary DESC, employee_id ASC` |
| Top 5 | `ORDER BY salary DESC LIMIT 5` |
| Bottom 5 | `ORDER BY salary ASC LIMIT 5` |
| First page | `LIMIT 10 OFFSET 0` |
| Second page | `LIMIT 10 OFFSET 10` |
| Page 5 | `LIMIT 10 OFFSET 40` |
| Parameterized limit | `LIMIT ?` |
| Parameterized pagination | `LIMIT ? OFFSET ?` |
| Keyset boundary | `WHERE salary < ? OR (salary = ? AND employee_id > ?)` |
| Top-N per group | Window function such as `ROW_NUMBER()` |
| Explicit NULL placement | `CASE` expression or database-specific NULL-ordering syntax |

---

## Core principles

The central principles demonstrated by the implementations are:

1. `ORDER BY` defines the required result ordering.
2. `ASC` represents ascending order.
3. `DESC` represents descending order.
4. Multiple sort keys establish hierarchical ordering.
5. A non-unique sort key does not necessarily establish a complete deterministic order.
6. A unique tie-breaker can make the ordering deterministic.
7. `LIMIT` restricts the number of returned rows.
8. `OFFSET` skips rows before returning the requested page.
9. Pagination should always use a deliberate and stable ordering strategy.
10. Large offsets can become inefficient.
11. Keyset pagination can provide an efficient sequential-navigation model.
12. NULL placement should be explicit when it affects application behavior.
13. Dynamic SQL identifiers should be allow-listed rather than copied from raw user input.
14. Pagination inputs should be validated and bounded.
15. Indexes can improve ordering and pagination performance when designed for the actual workload.
16. Query plans provide more reliable performance information than assumptions based solely on SQL syntax.
17. SQL dialect differences must be considered when moving from one database system to another.
