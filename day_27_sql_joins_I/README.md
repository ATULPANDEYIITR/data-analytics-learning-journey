# SQL Joins I

## INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN, and Join Keys

## 1. Topic Introduction

A SQL join combines rows from two or more relations according to a specified matching condition. Joins are fundamental to relational database work because useful information is frequently distributed across multiple normalized tables.

For example, an organization may store employees and departments separately:

- `employees` contains employee information.
- `departments` contains department information.
- `employees.department_id` identifies the department associated with an employee.
- `departments.department_id` uniquely identifies a department.

A join can combine those relations into a result containing both employee and department information.

The central questions when designing a join are:

1. What does one result row represent?
2. Which columns establish correspondence between the tables?
3. Can the join key repeat?
4. Should unmatched rows be preserved?
5. Can the join multiply rows?
6. Are NULL values possible?
7. Are filters being applied at the correct stage?
8. Does the query have appropriate indexes for its workload?

The three implementations in this study approach the subject differently:

- Python uses the built-in `sqlite3` module to execute actual SQL.
- JavaScript implements relational join behavior using arrays and `Map`.
- C++ develops an in-memory, hash-indexed join engine around a realistic organizational dataset.

---

## 2. Relational Database Terminology

### Table

A table is a named relation consisting of rows and columns.

Examples:

`employees`

`departments`

`projects`

### Row

A row represents one record.

An employee row might contain:

`employee_id = 2`

`employee_name = Ravi`

`department_id = 10`

### Column

A column represents an attribute shared by rows in a table.

Examples include:

- `employee_id`
- `employee_name`
- `department_id`
- `salary`

### Primary Key

A primary key uniquely identifies a row.

For example:

`departments.department_id`

can uniquely identify a department.

A primary key must identify a single logical row and cannot contain SQL NULL.

### Foreign Key

A foreign key establishes a referential relationship to a key in another table.

For example:

`employees.department_id`

can reference:

`departments.department_id`

The foreign key normally represents the relationship from a child table to a parent table.

### Join Key

A join key is the column or collection of columns used to establish row correspondence during a join.

A common equality predicate is:

`employees.department_id = departments.department_id`

The two columns do not need to have the same name, but their values and meanings must be compatible.

---

## 3. Join Cardinality

Understanding cardinality is essential before writing joins.

### One-to-One

One row on one side corresponds to at most one row on the other side.

### One-to-Many

One row on the parent side can correspond to multiple rows on the child side.

For example:

`Engineering -> Asha`

`Engineering -> Ravi`

One department can contain many employees.

### Many-to-Many

Many rows on each side can correspond to many rows on the other side.

Employees and projects are a common example.

An employee can participate in several projects, while a project can contain several employees.

A junction table is normally used:

`employee_projects`

with columns such as:

- `employee_id`
- `project_id`
- `role`

---

## 4. Join Syntax

The general structure of an inner join is:

`SELECT columns FROM table_a AS a INNER JOIN table_b AS b ON a.key = b.key;`

The `INNER` keyword can be omitted:

`SELECT columns FROM table_a AS a JOIN table_b AS b ON a.key = b.key;`

For a left join:

`SELECT columns FROM table_a AS a LEFT JOIN table_b AS b ON a.key = b.key;`

For a right join:

`SELECT columns FROM table_a AS a RIGHT JOIN table_b AS b ON a.key = b.key;`

For a full outer join:

`SELECT columns FROM table_a AS a FULL OUTER JOIN table_b AS b ON a.key = b.key;`

Database products differ in which join types they support directly. A portable query may sometimes express a right join by reversing the table order and using a left join. A full outer join can also be constructed from left-join operations in systems without native support.

---

## 5. INNER JOIN

An `INNER JOIN` returns only rows for which the join condition succeeds.

Suppose the tables contain:

- Engineering with ID 10
- Finance with ID 20
- Security with ID 40

and employees contain:

- Asha with department ID 10
- Ravi with department ID 10
- Meera with department ID 20
- Kabir with no department
- Isha with department ID 30
- Arjun with department ID 40

An inner join excludes Kabir because his department identifier does not match a department.

It also excludes Isha if department 30 does not exist in the department table.

The conceptual rule is:

**Only matching relationships are returned.**

The Python implementation executes an actual SQL `INNER JOIN`.

The JavaScript implementation builds an index with `Map`, then returns only matching pairs.

The C++ implementation creates an `unordered_multimap` index and produces result rows for matching keys.

---

## 6. LEFT JOIN

A `LEFT JOIN` preserves every row from the left relation.

If a matching row exists on the right, the matching information is returned.

If no match exists, the right-side columns are represented as NULL in SQL.

For:

`employees LEFT JOIN departments`

every employee remains in the result.

This makes left joins useful for questions such as:

- Which employees exist, including those without departments?
- Which customers have never placed an order?
- Which products have no sales?
- Which accounts have no associated transaction?
- Which records from the master system are missing from the reference system?

A common unmatched-record pattern is:

`LEFT JOIN ... WHERE right_table.key IS NULL`

This identifies left-side records without a matching right-side record.

---

## 7. RIGHT JOIN

A `RIGHT JOIN` preserves every row from the right relation.

For:

`employees RIGHT JOIN departments`

every department remains visible, including departments with no employees.

Right joins can frequently be expressed as reversed left joins.

For example, the following conceptual transformation is equivalent:

`employees RIGHT JOIN departments`

becomes:

`departments LEFT JOIN employees`

Many teams prefer left joins because a query can be structured with the principal preserved relation on the left, but the important concept is the preservation rule rather than the direction keyword itself.

The C++ case study explicitly demonstrates right-join behavior by reusing the left-join mechanism with reversed relations.

---

## 8. FULL OUTER JOIN

A `FULL OUTER JOIN` preserves:

1. Matching rows.
2. Unmatched left rows.
3. Unmatched right rows.

It therefore provides a useful way to compare two datasets and identify discrepancies on either side.

Typical applications include:

- comparing two customer systems
- reconciling financial records
- comparing planned and actual datasets
- migration validation
- master-data reconciliation
- identifying records present in only one source

Conceptually:

`FULL OUTER JOIN = matched rows + left-only rows + right-only rows`

Database support for full outer joins varies. Where native support is unavailable, a common relational construction uses a left join combined with the unmatched records from the opposite direction.

---

## 9. Join Keys and Data Integrity

A join is only as meaningful as its join key.

Suppose:

`employees.department_id`

is matched against:

`departments.department_id`

This is appropriate because both columns represent the same business identifier.

A poor join might compare unrelated attributes such as:

`employees.employee_name = departments.department_name`

Even if a few values happen to match, the relationship would not represent the intended business model.

A proper join key should have:

- consistent meaning
- compatible data types
- predictable formatting
- appropriate uniqueness
- clear ownership
- documented semantics

Primary and foreign key constraints help databases enforce data integrity.

---

## 10. Composite Join Keys

Some relationships require more than one column.

The regional sales case study contains:

- `region`
- `product`
- `amount`

The regional target table contains:

- `region`
- `product`
- `target`

The correct business identity is:

`region + product`

Therefore the join must compare both:

`sales.region = targets.region`

and:

`sales.product = targets.product`

Using only `region` would allow unrelated products within the same region to match.

Composite keys are common in:

- sales data
- inventory
- geographic datasets
- academic records
- pricing tables
- time-series data
- multi-tenant applications

When a relationship logically depends on multiple attributes, all relevant attributes must participate in the join condition.

---

## 11. NULL Semantics

SQL NULL does not mean zero.

It does not mean an empty string.

It does not mean false.

It represents an absent or unknown value.

This creates an important SQL rule:

`NULL = NULL`

does not evaluate to TRUE.

To test for NULL, use:

`IS NULL`

or:

`IS NOT NULL`

For example:

`WHERE department_id IS NULL`

correctly identifies employees without a stored department identifier.

The Python implementation intentionally demonstrates the difference between:

`department_id IS NULL`

and:

`department_id = NULL`

The latter does not produce the expected result.

Outer joins also introduce NULL values when one side has no matching row.

---

## 12. ON Versus WHERE

This distinction is particularly important with outer joins.

Consider:

`LEFT JOIN departments d ON e.department_id = d.department_id`

This determines which department row can match an employee.

Now consider:

`WHERE d.department_id = 10`

The WHERE condition is applied to the resulting rows.

Rows where the right side is NULL fail that condition and disappear.

This can make a left join behave like an inner join for the filtered condition.

By contrast, putting a restriction into the join condition:

`ON e.department_id = d.department_id AND d.department_id = 10`

allows the employee row to remain while controlling which department row can match.

The location of a predicate is therefore part of the query's semantics, not merely formatting.

---

## 13. One-to-Many Joins and Row Multiplication

Suppose a department has two employees.

Joining:

`departments`

to:

`employees`

can produce two result rows for that department.

This is correct because there are two relationships.

A frequent SQL mistake is assuming that joining two tables always preserves the number of rows from one input.

It does not.

If one left row matches three right rows, it can generate three result rows.

If two rows on the left each match three rows on the right, the six relationships may legitimately produce six output rows.

Before joining, determine the expected grain.

Examples of grain:

- one row per employee
- one row per department
- one row per employee-project assignment
- one row per customer-order
- one row per product-region

If the intended grain is one row per employee but the query joins a one-to-many relation, aggregation or another design decision may be necessary.

---

## 14. Many-to-Many Relationships

Employees and projects form a many-to-many relationship.

The direct relationship is represented through:

`employee_projects`

The logical path is:

`employees -> employee_projects -> projects`

The first join connects employees to their assignments.

The second join connects assignments to projects.

This produces information such as:

- employee name
- project name
- role

A junction table usually contains foreign keys referencing both participating relations.

The Python, JavaScript, and C++ implementations all demonstrate this relationship.

---

## 15. Semi-Joins and Anti-Joins

Sometimes the goal is not to return data from the second table.

The requirement may simply be:

"Which employees have at least one project?"

An SQL `EXISTS` query is appropriate:

`WHERE EXISTS (...)`

This is commonly described as a semi-join pattern.

The opposite question is:

"Which employees have no projects?"

This can be expressed with:

`WHERE NOT EXISTS (...)`

This is an anti-join pattern.

These approaches are often clearer than joining and then using `DISTINCT` when the second table's columns are not required in the final result.

---

## 16. Self Joins

A self join joins a table to itself.

The employee data includes:

`manager_id`

which refers to:

`employee_id`

in the same employee table.

This allows a query to represent:

`employee -> manager`

The two logical instances of the table need different aliases.

For example:

`employees AS employee`

and:

`employees AS manager`

Self joins are useful for hierarchical data such as:

- employees and managers
- categories and parent categories
- organizational structures
- folder hierarchies
- reporting relationships

More complex hierarchical requirements may be better handled using recursive common table expressions, but a basic manager lookup is naturally represented with a self join.

---

## 17. CROSS JOIN

A `CROSS JOIN` creates the Cartesian product.

If the first table contains `m` rows and the second contains `n` rows, the result contains:

`m × n`

rows before further filtering.

For example:

10 rows combined with 20 rows produce:

`200`

combinations.

Cross joins are useful when combinations are intentionally required.

They can also occur accidentally when a developer forgets a join predicate.

An unintended Cartesian product can cause:

- extremely large results
- excessive memory usage
- slow execution
- unnecessary network transfer
- incorrect reports

For this reason, join conditions should always be reviewed carefully.

---

## 18. Aggregation After Joins

Joins are frequently combined with:

- `GROUP BY`
- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`

The department reporting example calculates employee counts and average salaries.

An important detail is the difference between:

`COUNT(*)`

and:

`COUNT(employee_id)`

After a left join, an unmatched department still produces a result row, but `employee_id` is NULL.

Therefore:

`COUNT(*)`

counts the preserved department row.

`COUNT(employee_id)`

counts only actual matching employees.

This distinction matters in reporting queries.

---

## 19. COALESCE and Missing Values

`COALESCE` can convert NULL into a chosen fallback value.

For example:

`COALESCE(average_salary, 0)`

can produce zero instead of NULL when an aggregate or joined value is missing.

The semantic choice should be deliberate.

A missing value is not necessarily equivalent to zero.

For example:

- zero sales means sales were measured and the value is zero
- NULL sales may mean no matching record exists
- NULL salary may mean salary data is unavailable

Replacing NULL with zero can therefore change the meaning of a report.

---

## 20. Duplicate Join Keys

A join key does not automatically have to be unique.

Suppose the right table contains:

`employee_id = 1, alias = "Asha P."`

and:

`employee_id = 1, alias = "Architect Asha"`

An employee with ID 1 matches both rows.

The result therefore contains two rows for that employee.

This is expected relational behavior.

Unexpected row multiplication often comes from joining on a column that the developer incorrectly assumed was unique.

Useful diagnostic questions include:

- Is this key actually unique?
- Is uniqueness enforced by the database?
- Is this a one-to-many relationship?
- Should the result contain multiple rows?
- Should the query aggregate?
- Should the query use `EXISTS` instead?

---

## 21. Python Implementation

The Python implementation uses the standard-library `sqlite3` module.

This provides an actual SQL execution environment without requiring an external database server.

The implementation demonstrates:

- table creation
- primary keys
- foreign keys
- sample relational data
- inner joins
- left joins
- right-join equivalence
- full-outer-join construction
- one-to-many relationships
- many-to-many relationships
- composite keys
- `ON` versus `WHERE`
- NULL behavior
- duplicate keys
- semi-joins
- anti-joins
- self joins
- cross joins
- aggregation
- parameterized SQL
- query plans
- validation

The script uses an in-memory SQLite database, so running it does not create a persistent database file.

### Parameterized SQL

The Python example passes a department identifier as a SQL parameter rather than concatenating it into the query.

This pattern is important for security because application input should not be inserted directly into SQL source text.

---

## 22. JavaScript Implementation

The JavaScript implementation does not use a database engine.

Instead, it models relations as arrays of objects and implements join operations directly.

This makes the underlying mechanics visible.

The central implementation uses `Map` as a hash-based index.

For an inner join:

1. Build an index for the right relation.
2. Read each left row.
3. Calculate its join key.
4. Find matching right rows.
5. Produce the corresponding result rows.

This approach demonstrates an important idea behind hash-based join processing.

The implementation includes:

- `innerJoin`
- `leftJoin`
- `rightJoin`
- `fullOuterJoin`
- composite-key joins
- many-to-many relationships
- unmatched-record detection
- semi-joins
- anti-joins
- self-join logic
- aggregation
- duplicate-key behavior
- performance measurement

JavaScript's `Map` is particularly useful for demonstrating indexed lookup because it provides key-based access without requiring a third-party package.

---

## 23. C++ Case Study

### Problem Being Solved

The C++ program models a small organizational reporting system.

The system needs to answer questions involving:

- employees
- departments
- projects
- employee-project assignments
- regional sales
- regional targets

The objective is to construct a reusable in-memory join mechanism and use it for realistic relational operations.

### Major Components

The data model contains:

`Department`

Represents organizational departments.

`Employee`

Represents employees and contains optional department and manager identifiers.

`Project`

Represents organizational projects.

`EmployeeProject`

Acts as a junction relation between employees and projects.

`Sales`

Represents regional product sales.

`Target`

Represents regional product targets.

### Generic Join Engine

The C++ implementation provides generic templates for:

- `innerJoin`
- `leftJoin`
- `rightJoin`
- `fullOuterJoin`

The implementation uses callable key extractors and result combiners.

This separates join mechanics from the business-specific data being joined.

### Hash-Based Index

The join implementation uses:

`unordered_multimap`

A multi-map is appropriate because a join key may appear multiple times.

For example, one department can match many employees.

Using a structure that supports multiple values for a key prevents the implementation from incorrectly assuming uniqueness.

### NULL Representation

C++ does not have SQL NULL as a native relational value.

The program uses:

`std::optional`

to represent values that may be absent.

For example:

`optional<int> departmentId`

can represent either:

- a valid department ID
- no department ID

This is conceptually similar to nullable data in SQL.

---

## 24. C++ Join Complexity

A naive nested-loop equality join can compare every left row with every right row.

For `m` left rows and `n` right rows, that approach can require approximately:

`O(m × n)`

comparisons.

The hash-index implementation generally performs:

`O(m + n + r)`

expected work, where `r` is the number of result rows.

The result size matters because a one-to-many relationship can legitimately produce many output rows.

Hash-based joins are not universally optimal. Real database systems may choose among several strategies depending on data distribution, indexes, ordering, memory, statistics, and query predicates.

---

## 25. Join Algorithms in Database Systems

A database optimizer may choose different physical implementations for the same SQL join.

### Nested-Loop Join

For each row on one side, search the other side.

Simple and sometimes effective for:

- very small relations
- highly selective indexed lookups
- suitable index structures

Potential worst-case behavior can approach:

`O(m × n)`

### Hash Join

Build a hash structure for one relation and probe it using rows from the other relation.

Often effective for equality joins.

Typical expected complexity is approximately:

`O(m + n)`

before accounting for output size and implementation-specific factors.

### Merge Join

If both inputs are ordered by the join key, the engine can traverse them in order.

This can be efficient for large sorted relations.

The physical algorithm is selected by the database optimizer rather than dictated directly by the SQL syntax.

---

## 26. Indexing and Join Performance

Indexes can significantly improve join performance.

A frequently used join key may benefit from an index.

For example:

`employees.department_id`

is a natural candidate because it is frequently used to connect employees with departments.

Indexing has costs:

- additional storage
- additional write work
- index maintenance
- memory consumption
- possible optimizer trade-offs

An index should therefore be evaluated in the context of actual workloads.

An index is not automatically useful simply because a column appears in a join.

---

## 27. Query Plan Analysis

The Python implementation uses:

`EXPLAIN QUERY PLAN`

to expose SQLite's chosen execution strategy.

Query plans can reveal whether a database is:

- scanning a table
- using an index
- searching by a key
- materializing intermediate data
- changing join order

For large production systems, execution plans are an important debugging and optimization tool.

Performance analysis should be based on measured query behavior rather than assumptions about how a database must execute a statement.

---

## 28. Security Considerations

SQL joins themselves are not inherently a security vulnerability, but applications that construct SQL incorrectly can introduce security problems.

### SQL Injection

Avoid constructing queries by concatenating untrusted input.

Unsafe conceptual pattern:

`"... WHERE department_id = " + userInput`

Use parameterized statements instead.

The Python implementation demonstrates parameter binding with `?`.

### Least Privilege

Applications should use database accounts with only the permissions required for their workloads.

A reporting application generally does not need unrestricted database administration privileges.

### Sensitive Data

Joining tables can bring sensitive fields together.

Access controls should consider the resulting dataset, not just individual tables.

For example, a join combining identity information with financial records may produce a more sensitive result than either table considered independently.

---

## 29. Common Mistakes

### Mistake 1: Using the Wrong Join Key

Joining unrelated columns can produce syntactically valid but logically incorrect results.

### Mistake 2: Assuming a Key Is Unique

A non-unique key can multiply rows.

### Mistake 3: Forgetting the Join Predicate

This can create a Cartesian product.

### Mistake 4: Using `= NULL`

Use:

`IS NULL`

instead.

### Mistake 5: Accidentally Converting a LEFT JOIN to an INNER JOIN

A WHERE condition on a nullable right-side column can remove unmatched rows.

### Mistake 6: Ignoring Composite Keys

Joining only part of a composite business key can produce incorrect matches.

### Mistake 7: Aggregating After an Unexpected Row Multiplication

A join that multiplies rows can inflate:

- `SUM`
- `COUNT`
- averages
- financial metrics

The relationship cardinality must be understood before aggregation.

### Mistake 8: Selecting Columns Without Considering Grain

A result containing repeated customer information may be correct if the grain is one row per order.

It may be incorrect if the intended grain is one row per customer.

### Mistake 9: Using DISTINCT to Hide a Logical Error

`DISTINCT` can remove duplicate-looking output, but it does not necessarily repair an incorrect join.

The relationship should be fixed first.

### Mistake 10: Ignoring Data Quality

Whitespace, case differences, inconsistent identifiers, NULL values, incorrect foreign keys, and malformed business keys can all affect matching.

---

## 30. Join Debugging Method

A practical debugging sequence is:

1. Identify the intended result grain.
2. List the participating tables.
3. Identify the relationship between each table.
4. Identify the join key.
5. Check key uniqueness.
6. Check for NULL values.
7. Test the join without additional filters.
8. Inspect the row count.
9. Inspect sample rows.
10. Check for unexpected duplication.
11. Add filters carefully.
12. Compare `ON` and `WHERE` behavior for outer joins.
13. Validate aggregates.
14. Inspect the execution plan when performance matters.
15. Add or modify indexes based on measured workload.

This approach separates logical correctness from optimization.

---

## 31. Important Join Comparisons

| Join Type | Preserves Left Rows | Preserves Right Rows | Requires Match |
|---|---:|---:|---:|
| INNER JOIN | No | No | Yes |
| LEFT JOIN | Yes | Only matching rows | No |
| RIGHT JOIN | Only matching rows | Yes | No |
| FULL OUTER JOIN | Yes | Yes | No |

The phrase "preserves" means that the row remains represented even when the other side has no matching record.

---

## 32. Choosing a Join Type

Use `INNER JOIN` when only matching relationships are relevant.

Use `LEFT JOIN` when every record from the primary left-side relation must remain visible.

Use `RIGHT JOIN` when preserving the right relation expresses the query more naturally.

Use `FULL OUTER JOIN` when discrepancies on both sides must be visible.

Use `EXISTS` when the requirement is primarily to determine whether a matching record exists.

Use `NOT EXISTS` when the requirement is to find records without a corresponding relation.

Use a self join when two logical roles are represented by the same table.

Use a cross join only when Cartesian combinations are intentionally required.

---

## 33. Production Considerations

Production join design should consider more than SQL syntax.

### Data Volume

A join involving a few hundred rows behaves differently from a join involving billions of rows.

### Cardinality

The expected relationship between keys should be documented.

### Indexes

Frequently joined and filtered columns may require appropriate indexes.

### Statistics

Database optimizers use statistics to estimate row counts and choose execution plans.

### Data Distribution

Highly skewed key distributions can influence join performance.

### Memory

Hash-based operations can require substantial memory.

### Network Transfer

Returning unnecessary columns or rows can increase application and network costs.

### Transactions

Reports running concurrently with writes may require appropriate isolation behavior.

### Constraints

Primary keys and foreign keys help preserve data integrity.

### Testing

Join queries should be tested against:

- matching rows
- missing rows
- duplicate keys
- NULL values
- empty tables
- multiple matches
- composite keys
- large datasets

---

## 34. Edge Cases Demonstrated

The implementations explicitly cover:

- employee without a department
- department without employees
- multiple employees in one department
- employee working on multiple projects
- project assigned to multiple employees
- composite region/product keys
- duplicate join keys
- NULL values
- missing relationships
- self-referential relationships
- aggregation after an outer join
- intentional Cartesian combinations
- parameterized filtering
- execution-plan inspection

These cases are important because simple matching examples often hide the behaviors that cause real-world SQL bugs.

---

## 35. Python, JavaScript, and C++ Comparison

### Python

Python is useful for studying actual SQL because `sqlite3` provides a lightweight relational database engine.

It demonstrates database behavior directly, including SQL syntax, NULL semantics, aggregation, foreign keys, and query plans.

### JavaScript

JavaScript makes the mechanics of joins visible without a database engine.

The array and `Map` implementation shows how a program can conceptually construct indexes and combine records.

This is particularly useful for understanding application-side data processing.

### C++

C++ demonstrates how a lower-level implementation can model relational operations using explicit data structures, templates, pointers, `optional`, and hash indexes.

The case study emphasizes implementation architecture, generic algorithms, memory representation, and performance.

The three approaches therefore complement each other:

- Python demonstrates SQL as a database language.
- JavaScript demonstrates relational operations as application-level algorithms.
- C++ demonstrates a lower-level implementation of the same relational ideas.

---

## 36. Practical Applications

SQL joins are used in:

- customer analytics
- financial reporting
- inventory systems
- banking systems
- human-resource systems
- enterprise resource planning
- sales reporting
- e-commerce
- cybersecurity analytics
- log analysis
- data warehouses
- business intelligence
- research databases
- healthcare information systems
- education systems
- fraud detection
- reconciliation systems
- data migration validation

The core idea remains the same: establish a meaningful relationship between rows and select the preservation behavior required by the business question.

---

## 37. Implementation Checklist

Before considering a join query complete, verify:

- [ ] The intended result grain is known.
- [ ] The join key has been identified.
- [ ] The relationship cardinality is understood.
- [ ] Primary and foreign keys are correct where applicable.
- [ ] Composite key columns are all included.
- [ ] NULL behavior is intentional.
- [ ] The selected join type matches the requirement.
- [ ] Duplicate keys have been considered.
- [ ] `ON` and `WHERE` conditions have the intended semantics.
- [ ] Aggregates are not inflated by unexpected row multiplication.
- [ ] Unmatched rows have been tested.
- [ ] Empty-table behavior has been tested.
- [ ] Query parameters are handled safely.
- [ ] Relevant indexes have been considered.
- [ ] Execution plans have been inspected when performance requires it.
- [ ] Result counts have been validated.

## 38. Files and Execution

### Python

The Python program requires only Python 3 and its standard `sqlite3` module.

It creates an in-memory database, inserts the case-study data, executes the SQL examples, displays results, and runs validation checks.

### JavaScript

The JavaScript program is designed for a modern Node.js runtime.

It requires no npm dependencies.

### C++

The C++ case study requires a compiler supporting C++17 or later.

It uses only the C++ standard library.

The three programs are intentionally self-contained so that the join concepts can be studied without setting up an external database server or installing third-party packages.
