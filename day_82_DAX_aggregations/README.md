
# DAX Aggregations: SUM, AVERAGE, COUNT, DISTINCTCOUNT, CALCULATE and FILTER

## 1. Analytical Foundation

Data Analysis Expressions (DAX) is a formula language used in Power BI, Analysis Services, and Power Pivot. It supports analytical calculations over tabular data models.

DAX aggregations operate on columns and evaluate expressions within an analytical context. Their results depend not only on the stored data but also on the filters active when a measure is evaluated.

This implementation examines six important DAX functions:

| Function | Primary purpose |
|---|---|
| `SUM` | Adds numeric values in a column |
| `AVERAGE` | Calculates the arithmetic mean of numeric values |
| `COUNT` | Counts nonblank numeric values |
| `DISTINCTCOUNT` | Counts unique values, including BLANK |
| `CALCULATE` | Evaluates an expression under a modified filter context |
| `FILTER` | Returns rows satisfying a specified condition |

The implementations use a retail transaction dataset containing customers, products, categories, regions, quantities, revenue, order dates, and transaction statuses.

The central analytical distinction is between the underlying transaction data and the context in which a measure is evaluated.

## 2. Analytical Data Model

The example represents a retail organization with multiple products and customers operating across four regions.

### Transaction structure

| Attribute | Description |
|---|---|
| Transaction ID | Unique transaction identifier |
| Order Date | Date of the transaction |
| Customer ID | Customer associated with the transaction |
| Product ID | Product associated with the transaction |
| Region | Geographic sales region |
| Category | Product category |
| Quantity | Number of units sold |
| Unit Price | Price per unit |
| Revenue | Recorded transaction revenue |
| Status | Completed, Pending, or Cancelled |

The dataset contains ten transactions, including a transaction with missing customer and revenue values.

The missing values are intentional. They demonstrate the difference between row counts, nonblank counts, and distinct counts.

### Domain relationships

```text
Customers
    |
    | Customer ID
    |
Sales Transactions
    |
    | Product ID
    |
Products

Sales Transactions
    |
    +---- Order Date
    |
    +---- Region
    |
    +---- Category
    |
    +---- Status
    |
    +---- Quantity
    |
    +---- Revenue
```

The PostgreSQL implementation uses separate customer and product tables with foreign-key relationships. The Python, JavaScript, C++, and Java implementations use transaction records containing the attributes required for analytical calculations.

## 3. SUM

`SUM` adds all nonblank numeric values in a specified column.

DAX expression:

`Total Revenue = SUM(Sales[Revenue])`

Mathematically:

\[
\text{Total Revenue}=\sum_{i=1}^{n}R_i
\]

Where:

- \(R_i\) represents the revenue of transaction \(i\).
- \(n\) represents the number of transactions containing nonblank revenue.

For the sample dataset:

\[
\begin{aligned}
\text{Total Revenue}={}&1000+800+600+700+500\\
&+1200+600+900+300
\end{aligned}
\]

\[
\boxed{\text{Total Revenue}=6600}
\]

The transaction containing blank revenue does not contribute to the result.

### Important behavior

- `SUM` ignores BLANK values.
- A numeric column is required.
- The result changes when the filter context changes.
- A measure using `SUM` is recalculated when report filters or slicers change.

In DAX, `SUM` is appropriate for additive business measures such as revenue, sales quantity, expenditure, and transaction amounts.

### Implementation comparison

| Language | Mechanism |
|---|---|
| Python | Decimal accumulation |
| JavaScript | Numeric reduction |
| C++17 | Iterative accumulation |
| Java 17 | BigDecimal reduction |
| PostgreSQL | `SUM()` aggregate |

The Python and Java implementations use decimal arithmetic for financial values to reduce binary floating-point precision problems.

The C++ and JavaScript implementations use floating-point numeric values for the demonstration.

## 4. AVERAGE

`AVERAGE` calculates the arithmetic mean of nonblank numeric values.

DAX expression:

`Average Revenue = AVERAGE(Sales[Revenue])`

Mathematical representation:

\[
\text{Average Revenue}=
\frac{\sum_{i=1}^{n}R_i}{n}
\]

For the sample dataset:

\[
\text{Average Revenue}=\frac{6600}{9}
\]

\[
\boxed{\text{Average Revenue}=733.3333\ldots}
\]

The denominator is nine rather than ten because one transaction has blank revenue.

### Important distinctions

`AVERAGE` is not equivalent to dividing total revenue by the total number of transaction rows when some revenue values are blank.

For example:

\[
\frac{6600}{10}=660
\]

This is not the correct result for the sample dataset's nonblank revenue values.

The correct calculation is:

\[
\frac{6600}{9}=733.3333\ldots
\]

### Empty data behavior

When the current filter context contains no nonblank numeric values, DAX `AVERAGE` returns BLANK.

The implementations represent this state differently:

- Python: `None`
- JavaScript: `null`
- C++17: `std::nullopt`
- Java 17: `null`
- PostgreSQL: `NULL`

This distinction is important because zero and BLANK have different analytical meanings.

Zero represents a numeric value. BLANK represents the absence of a usable value.

## 5. COUNT

`COUNT` counts nonblank values in a numeric column.

DAX expression:

`Revenue Count = COUNT(Sales[Revenue])`

For the sample dataset:

\[
\boxed{\text{COUNT(Revenue)}=9}
\]

### COUNT versus COUNTROWS

These functions have different purposes.

| Function | What it counts |
|---|---|
| `COUNT(Column)` | Nonblank numeric values |
| `COUNTROWS(Table)` | Rows in a table |
| `COUNTA(Column)` | Nonblank values, including text |
| `DISTINCTCOUNT(Column)` | Unique values, including BLANK |

For ten transaction rows:

- `COUNTROWS(Sales)` returns 10.
- `COUNT(Sales[Revenue])` returns 9.
- `COUNT(Sales[Quantity])` returns 9.

A common analytical error is using `COUNT` when the requirement is to count transaction records.

### Practical applications

- Counting recorded sales values.
- Checking the completeness of numeric measurements.
- Comparing transaction volume with populated financial records.
- Identifying differences between row availability and data availability.

## 6. DISTINCTCOUNT

`DISTINCTCOUNT` returns the number of unique values in a column.

DAX expression:

`Unique Customers = DISTINCTCOUNT(Sales[CustomerID])`

The sample contains the following customer identifiers:

`101, 102, 101, 103, 104, 102, 105, 103, BLANK, 106`

The unique values are:

`101, 102, 103, 104, 105, 106, BLANK`

Therefore:

\[
\boxed{\text{DISTINCTCOUNT(CustomerID)}=7}
\]

### BLANK handling

A critical distinction exists between DAX and PostgreSQL.

DAX `DISTINCTCOUNT` includes BLANK as a distinct value when one exists.

PostgreSQL `COUNT(DISTINCT customer_id)` excludes NULL.

Consequently, the SQL implementation explicitly adds one when at least one NULL customer identifier exists.

| Database expression | Result |
|---|---|
| `COUNT(DISTINCT customer_id)` | 6 |
| DAX-equivalent distinct count | 7 |

If the dataset contains no blank customer identifiers, both results are six.

### Practical applications

- Unique customer measurement.
- Distinct product counts.
- Unique account analysis.
- Customer acquisition reporting.
- Geographic customer distribution.

### Performance considerations

Distinct counting requires identifying unique values.

For small datasets, an in-memory set is sufficient.

For large analytical models, cardinality, column encoding, data distribution, and storage-engine optimization influence query performance.

## 7. Filter Context

Filter context determines which rows are visible to an expression during evaluation.

A filter can originate from:

- Report-level filters.
- Page-level filters.
- Visual-level filters.
- Slicers.
- Relationships between tables.
- Filter arguments supplied to `CALCULATE`.

For example, a report might contain a regional slicer selecting North.

The revenue measure is then evaluated using only transactions visible under that selection.

DAX measure:

`North Revenue = SUM(Sales[Revenue])`

With the North region filter:

\[
1000+600+600+300=2500
\]

\[
\boxed{\text{North Revenue}=2500}
\]

The underlying transaction table remains unchanged.

Only the evaluation context changes.

### Multiple filters

Multiple independent filter conditions normally operate together using AND semantics.

Example:

`North Electronics Revenue`

Conditions:

- Region equals North.
- Category equals Electronics.
- Status equals Completed.

The qualifying transactions are 1001, 1003, and 1010.

Therefore:

\[
1000+600+300=1900
\]

This is different from calculating North revenue across every category and transaction status.

## 8. FILTER

`FILTER` evaluates a table and returns the rows satisfying a specified Boolean condition.

DAX expression:

`High Value Sales = FILTER(Sales, Sales[Revenue] >= 800)`

This returns transactions meeting the minimum revenue threshold.

The sample qualifying transactions are:

| Transaction ID | Region | Revenue |
|---|---|---|
| 1001 | North | 1000 |
| 1002 | South | 800 |
| 1006 | South | 1200 |
| 1008 | East | 900 |

### FILTER mechanics

Conceptually:

1. Receive a table.
2. Evaluate the specified condition for each row.
3. Retain rows for which the condition evaluates to TRUE.
4. Return the resulting table.

BLANK revenue does not satisfy the specified numeric comparison.

### FILTER and CALCULATE

These functions perform different operations.

`FILTER` produces a filtered table.

`CALCULATE` evaluates an expression under a modified filter context.

For example:

`CALCULATE(SUM(Sales[Revenue]), FILTER(Sales, Sales[Revenue] >= 800))`

The expression calculates revenue using the filtered transaction set.

### Performance considerations

A Boolean filter argument in `CALCULATE` is often preferable for straightforward column conditions.

`FILTER` is useful when the filtering requirement needs a table expression, complex row-level conditions, or logic that cannot be expressed conveniently as a simple Boolean filter argument.

Unnecessarily iterating large tables can increase evaluation cost.

## 9. CALCULATE

`CALCULATE` is one of the most important DAX functions because it evaluates an expression after modifying filter context.

General syntax:

`CALCULATE(Expression, Filter1, Filter2, ...)`

The expression is evaluated under the resulting context.

Example:

`South Revenue = CALCULATE(SUM(Sales[Revenue]), Sales[Region] = "South")`

The calculation returns:

\[
800+1200=2000
\]

### Existing filter replacement

One important feature of `CALCULATE` is its handling of filters on the same column.

Consider an existing North region filter.

The following expression applies a South region filter:

`CALCULATE([Total Revenue], Sales[Region] = "South")`

Under ordinary Boolean filter semantics, the new filter replaces the existing filter on the same column.

The resulting revenue is:

\[
2000
\]

It does not return zero merely because the previous context selected North.

### Filter preservation

When a filter is added on another column, existing filters remain active.

Example:

`CALCULATE([Total Revenue], Sales[Category] = "Electronics")`

If the original context already selects North, the calculation evaluates North electronics revenue.

\[
\boxed{1900}
\]

### Filter modification distinctions

| Situation | Behavior |
|---|---|
| New filter on an unfiltered column | Adds a filter |
| New filter on an already filtered column | Normally replaces that column's filter |
| `KEEPFILTERS` | Intersects the new filter with the existing filter |
| `REMOVEFILTERS` | Removes applicable filters |
| `ALL` | Returns a table or removes filters depending on usage |
| `ALLEXCEPT` | Removes filters except those specified |

The implementations model ordinary filter addition and replacement explicitly.

They do not attempt to reproduce every DAX context-modification function.

### CALCULATE and context transition

DAX also supports row context.

When `CALCULATE` executes inside a row context, it can perform context transition, converting the current row context into filter context.

This behavior is important in calculated columns and iterator-based expressions.

The five implementations focus on filter-context evaluation rather than reproducing the complete DAX evaluation engine.

## 10. Filter Context and Row Context

These are separate concepts in DAX.

| Context | Meaning |
|---|---|
| Filter context | Determines which model rows are visible |
| Row context | Identifies the current row during row-by-row evaluation |

A measure normally evaluates under filter context.

An iterator such as `SUMX` introduces row context while evaluating an expression for each row.

`CALCULATE` can transition row context into filter context.

This distinction becomes important when moving beyond simple column aggregations.

The provided programs implement an explicit filter-context abstraction. They do not implement a complete row-context and context-transition engine.

## 11. Python Implementation

File: `dax_aggregations.py`

The Python implementation provides an object-oriented simulation of DAX analytical operations.

### Main components

| Component | Responsibility |
|---|---|
| `SalesRecord` | Immutable transaction representation |
| `FilterCondition` | Represents a filter predicate |
| `FilterContext` | Maintains active conditions |
| `SalesModel` | Executes aggregations and filtering |
| `FilterOperator` | Defines supported comparison operations |
| Custom exceptions | Report invalid columns and operations |

### Technical mechanisms

- Dataclasses model transaction records.
- Enums prevent inconsistent filter operator values.
- Decimal arithmetic supports financial calculations.
- Dictionaries support regional aggregation.
- Sets support distinct counting.
- Exceptions identify invalid operations.
- Assertions verify known analytical results.

The `calculate` method evaluates an expression under a modified context.

Its `replace_columns` argument models the replacement of ordinary filters on specified columns.

The implementation is designed for an in-memory dataset. It is not a replacement for the VertiPaq storage engine or the complete DAX formula engine.

## 12. JavaScript Implementation

File: `dax_aggregations.js`

The JavaScript implementation provides an event-driven analytical engine.

### Main components

| Component | Responsibility |
|---|---|
| `AnalyticsEngine` | Executes analytical operations |
| `Filter` | Represents a typed filter |
| `FilterContext` | Maintains immutable filtering conditions |
| `OPERATORS` | Defines supported comparisons |
| `COLUMN_TYPES` | Validates model columns |
| `EventEmitter` | Reports query success and failure |

### Technical mechanisms

The implementation uses:

- JavaScript classes.
- Immutable objects.
- `Map` for grouped analytical results.
- `Set` for unique values and replacement-column tracking.
- `Array.filter()` for row selection.
- `Array.reduce()` for summation.
- Promises for asynchronous query orchestration.
- Event listeners for query monitoring.

The `query` method creates an asynchronous execution boundary and publishes completion or failure events.

This is useful for understanding how analytical services can integrate with applications that schedule queries and monitor execution.

The asynchronous interface does not imply that its in-memory aggregation is automatically parallelized.

## 13. C++17 Implementation

File: `dax_aggregations.cpp`

The C++ implementation models analytical operations through strongly typed structures and explicit evaluation logic.

### Main components

| Component | Responsibility |
|---|---|
| `Transaction` | Represents a sales transaction |
| `Filter` | Represents a column comparison |
| `FilterContext` | Maintains analytical filters |
| `SalesAnalytics` | Executes calculations |
| `Region` | Defines regional values |
| `Category` | Defines product categories |
| `Status` | Defines transaction states |
| `Operator` | Defines comparison operations |

### Technical mechanisms

- `std::vector` stores transaction records.
- `std::optional` represents missing revenue.
- `std::set` supports distinct-value calculations.
- `std::map` supports grouped reporting.
- `std::unordered_set` checks duplicate transaction identifiers.
- Templates allow `calculate` to evaluate different expression return types.
- Exceptions handle invalid analytical operations.

The implementation explicitly separates transaction storage from filter evaluation.

This makes the relationship between source data, active filters, and aggregation results visible.

Its implementation uses linear scans for filtering. For large datasets, indexes, precomputed aggregates, or column-oriented storage would be necessary to improve performance.

## 14. Java 17 Implementation

File: `DaxAggregations.java`

The Java implementation emphasizes enterprise-oriented analytical service design.

### Main components

| Component | Responsibility |
|---|---|
| `Transaction` record | Immutable transaction domain object |
| `Filter` record | Typed filter definition |
| `FilterContext` | Immutable analytical context |
| `AnalyticsService` | Aggregation and evaluation service |
| `Measure` interface | Reusable analytical expression |
| `SalesMeasures` | Named business measures |
| Domain enums | Controlled categories, statuses, and operators |

### Technical mechanisms

Java 17 provides records for concise immutable domain types.

The implementation also uses:

- Enums for strongly typed dimensions.
- `BigDecimal` for financial calculations.
- Streams for filtering and aggregation.
- Collections for distinct values.
- Generic expression evaluation.
- Functional interfaces for reusable measures.
- Custom exceptions for business validation.

### Reusable measures

The `SalesMeasures` class demonstrates how business calculations can be represented as reusable measure objects.

Three measures are defined:

- Total revenue.
- Average revenue.
- Completed revenue.

The completed revenue measure applies an additional status filter without changing the underlying dataset.

This separation supports the design of reusable enterprise reporting services.

## 15. PostgreSQL Implementation

File: `dax_aggregations.sql`

The PostgreSQL implementation translates the analytical concepts into relational database operations.

### Database architecture

| Object | Purpose |
|---|---|
| `customers` | Customer dimension |
| `products` | Product dimension |
| `sales_transactions` | Transaction fact table |
| `dax_sum_revenue` | Revenue aggregation function |
| `dax_average_revenue` | Average revenue function |
| `dax_count_revenue` | Nonblank revenue count |
| `dax_distinct_customer_count` | Distinct customer calculation |
| `dax_filter_transactions` | Filtered transaction retrieval |
| `dax_calculate_revenue` | Modified-context revenue calculation |
| `v_sales_analytical_detail` | Joined analytical detail |
| `v_regional_sales_summary` | Regional aggregation |
| `v_category_sales_summary` | Category aggregation |
| `dax_validation_report` | Analytical validation |

### Relational integrity

The schema includes:

- Primary keys.
- Foreign keys.
- Unique product names.
- Numeric range constraints.
- Controlled transaction statuses.
- Indexes for frequently filtered attributes.

These constraints prevent invalid data from entering the analytical model through ordinary database operations.

### Aggregation functions

PostgreSQL directly supports:

- `SUM()`
- `AVG()`
- `COUNT()`
- `COUNT(DISTINCT ...)`

The implementation adds a specific adjustment for DAX-style distinct counting.

### CALCULATE equivalent

The `dax_calculate_revenue` function accepts:

- An existing region.
- A replacement region.
- A product category.
- A transaction status.

It resolves the effective region before evaluating the aggregation.

This demonstrates ordinary filter replacement and preservation.

It is a controlled relational equivalent, not a full implementation of DAX filter propagation.

### FILTER equivalent

The `dax_filter_transactions` function returns rows meeting the specified revenue threshold, region, and transaction status.

The returned result is a table rather than a single scalar measure.

### Query optimization

The SQL implementation includes indexes on:

- Order date.
- Region.
- Product.
- Customer.
- Transaction status.
- Nonblank revenue.

A partial index supports completed transactions.

The `EXPLAIN (ANALYZE, BUFFERS)` query demonstrates how to inspect actual query execution.

An index is not guaranteed to improve every aggregation. PostgreSQL selects execution plans based on statistics, table size, selectivity, and estimated costs.

## 16. Cross-Language Analytical Results

All five implementations use the same ten-transaction business scenario.

| Calculation | Expected result |
|---|---|
| Total revenue | 6,600 |
| Average nonblank revenue | 733.3333... |
| Nonblank revenue count | 9 |
| Distinct customers including BLANK | 7 |
| North revenue | 2,500 |
| South revenue | 2,000 |
| North electronics revenue | 1,900 |
| North completed electronics revenue | 1,900 |
| Completed revenue | 4,400 |
| Empty-filter SUM | 0 |
| Empty-filter AVERAGE | BLANK |
| Empty-filter COUNT | 0 |
| Empty-filter DISTINCTCOUNT | 0 |

The implementations use language-specific representations of missing values.

| Language | Representation |
|---|---|
| Python | `None` |
| JavaScript | `null` |
| C++17 | `std::nullopt` |
| Java 17 | `null` |
| PostgreSQL | `NULL` |

These representations must not be confused with numeric zero.

## 17. Important Differences Between DAX and SQL

DAX and SQL support many equivalent aggregation operations, but they do not use identical evaluation models.

| Feature | DAX | PostgreSQL |
|---|---|---|
| SUM | `SUM(Column)` | `SUM(column)` |
| AVERAGE | `AVERAGE(Column)` | `AVG(column)` |
| COUNT | `COUNT(Column)` | `COUNT(column)` |
| Distinct count | `DISTINCTCOUNT(Column)` | `COUNT(DISTINCT column)` |
| Filtered rows | `FILTER(Table, Condition)` | `WHERE Condition` |
| Context modification | `CALCULATE()` | Explicit query predicates or functions |
| Blank representation | BLANK | NULL |
| Relationship propagation | Tabular model relationships | Explicit joins and relational constraints |

### Critical differences

**Filter context**

DAX measures automatically respond to the active filter context of a tabular model.

SQL queries generally require the developer to express the required filters explicitly.

**Relationships**

DAX can propagate filters through configured model relationships.

PostgreSQL requires joins, views, subqueries, or other relational operations to retrieve related data.

**Distinct counting**

DAX `DISTINCTCOUNT` includes BLANK.

PostgreSQL `COUNT(DISTINCT column)` excludes NULL.

**Empty aggregation**

PostgreSQL `SUM` returns NULL for an empty input set. DAX `SUM` returns BLANK when there are no applicable values. The Python, JavaScript, and C++ examples use zero for empty SUM results, while the SQL DAX-style function explicitly uses `COALESCE` to produce zero. This is a deliberate implementation convention and should not be confused with the distinction between zero and BLANK in DAX.

**Context transition**

DAX supports context transition through `CALCULATE` when row context is present.

The relational SQL implementation does not reproduce this behavior automatically.

## 18. Edge Cases and Validation

Reliable analytical calculations require explicit handling of incomplete and inconsistent data.

The implementations address the following cases.

| Condition | Expected handling |
|---|---|
| Missing revenue | Excluded from SUM and AVERAGE |
| Missing numeric value | Excluded from COUNT |
| Missing customer ID | Included as BLANK in DAX DISTINCTCOUNT |
| No matching records | Empty aggregation result |
| Unknown column | Validation error |
| Text column passed to SUM | Aggregation error |
| Negative revenue | Rejected during data validation |
| Duplicate transaction ID | Rejected |
| Invalid filter operator | Validation error |
| Conflicting filters | Evaluated using the active context rules |
| Missing customer relationship | Allowed only where the transaction model permits it |

The PostgreSQL implementation additionally uses foreign keys and check constraints to protect relational integrity.

## 19. Performance and Scalability

### In-memory processing

The Python, JavaScript, C++17, and Java 17 implementations use in-memory records.

For \(n\) transactions:

| Operation | Typical time complexity |
|---|---|
| SUM | \(O(n)\) |
| AVERAGE | \(O(n)\) |
| COUNT | \(O(n)\) |
| DISTINCTCOUNT | \(O(n)\) expected with hash sets |
| FILTER | \(O(n)\) |
| CALCULATE | \(O(n)\) per complete evaluation |
| GROUP BY | \(O(n)\) expected with hash-based grouping |

Repeated calculations can scan the same records multiple times.

For production systems, useful optimizations include:

- Reusing filtered intermediate results.
- Maintaining appropriate indexes.
- Using column-oriented storage.
- Precomputing frequently requested aggregations.
- Avoiding unnecessary high-cardinality distinct calculations.
- Applying selective filters early.
- Monitoring memory consumption.
- Using database query plans to identify expensive operations.

### Financial precision

Financial reporting requires deliberate numeric-type selection.

Python `Decimal`, Java `BigDecimal`, and PostgreSQL `NUMERIC` provide decimal arithmetic.

JavaScript `Number` and C++ `double` use binary floating-point representations and can introduce rounding differences.

For financial systems using these languages, decimal arithmetic or integer minor currency units should be considered.

## 20. Practical DAX Measure Design

The following expressions illustrate the six functions in a Power BI model.

| Business requirement | DAX expression |
|---|---|
| Total revenue | `Total Revenue = SUM(Sales[Revenue])` |
| Average revenue | `Average Revenue = AVERAGE(Sales[Revenue])` |
| Recorded revenue values | `Revenue Count = COUNT(Sales[Revenue])` |
| Unique customers | `Unique Customers = DISTINCTCOUNT(Sales[CustomerID])` |
| Completed revenue | `Completed Revenue = CALCULATE([Total Revenue], Sales[Status] = "Completed")` |
| High-value transactions | `High Value Sales = FILTER(Sales, Sales[Revenue] >= 800)` |
| South revenue | `South Revenue = CALCULATE([Total Revenue], Sales[Region] = "South")` |
| North electronics revenue | `North Electronics = CALCULATE([Total Revenue], Sales[Region] = "North", Sales[Category] = "Electronics")` |

These expressions are DAX examples for a model containing a `Sales` table and the specified columns. The executable source files implement corresponding analytical behavior using their respective language and database capabilities.

## 21. Limitations of the Implementations

The five implementations intentionally focus on foundational aggregation and filter-context behavior.

They do not implement the complete DAX language or Power BI tabular engine.

Important excluded capabilities include:

- `SUMX` and other iterator functions.
- Full row-context evaluation.
- Complete context transition.
- `ALL`, `ALLEXCEPT`, and `ALLSELECTED`.
- `KEEPFILTERS` and `REMOVEFILTERS`.
- Bidirectional relationship propagation.
- Inactive relationship activation.
- Calculation groups.
- Time-intelligence functions.
- Query-plan generation by the VertiPaq engine.
- Storage-engine and formula-engine coordination.
- DirectQuery execution semantics.
- RLS and OLS security evaluation.

The filter-context simulations also use simplified equality and comparison rules. They do not reproduce every aspect of DAX data lineage, relationship propagation, blank-row behavior, or type coercion.

These limitations matter when using the implementations as reference models for actual Power BI calculations.

## 22. Core Conceptual Distinctions

The six functions have different responsibilities.

| Function | Main responsibility | Output |
|---|---|---|
| SUM | Numerical aggregation | Scalar |
| AVERAGE | Mean calculation | Scalar |
| COUNT | Nonblank numeric counting | Scalar |
| DISTINCTCOUNT | Unique-value counting | Scalar |
| FILTER | Row selection | Table |
| CALCULATE | Modified-context expression evaluation | Depends on expression |

Their relationship can be represented as:

```text
Underlying Data Model
        |
        v
Current Filter Context
        |
        +--------------------+
        |                    |
        v                    v
      FILTER             CALCULATE
        |                    |
        v                    v
  Filtered Table       Modified Context
                             |
                             v
                      Aggregation Expression
                             |
               +--------------+--------------+
               |              |              |
               v              v              v
              SUM          AVERAGE          COUNT
                                             |
                                             v
                                        DISTINCTCOUNT
```

The central principle is that aggregation functions calculate results from the values visible in the applicable context.

`FILTER` determines a row subset, while `CALCULATE` modifies the context under which an expression is evaluated.

Understanding this distinction is fundamental to designing correct DAX measures and interpreting analytical results.
