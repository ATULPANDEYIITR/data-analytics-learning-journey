# SQL SELECT: From Basic Queries to Advanced Relational Analysis

## Topic Introduction

`SELECT` is the central SQL statement for retrieving and analyzing data from relational databases. A SELECT query can perform simple column projection, filtering, sorting, aggregation, grouping, joins, subqueries, common table expressions, window calculations, set operations, and recursive traversal.

The fundamental form is:

`SELECT column_list FROM table_name;`

A more complete query can contain clauses such as:

`SELECT ... FROM ... JOIN ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... LIMIT ...`

SQL is declarative. The query describes the desired result rather than prescribing every algorithmic step used to obtain that result. The database management system can choose an execution strategy based on indexes, statistics, available memory, data distribution, join algorithms, and other optimization information.

This study uses three implementations to examine SELECT from different technical perspectives:

- Python uses SQLite through Python's built-in `sqlite3` module, allowing real SQL statements to execute against an actual relational database.
- JavaScript models SELECT operations with arrays and objects while also demonstrating how application code constructs parameterized SQL.
- C++ builds an in-memory relational case study using strongly typed structures and standard-library algorithms, exposing the mechanics behind selection, joins, grouping, sorting, and aggregation.

The examples use an enterprise-style dataset containing employees, departments, projects, customers, orders, and sales targets.

## Fundamental Concepts

### Projection

Projection means selecting which columns appear in the result.

A query such as:

`SELECT employee_name, salary FROM employees;`

does not retrieve every column. It asks the database to return only `employee_name` and `salary`.

An explicit column list is generally clearer than `SELECT *` when an application knows exactly which fields it needs. `SELECT *` can be useful while exploring a schema, but production queries that depend on a stable result shape are often more maintainable when the required columns are explicit.

SQL expressions can also appear in the SELECT list:

`SELECT salary, salary * 12 AS annual_salary FROM employees;`

The database evaluates the expression for each qualifying row.

### Aliases

An alias gives a selected expression a readable result name:

`SELECT employee_name AS name, salary AS monthly_salary FROM employees;`

Aliases are especially useful for calculated expressions and aggregate values.

### Filtering

`WHERE` applies a condition to individual rows:

`SELECT employee_name, salary FROM employees WHERE salary >= 100000;`

Common predicates include:

- `=`
- `<>`
- `>`
- `<`
- `>=`
- `<=`
- `IN`
- `BETWEEN`
- `LIKE`
- `IS NULL`
- `IS NOT NULL`

Multiple predicates can be combined with `AND`, `OR`, and `NOT`.

### DISTINCT

`DISTINCT` removes duplicate result rows:

`SELECT DISTINCT department_id FROM employees;`

The operation applies to the complete selected row. If multiple columns are selected, duplicate combinations of those columns are removed.

### Sorting

`ORDER BY` establishes the requested result order:

`SELECT employee_name, salary FROM employees ORDER BY salary DESC;`

Multiple sort keys can be specified:

`ORDER BY salary DESC, employee_name ASC`

The second expression is used when the first expression produces equal values.

Without `ORDER BY`, a query result should not be treated as having a guaranteed business-defined order.

### Pagination

`LIMIT` restricts the number of returned rows and `OFFSET` skips rows:

`LIMIT 10 OFFSET 20`

Pagination should normally use a deterministic ordering. Without an explicit ordering, the meaning of "page 2" is not reliably defined.

## NULL and Three-Valued Logic

SQL `NULL` represents an absent, unknown, or inapplicable value. It is not the same as zero, an empty string, or an ordinary value.

This is incorrect:

`WHERE commission = NULL`

The correct test is:

`WHERE commission IS NULL`

Similarly:

`WHERE commission IS NOT NULL`

SQL predicates involving NULL can produce `UNKNOWN`, which is part of SQL's three-valued logic:

- TRUE
- FALSE
- UNKNOWN

A WHERE clause retains rows for which the predicate evaluates to TRUE. FALSE and UNKNOWN do not qualify.

The Python implementation explicitly creates employees with missing departments, email addresses, and commissions. It demonstrates `IS NULL`, `IS NOT NULL`, `COALESCE`, and the difference between `COUNT(*)` and `COUNT(column)`.

`COUNT(*)` counts rows.

`COUNT(commission)` counts only rows where `commission` is non-NULL.

`COALESCE(commission, 0)` returns the commission when it exists and `0` otherwise.

The JavaScript implementation uses `null` and the nullish-coalescing operator `??` to illustrate application-side handling of database NULL values. The C++ implementation uses `std::optional` to represent values that may be absent.

## Aggregate Functions

Aggregate functions reduce multiple rows into calculated values.

Important aggregate functions include:

- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`

For example:

`SELECT COUNT(*) FROM employees;`

calculates the number of rows.

A multi-aggregate query can calculate several statistics at once:

`SELECT COUNT(*), MIN(salary), MAX(salary), AVG(salary), SUM(salary) FROM employees;`

Aggregates are important for reporting because they transform detailed transactional rows into business measurements.

Aggregate behavior around NULL values must be understood carefully. For example, `AVG(column)` does not treat NULL as zero. It ignores NULL values when calculating the average.

## GROUP BY

`GROUP BY` partitions rows into groups so aggregate functions can be calculated independently for each group.

Example:

`SELECT department_id, AVG(salary) FROM employees GROUP BY department_id;`

The Python program groups employees by department and calculates employee count, average salary, and highest salary.

The JavaScript program reproduces the conceptual operation with a `Map`, where each key represents a group.

The C++ program uses an `unordered_map` accumulator to model the same operation with strongly typed data.

### WHERE Versus HAVING

`WHERE` filters individual rows before grouping.

`HAVING` filters groups after aggregation.

A typical pattern is:

`SELECT department_id, COUNT(*) AS employee_count FROM employees WHERE status = 'active' GROUP BY department_id HAVING COUNT(*) >= 2;`

The distinction matters because a group does not exist until grouping has occurred.

## JOIN Operations

Relational data is normally distributed across multiple tables. JOIN operations combine related rows.

### INNER JOIN

An INNER JOIN returns rows for which the join condition matches:

`SELECT e.employee_name, d.department_name FROM employees AS e JOIN departments AS d ON e.department_id = d.department_id;`

Employees without a matching department are excluded.

### LEFT JOIN

A LEFT JOIN preserves every row from the left table:

`SELECT d.department_name, e.employee_name FROM departments AS d LEFT JOIN employees AS e ON e.department_id = d.department_id;`

If no employee matches a department, the department remains in the result and employee columns become NULL.

This distinction is important for reporting. A report of all departments should generally not accidentally disappear departments that currently have no matching employees.

### Self-Join

A table can be joined to itself. Employee-manager relationships are a common example:

`employee.manager_id` can reference another `employee.employee_id`.

The Python implementation demonstrates this relationship directly.

### Join Cardinality

An incomplete or incorrect join condition can multiply rows unexpectedly.

If one customer has five orders, joining customers to orders naturally produces five customer-order rows for that customer. This is not necessarily an error. It is a consequence of one-to-many cardinality.

Before writing a join, identify whether the relationship is:

- one-to-one
- one-to-many
- many-to-one
- many-to-many

Many-to-many relationships usually require an associative table.

## Expressions and CASE

SQL expressions can calculate derived values.

A CASE expression provides conditional logic:

`CASE WHEN salary >= 130000 THEN 'Executive Range' WHEN salary >= 100000 THEN 'Senior Range' ELSE 'Entry Range' END`

The Python and C++ implementations use CASE-style salary classifications. The JavaScript implementation provides an equivalent `classifySalary` function.

CASE expressions are useful for:

- categorization
- status classification
- conditional labels
- business rules
- threshold analysis
- reporting dimensions

Conditional expressions should be kept understandable. Very large CASE expressions can become difficult to maintain and may indicate that business classification logic belongs in a dedicated reference table or application/domain layer.

## Subqueries

A subquery is a query nested inside another query.

A scalar subquery can calculate a value used by an outer query:

`SELECT employee_name, salary FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);`

The inner query calculates the company average. The outer query compares each employee's salary with that value.

Subqueries can also return sets:

`WHERE department_id IN (SELECT department_id FROM departments WHERE location = 'Pune')`

The Python implementation demonstrates scalar subqueries, set-based subqueries, and correlated `EXISTS` queries.

## EXISTS and NOT EXISTS

`EXISTS` asks whether a subquery returns at least one row.

Example:

`SELECT c.customer_name FROM customers AS c WHERE EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);`

This is useful when the requirement is existence rather than retrieving the matching rows themselves.

`NOT EXISTS` is useful for finding entities with no related records.

For example, it can identify departments with no employees.

The JavaScript implementation demonstrates equivalent existence semantics with `Array.prototype.some()`.

## Common Table Expressions

A common table expression, or CTE, is introduced using `WITH`.

Example:

`WITH active_employees AS (SELECT * FROM employees WHERE status = 'active') SELECT employee_name FROM active_employees;`

CTEs can improve readability by separating complex logic into named stages.

They are useful for:

- multi-stage transformations
- reusable intermediate result sets within a statement
- hierarchical queries
- analytical reporting
- recursive relationships

A CTE does not automatically mean that the intermediate result is physically materialized. The database optimizer determines the actual execution strategy according to the database system and query.

## Window Functions

Window functions calculate values across related rows without collapsing those rows into a single aggregate result.

For example:

`AVG(salary) OVER (PARTITION BY department_id)`

calculates the department average while retaining every employee row.

This is fundamentally different from:

`GROUP BY department_id`

A GROUP BY query produces one row per group. A window function can produce one calculated value for every input row.

Important window functions include:

- `ROW_NUMBER`
- `RANK`
- `DENSE_RANK`
- `LAG`
- `LEAD`
- `SUM() OVER`
- `AVG() OVER`
- `MIN() OVER`
- `MAX() OVER`

The Python implementation demonstrates department averages, salary ranking, row numbering, and `LAG`.

The JavaScript implementation models ranking and running totals.

The C++ case study implements a salary-ranking mechanism using sorted records.

### RANK Versus DENSE_RANK

For values:

`100, 100, 90`

`RANK()` produces:

`1, 1, 3`

`DENSE_RANK()` produces:

`1, 1, 2`

The distinction becomes important in reports where tied values exist.

## Set Operations

SQL can combine compatible result sets with set operators.

`UNION` combines results and removes duplicate rows.

`UNION ALL` combines results without duplicate elimination.

`INTERSECT` returns rows present in both result sets.

`EXCEPT` returns rows present in the first result but not the second.

The participating SELECT statements must produce compatible column structures.

`UNION ALL` is generally less expensive than `UNION` when duplicate removal is unnecessary because duplicate elimination requires additional work.

The Python implementation demonstrates all four operations.

## Recursive CTEs

Recursive CTEs allow SQL to process hierarchical relationships.

The Python implementation uses:

`WITH RECURSIVE employee_hierarchy AS (...)`

to traverse employee-manager relationships.

The recursive query contains:

1. An anchor query.
2. A recursive query.
3. A termination condition provided by the absence of additional matching rows.

Recursive CTEs are useful for:

- organizational hierarchies
- category trees
- dependency graphs
- bill-of-material structures
- directory-like structures

Production implementations must consider cycle detection, maximum recursion depth, data quality, and potentially large hierarchies.

## Logical Processing Order

A useful conceptual model for SELECT processing is:

1. `FROM`
2. `JOIN`
3. `WHERE`
4. `GROUP BY`
5. `HAVING`
6. `SELECT`
7. `DISTINCT`
8. `ORDER BY`
9. `LIMIT / OFFSET`

This describes logical query semantics rather than guaranteeing the physical execution order inside the database engine.

Database optimizers can rearrange operations when the result remains semantically equivalent. Predicate pushdown, index access, join reordering, and other transformations are examples of optimization.

Understanding logical order helps explain why a SELECT alias may not be available in every clause and why aggregate expressions behave differently from row-level predicates.

## Python Implementation

The Python program uses the standard-library `sqlite3` module, so it executes genuine SQL statements against a real relational engine without requiring an external package.

The database contains:

- `departments`
- `employees`
- `projects`
- `employee_projects`
- `customers`
- `orders`
- `sales_targets`

The implementation begins with basic SELECT projection and progresses through increasingly advanced operations.

The `fundamentals` function demonstrates:

- explicit column selection
- `SELECT *`
- expressions
- aliases

The filtering section demonstrates:

- `DISTINCT`
- `WHERE`
- `BETWEEN`
- `IN`
- `LIKE`
- `IS NULL`
- `IS NOT NULL`
- `AND`
- `OR`

The ordering section demonstrates:

- ascending and descending ordering
- multiple ordering expressions
- `LIMIT`
- `OFFSET`

The aggregation section demonstrates:

- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`

The grouping section demonstrates:

- `GROUP BY`
- `HAVING`
- aggregation after filtering
- LEFT JOIN with grouped results

The join section demonstrates:

- INNER JOIN
- LEFT JOIN
- multiple joins
- self-joins

The advanced sections demonstrate:

- subqueries
- `EXISTS`
- `NOT EXISTS`
- CTEs
- window functions
- set operations
- date expressions
- text expressions
- recursive CTEs
- parameterized SELECT statements
- query plans
- indexes
- validation
- testing
- edge cases

The Python program therefore represents the closest thing among the three implementations to actual SQL execution.

## JavaScript Implementation

The JavaScript file takes a complementary approach.

It stores relational-style data in arrays of objects and provides functions corresponding conceptually to SQL operations.

For example:

- `where()` models row filtering.
- `selectColumns()` models projection.
- `distinctBy()` models DISTINCT-like duplicate elimination.
- `orderBy()` models ORDER BY.
- `groupBy()` models grouping.
- `sum()` and `average()` model aggregate calculations.
- `innerJoin()` models INNER JOIN.
- `leftJoin()` models LEFT JOIN.

This implementation is deliberately not presented as a replacement for a database engine.

The difference is important. JavaScript array processing requires the application to hold and process the data itself. SQL allows the database engine to optimize the operation and can often avoid transferring unnecessary rows across a network connection.

The JavaScript implementation also demonstrates how an application can construct parameterized SQL:

`SELECT employee_name, salary FROM employees WHERE salary >= ? AND department_id = ?`

The values are kept separately from SQL syntax. A real database driver should bind these parameters through its parameter API.

The file also demonstrates validation, NULL handling, customer revenue analysis, ranking, running totals, and basic performance measurement.

## C++ Case Study

The C++ program models an enterprise reporting system using strongly typed structures.

The central entities are:

- `Employee`
- `Department`
- `Project`
- `Customer`
- `Order`

The program uses `std::optional` for nullable values such as an employee's department, manager, commission, or customer's city.

This is an important distinction between application data structures and SQL tables. SQL has a native NULL semantic system, while C++ requires a deliberate representation for values that may not exist.

### Problem Being Solved

The modeled organization needs reporting operations such as:

- finding high-earning employees
- sorting employees by salary
- paginating results
- joining employees to departments
- calculating department statistics
- finding employees above the company average
- classifying employees into salary bands
- calculating paid customer revenue
- ranking employees
- validating report parameters

### Design Approach

The C++ implementation separates the data model from processing functions.

Filtering is represented by `selectHighEarners`.

Joining is represented by `leftJoinEmployeesDepartments`.

Aggregation is represented by `groupEmployeesByDepartment`.

Subquery-style reasoning is represented by calculating the company average before selecting employees above that average.

CASE-style logic is represented by `salaryBand`.

Customer revenue reporting combines customers and orders into a derived report.

Assertions verify important assumptions about the data and join behavior.

### Data Structures

`vector` stores relation-like collections.

`unordered_map` is used for aggregation.

`optional` represents nullable values.

`sort` provides ordering.

`accumulate` provides a standard-library aggregation mechanism.

`find_if` performs predicate-based searches.

These structures make the underlying relational operations explicit.

### Join Complexity

The C++ join implementation uses direct iteration and lookup.

A naive nested-loop join can have approximately O(n × m) time complexity for two input collections of sizes n and m.

A real database system may use:

- nested-loop joins
- indexed nested-loop joins
- hash joins
- merge joins

The database optimizer selects a strategy based on available information and expected cost.

### Aggregation Complexity

A single-pass grouping operation can generally be implemented in approximately O(n) expected time when a hash table is used effectively.

The C++ implementation uses an `unordered_map` accumulator.

A database engine can implement grouping through hashing, sorting, parallel aggregation, or other execution strategies.

## Important Distinctions and Comparisons

### WHERE Versus HAVING

`WHERE` operates on rows before grouping.

`HAVING` operates on groups after aggregation.

Use WHERE when the condition concerns individual source rows. Use HAVING when the condition concerns aggregate results.

### GROUP BY Versus Window Functions

GROUP BY reduces multiple rows into groups.

Window functions preserve individual rows while calculating values across a window of related rows.

For example:

`GROUP BY department_id`

can produce one row for each department.

`AVG(salary) OVER (PARTITION BY department_id)`

can produce one average value alongside every employee.

### UNION Versus UNION ALL

`UNION` removes duplicates.

`UNION ALL` preserves duplicates.

When duplicate elimination is unnecessary, UNION ALL can avoid the additional work associated with deduplication.

### INNER JOIN Versus LEFT JOIN

INNER JOIN returns only matching combinations.

LEFT JOIN preserves all rows from the left relation.

The correct choice depends on the reporting requirement, not merely on which syntax is shorter.

### EXISTS Versus JOIN

Both can be useful for relationship-based conditions, but they express different intent.

`EXISTS` directly communicates that at least one related row must exist.

A JOIN constructs a combined row set and may create multiple rows when several matches exist.

The correct formulation depends on whether the query needs related values or merely needs to test existence.

## Edge Cases

### Empty Result Sets

A SELECT query can legitimately return zero rows.

Application code should not assume that every query produces data.

### Empty Aggregation

Aggregate queries can behave differently from ordinary SELECT statements when no rows qualify.

For example, `COUNT(*)` can produce zero, while `SUM()` and `AVG()` can produce NULL when no input values exist.

Applications should explicitly handle these results.

### NULL

NULL must be handled deliberately.

Incorrect assumptions about NULL can produce silently incorrect reports.

### Duplicate Rows

Duplicates can result from legitimate one-to-many or many-to-many relationships.

Adding `DISTINCT` blindly can hide an underlying join-cardinality problem.

### Pagination

Pagination should use a deterministic ORDER BY.

For high-volume systems, offset-based pagination can become expensive at large offsets. Keyset or cursor-based pagination can be more appropriate when the application has a suitable ordering key.

### Empty Groups

LEFT JOIN is important when the report must retain parent entities that have no child records.

### Ties

Ranking functions behave differently when values are tied. Reports should choose the ranking function according to the required semantics.

## Common Mistakes

### Selecting Unnecessary Columns

Avoid returning large columns when the application does not need them.

Explicit projections make result shapes clearer.

### Missing ORDER BY

Without ORDER BY, result order should not be assumed.

### Incorrect NULL Comparison

Do not use:

`column = NULL`

Use:

`column IS NULL`

### Accidental Join Multiplication

A missing or incomplete join condition can produce many more rows than expected.

Inspect relationship cardinality before interpreting a result.

### Filtering a LEFT JOIN Incorrectly

Consider:

`FROM departments d LEFT JOIN employees e ON e.department_id = d.department_id WHERE e.status = 'active'`

The WHERE condition removes rows where the right side is NULL, which can defeat the purpose of preserving unmatched departments.

If the requirement is to retain every department while matching only active employees, the status predicate can instead be placed in the ON condition:

`LEFT JOIN employees e ON e.department_id = d.department_id AND e.status = 'active'`

### Using HAVING for Row Filtering

A condition that can be applied before grouping should normally be expressed as a WHERE predicate.

### Assuming SELECT Evaluation Is Physical Execution Order

The logical processing model helps understand SQL semantics, but database engines can optimize execution.

### Concatenating Untrusted Input

Constructing SQL by string concatenation with untrusted input can create SQL injection vulnerabilities.

Use parameterized statements.

## Parameterized SELECT

The Python implementation uses SQLite parameter binding:

`SELECT employee_name, salary FROM employees WHERE salary >= ?`

and supplies the value separately.

This is fundamentally different from constructing:

`SELECT employee_name, salary FROM employees WHERE salary >= ` followed by user-controlled text.

Parameters treat supplied values as data rather than SQL syntax.

Parameterized queries should be the normal approach for values originating from users, APIs, forms, files, or other untrusted sources.

Parameters do not generally replace dynamic SQL construction for identifiers such as table names or column names. When identifiers must be dynamic, applications need a strict allowlist or an appropriate database-driver mechanism.

## Security Considerations

SQL SELECT is primarily a data retrieval operation, but SELECT queries can still create security problems.

### SQL Injection

The most important application-level concern is SQL injection.

The solution is parameterized SQL rather than string concatenation.

### Least Privilege

Database accounts should receive only the permissions required for their workload.

A reporting account generally should not receive unnecessary write or administrative privileges.

### Sensitive Data

SELECT can expose sensitive fields even when the query itself is syntactically correct.

Applications should carefully control which columns are returned.

### Authorization

Filtering data for a user is not a substitute for database-level or application-level authorization.

A query can be technically correct while still exposing records that the requesting identity should not see.

### Logging

SQL logging can be useful for diagnostics, but logs must not accidentally expose sensitive parameter values or credentials.

## Performance Considerations

SQL performance depends on much more than the number of characters in a query.

Important factors include:

- indexes
- table size
- row selectivity
- cardinality
- join strategy
- statistics
- sorting
- grouping
- memory
- disk I/O
- network transfer
- concurrency
- data distribution

### Indexes

Indexes can significantly accelerate selective lookups.

The Python implementation creates:

`idx_employees_salary`

and:

`idx_employees_department_salary`

and uses `EXPLAIN QUERY PLAN` to inspect the optimizer's chosen strategy.

Indexes also have costs:

- storage
- additional write work
- maintenance
- memory consumption
- potential optimizer trade-offs

An index should exist because it supports actual workload requirements, not simply because a column appears in a query.

### Query Plans

`EXPLAIN QUERY PLAN` is a useful diagnostic mechanism in SQLite.

Other database systems provide more detailed execution-plan tools.

A query that looks simple can still be expensive if it scans millions of rows, performs large sorts, or generates a large intermediate join result.

### Filtering Early

Reducing unnecessary rows can reduce downstream work.

A selective WHERE predicate can be valuable before expensive joins or aggregations, subject to optimizer transformations.

### Selecting Only Required Columns

Returning fewer columns reduces data movement and can reduce memory and I/O.

## Implementation Considerations

The Python implementation executes SQL directly and therefore demonstrates actual SQL syntax and database semantics.

The JavaScript implementation demonstrates the conceptual relationship between SQL operations and application-side data processing.

The C++ implementation exposes the algorithms and data structures behind relational operations.

These differences matter:

| Aspect | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| Database execution | Real SQLite | Conceptual in-memory model | Conceptual in-memory model |
| Type system | Dynamic | Dynamic | Static |
| SQL syntax | Executed directly | SQL represented as strings | SQL concepts modeled algorithmically |
| NULL representation | SQLite NULL / Python None | JavaScript null | `std::optional` |
| Filtering | SQL WHERE | Array filtering | Explicit loops/algorithms |
| Grouping | SQL GROUP BY | Map grouping | unordered_map aggregation |
| Joining | SQL JOIN | Join functions | Explicit join implementation |
| Ranking | SQL window functions | Array-based ranking | Sorted ranking |
| Query planning | SQLite optimizer | Not present | Explicit algorithm discussion |
| Parameterization | SQLite bindings | Parameter representation | Input validation |

## Real-World Applications

SELECT is foundational to almost every relational data workload.

Typical applications include:

- financial reporting
- customer analytics
- inventory management
- security monitoring
- employee management
- audit systems
- healthcare data systems
- logistics
- e-commerce
- telecommunications
- manufacturing
- scientific databases
- business intelligence
- operational dashboards

Simple SELECT statements are often the building blocks of much larger systems.

For example, a customer dashboard may combine:

1. customer filtering
2. order joins
3. revenue aggregation
4. date filtering
5. ranking
6. segmentation
7. pagination

Each of those operations is represented in the examples in this study.

## Production Considerations

A production SELECT query should be evaluated from several perspectives:

- Is the result semantically correct?
- Are NULL values handled correctly?
- Are joins based on the intended keys?
- Can duplicate rows occur?
- Is ordering deterministic where required?
- Is pagination stable?
- Is the query parameterized?
- Does the query return only required columns?
- Does an appropriate index exist?
- Has the query plan been inspected for important workloads?
- Does the query remain acceptable as the dataset grows?
- Are authorization requirements satisfied?
- Are sensitive fields protected?
- Is the result shape stable for consuming applications?
- Are tests available for important edge cases?

Correctness should be established before optimization. Optimization should then be guided by measurements and execution plans rather than assumptions.

## Implementation Coverage

The Python program provides the broadest direct SQL coverage. It executes actual SELECT statements and demonstrates the relationship between SQL syntax and a database engine.

The JavaScript program focuses on the boundary between SQL and application code. It shows how relational operations can be expressed through array transformations while emphasizing that application-side processing is not equivalent to database execution.

The C++ program focuses on implementation mechanics. Its strongly typed structures and explicit algorithms reveal what operations such as filtering, grouping, joining, and ranking can look like when the database abstraction is removed.

Together, the implementations demonstrate three complementary levels:

1. SQL as a declarative database language.
2. SQL concepts as application-level data transformations.
3. Relational operations as explicit algorithms and data structures.

## Technical Scope

The implementations cover:

- SELECT projection
- SELECT *
- aliases
- expressions
- DISTINCT
- WHERE
- AND
- OR
- IN
- BETWEEN
- LIKE
- NULL
- IS NULL
- IS NOT NULL
- COALESCE
- CASE
- ORDER BY
- LIMIT
- OFFSET
- COUNT
- SUM
- AVG
- MIN
- MAX
- GROUP BY
- HAVING
- INNER JOIN
- LEFT JOIN
- SELF JOIN
- subqueries
- correlated EXISTS
- NOT EXISTS
- common table expressions
- recursive CTEs
- window functions
- ROW_NUMBER
- RANK
- DENSE_RANK
- LAG
- set operations
- UNION
- UNION ALL
- INTERSECT
- EXCEPT
- parameterized queries
- validation
- query testing
- query plans
- indexes
- performance
- NULL semantics
- join cardinality
- production considerations
- security considerations

The central principle is that SQL SELECT is not merely a command for displaying rows. It is a declarative framework for expressing relational transformations, filtering, combination, aggregation, analysis, and controlled retrieval of structured data.
