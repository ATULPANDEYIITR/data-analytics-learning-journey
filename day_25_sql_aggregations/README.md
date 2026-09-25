# SQL Aggregations: COUNT, SUM, AVG, MIN, MAX, NULL Handling, and Aggregate Expressions

## 1. Topic Introduction

SQL aggregation transforms multiple rows into meaningful statistical or business measurements.

The principal aggregate functions covered in this study are:

- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`

Aggregation becomes especially important when raw transactional data must be converted into reports such as:

- number of customers
- number of orders
- total revenue
- average order value
- minimum and maximum transaction values
- departmental salary statistics
- missing-data counts
- operational KPIs
- conditional business metrics

The three implementations use the same conceptual topic from different perspectives:

- Python uses SQLite to execute actual SQL queries.
- JavaScript implements the aggregation semantics directly with arrays, objects, `Map`, and `Set`, while also displaying equivalent SQL.
- C++ develops an industry-style order analytics case study using `std::optional`, `std::map`, `std::set`, and aggregation algorithms.

A central theme throughout all three implementations is that `NULL` is not the same thing as zero.

---

## 2. Fundamental Aggregation Concept

Suppose a table contains these values:

`10, 20, NULL, 30, NULL`

There are five rows, but only three known numeric values.

The following concepts are therefore different:

- `COUNT(*)` = 5
- `COUNT(value)` = 3
- `SUM(value)` = 60
- `AVG(value)` = 20
- `MIN(value)` = 10
- `MAX(value)` = 30

SQL aggregate functions generally ignore `NULL` values when evaluating an aggregate expression.

This distinction is one of the most important principles in SQL aggregation.

---

## 3. COUNT

### 3.1 COUNT(*)

`COUNT(*)` counts rows.

Example:

`SELECT COUNT(*) FROM employees;`

It counts every row that survives the `WHERE` clause.

If a row contains many `NULL` values, it is still counted.

### 3.2 COUNT(column)

`COUNT(column)` counts only non-`NULL` values of the specified expression.

Example:

`SELECT COUNT(salary) FROM employees;`

If ten employees exist but three have `NULL` salary values:

- `COUNT(*)` = 10
- `COUNT(salary)` = 7

These two expressions answer different questions.

### 3.3 COUNT(DISTINCT column)

`COUNT(DISTINCT column)` counts unique non-`NULL` values.

Example:

`SELECT COUNT(DISTINCT department) FROM employees;`

If the departments are:

`Engineering, Engineering, Sales, Sales, HR`

the distinct count is 3.

### 3.4 Counting missing values

A useful pattern is:

`COUNT(*) - COUNT(column)`

This calculates the number of rows where the column is `NULL`.

Another explicit approach is:

`SUM(CASE WHEN column IS NULL THEN 1 ELSE 0 END)`

---

## 4. SUM

`SUM` adds numeric values.

Example:

`SELECT SUM(salary) FROM employees;`

`NULL` inputs are ignored.

If the values are:

`100, 200, NULL, 300`

then:

`SUM(value) = 600`

### 4.1 SUM of an expression

Aggregates can operate on expressions rather than only physical columns.

For an order table:

`quantity * unit_price`

can be aggregated as:

`SUM(quantity * unit_price)`

This calculates total gross order value when both values are present.

### 4.2 SUM and NULL expressions

SQL expressions themselves can become `NULL`.

If:

- `quantity = 3`
- `unit_price = NULL`

then:

`quantity * unit_price`

is `NULL`.

That row does not contribute a value to `SUM(quantity * unit_price)`.

This is different from deliberately converting missing data to zero.

---

## 5. AVG

`AVG` calculates an arithmetic mean.

Conceptually:

`AVG(value) = SUM(value) / COUNT(value)`

The denominator is effectively based on non-`NULL` values.

For:

`10, 20, NULL, 30`

the result is:

`60 / 3 = 20`

It is not:

`60 / 4 = 15`

### 5.1 Important distinction

This:

`AVG(salary)`

is not equivalent to:

`SUM(salary) / COUNT(*)`

when `salary` can contain `NULL`.

The second expression includes rows with missing salaries in the denominator.

### 5.2 Business interpretation

Before using an average, determine what the missing value means.

If a missing salary means "salary not yet recorded", excluding it may be appropriate.

If a missing value means "zero", then the business logic may require an explicit transformation.

Those are different data models and should not be confused.

---

## 6. MIN and MAX

`MIN` returns the smallest non-`NULL` value.

`MAX` returns the largest non-`NULL` value.

Example:

`SELECT MIN(salary), MAX(salary) FROM employees;`

For:

`50000, 60000, NULL, 90000`

the results are:

- minimum = 50000
- maximum = 90000

`MIN` and `MAX` are not restricted to numbers. They can also be applied to other comparable SQL data types, subject to the database engine's comparison and type rules.

---

## 7. NULL Semantics

`NULL` represents the absence of a known value.

It does not mean:

- zero
- false
- an empty string
- an ordinary missing text value
- a known value that happens to be zero

SQL uses three-valued logic involving:

- `TRUE`
- `FALSE`
- `UNKNOWN`

This is particularly important when filtering data.

### 7.1 Testing for NULL

Use:

`WHERE salary IS NULL`

or:

`WHERE salary IS NOT NULL`

Do not use:

`WHERE salary = NULL`

The latter does not correctly test for SQL `NULL`.

---

## 8. COALESCE

`COALESCE` returns the first non-`NULL` expression.

A common pattern is:

`COALESCE(bonus, 0)`

This means:

- use `bonus` when it exists
- otherwise use zero

For an order discount:

`COALESCE(discount, 0)`

can mean that a missing discount should be treated as no discount.

This is a business rule and should only be used when that interpretation is valid.

For example:

`SUM(quantity * unit_price * (1 - COALESCE(discount, 0)))`

calculates net revenue while treating a missing discount as zero.

---

## 9. NULLIF

`NULLIF(a, b)` returns:

- `NULL` when `a = b`
- otherwise `a`

A common use is protecting against division by zero.

Example:

`successes / NULLIF(attempts, 0)`

If `attempts` is zero, `NULLIF` produces `NULL`, preventing a division-by-zero operation.

This pattern is particularly useful for rates and ratios.

---

## 10. Aggregate Expressions

An aggregate expression contains a calculation that is evaluated for individual rows and then aggregated.

Example:

`SUM(quantity * unit_price)`

The conceptual process is:

1. Evaluate `quantity * unit_price` for each row.
2. Produce a value or `NULL`.
3. Apply `SUM` to those results.

A more complex example is:

`SUM(quantity * unit_price * (1 - COALESCE(discount, 0)))`

This combines:

- multiplication
- `COALESCE`
- subtraction
- aggregation

The Python, JavaScript, and C++ implementations all demonstrate this pattern.

---

## 11. GROUP BY

`GROUP BY` divides rows into groups.

Example:

`SELECT department, COUNT(*) FROM employees GROUP BY department;`

The database conceptually performs:

1. Read the input rows.
2. Determine each row's group key.
3. Place rows into groups.
4. Calculate the aggregate independently for each group.

For example:

| Department | Employee Count |
|---|---:|
| Engineering | 3 |
| HR | 2 |
| Research | 1 |
| Sales | 3 |

### 11.1 Multiple aggregates

A single grouped query can calculate several metrics:

`SELECT
    department,
    COUNT(*) AS employee_count,
    SUM(salary) AS salary_sum,
    AVG(salary) AS average_salary,
    MIN(salary) AS minimum_salary,
    MAX(salary) AS maximum_salary
 FROM employees
 GROUP BY department;`

Each aggregate operates over the rows belonging to its group.

---

## 12. WHERE Versus HAVING

`WHERE` filters rows before grouping.

`HAVING` filters groups after aggregation.

### WHERE

Example:

`WHERE status = 'completed'`

This removes individual rows before aggregation.

### HAVING

Example:

`HAVING SUM(revenue) > 100000`

This evaluates an aggregate result for each group.

The conceptual sequence is:

1. `FROM`
2. `WHERE`
3. `GROUP BY`
4. aggregate calculation
5. `HAVING`
6. `SELECT`
7. `ORDER BY`

The exact optimizer execution may differ internally, but this logical model is useful for understanding query semantics.

---

## 13. Conditional Aggregation

Conditional aggregation combines `CASE` with an aggregate.

Example:

`SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)`

This counts completed rows.

Other examples include:

`SUM(CASE WHEN salary >= 80000 THEN 1 ELSE 0 END)`

and:

`SUM(CASE WHEN salary IS NULL THEN 1 ELSE 0 END)`

Conditional aggregation is useful for dashboards because several business metrics can be calculated in one grouped query.

Example:

`SELECT
    department,
    SUM(CASE WHEN performance_score >= 90 THEN 1 ELSE 0 END)
        AS high_performers,
    SUM(CASE WHEN performance_score < 90 THEN 1 ELSE 0 END)
        AS below_90
 FROM employees
 GROUP BY department;`

---

## 14. DISTINCT and Aggregation

`DISTINCT` changes the set of values being considered.

Compare:

`COUNT(customer)`

with:

`COUNT(DISTINCT customer)`

The first counts non-`NULL` customer values.

The second counts unique non-`NULL` customer values.

This distinction is critical when a table contains multiple rows for the same customer.

The same principle applies to:

- accounts
- users
- products
- employees
- devices
- transactions
- sessions

The correct expression depends on the business question.

---

## 15. Empty-Set Behavior

An empty input is an important edge case.

For an empty input:

`COUNT(*)`

returns:

`0`

But these aggregates generally return `NULL`:

- `SUM`
- `AVG`
- `MIN`
- `MAX`

For example:

`SELECT SUM(salary)
 FROM employees
 WHERE 1 = 0;`

returns `NULL`.

If the application requires zero instead, an explicit expression can be used:

`COALESCE(SUM(salary), 0)`

This distinction prevents incorrect assumptions in reporting systems.

---

## 16. Python Implementation

The Python implementation uses the standard-library `sqlite3` module.

This is useful because it executes actual SQL rather than merely simulating SQL syntax.

The script creates an in-memory SQLite database containing:

- employees
- orders
- measurements
- employee-project relationships

It demonstrates:

- `COUNT(*)`
- `COUNT(column)`
- `COUNT(DISTINCT column)`
- `SUM`
- `AVG`
- `MIN`
- `MAX`
- `GROUP BY`
- `HAVING`
- `CASE`
- `COALESCE`
- `NULLIF`
- aggregate expressions
- empty-set behavior
- join multiplication
- query-plan inspection
- validation tests

### Python-specific educational value

Python makes it easy to execute a large collection of SQL examples and inspect their results.

The helper functions also demonstrate how a program can separate:

- database access
- query execution
- result display
- validation

The script intentionally uses an in-memory database, so it does not require an external database server or a persistent database file.

---

## 17. JavaScript Implementation

The JavaScript implementation does not require an external database package.

Instead, it models SQL aggregate semantics using:

- arrays
- objects
- `Map`
- `Set`
- functions
- filtering
- reduction
- optional-style `null` handling

Functions such as:

`sqlCountStar`

`sqlCountColumn`

`sqlCountDistinct`

`sqlSum`

`sqlAverage`

`sqlMin`

and:

`sqlMax`

represent the logical behavior of the corresponding SQL aggregates.

### Why this is useful

It exposes the algorithmic ideas behind aggregation.

For example, `SUM` can be understood as:

1. obtain the input expression for every row
2. remove `NULL` values
3. add the remaining values
4. return `NULL` if no usable value exists

Similarly, `AVG` requires both a sum and a count of non-`NULL` values.

### JavaScript-specific perspective

The implementation uses `Map` to model grouping.

It uses `Set` to model distinct-value tracking.

It uses `null` to represent missing data.

This makes the relationship between SQL aggregation and general-purpose data-processing algorithms explicit.

---

## 18. C++ Industry Case Study

The C++ implementation models an e-commerce analytics system.

Each order contains:

- order ID
- customer
- category
- quantity
- unit price
- discount
- status

The system produces operational and financial metrics.

### Problem being solved

The business needs to answer questions such as:

- How many orders exist?
- How many quantities are known?
- How many unique customers exist?
- What is total revenue?
- What is average order value?
- What are minimum and maximum prices?
- What is revenue by category?
- Which categories exceed a revenue threshold?
- How many orders are completed, pending, or cancelled?
- How should missing values be handled?

---

## 19. C++ Data Model

The `Order` structure represents one transactional row.

Fields that can be `NULL` are represented using:

`std::optional<T>`

For example:

`optional<int> quantity`

represents a quantity that may be unknown.

Similarly:

`optional<double> unitPrice`

represents a unit price that may be unknown.

This is a natural C++ representation of nullable database fields.

---

## 20. C++ Aggregation Functions

The program implements generic functions for:

- sum
- average
- minimum
- maximum

The functions accept vectors of optional values.

For example, `sumOptional` ignores empty `std::optional` values.

This corresponds to SQL's handling of `NULL` in ordinary aggregate functions.

The functions also return `std::optional<T>`.

That allows the implementation to distinguish:

- zero
- a real numeric result
- no non-`NULL` values

This is an important modeling decision.

---

## 21. C++ GROUP BY Design

The program represents `GROUP BY category` with:

`std::map<string, vector<Order>>`

The process is:

1. Read each order.
2. Extract its category.
3. Insert the order into the corresponding group.
4. Calculate aggregates for each group.
5. Produce a category report.

This closely models the conceptual behavior of SQL `GROUP BY`.

---

## 22. Category Report

The C++ case study calculates:

- order count
- known quantity count
- total units
- average quantity
- minimum quantity
- maximum quantity
- gross revenue
- net revenue

The resulting structure is represented by `CategoryReport`.

This separates raw transaction data from derived analytical results.

---

## 23. HAVING-Style Filtering

The C++ program includes a post-group filtering stage.

This represents a query such as:

`SELECT
    category,
    SUM(...)
 FROM orders
 GROUP BY category
 HAVING SUM(...) >= 100000;`

The important conceptual distinction is:

- row filtering occurs before grouping
- group filtering occurs after aggregation

This is why `WHERE` and `HAVING` should not be treated as interchangeable.

---

## 24. Conditional Aggregation in the C++ Case Study

The program counts:

- completed orders
- pending orders
- cancelled orders
- orders with missing quantity

This corresponds conceptually to SQL expressions such as:

`SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)`

Conditional aggregation is especially useful for KPI systems.

---

## 25. Join Multiplication

One of the most important production risks is accidental row multiplication.

Suppose an order has two associated tags.

A one-to-many join can produce two joined rows for that one order.

Then:

`COUNT(*)`

counts the joined rows.

It does not necessarily count the original orders.

Similarly:

`SUM(order_amount)`

can count the same order amount multiple times.

When the question concerns unique orders, a common solution is:

`COUNT(DISTINCT order_id)`

The C++ case study explicitly demonstrates this issue.

---

## 26. Aggregate Expressions and NULL

Consider:

`quantity * unit_price`

If either value is `NULL`, the SQL expression result is `NULL`.

This means the expression does not contribute a numeric value to `SUM`.

For a discount calculation:

`quantity * unit_price * (1 - COALESCE(discount, 0))`

the discount is deliberately normalized.

The business meaning is:

- known discount: use it
- missing discount: treat it as zero

This is appropriate only if missing discount means no discount.

---

## 27. Safe Ratios

Metrics such as conversion rate, success rate, and defect rate often involve division.

A dangerous expression is:

`successes / attempts`

when `attempts` can be zero.

A safer SQL pattern is:

`SUM(successes) / NULLIF(SUM(attempts), 0)`

If the denominator is zero, the result becomes `NULL`.

The application can then decide how to display or interpret the missing rate.

---

## 28. Important Distinctions

### COUNT(*) versus COUNT(column)

`COUNT(*)` counts rows.

`COUNT(column)` counts non-`NULL` values.

### COUNT(column) versus COUNT(DISTINCT column)

`COUNT(column)` counts all non-`NULL` values.

`COUNT(DISTINCT column)` counts unique non-`NULL` values.

### SUM versus COUNT

`SUM` measures accumulated numeric value.

`COUNT` measures the number of qualifying values or rows.

### AVG versus SUM / COUNT(*)

`AVG(column)` ignores `NULL` values.

`SUM(column) / COUNT(*)` does not necessarily have the same meaning.

### WHERE versus HAVING

`WHERE` filters rows.

`HAVING` filters groups.

### NULL versus zero

`NULL` means no known value.

Zero is a known numeric value.

These must not be substituted for one another without a deliberate business rule.

---

## 29. Common Mistakes

### Mistake 1: Using `COUNT(*)` when counting known values

If the column can be `NULL`, `COUNT(*)` does not measure column completeness.

Use:

`COUNT(column)`

when the question concerns known values.

### Mistake 2: Using `= NULL`

Incorrect:

`WHERE salary = NULL`

Correct:

`WHERE salary IS NULL`

### Mistake 3: Treating NULL as zero automatically

`COALESCE` is useful, but it changes semantics.

Do not use it merely because `NULL` looks inconvenient.

### Mistake 4: Dividing by COUNT(*)

When NULL values exist, `COUNT(*)` can produce a denominator that does not match the number of known values.

### Mistake 5: Ignoring join multiplication

A join can duplicate rows before aggregation.

Always establish the intended grain of the result.

### Mistake 6: Using HAVING for ordinary row filtering

If a condition concerns individual rows, `WHERE` is normally the appropriate mechanism.

### Mistake 7: Ignoring empty inputs

`SUM`, `AVG`, `MIN`, and `MAX` can return `NULL` when no input value exists.

### Mistake 8: Assuming missing data has a business meaning without verification

A missing discount might mean:

- no discount
- unknown discount
- data-entry failure
- not applicable

The correct treatment depends on the data model.

---

## 30. Edge Cases

Important aggregate edge cases include:

1. An entirely empty input.
2. A column containing only `NULL`.
3. A mixture of `NULL` and numeric values.
4. Duplicate values.
5. Duplicate entities.
6. Zero denominators.
7. Negative numeric values.
8. Large numeric values.
9. One-to-many joins.
10. Groups containing no usable numeric values.
11. Missing values in aggregate expressions.
12. Conditional aggregates that match no rows.

Each should be explicitly tested when building production analytics.

---

## 31. Performance Considerations

For `n` rows, a simple aggregation such as `SUM`, `AVG`, `MIN`, or `MAX` generally requires a pass over the relevant input and has a basic algorithmic cost around `O(n)`.

`GROUP BY` can commonly be implemented with hashing or sorting.

A hash-based grouping strategy has expected time around `O(n)` under typical assumptions.

A sort-based grouping strategy commonly involves approximately `O(n log n)` sorting work.

`COUNT(DISTINCT value)` can require additional memory for tracking unique values or additional sorting work.

If a grouped result contains `k` groups and those groups are sorted, sorting the groups commonly costs approximately:

`O(k log k)`

Actual database performance depends on:

- database engine
- indexes
- query optimizer
- statistics
- data distribution
- available memory
- disk or storage performance
- parallel execution
- query shape
- table size

The Python implementation demonstrates query-plan inspection with SQLite.

---

## 32. Indexing Considerations

Indexes can improve filtering and joining.

Potentially useful columns include those frequently used in:

- `WHERE`
- `JOIN`
- grouping-related access patterns

Indexes are not automatically beneficial for every aggregation query.

They consume storage and can increase write costs.

The correct decision should be based on:

- actual workload
- query plans
- selectivity
- table size
- read/write balance

---

## 33. Financial Data Considerations

Financial aggregation requires special care.

Binary floating-point arithmetic may introduce representation differences.

For financial systems, the database and application architecture should use an appropriate exact numeric representation, such as a database decimal/numeric type, where required.

The examples use ordinary numeric values to keep the educational implementation simple.

The important conceptual lesson is that aggregate correctness includes both:

- SQL semantics
- numeric representation

---

## 34. Security Considerations

Aggregation itself is not inherently insecure, but production SQL code must still address security.

Important practices include:

- parameterized SQL
- avoiding string concatenation for user-supplied values
- appropriate database permissions
- least-privilege database accounts
- validation of input parameters
- controlled access to sensitive aggregate results
- auditing where required

For example, the Python examples use parameterized execution where parameters are needed rather than constructing SQL by concatenating untrusted input.

---

## 35. Debugging Aggregation Queries

When an aggregate result looks suspicious, inspect the data in stages.

A practical debugging sequence is:

1. Inspect the raw rows.
2. Apply the `WHERE` condition.
3. Count rows after filtering.
4. Inspect nullable columns.
5. Calculate row-level expressions separately.
6. Group the rows.
7. Inspect group sizes.
8. Apply aggregates.
9. Check whether a join multiplied rows.
10. Apply `HAVING`.
11. Compare against an independently calculated result.

For example, before trusting:

`SUM(quantity * unit_price)`

inspect:

`quantity`

`unit_price`

and:

`quantity * unit_price`

for each row.

This exposes `NULL` propagation and unexpected values.

---

## 36. Python, JavaScript, and C++ Comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| SQL execution | Actual SQLite queries | SQL semantics modeled directly | SQL semantics modeled directly |
| NULL representation | SQLite `NULL` and Python `None` | `null` | `std::optional` |
| Grouping | SQL `GROUP BY` | `Map` | `std::map` |
| Distinct values | SQL `DISTINCT` | `Set` | `std::set` |
| Aggregation | SQLite engine | Explicit algorithms | Explicit algorithms |
| Validation | Python assertions/tests | JavaScript tests | C++ assertions |
| Primary strength | Direct SQL experimentation | Algorithmic and application perspective | Systems-oriented case study |
| External dependency | None beyond standard library | None | None |

Each implementation emphasizes a different layer of understanding.

---

## 37. Practical Applications

SQL aggregation is fundamental to:

- business intelligence
- data analytics
- financial reporting
- sales dashboards
- customer analytics
- product analytics
- inventory management
- operational monitoring
- performance reporting
- fraud analysis
- application metrics
- data quality measurement
- scientific data analysis
- database administration

Typical production metrics include:

`COUNT(*)`

`COUNT(DISTINCT user_id)`

`SUM(revenue)`

`AVG(order_value)`

`MIN(transaction_time)`

`MAX(transaction_time)`

and conditional expressions such as:

`SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)`

---

## 38. Conceptual Workflow for Aggregation

A reliable way to reason about an aggregate query is:

1. Define the unit represented by each source row.
2. Identify the population being analyzed.
3. Decide which rows should be filtered.
4. Decide which columns can be `NULL`.
5. Define the meaning of `NULL`.
6. Determine whether the metric counts rows or distinct entities.
7. Define any row-level expression.
8. Decide whether grouping is required.
9. Choose the aggregate function.
10. Decide whether groups need filtering.
11. Test empty and NULL-heavy cases.
12. Test duplicates and joins.
13. Validate the result against known examples.
14. Examine performance for realistic data volumes.

This process reduces both semantic and technical errors.

---

## 39. Core SQL Patterns Demonstrated

Basic aggregate:

`SELECT COUNT(*), SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM transactions;`

Grouped aggregate:

`SELECT category, SUM(amount) FROM transactions GROUP BY category;`

Distinct count:

`SELECT COUNT(DISTINCT customer_id) FROM orders;`

Conditional count:

`SELECT SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) FROM orders;`

NULL-safe expression:

`SUM(amount * COALESCE(discount_factor, 1))`

Safe ratio:

`SUM(successful) / NULLIF(SUM(attempts), 0)`

Group filtering:

`GROUP BY category HAVING SUM(amount) > 100000`

Missing-value count:

`COUNT(*) - COUNT(amount)`

These patterns cover a substantial portion of practical aggregation work.

---

## 40. Implementation Correspondence

The Python implementation directly executes these concepts using SQLite.

The JavaScript implementation makes the aggregation algorithms explicit, which helps expose what the database engine is conceptually doing.

The C++ implementation turns the same ideas into a structured analytics system with explicit data modeling, grouping, nullable values, reporting objects, validation, complexity discussion, and join-multiplication analysis.

The three implementations therefore address different layers of the same topic:

- SQL execution
- algorithmic aggregation
- production-oriented system design
